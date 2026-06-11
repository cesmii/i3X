'use strict';

const { pass, fail, warn, skip, httpProblem, okJson } = require('../results');
const V = require('../validators');

// Core transport, versioning, and /info tests.
// ctx fields produced: ctx.info, ctx.capabilities

module.exports = [
  {
    id: 'CORE-01',
    name: 'GET /info responds with HTTP 200 and a JSON body',
    level: 'MUST',
    ref: 'serverCapabilities',
    async run(ctx) {
      // /info must not require auth, so try without credentials first.
      let res = await ctx.client.request('GET', '/info', { noAuth: true });
      ctx.infoAuthlessRes = res;
      if (!okJson(res)) {
        // Retry with credentials so the rest of the suite can still run;
        // CORE-02 will report the authentication violation.
        const authed = await ctx.client.request('GET', '/info');
        if (okJson(authed)) {
          ctx.infoRes = authed;
          return pass('Reachable (only with credentials — see CORE-02)');
        }
        return fail(
          `${httpProblem(res, 'GET /info')}. Every i3X server must expose GET {baseURL}/v1/info as its capabilities and health endpoint.`
        );
      }
      ctx.infoRes = res;
      return pass(`HTTP 200 in ${res.ms}ms`);
    }
  },
  {
    id: 'CORE-02',
    name: 'GET /info does not require authentication',
    level: 'MUST',
    ref: 'serverCapabilities',
    async run(ctx) {
      const res = ctx.infoAuthlessRes;
      if (!res) return skip('GET /info was unreachable', 'blocked');
      if (res.status === 401 || res.status === 403) {
        return fail(
          `GET /info returned HTTP ${res.status} without credentials. The spec requires: "This endpoint MUST NOT require authentication" — it doubles as a health check.`
        );
      }
      if (!okJson(res)) return skip('GET /info was unreachable without credentials for a non-auth reason', 'blocked');
      return pass('Accessible without credentials');
    }
  },
  {
    id: 'CORE-03',
    name: 'ServerInfo declares specVersion and a complete capabilities matrix',
    level: 'MUST',
    ref: 'serverCapabilities',
    async run(ctx) {
      const res = ctx.infoRes;
      if (!res) return skip('GET /info was unreachable', 'blocked');
      const info = res.json && res.json.result !== undefined ? res.json.result : res.json;
      const problems = V.validateShape('ServerInfo', info);
      if (problems.length) {
        return fail(
          `ServerInfo is missing required fields: ${problems.join('; ')}. The capabilities matrix (query.history, update.current, update.history, subscribe.stream) must always be present with boolean values.`
        );
      }
      ctx.info = info;
      ctx.capabilities = info.capabilities;
      const notes = [`specVersion="${info.specVersion}"`];
      if (!/^1(\.|$)/.test(String(info.specVersion))) {
        return warn(
          `specVersion is "${info.specVersion}" — this suite validates the 1.0 specification; results may not apply.`
        );
      }
      return pass(notes.join(', '));
    }
  },
  {
    id: 'CORE-04',
    name: 'Server compresses responses with gzip when the client sends Accept-Encoding: gzip',
    level: 'MUST',
    ref: 'transport',
    async run(ctx) {
      const probe = await ctx.client.rawGzipProbe('/namespaces');
      if (!probe.ok) return skip(`Could not probe (${probe.error})`, 'untestable');
      if (!probe.encoding.includes('gzip')) {
        return fail(
          `GET /namespaces with "Accept-Encoding: gzip" returned Content-Encoding: ${probe.encoding || '(none)'}. The spec requires: "When i3X requests include Accept-Encoding: gzip, servers MUST respond with Content-Encoding: gzip".`
        );
      }
      if (!probe.decodedOk) {
        return fail('Response claimed Content-Encoding: gzip but the body was not valid gzip-compressed JSON.');
      }
      return pass(`gzip honored (${probe.bytes} compressed bytes)`);
    }
  },
  {
    id: 'CORE-05',
    name: 'Endpoint is served over HTTPS',
    level: 'SHOULD',
    ref: 'security',
    async run(ctx) {
      if (ctx.client.base.startsWith('https://')) {
        if (ctx.config.insecure) {
          return warn(
            'Endpoint is HTTPS, but TLS certificate verification was disabled for this run (insecure mode) — the server\'s identity was not verified. Acceptable for development/internal testing only; production servers MUST present a certificate clients can validate.'
          );
        }
        return pass();
      }
      return warn(
        'Endpoint is plain HTTP. Implementations MUST support encrypted transport (HTTPS) in production; HTTP is acceptable only for development/internal testing.'
      );
    }
  },
  {
    id: 'CORE-06',
    name: 'Server requires authentication on data endpoints',
    level: 'SHOULD',
    ref: 'security',
    async run(ctx) {
      // /info is exempt (it MUST NOT require auth) — probe /namespaces instead.
      const res = await ctx.client.request('GET', '/namespaces', { noAuth: true });
      if (!res.ok) return skip(`Could not probe (${res.error})`, 'untestable');
      if (res.status === 401 || res.status === 403) return pass('Unauthenticated requests are rejected');
      if (res.status >= 200 && res.status < 300) {
        return warn(
          'The server accepted an unauthenticated request to GET /namespaces. This is acceptable for development and testing, but in production implementations MUST require authentication.'
        );
      }
      return skip(`Unauthenticated probe returned HTTP ${res.status} — could not determine auth posture`, 'untestable');
    }
  }
];
