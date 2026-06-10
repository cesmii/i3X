'use strict';

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { runSuite } = require('../lib/engine');

const PUBLIC_DIR = path.join(__dirname, 'public');
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.json': 'application/json'
};

// Cap concurrent runs so a public deployment can't be trivially exhausted.
const MAX_CONCURRENT_RUNS = parseInt(process.env.I3X_MAX_RUNS || '4', 10);
let activeRuns = 0;

function readBody(req, limit = 64 * 1024) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > limit) {
        reject(new Error('request body too large'));
        req.destroy();
        return;
      }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

async function handleRun(req, res) {
  let config;
  try {
    config = JSON.parse(await readBody(req));
  } catch (e) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: `Invalid request: ${e.message}` }));
    return;
  }

  if (activeRuns >= MAX_CONCURRENT_RUNS) {
    res.writeHead(429, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Too many concurrent test runs; try again in a minute.' }));
    return;
  }

  // Only accept the fields we expect — never let a client set arbitrary config.
  const safeConfig = {
    endpoint: String(config.endpoint || ''),
    auth: config.auth && typeof config.auth === 'object' ? config.auth : { type: 'none' },
    headers: {},
    includeWrites: config.includeWrites !== false,
    timeoutMs: Math.min(Math.max(parseInt(config.timeoutMs, 10) || 20000, 1000), 60000)
  };
  if (config.headers && typeof config.headers === 'object') {
    for (const [k, v] of Object.entries(config.headers)) {
      if (/^[\w-]+$/.test(k) && typeof v === 'string') safeConfig.headers[k] = v;
    }
  }

  activeRuns++;
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no'
  });
  const send = (event) => {
    if (!res.writableEnded) res.write(`data: ${JSON.stringify(event)}\n\n`);
  };
  const keepalive = setInterval(() => {
    if (!res.writableEnded) res.write(': keepalive\n\n');
  }, 15000);

  let aborted = false;
  req.on('close', () => {
    aborted = true;
  });

  try {
    await runSuite(safeConfig, (e) => {
      if (!aborted) send(e);
    });
  } catch (e) {
    send({ type: 'done', summary: { verdict: 'Error', headline: e.message, counts: {}, notes: [] }, results: [] });
  } finally {
    activeRuns--;
    clearInterval(keepalive);
    res.end();
  }
}

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let file = urlPath === '/' ? '/index.html' : urlPath;
  file = path.normalize(file).replace(/^(\.\.[/\\])+/, '');
  const full = path.join(PUBLIC_DIR, file);
  if (!full.startsWith(PUBLIC_DIR) || !fs.existsSync(full) || !fs.statSync(full).isFile()) {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
    return;
  }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(full)] || 'application/octet-stream' });
  fs.createReadStream(full).pipe(res);
}

function startServer(port = 8330, host = process.env.I3X_HOST || '0.0.0.0') {
  const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/api/run') return handleRun(req, res);
    if (req.method === 'GET' && req.url === '/api/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, activeRuns }));
      return;
    }
    if (req.method === 'GET') return serveStatic(req, res);
    res.writeHead(405, { 'Content-Type': 'text/plain' });
    res.end('Method not allowed');
  });
  server.listen(port, host, () => {
    console.log(`i3X Test Suite web UI listening on http://${host === '0.0.0.0' ? 'localhost' : host}:${port}`);
  });
  return server;
}

module.exports = { startServer };

if (require.main === module) startServer(parseInt(process.env.PORT || '8330', 10));
