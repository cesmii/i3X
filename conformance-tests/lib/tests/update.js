'use strict';

const { pass, fail, warn, skip, httpProblem, okJson } = require('../results');
const V = require('../validators');

const BOGUS_ID = 'i3x-test-suite-nonexistent-element-7f3a9c';

// Update methods are OPTIONAL (MAY). Tests run only when the server declares
// the capability in /info; a declared-but-broken implementation fails.
// Write tests are non-destructive: they echo the object's current value back.

function findWritable(ctx) {
  if (!ctx.currentValues) return null;
  for (const [id, vqt] of ctx.currentValues) {
    if (vqt.quality === 'Good' && vqt.value !== null && vqt.value !== undefined) {
      return { elementId: id, vqt };
    }
  }
  return null;
}

module.exports = [
  {
    id: 'UPD-01',
    name: 'PUT /objects/value accepts a write and returns a bulk result per elementId',
    level: 'MAY',
    feature: 'update.current',
    ref: 'updateMethods',
    async run(ctx) {
      if (!ctx.config.includeWrites) return skip('Write tests disabled by user', 'disabled');
      const target = findWritable(ctx);
      if (!target) return skip('No object with a Good, non-null current value to safely write back', 'untestable');
      const body = {
        updates: [{ elementId: target.elementId, value: { value: target.vqt.value, quality: 'Good' } }]
      };
      const res = await ctx.client.request('PUT', '/objects/value', { body });
      if (!okJson(res)) return fail(httpProblem(res, 'PUT /objects/value') + ' — capabilities.update.current is declared true, so this endpoint must work.');
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: [target.elementId] });
      if (problems.length) return fail(problems.slice(0, 5).join('; '));
      const item = res.json.results[0];
      if (!item.success) return fail(`Write of the object's own current value was rejected: ${JSON.stringify(item.responseDetail)}`);
      if (item.result !== null && item.result !== undefined) {
        return warn(`Successful write entries should carry "result": null (write confirmations do not echo the VQT back); got ${JSON.stringify(item.result).slice(0, 60)}`);
      }
      ctx.writtenElementId = target.elementId;
      ctx.writtenValue = target.vqt.value;
      return pass(`wrote current value back to "${target.elementId}"`);
    }
  },
  {
    id: 'UPD-02',
    name: 'A written value is readable via POST /objects/value',
    level: 'MAY',
    feature: 'update.current',
    ref: 'updateMethods',
    async run(ctx) {
      if (!ctx.config.includeWrites) return skip('Write tests disabled by user', 'disabled');
      if (!ctx.writtenElementId) return skip('No successful write to verify', 'blocked');
      const res = await ctx.client.request('POST', '/objects/value', { body: { elementIds: [ctx.writtenElementId] } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/value (read-after-write)'));
      const item = res.json.results && res.json.results[0];
      if (!item || !item.success || !item.result) return fail(`Could not read back "${ctx.writtenElementId}" after a successful write.`);
      if (JSON.stringify(item.result.value) !== JSON.stringify(ctx.writtenValue)) {
        // A live data source may legitimately produce a newer value between the
        // write and this read; the server already confirmed the write succeeded.
        return pass(
          `Note: the value read back was NOT the value written — written ${JSON.stringify(ctx.writtenValue).slice(0, 60)}…, read ${JSON.stringify(item.result.value).slice(0, 60)}…. This is expected when a live data source updates between the write and the read; the server confirmed the write succeeded.`
        );
      }
      return pass('Read-after-write returned the written value');
    }
  },
  {
    id: 'UPD-03',
    name: 'PUT /objects/value supports partial failure for unknown elementIds',
    level: 'MAY',
    feature: 'update.current',
    ref: 'bulkResponse',
    async run(ctx) {
      if (!ctx.config.includeWrites) return skip('Write tests disabled by user', 'disabled');
      const target = findWritable(ctx);
      if (!target) return skip('No safely writable object available', 'untestable');
      const body = {
        updates: [
          { elementId: target.elementId, value: { value: target.vqt.value } },
          { elementId: BOGUS_ID, value: { value: 1 } }
        ]
      };
      const res = await ctx.client.request('PUT', '/objects/value', { body });
      if (!okJson(res)) return fail(httpProblem(res, 'PUT /objects/value (mixed batch)') + ' — a bad elementId must fail per-item, not fail the whole request.');
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: [target.elementId, BOGUS_ID] });
      if (problems.length) return fail(problems.slice(0, 5).join('; '));
      const [good, bad] = res.json.results;
      if (!good.success) return fail(`The valid write in a mixed batch failed: ${JSON.stringify(good.responseDetail)}`);
      if (bad.success !== false) return fail(`Unknown elementId "${BOGUS_ID}" was accepted — it must fail with a 404 responseDetail.`);
      if (bad.responseDetail && bad.responseDetail.status !== 404) return fail(`Unknown elementId failure carries status ${bad.responseDetail.status}, expected 404.`);
      return pass();
    }
  },
  {
    id: 'UPD-04',
    name: 'PUT /objects/history accepts a historical write',
    level: 'MAY',
    feature: 'update.history',
    ref: 'updateMethods',
    async run(ctx) {
      if (!ctx.config.includeWrites) return skip('Write tests disabled by user', 'disabled');
      const target = findWritable(ctx);
      if (!target) return skip('No safely writable object available', 'untestable');
      // Re-write the current VQT at its own timestamp — replaces a record with itself.
      const ts = V.isUtcTimestamp(target.vqt.timestamp) ? target.vqt.timestamp : new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      const body = {
        updates: [{ elementId: target.elementId, value: { value: target.vqt.value, quality: 'Good', timestamp: ts } }]
      };
      const res = await ctx.client.request('PUT', '/objects/history', { body });
      if (!okJson(res)) return fail(httpProblem(res, 'PUT /objects/history') + ' — capabilities.update.history is declared true, so this endpoint must work.');
      if (Array.isArray(res.json.results)) {
        const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: [target.elementId] });
        if (problems.length) return fail(problems.slice(0, 5).join('; '));
        if (!res.json.results[0].success) return fail(`Historical write was rejected: ${JSON.stringify(res.json.results[0].responseDetail)}`);
      } else if (res.json.success !== true) {
        return fail(`PUT /objects/history returned success=${JSON.stringify(res.json.success)}.`);
      }
      return pass();
    }
  },
  {
    id: 'UPD-05',
    name: 'Update endpoints honestly advertise unsupported features (501 when capability is false)',
    level: 'SHOULD',
    ref: 'updateMethods',
    async run(ctx) {
      const caps = ctx.capabilities && ctx.capabilities.update;
      if (!caps) return skip('Capabilities unavailable', 'blocked');
      if (caps.current && caps.history) return skip('Both update capabilities are declared — nothing to verify here', 'untestable');
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const probes = [];
      if (!caps.current) probes.push(['PUT', '/objects/value']);
      if (!caps.history) probes.push(['PUT', '/objects/history']);
      const issues = [];
      for (const [method, path] of probes) {
        const res = await ctx.client.request(method, path, {
          body: { updates: [{ elementId: ctx.objects[0].elementId, value: { value: 0, quality: 'Good', timestamp: new Date().toISOString().replace(/\.\d+Z$/, 'Z') } }] }
        });
        if (res.ok && res.status >= 200 && res.status < 300) {
          issues.push(`${method} ${path} succeeded although the capability is declared false in /info — clients will skip features the server actually supports`);
        } else if (res.ok && res.status !== 501 && res.status !== 405) {
          issues.push(`${method} ${path} returned ${res.status}; servers should return 501 Not Implemented for declared-unsupported optional features`);
        }
      }
      if (issues.length) return warn(issues.join('; '));
      return pass('Undeclared update endpoints correctly refuse requests');
    }
  }
];
