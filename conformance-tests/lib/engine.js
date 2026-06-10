'use strict';

const { makeClient } = require('./client');
const { REFS, SDK_DOCS } = require('./specrefs');
const { computeSummary } = require('./report');

const PHASES = [
  { name: 'Transport & Server Info', tests: require('./tests/transport') },
  { name: 'Exploratory Methods', tests: require('./tests/exploratory') },
  { name: 'Query Methods', tests: require('./tests/query') },
  { name: 'Update Methods (optional)', tests: require('./tests/update') },
  { name: 'Subscribe Methods', tests: require('./tests/subscribe') }
];

function allTests() {
  return PHASES.flatMap((p) => p.tests.map((t) => ({ ...t, phase: p.name })));
}

/** Read a dotted capability path like "update.current" from /info capabilities. */
function capability(caps, path) {
  if (!caps) return undefined;
  return path.split('.').reduce((acc, k) => (acc && typeof acc === 'object' ? acc[k] : undefined), caps);
}

/**
 * Resolve the base URL: accept endpoints supplied with or without the
 * /v1 version prefix, probing GET /info at each candidate.
 */
async function resolveBaseUrl(config, emit) {
  const supplied = String(config.endpoint || '').trim().replace(/\/+$/, '');
  if (!supplied) throw new Error('No endpoint supplied');
  if (!/^https?:\/\//i.test(supplied)) throw new Error(`Endpoint must start with http:// or https:// (got "${supplied}")`);
  const candidates = /\/v\d+$/.test(supplied) ? [supplied] : [supplied + '/v1', supplied];
  for (const base of candidates) {
    const client = makeClient({ ...config, baseUrl: base });
    const res = await client.request('GET', '/info', { noAuth: true });
    if (res.ok && res.json !== null && res.status < 500) {
      if (base !== supplied) emit({ type: 'note', message: `Using base URL ${base} (resolved from ${supplied})` });
      return base;
    }
    // Auth-protected /info violates the spec, but still identifies the base.
    if (res.ok && (res.status === 401 || res.status === 403)) return base;
  }
  // Fall back to the supplied URL so CORE-01 reports the failure with detail.
  return candidates[0];
}

/**
 * Run the full suite.
 *
 * config: {
 *   endpoint, auth: {type, token, username, password, name, value},
 *   headers: {..}, includeWrites: true, timeoutMs: 20000, insecure: false
 * }
 * onEvent: receives {type: 'start'|'note'|'phase'|'test:start'|'test:end'|'done', ...}
 *
 * Returns { results, summary, config }.
 */
async function runSuite(config = {}, onEvent = () => {}) {
  const emit = (e) => {
    try {
      onEvent(e);
    } catch {
      /* listener errors must not abort the run */
    }
  };

  if (config.insecure) process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

  const cfg = {
    includeWrites: true,
    timeoutMs: 20000,
    ...config,
    auth: config.auth || { type: 'none' },
    headers: config.headers || {}
  };

  const tests = allTests();
  const results = [];
  const ctx = { config: cfg };

  let base;
  try {
    base = await resolveBaseUrl(cfg, emit);
  } catch (e) {
    const summary = {
      verdict: 'Error',
      headline: e.message,
      counts: { pass: 0, fail: 0, warn: 0, skip: 0, total: tests.length },
      mustFailures: [],
      mayFailures: [],
      omittedFeatures: [],
      notes: [e.message],
      docsUrl: SDK_DOCS
    };
    emit({ type: 'done', summary, results });
    return { results, summary, config: cfg };
  }

  ctx.client = makeClient({ ...cfg, baseUrl: base });
  emit({ type: 'start', endpoint: base, total: tests.length, startedAt: new Date().toISOString() });

  let lastPhase = null;
  let index = 0;
  for (const test of tests) {
    index++;
    if (test.phase !== lastPhase) {
      lastPhase = test.phase;
      emit({ type: 'phase', name: test.phase });
    }
    const ref = REFS[test.ref] || null;
    const meta = {
      id: test.id,
      name: test.name,
      level: test.level,
      feature: test.feature || null,
      phase: test.phase,
      refTitle: ref && ref.title,
      refUrl: ref && ref.url
    };
    emit({ type: 'test:start', ...meta, index, total: tests.length });

    let outcome;
    const started = Date.now();

    // Feature-gated (MAY) tests: skip when the server does not declare the capability.
    const declared = test.feature ? capability(ctx.capabilities, test.feature) : undefined;
    if (test.feature && declared === false) {
      outcome = {
        status: 'skip',
        reason: 'omitted',
        message: `Optional feature not declared by the server (capabilities.${test.feature} = false) — omission is allowed`
      };
    } else if (test.feature && declared === undefined && ctx.capabilities) {
      outcome = { status: 'skip', reason: 'blocked', message: `capabilities.${test.feature} missing from /info` };
    } else {
      try {
        outcome = await test.run(ctx);
      } catch (e) {
        outcome = { status: 'fail', message: `Test crashed: ${e.message}` };
      }
    }

    const result = { ...meta, ...outcome, ms: Date.now() - started, index };
    results.push(result);
    emit({ type: 'test:end', ...result, total: tests.length });
  }

  const summary = computeSummary(results, ctx);
  emit({ type: 'done', summary, results });
  return { results, summary, config: cfg };
}

module.exports = { runSuite, allTests, PHASES };
