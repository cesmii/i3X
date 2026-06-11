#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { runSuite } = require('../lib/engine');
const { SDK_DOCS } = require('../lib/specrefs');

const USAGE = `i3X 1.0 Conformance Test Suite

Usage:
  i3x-test run <endpoint> [options]   Run the suite against a server
  i3x-test serve [-p PORT]            Launch the web UI locally (default port 8330)
  i3x-test mock [-p PORT]             Run the built-in compliant reference server (default port 8331)

Run options:
  --token <token>            Bearer token authentication
  --basic <user:pass>        HTTP Basic authentication
  --header "<Name: value>"   Custom header (repeatable; first use wins for auth)
  --no-writes                Skip write tests even if the server declares update capabilities
  --timeout <ms>             Per-request timeout (default 20000)
  --insecure                 Accept self-signed TLS certificates (development only;
                             the run is flagged with an advisory warning, CORE-05)
  --json <file>              Also write the full report as JSON
  --quiet                    Only print failures and the final summary

The endpoint is the server's versioned base URL, including the /v1 prefix.

Examples:
  i3x-test run https://factory.example.com/i3x/v1 --token abc123
  i3x-test run http://10.0.0.5:8080/v1 --basic admin:secret --json report.json
  i3x-test serve -p 9000
`;

const useColor = process.stdout.isTTY && !process.env.NO_COLOR;
const c = (code, s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const green = (s) => c('32', s);
const red = (s) => c('31', s);
const yellow = (s) => c('33', s);
const dim = (s) => c('2', s);
const bold = (s) => c('1', s);
const cyan = (s) => c('36', s);

const SYMBOL = {
  pass: green('✓'),
  fail: red('✗'),
  warn: yellow('⚠'),
  skip: dim('–')
};

function parseRunArgs(argv) {
  const config = { auth: { type: 'none' }, headers: {}, includeWrites: true };
  const out = { config, jsonPath: null, quiet: false };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--token') config.auth = { type: 'bearer', token: argv[++i] };
    else if (a === '--basic') {
      const [username, ...rest] = String(argv[++i] || '').split(':');
      config.auth = { type: 'basic', username, password: rest.join(':') };
    } else if (a === '--header') {
      const raw = String(argv[++i] || '');
      const idx = raw.indexOf(':');
      if (idx > 0) config.headers[raw.slice(0, idx).trim()] = raw.slice(idx + 1).trim();
    } else if (a === '--no-writes') config.includeWrites = false;
    else if (a === '--timeout') config.timeoutMs = parseInt(argv[++i], 10) || 20000;
    else if (a === '--insecure') config.insecure = true;
    else if (a === '--json') out.jsonPath = argv[++i];
    else if (a === '--quiet') out.quiet = true;
    else if (a === '-h' || a === '--help') out.help = true;
    else positional.push(a);
  }
  config.endpoint = positional[0];
  return out;
}

function verdictColor(verdict) {
  if (verdict === 'Full 1.0 Compliance') return green;
  if (verdict === '1.0 Compliance, Immature Type System') return green;
  if (verdict === '1.0 Compatible') return cyan;
  return red;
}

async function cmdRun(argv) {
  const { config, jsonPath, quiet, help } = parseRunArgs(argv);
  if (help || !config.endpoint) {
    process.stdout.write(USAGE);
    process.exit(config.endpoint ? 0 : 1);
  }

  console.log(bold(`\ni3X 1.0 Conformance Test Suite`));
  console.log(dim(`Target: ${config.endpoint}\n`));

  let lastPhase = null;
  const { results, summary } = await runSuite(config, (e) => {
    if (e.type === 'note') console.log(dim(`  ${e.message}`));
    if (e.type === 'phase' && !quiet) {
      lastPhase = e.name;
      console.log(bold(`\n${e.name}`));
    }
    if (e.type === 'test:end') {
      const line = `  ${SYMBOL[e.status] || '?'} ${dim(`[${String(e.index).padStart(2)}/${e.total}]`)} ${e.id} ${e.name}`;
      if (quiet && e.status !== 'fail') return;
      if (quiet && lastPhase) {
        console.log(bold(`\n${lastPhase}`));
        lastPhase = null;
      }
      console.log(line);
      if (e.status === 'fail') {
        console.log(red(`        ${wrap(e.message, 96, 8)}`));
        if (e.refUrl) console.log(dim(`        See: ${e.refTitle} — ${e.refUrl}`));
      } else if (e.status === 'warn' && e.message && !quiet) {
        console.log(yellow(`        ${wrap(e.message, 96, 8)}`));
      } else if (e.status === 'skip' && e.message && !quiet) {
        console.log(dim(`        ${e.message}`));
      } else if (e.status === 'pass' && e.message && e.message.startsWith('Note:') && !quiet) {
        console.log(dim(`        ${wrap(e.message, 96, 8)}`));
      }
    }
  });

  // ----- summary -----
  const vc = verdictColor(summary.verdict);
  const bar = '═'.repeat(64);
  console.log(`\n${bar}`);
  console.log(bold(vc(`  Result: ${summary.verdict}`)));
  console.log(`${bar}`);
  console.log(wrap(summary.headline, 76, 2));
  const cts = summary.counts;
  console.log(
    `\n  ${green(`${cts.pass} passed`)}  ${cts.fail ? red(`${cts.fail} failed`) : dim('0 failed')}  ${
      cts.warn ? yellow(`${cts.warn} warnings`) : dim('0 warnings')
    }  ${dim(`${cts.skip} skipped`)}  ${dim(`(${cts.total} total)`)}`
  );
  for (const note of summary.notes || []) console.log(dim(`  ${wrap(note, 90, 2)}`));
  const failures = [...(summary.mustFailures || []), ...(summary.mayFailures || [])];
  if (failures.length) {
    console.log(bold(`\n  Failures:`));
    for (const f of failures) {
      console.log(`  ${red('✗')} ${bold(f.id)} (${f.level}) ${f.name}`);
      console.log(`      ${wrap(f.message || '', 90, 6)}`);
      if (f.refUrl) console.log(dim(`      Spec: ${f.refUrl}`));
    }
    console.log(dim(`\n  Server developer resources: ${SDK_DOCS}`));
  }
  if ((summary.warnings || []).length) {
    console.log(bold(`\n  Warnings (advisory — do not affect the verdict):`));
    for (const w of summary.warnings) {
      console.log(`  ${yellow('⚠')} ${bold(w.id)} ${w.name}`);
      console.log(yellow(`      ${wrap(w.message || '', 90, 6)}`));
      if (w.refUrl) console.log(dim(`      Spec: ${w.refUrl}`));
    }
  }
  console.log('');

  if (jsonPath) {
    const report = { generatedBy: 'i3x-test-suite', endpoint: config.endpoint, summary, results };
    fs.writeFileSync(path.resolve(jsonPath), JSON.stringify(report, null, 2));
    console.log(dim(`Report written to ${jsonPath}\n`));
  }

  process.exit(summary.verdict === 'Not Compliant' || summary.verdict === 'Error' ? 1 : 0);
}

function wrap(text, width, indent) {
  const words = String(text || '').split(/\s+/);
  const lines = [];
  let line = '';
  for (const w of words) {
    if (line && line.length + w.length + 1 > width) {
      lines.push(line);
      line = w;
    } else {
      line = line ? `${line} ${w}` : w;
    }
  }
  if (line) lines.push(line);
  return lines.join('\n' + ' '.repeat(indent));
}

function parsePort(argv, fallback) {
  const i = argv.findIndex((a) => a === '-p' || a === '--port');
  if (i >= 0) return parseInt(argv[i + 1], 10) || fallback;
  return fallback;
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  if (cmd === 'run') return cmdRun(rest);
  if (cmd === 'serve') {
    const { startServer } = require('../server/serve');
    return startServer(parsePort(rest, 8330));
  }
  if (cmd === 'mock') {
    const { startMock } = require('../mock/server');
    return startMock(parsePort(rest, 8331));
  }
  process.stdout.write(USAGE);
  process.exit(cmd && cmd !== '-h' && cmd !== '--help' ? 1 : 0);
}

main().catch((e) => {
  console.error(red(`\nFatal: ${e.message}\n`));
  process.exit(1);
});
