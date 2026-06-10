'use strict';

const crypto = require('node:crypto');
const { pass, fail, warn, skip, httpProblem, okJson } = require('../results');
const V = require('../validators');

const BOGUS_ID = 'i3x-test-suite-nonexistent-element-7f3a9c';
const BOGUS_SUB = 'i3x-test-suite-nonexistent-subscription-2b81e0';

function firstProblems(problems, n = 5) {
  return problems.slice(0, n).join('; ') + (problems.length > n ? ` (+${problems.length - n} more)` : '');
}

module.exports = [
  {
    id: 'SUB-01',
    name: 'POST /subscriptions creates a subscription and returns a subscriptionId',
    level: 'MUST',
    ref: 'subscriptions',
    async run(ctx) {
      ctx.clientId = `i3x-test-suite-${crypto.randomUUID()}`;
      const res = await ctx.client.request('POST', '/subscriptions', {
        body: { clientId: ctx.clientId, displayName: 'i3X Test Suite' }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions'));
      const env = V.successEnvelopeProblems(res.json);
      if (env.length) return fail(`POST /subscriptions: ${firstProblems(env)}`);
      const problems = V.validateShape('CreateSubscriptionResponse', res.json.result, '$.result');
      if (problems.length) return fail(`CreateSubscriptionResponse is malformed: ${firstProblems(problems)} — the client must receive a subscriptionId to cache.`);
      ctx.subscriptionId = res.json.result.subscriptionId;
      return pass();
    }
  },
  {
    id: 'SUB-02',
    name: 'POST /subscriptions/list returns the subscription keyed by subscriptionId',
    level: 'MUST',
    ref: 'subscriptions',
    async run(ctx) {
      if (!ctx.subscriptionId) return skip('No subscription was created', 'blocked');
      const res = await ctx.client.request('POST', '/subscriptions/list', {
        body: { clientId: ctx.clientId, subscriptionIds: [ctx.subscriptionId] }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions/list'));
      const problems = V.bulkEnvelopeProblems(res.json, {
        requestedIds: [ctx.subscriptionId],
        keyField: 'subscriptionId',
        itemShape: 'SubscriptionDetail'
      });
      if (problems.length) return fail(firstProblems(problems));
      const item = res.json.results[0];
      if (!item.success) return fail(`The just-created subscription was not found: ${JSON.stringify(item.responseDetail)}`);
      return pass();
    }
  },
  {
    id: 'SUB-03',
    name: 'POST /subscriptions/register registers objects and returns per-item results',
    level: 'MUST',
    ref: 'registering',
    async run(ctx) {
      if (!ctx.subscriptionId) return skip('No subscription was created', 'blocked');
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available to register', 'blocked');
      const ids = ctx.objects.slice(0, 2).map((o) => o.elementId);
      const res = await ctx.client.request('POST', '/subscriptions/register', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId, elementIds: ids }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions/register'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const failed = res.json.results.filter((r) => !r.success);
      if (failed.length) return fail(`Registering valid elementIds failed: ${JSON.stringify(failed[0].responseDetail)}`);
      ctx.registeredIds = ids;
      return pass(`registered ${ids.length} object(s)`);
    }
  },
  {
    id: 'SUB-04',
    name: 'Re-registering an already-registered object succeeds (idempotent)',
    level: 'MUST',
    ref: 'registering',
    async run(ctx) {
      if (!ctx.registeredIds) return skip('No objects were registered', 'blocked');
      const res = await ctx.client.request('POST', '/subscriptions/register', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId, elementIds: [ctx.registeredIds[0]] }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions/register (duplicate)'));
      const item = res.json.results && res.json.results[0];
      if (!item || item.success !== true) {
        return fail('Duplicate registration was rejected. "If an Object is registered more than once the Server MUST return success and ignore the subsequent registration".');
      }
      return pass();
    }
  },
  {
    id: 'SUB-05',
    name: 'Registration supports partial failure for unknown elementIds',
    level: 'MUST',
    ref: 'registering',
    async run(ctx) {
      if (!ctx.registeredIds) return skip('No subscription/registration available', 'blocked');
      const ids = [ctx.registeredIds[0], BOGUS_ID];
      const res = await ctx.client.request('POST', '/subscriptions/register', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId, elementIds: ids }
      });
      if (!okJson(res)) {
        return fail(httpProblem(res, 'POST /subscriptions/register (mixed batch)') + ' — "The Server MUST support partial failures (e.g. bad elementId) and not fail the full request".');
      }
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const [good, bad] = res.json.results;
      if (good.success !== true) return fail('The valid elementId in a mixed registration batch failed.');
      if (bad.success !== false) return fail(`Unknown elementId "${BOGUS_ID}" was registered successfully — it must fail per-item with a 404 responseDetail.`);
      return pass();
    }
  },
  {
    id: 'SUB-06',
    name: 'POST /subscriptions/sync returns batches of well-formed updates',
    level: 'MUST',
    ref: 'sync',
    async run(ctx) {
      if (!ctx.subscriptionId) return skip('No subscription was created', 'blocked');
      const res = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions/sync'));
      if (res.status !== 200 && res.status !== 206) return fail(`Expected HTTP 200 (or 206 after queue overflow), got ${res.status}.`);
      const env = V.successEnvelopeProblems(res.json);
      if (env.length) return fail(`POST /subscriptions/sync: ${firstProblems(env)}`);
      if (!Array.isArray(res.json.result)) return fail('"result" must be an array of SyncBatch objects (empty when there are no updates).');
      const problems = [];
      res.json.result.forEach((batch, i) => {
        problems.push(...V.validateShape('SyncBatch', batch, `$.result[${i}]`));
        (batch.updates || []).forEach((u, j) => problems.push(...V.vqtProblems(u, `$.result[${i}].updates[${j}]`)));
      });
      if (problems.length) return fail(`Sync batches are malformed: ${firstProblems(problems)}.`);
      ctx.firstSyncBatches = res.json.result;
      return pass(`${res.json.result.length} pending batch(es)`);
    }
  },
  {
    id: 'SUB-07',
    name: 'Sync acknowledgement: lastSequenceNumber removes acknowledged batches',
    level: 'MUST',
    ref: 'sync',
    async run(ctx) {
      if (!ctx.subscriptionId || !ctx.firstSyncBatches) return skip('Sync did not succeed', 'blocked');

      // Try to generate an update so there is something to acknowledge:
      // write the current value back if the server supports writes.
      if (!ctx.firstSyncBatches.length && ctx.capabilities?.update?.current && ctx.config.includeWrites && ctx.currentValues) {
        const id = (ctx.registeredIds || []).find((i) => ctx.currentValues.has(i) && ctx.currentValues.get(i).quality === 'Good');
        if (id) {
          await ctx.client.request('PUT', '/objects/value', {
            body: { updates: [{ elementId: id, value: { value: ctx.currentValues.get(id).value, quality: 'Good' } }] }
          });
          await new Promise((r) => setTimeout(r, 500));
        }
      }

      const first = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId }
      });
      if (!okJson(first) || !Array.isArray(first.json.result)) return fail(httpProblem(first, 'POST /subscriptions/sync'));
      const batches = first.json.result;
      if (!batches.length) {
        return skip('No updates were observed on the subscription (server may capture values only on change); acknowledgement semantics could not be exercised', 'untestable');
      }
      const seqs = batches.map((b) => b.sequenceNumber);
      const strictlyIncreasing = seqs.every((s, i) => i === 0 || s > seqs[i - 1]);
      if (!strictlyIncreasing) return fail(`Batch sequence numbers are not strictly increasing: [${seqs.join(', ')}]. The server MUST provide an incrementing sequenceNumber.`);
      const last = seqs[seqs.length - 1];
      const second = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId, lastSequenceNumber: last }
      });
      if (!okJson(second) || !Array.isArray(second.json.result)) return fail(httpProblem(second, 'POST /subscriptions/sync (ack)'));
      const stale = second.json.result.filter((b) => b.sequenceNumber <= last);
      if (stale.length) {
        return fail(
          `After acknowledging lastSequenceNumber=${last}, the server returned batch(es) with sequenceNumber ≤ ${last} ([${stale.map((b) => b.sequenceNumber).join(', ')}]). Acknowledged updates MUST be removed.`
        );
      }
      return pass(`acknowledged through sequence ${last}`);
    }
  },
  {
    // SUB-13 runs between SUB-07 and SUB-08 so the subscription still has all
    // its registered objects; the id is appended per the numbering convention.
    id: 'SUB-13',
    name: 'Sync acknowledgement: lastSequenceNumber = -1 clears all pending updates',
    level: 'MUST',
    ref: 'sync',
    async run(ctx) {
      if (!ctx.subscriptionId || !ctx.firstSyncBatches) return skip('Sync did not succeed', 'blocked');
      const first = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId }
      });
      if (!okJson(first) || !Array.isArray(first.json.result)) return fail(httpProblem(first, 'POST /subscriptions/sync'));
      if (!first.json.result.length) {
        return skip('No pending updates were observed (server may capture values only on change); clearing the queue with lastSequenceNumber=-1 could not be exercised', 'untestable');
      }
      const maxSeen = Math.max(...first.json.result.map((b) => b.sequenceNumber));
      const ackAll = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId, lastSequenceNumber: -1 }
      });
      if (!okJson(ackAll) || !Array.isArray(ackAll.json.result)) {
        return fail(
          httpProblem(ackAll, 'POST /subscriptions/sync (lastSequenceNumber=-1)') +
            ' — "Server MUST clear the queue if lastSequenceNumber=-1 is provided, acknowledging all pending updates".'
        );
      }
      const next = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId }
      });
      if (!okJson(next) || !Array.isArray(next.json.result)) return fail(httpProblem(next, 'POST /subscriptions/sync (after -1)'));
      const stale = [...ackAll.json.result, ...next.json.result].filter((b) => b.sequenceNumber <= maxSeen);
      if (stale.length) {
        return fail(
          `After lastSequenceNumber=-1 the server returned batch(es) with sequenceNumber ≤ ${maxSeen} ([${stale.map((b) => b.sequenceNumber).join(', ')}]). The server MUST clear the entire queue when -1 is provided.`
        );
      }
      return pass(`queue cleared through sequence ${maxSeen} in a single round trip`);
    }
  },
  {
    id: 'SUB-08',
    name: 'POST /subscriptions/unregister removes objects with per-item results',
    level: 'MUST',
    ref: 'registering',
    async run(ctx) {
      if (!ctx.registeredIds) return skip('No objects were registered', 'blocked');
      const ids = [ctx.registeredIds[0], BOGUS_ID];
      const res = await ctx.client.request('POST', '/subscriptions/unregister', {
        body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId, elementIds: ids }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions/unregister'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const [good, bad] = res.json.results;
      if (good.success !== true) return fail(`Unregistering a registered object failed: ${JSON.stringify(good.responseDetail)}`);
      if (bad.success !== false) return fail(`Unregistering unknown elementId "${BOGUS_ID}" reported success — partial failures must be reported per-item.`);
      return pass();
    }
  },
  {
    id: 'SUB-09',
    name: 'POST /subscriptions/stream opens a Server-Sent Events stream',
    level: 'MAY',
    feature: 'subscribe.stream',
    ref: 'streaming',
    async run(ctx) {
      if (!ctx.subscriptionId) return skip('No subscription was created', 'blocked');
      let res;
      try {
        res = await ctx.client.open('POST', '/subscriptions/stream', {
          body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId },
          timeout: 10000
        });
      } catch (e) {
        return fail(`POST /subscriptions/stream: request failed (${e.message}) — capabilities.subscribe.stream is declared true, so SSE streaming must work.`);
      }
      const ctype = res.headers.get('content-type') || '';
      try {
        if (res.status !== 200) {
          return fail(`POST /subscriptions/stream returned HTTP ${res.status}; expected 200 with an open SSE stream.`);
        }
        if (!ctype.includes('text/event-stream')) {
          return fail(`Stream responded with Content-Type "${ctype}" — SSE requires "text/event-stream".`);
        }
        return pass();
      } finally {
        try { await res.body?.cancel(); } catch { /* closing the probe stream */ }
      }
    }
  },
  {
    // SUB-14 runs after SUB-09, while the suite's subscription still exists.
    id: 'SUB-14',
    name: 'Opening a second stream closes the existing stream (single stream per subscription)',
    level: 'MAY',
    feature: 'subscribe.stream',
    ref: 'streaming',
    async run(ctx) {
      if (!ctx.subscriptionId) return skip('No subscription was created', 'blocked');
      let resA;
      try {
        resA = await ctx.client.open('POST', '/subscriptions/stream', {
          body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId },
          timeout: 30000
        });
      } catch (e) {
        return skip(`Could not open the first stream (${e.message}) — stream behavior is covered by SUB-09`, 'blocked');
      }
      if (resA.status !== 200 || !resA.body) {
        try { await resA.body?.cancel(); } catch { /* probe cleanup */ }
        return skip(`First stream did not open (HTTP ${resA.status}) — stream behavior is covered by SUB-09`, 'blocked');
      }
      const readerA = resA.body.getReader();
      // Drain stream A in the background; resolves "closed" on a clean end-of-stream.
      const closedA = (async () => {
        try {
          for (;;) {
            const { done } = await readerA.read();
            if (done) return 'closed';
          }
        } catch (e) {
          return `error: ${e.message}`;
        }
      })();
      let resB;
      try {
        resB = await ctx.client.open('POST', '/subscriptions/stream', {
          body: { clientId: ctx.clientId, subscriptionId: ctx.subscriptionId },
          timeout: 10000
        });
      } catch (e) {
        try { await readerA.cancel(); } catch { /* probe cleanup */ }
        return fail(`Opening a second stream failed (${e.message}). "If a client opens a new stream while one is already active, the server MUST close the existing stream and open the new one".`);
      }
      try {
        const ctype = resB.headers.get('content-type') || '';
        if (resB.status !== 200 || !ctype.includes('text/event-stream')) {
          return fail(
            `The second stream was refused (HTTP ${resB.status}, Content-Type "${ctype}"). "If a client opens a new stream while one is already active, the server MUST close the existing stream and open the new one".`
          );
        }
        const outcome = await Promise.race([closedA, new Promise((r) => setTimeout(r, 5000, 'timeout'))]);
        if (outcome === 'timeout') {
          return fail(
            'The first stream was still open 5s after the server accepted a second stream. "Server MUST only allow a single SSE stream per subscription" — the existing stream must be closed when a new one opens.'
          );
        }
        if (outcome !== 'closed') {
          return fail(
            `The first stream was terminated abruptly (${outcome}). "The previously connected client will receive an SSE stream close with no error" — the server must end the stream cleanly.`
          );
        }
        return pass('previous stream closed cleanly when the new stream opened');
      } finally {
        try { await readerA.cancel(); } catch { /* probe cleanup */ }
        try { await resB.body?.cancel(); } catch { /* probe cleanup */ }
      }
    }
  },
  {
    id: 'SUB-10',
    name: 'POST /subscriptions/delete deletes the subscription',
    level: 'MUST',
    ref: 'subscriptions',
    async run(ctx) {
      if (!ctx.subscriptionId) return skip('No subscription was created', 'blocked');
      const res = await ctx.client.request('POST', '/subscriptions/delete', {
        body: { clientId: ctx.clientId, subscriptionIds: [ctx.subscriptionId] }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /subscriptions/delete'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: [ctx.subscriptionId], keyField: 'subscriptionId' });
      if (problems.length) return fail(firstProblems(problems));
      if (!res.json.results[0].success) return fail(`Deleting the suite's own subscription failed: ${JSON.stringify(res.json.results[0].responseDetail)}`);
      ctx.deletedSubscriptionId = ctx.subscriptionId;
      return pass();
    }
  },
  {
    id: 'SUB-11',
    name: 'Sync against a deleted or unknown subscription returns 404',
    level: 'MUST',
    ref: 'lifecycle',
    async run(ctx) {
      const target = ctx.deletedSubscriptionId || BOGUS_SUB;
      const res = await ctx.client.request('POST', '/subscriptions/sync', {
        body: { clientId: ctx.clientId || 'i3x-test-suite', subscriptionId: target }
      });
      if (!res.ok) return fail(httpProblem(res, 'POST /subscriptions/sync (deleted subscription)'));
      if (res.status !== 404) {
        return fail(
          `Sync on a ${ctx.deletedSubscriptionId ? 'deleted' : 'non-existent'} subscription returned HTTP ${res.status}; "Subsequent calls to /sync or /stream for a deleted or non-existent Subscription MUST return 404 Not Found".`
        );
      }
      const problems = V.errorEnvelopeProblems(res.json, 404);
      if (problems.length) return fail(`404 error body is malformed: ${firstProblems(problems)}.`);
      return pass();
    }
  },
  {
    id: 'SUB-12',
    name: 'Stream endpoint honestly advertises lack of support (501 when capability is false)',
    level: 'SHOULD',
    ref: 'streaming',
    async run(ctx) {
      const caps = ctx.capabilities && ctx.capabilities.subscribe;
      if (!caps) return skip('Capabilities unavailable', 'blocked');
      if (caps.stream) return skip('Streaming is declared supported — covered by SUB-09', 'untestable');
      // Need a live subscription to probe; create a throwaway one.
      const create = await ctx.client.request('POST', '/subscriptions', {
        body: { clientId: ctx.clientId || 'i3x-test-suite-probe', displayName: 'i3X Test Suite stream probe' }
      });
      if (!okJson(create) || !create.json.result) return skip('Could not create a probe subscription', 'blocked');
      const subId = create.json.result.subscriptionId;
      const res = await ctx.client.request('POST', '/subscriptions/stream', {
        body: { clientId: ctx.clientId || 'i3x-test-suite-probe', subscriptionId: subId }
      });
      await ctx.client.request('POST', '/subscriptions/delete', {
        body: { clientId: ctx.clientId || 'i3x-test-suite-probe', subscriptionIds: [subId] }
      });
      if (res.ok && res.status >= 200 && res.status < 300 && (res.contentType || '').includes('text/event-stream')) {
        return warn('capabilities.subscribe.stream is false but /subscriptions/stream opened an SSE stream — declare the capability so clients can use it.');
      }
      if (res.ok && res.status !== 501) {
        return warn(`/subscriptions/stream returned ${res.status} for a declared-unsupported feature; servers should return 501 Not Implemented.`);
      }
      return pass();
    }
  }
];
