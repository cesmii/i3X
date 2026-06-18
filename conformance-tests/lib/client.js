'use strict';

const http = require('node:http');
const https = require('node:https');
const zlib = require('node:zlib');

/**
 * HTTP client for the suite. Wraps global fetch (Node 18+), applies the
 * required i3X headers (Content-Type / Accept: application/json), the
 * configured authentication, and a per-request timeout.
 *
 * auth: { type: 'none' | 'bearer' | 'basic' | 'header',
 *         token?, username?, password?, name?, value? }
 */
function buildAuthHeaders(auth) {
  if (!auth || auth.type === 'none' || !auth.type) return {};
  if (auth.type === 'bearer' && auth.token) return { Authorization: `Bearer ${auth.token}` };
  if (auth.type === 'basic') {
    const cred = Buffer.from(`${auth.username || ''}:${auth.password || ''}`).toString('base64');
    return { Authorization: `Basic ${cred}` };
  }
  if (auth.type === 'header' && auth.name) return { [auth.name]: auth.value || '' };
  return {};
}

function makeClient({ baseUrl, auth, headers = {}, timeoutMs = 15000 } = {}) {
  const base = String(baseUrl || '').replace(/\/+$/, '');
  const authHeaders = buildAuthHeaders(auth);

  async function request(method, path, { body, query, noAuth = false, accept } = {}) {
    let url = base + path;
    if (query) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== null) qs.set(k, String(v));
      const s = qs.toString();
      if (s) url += `?${s}`;
    }
    const reqHeaders = {
      'Content-Type': 'application/json',
      Accept: accept || 'application/json',
      ...headers,
      ...(noAuth ? {} : authHeaders)
    };
    const started = Date.now();
    try {
      const res = await fetch(url, {
        method,
        headers: reqHeaders,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(timeoutMs),
        redirect: 'follow'
      });
      const ms = Date.now() - started;
      const text = await res.text();
      let json = null;
      let parseError = null;
      if (text.length) {
        try {
          json = JSON.parse(text);
        } catch (e) {
          parseError = e.message;
        }
      }
      return {
        ok: true,
        url,
        status: res.status,
        headers: res.headers,
        contentType: res.headers.get('content-type') || '',
        json,
        text,
        parseError,
        ms
      };
    } catch (e) {
      return {
        ok: false,
        url,
        status: 0,
        headers: new Headers(),
        contentType: '',
        json: null,
        text: '',
        parseError: null,
        error: e.cause?.message || e.message,
        ms: Date.now() - started
      };
    }
  }

  /**
   * Open the request and return the raw Response without consuming the body.
   * Used for the SSE stream test. Caller must cancel the body.
   */
  async function open(method, path, { body, timeout = timeoutMs } = {}) {
    const url = base + path;
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', ...headers, ...authHeaders },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(timeout)
    });
    return res;
  }

  /**
   * Raw request via node:http(s) so we can control Accept-Encoding and see
   * the genuine Content-Encoding header (fetch decompresses transparently).
   * Used only for the gzip conformance test.
   */
  function rawGzipProbe(path) {
    return new Promise((resolve) => {
      let url;
      try {
        url = new URL(base + path);
      } catch (e) {
        return resolve({ ok: false, error: e.message });
      }
      const mod = url.protocol === 'https:' ? https : http;
      const req = mod.request(
        url,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'Accept-Encoding': 'gzip',
            ...headers,
            ...authHeaders
          },
          timeout: timeoutMs
        },
        (res) => {
          const chunks = [];
          res.on('data', (c) => chunks.push(c));
          res.on('end', () => {
            const buf = Buffer.concat(chunks);
            const encoding = res.headers['content-encoding'] || '';
            let decodedOk = false;
            if (encoding.includes('gzip')) {
              try {
                JSON.parse(zlib.gunzipSync(buf).toString('utf8'));
                decodedOk = true;
              } catch {
                decodedOk = false;
              }
            }
            resolve({ ok: true, status: res.statusCode, encoding, decodedOk, bytes: buf.length });
          });
        }
      );
      req.on('timeout', () => {
        req.destroy(new Error('timeout'));
      });
      req.on('error', (e) => resolve({ ok: false, error: e.message }));
      req.end();
    });
  }

  return { request, open, rawGzipProbe, base };
}

module.exports = { makeClient, buildAuthHeaders };
