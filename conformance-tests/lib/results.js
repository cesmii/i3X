'use strict';

// Result helpers used by test implementations.
// status: pass | fail | warn | skip
// - warn: a SHOULD-level concern or informational caveat; never affects the verdict
// - skip: prerequisite missing, or an optional (MAY) feature the server omits

const pass = (message) => ({ status: 'pass', message });
const fail = (message, details) => ({ status: 'fail', message, details });
const warn = (message, details) => ({ status: 'warn', message, details });
const skip = (message, reason) => ({ status: 'skip', message, reason }); // reason: 'omitted'|'blocked'|'disabled'|'untestable'

/** Standard failure for a transport-level problem (non-2xx, network error, bad JSON). */
function httpProblem(res, what) {
  if (!res.ok) return `${what}: request failed (${res.error})`;
  if (res.parseError) return `${what}: response is not valid JSON (${res.parseError}) — all i3X responses must be JSON encoded`;
  return `${what}: HTTP ${res.status}${res.json && res.json.responseDetail ? ` — ${res.json.responseDetail.title}: ${res.json.responseDetail.detail}` : ''}`;
}

/** True when the response is a usable 2xx JSON body. */
function okJson(res) {
  return res.ok && res.status >= 200 && res.status < 300 && res.json !== null;
}

module.exports = { pass, fail, warn, skip, httpProblem, okJson };
