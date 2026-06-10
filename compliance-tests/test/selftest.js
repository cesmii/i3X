'use strict';

// Self-test: runs the conformance suite against the bundled mock server in
// several configurations and asserts the expected verdict for each.
// Usage: npm test

const { runSuite } = require('../lib/engine');

function withMock(env, port, fn) {
  return new Promise((resolve, reject) => {
    const prevBreak = process.env.MOCK_BREAK;
    const prevToken = process.env.MOCK_TOKEN;
    Object.assign(process.env, { MOCK_BREAK: '', MOCK_TOKEN: '' }, env);
    // mock/server reads env at require time — bust the cache per scenario
    delete require.cache[require.resolve('../mock/server')];
    const { startMock } = require('../mock/server');
    const server = startMock(port, '127.0.0.1');
    server.on('listening', async () => {
      try {
        resolve(await fn());
      } catch (e) {
        reject(e);
      } finally {
        server.close();
        process.env.MOCK_BREAK = prevBreak || '';
        process.env.MOCK_TOKEN = prevToken || '';
      }
    });
    server.on('error', reject);
  });
}

const SCENARIOS = [
  { name: 'compliant server', env: {}, config: {}, expect: 'Full 1.0 Compliance' },
  { name: 'updates omitted', env: { MOCK_BREAK: 'omit-updates' }, config: {}, expect: '1.0 Compatible' },
  { name: 'primitive-only types', env: { MOCK_BREAK: 'primitive' }, config: {}, expect: '1.0 Compliance, Immature Type System' },
  { name: 'broken server', env: { MOCK_BREAK: 'reverseof,nullgood,nogzip,badbulk' }, config: {}, expect: 'Not Compliant' },
  {
    name: 'bearer auth',
    env: { MOCK_TOKEN: 'selftest-token' },
    config: { auth: { type: 'bearer', token: 'selftest-token' } },
    expect: 'Full 1.0 Compliance'
  },
  { name: 'wrong credentials', env: { MOCK_TOKEN: 'selftest-token' }, config: {}, expect: 'Not Compliant' }
];

(async () => {
  let port = 18341;
  let failed = 0;
  for (const s of SCENARIOS) {
    const p = port++;
    const verdict = await withMock(s.env, p, async () => {
      const { summary } = await runSuite({ endpoint: `http://127.0.0.1:${p}`, ...s.config }, () => {});
      return summary.verdict;
    });
    const ok = verdict === s.expect;
    if (!ok) failed++;
    console.log(`${ok ? '✓' : '✗'} ${s.name}: ${verdict}${ok ? '' : ` (expected ${s.expect})`}`);
  }
  if (failed) {
    console.error(`\n${failed} self-test scenario(s) failed`);
    process.exit(1);
  }
  console.log('\nAll self-test scenarios passed.');
  process.exit(0); // open keep-alive sockets from stream probes would otherwise hold the loop
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
