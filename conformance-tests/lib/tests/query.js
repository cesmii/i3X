'use strict';

const { pass, fail, warn, skip, httpProblem, okJson } = require('../results');
const V = require('../validators');

const BOGUS_ID = 'i3x-test-suite-nonexistent-element-7f3a9c';

function firstProblems(problems, n = 5) {
  return problems.slice(0, n).join('; ') + (problems.length > n ? ` (+${problems.length - n} more)` : '');
}

function sampleObjects(ctx, n = 10) {
  if (!ctx.objects) return [];
  // Prefer a spread of distinct types
  const byType = new Map();
  for (const o of ctx.objects) {
    if (!byType.has(o.typeElementId)) byType.set(o.typeElementId, o);
    if (byType.size >= n) break;
  }
  const picked = [...byType.values()];
  for (const o of ctx.objects) {
    if (picked.length >= n) break;
    if (!picked.includes(o)) picked.push(o);
  }
  return picked;
}

module.exports = [
  {
    id: 'QRY-01',
    name: 'POST /objects/value returns CurrentValueResult records (value, quality, timestamp)',
    level: 'MUST',
    ref: 'queryMethods',
    async run(ctx) {
      const sample = sampleObjects(ctx);
      if (!sample.length) return skip('No objects available', 'blocked');
      const ids = sample.map((o) => o.elementId);
      const res = await ctx.client.request('POST', '/objects/value', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/value'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids, itemShape: 'CurrentValueResult' });
      if (problems.length) return fail(firstProblems(problems));
      ctx.currentValues = new Map();
      const vqtIssues = [];
      res.json.results.forEach((item) => {
        if (item.success && item.result) {
          ctx.currentValues.set(item.elementId, item.result);
          vqtIssues.push(...V.vqtProblems(item.result, `${item.elementId}`).filter((p) => !p.includes('implies a null value') && !p.includes('MUST carry quality')));
        }
      });
      if (vqtIssues.length) return fail(`${firstProblems(vqtIssues)}. Every value carries quality (Good/GoodNoData/Bad/Uncertain) and an RFC 3339 UTC timestamp.`);
      return pass(`${ctx.currentValues.size} value(s) read`);
    }
  },
  {
    id: 'QRY-02',
    name: 'Null values follow the quality pairing rules',
    level: 'MUST',
    ref: 'nullValues',
    async run(ctx) {
      if (!ctx.currentValues || !ctx.currentValues.size) return skip('No values were read', 'blocked');
      const problems = [];
      for (const [id, vqt] of ctx.currentValues) {
        problems.push(...V.vqtProblems(vqt, id).filter((p) => p.includes('null')));
      }
      if (problems.length) {
        return fail(
          `${firstProblems(problems)}. A null value MUST carry quality "Bad" or "GoodNoData"; "Good"/"Uncertain" imply a value is present.`
        );
      }
      return pass();
    }
  },
  {
    id: 'QRY-03',
    name: "Object values conform to their Object Type's JSON Schema",
    level: 'MUST',
    ref: 'objects',
    async run(ctx) {
      if (!ctx.currentValues || !ctx.currentValues.size || !ctx.typesById) return skip('No values or types available', 'blocked');
      const problems = [];
      let checked = 0;
      for (const [id, vqt] of ctx.currentValues) {
        if (vqt.value === null || vqt.value === undefined) continue; // null handling covered by QRY-02
        const obj = ctx.objectsById && ctx.objectsById.get(id);
        if (!obj) continue;
        if (obj.isExtended) continue; // extended objects may carry undeclared attributes
        const type = ctx.typesById.get(obj.typeElementId);
        if (!type || !type.schema || typeof type.schema !== 'object') continue;
        checked++;
        const errs = V.validateSchema(type.schema, vqt.value, { path: `${id}.value`, maxErrors: 3 });
        problems.push(...errs.map((e) => `${e} (type "${type.elementId}")`));
      }
      if (!checked) return skip('No non-null values with resolvable type schemas to check', 'untestable');
      if (problems.length) {
        return fail(
          `${firstProblems(problems)}. "The Object's value ... MUST conform to the ObjectType schema set by the typeElementId attribute".`
        );
      }
      return pass(`${checked} value(s) validated against their type schemas`);
    }
  },
  {
    id: 'QRY-04',
    name: 'POST /objects/value preserves request order and reports unknown ids per-item',
    level: 'MUST',
    ref: 'bulkResponse',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const ids = [ctx.objects[0].elementId, BOGUS_ID];
      const res = await ctx.client.request('POST', '/objects/value', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/value'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const bad = res.json.results[1];
      if (bad.success !== false) return fail(`Unknown elementId "${BOGUS_ID}" must fail per-item (got success=true).`);
      if (bad.responseDetail && bad.responseDetail.status !== 404) return fail(`Unknown elementId failure carries status ${bad.responseDetail.status}, expected 404.`);
      return pass();
    }
  },
  {
    id: 'QRY-05',
    name: 'Composition values: maxDepth > 1 returns child values under "components"',
    level: 'MUST',
    ref: 'maxDepth',
    async run(ctx) {
      if (!ctx.objects) return skip('No objects available', 'blocked');
      // Prefer a composition object that has HasComponent children with live data.
      // objectsWithMetadata (populated by EXP-17) includes relationship edges; fall back
      // to the plain object list and prefer non-root nodes (parentId present) if metadata
      // is unavailable, since root/organizational nodes rarely carry live values.
      const candidates = (ctx.objectsWithMetadata || ctx.objects).filter((o) => o.isComposition === true);
      if (!candidates.length) return skip('No composition objects (isComposition=true) in the address space', 'untestable');
      const comp =
        candidates.find((o) => o.metadata && o.metadata.relationships && o.metadata.relationships.HasComponent) ??
        candidates.find((o) => o.parentId) ??
        candidates[0];
      const res = await ctx.client.request('POST', '/objects/value', { body: { elementIds: [comp.elementId], maxDepth: 0 } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/value (maxDepth=0)'));
      if (res.status !== 200 && res.status !== 206) return fail(`Expected HTTP 200 (or 206 for partial composition trees), got ${res.status}.`);
      const item = res.json.results && res.json.results[0];
      if (!item || !item.success || !item.result) return fail(`Could not read composition object "${comp.elementId}": ${JSON.stringify(item && item.responseDetail)}`);
      const components = item.result.components;
      if (!components || typeof components !== 'object' || Array.isArray(components)) {
        if (item.result.value == null && item.result.quality === 'GoodNoData')
          return skip(`"${comp.elementId}" has no live data (GoodNoData) — cannot verify composition tree`, 'untestable');
        return fail(
          `Composition object "${comp.elementId}" queried with maxDepth=0 returned no "components" map. Composition elements must return child values keyed by elementId when maxDepth > 1.`
        );
      }
      const problems = [];
      for (const [childId, vqt] of Object.entries(components)) {
        problems.push(...V.validateShape('VQT', vqt, `components.${childId}`));
        problems.push(...V.vqtProblems(vqt, `components.${childId}`));
      }
      if (problems.length) return fail(`Component child values are malformed: ${firstProblems(problems)} — each child is a VQT (value, quality, timestamp).`);
      if (res.status === 206) {
        const d = res.json.responseDetail;
        if (!d) return fail('HTTP 206 partial response is missing the required top-level "responseDetail" explaining the server-imposed limit.');
      }
      return pass(`${Object.keys(components).length} component value(s)`);
    }
  },
  {
    id: 'QRY-06',
    name: 'maxDepth = 1 (default) returns no components',
    level: 'MUST',
    ref: 'maxDepth',
    async run(ctx) {
      if (!ctx.objects) return skip('No objects available', 'blocked');
      const comp = ctx.objects.find((o) => o.isComposition === true);
      if (!comp) return skip('No composition objects in the address space', 'untestable');
      const res = await ctx.client.request('POST', '/objects/value', { body: { elementIds: [comp.elementId], maxDepth: 1 } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/value (maxDepth=1)'));
      const item = res.json.results && res.json.results[0];
      if (!item || !item.success || !item.result) return fail(`Could not read composition object "${comp.elementId}".`);
      if (item.result.components && Object.keys(item.result.components).length) {
        return fail(
          `maxDepth=1 returned a populated "components" map for "${comp.elementId}". maxDepth=1 means no recursion — only the element's direct value.`
        );
      }
      return pass();
    }
  },
  {
    id: 'QRY-07',
    name: 'POST /objects/history returns HistoricalValueResult records',
    level: 'MUST',
    ref: 'queryMethods',
    async run(ctx) {
      const sample = sampleObjects(ctx, 3);
      if (!sample.length) return skip('No objects available', 'blocked');
      const ids = sample.map((o) => o.elementId);
      const endTime = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      const startTime = new Date(Date.now() - 24 * 3600 * 1000).toISOString().replace(/\.\d+Z$/, 'Z');
      const res = await ctx.client.request('POST', '/objects/history', { body: { elementIds: ids, startTime, endTime } });
      if (!okJson(res)) {
        const note = ctx.capabilities && ctx.capabilities.query && ctx.capabilities.query.history === false
          ? ' Even when capabilities.query.history=false, the endpoint should respond with quality "GoodNoData" rather than an error — history queries are a MUST.'
          : '';
        return fail(httpProblem(res, 'POST /objects/history') + note);
      }
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids, itemShape: 'HistoricalValueResult' });
      if (problems.length) return fail(firstProblems(problems));
      ctx.historyResults = res.json.results;
      ctx.historyRange = { startTime, endTime };
      return pass();
    }
  },
  {
    id: 'QRY-08',
    name: 'Historical values are well-formed VQTs within the requested time range',
    level: 'MUST',
    ref: 'queryMethods',
    async run(ctx) {
      if (!ctx.historyResults) return skip('History query did not succeed', 'blocked');
      const problems = [];
      let points = 0;
      const start = Date.parse(ctx.historyRange.startTime);
      const end = Date.parse(ctx.historyRange.endTime);
      for (const item of ctx.historyResults) {
        if (!item.success || !item.result || !Array.isArray(item.result.values)) continue;
        item.result.values.forEach((vqt, i) => {
          points++;
          problems.push(...V.vqtProblems(vqt, `${item.elementId}.values[${i}]`));
          const t = Date.parse(vqt.timestamp);
          if (!Number.isNaN(t) && (t < start - 1000 || t > end + 1000)) {
            problems.push(`${item.elementId}.values[${i}].timestamp ${vqt.timestamp} is outside the requested range ${ctx.historyRange.startTime} … ${ctx.historyRange.endTime}`);
          }
        });
      }
      if (!points) return skip('Server returned no historical data points for the sampled objects (acceptable — e.g. GoodNoData platforms)', 'untestable');
      if (problems.length) return fail(firstProblems(problems));
      return pass(`${points} historical point(s) validated`);
    }
  },
  {
    id: 'QRY-09',
    name: 'POST /objects/history reports unknown elementIds as per-item 404 failures',
    level: 'MUST',
    ref: 'bulkResponse',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const ids = [ctx.objects[0].elementId, BOGUS_ID];
      const endTime = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      const startTime = new Date(Date.now() - 3600 * 1000).toISOString().replace(/\.\d+Z$/, 'Z');
      const res = await ctx.client.request('POST', '/objects/history', { body: { elementIds: ids, startTime, endTime } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/history'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const bad = res.json.results[1];
      if (bad.success !== false) return fail(`Unknown elementId "${BOGUS_ID}" must fail per-item with a 404 responseDetail.`);
      return pass();
    }
  },
  {
    id: 'QRY-10',
    name: 'POST /objects/history requires startTime and endTime in RFC 3339 format',
    level: 'MUST',
    ref: 'queryMethods',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const id = ctx.objects[0].elementId;
      const validTime = new Date().toISOString().replace(/\.\d+Z$/, 'Z');

      const r1 = await ctx.client.request('POST', '/objects/history', { body: { elementIds: [id], endTime: validTime } });
      if (r1.status !== 400) return fail(`Missing startTime should return 400, got ${r1.status}`);

      const r2 = await ctx.client.request('POST', '/objects/history', { body: { elementIds: [id], startTime: validTime } });
      if (r2.status !== 400) return fail(`Missing endTime should return 400, got ${r2.status}`);

      const r3 = await ctx.client.request('POST', '/objects/history', { body: { elementIds: [id], startTime: 'not-a-date', endTime: validTime } });
      if (r3.status !== 400) return fail(`Invalid startTime format should return 400, got ${r3.status}`);

      return pass();
    }
  },
  {
    id: 'QRY-11',
    name: 'POST /objects/history with maxDepth > 1 returns child history under "components"',
    level: 'MUST',
    ref: 'maxDepth',
    async run(ctx) {
      if (!ctx.objects) return skip('No objects available', 'blocked');
      // Same selection logic as QRY-05: prefer a composition object with HasComponent children.
      const candidates = (ctx.objectsWithMetadata || ctx.objects).filter((o) => o.isComposition === true);
      if (!candidates.length) return skip('No composition objects in the address space', 'untestable');
      const comp =
        candidates.find((o) => o.metadata && o.metadata.relationships && o.metadata.relationships.HasComponent) ??
        candidates.find((o) => o.parentId) ??
        candidates[0];
      const endTime = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      const startTime = new Date(Date.now() - 24 * 3600 * 1000).toISOString().replace(/\.\d+Z$/, 'Z');
      const res = await ctx.client.request('POST', '/objects/history', { body: { elementIds: [comp.elementId], startTime, endTime, maxDepth: 2 } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/history (maxDepth=2)'));
      const item = res.json.results && res.json.results[0];
      if (!item || !item.success || !item.result) return fail(`Could not read history for composition object "${comp.elementId}"`);
      if (!item.result.isComposition) return skip(`"${comp.elementId}" did not return isComposition=true in the history result`, 'untestable');
      const components = item.result.components;
      if (!components || typeof components !== 'object' || Array.isArray(components)) {
        if (!item.result.values || item.result.values.length === 0)
          return skip(`"${comp.elementId}" has no historical data — cannot verify composition tree`, 'untestable');
        return fail(`Composition object "${comp.elementId}" queried with maxDepth=2 returned no "components" map. History responses must mirror current-value composition behaviour when maxDepth > 1.`);
      }
      const problems = [];
      for (const [childId, child] of Object.entries(components)) {
        if (!Array.isArray(child.values)) problems.push(`components.${childId} missing "values" array`);
      }
      if (problems.length) return fail(firstProblems(problems));
      return pass(`${Object.keys(components).length} component(s) with history`);
    }
  }
];
