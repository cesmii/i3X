# i3X 1.0 Conformance Test Suite — project context

Conformance test suite for i3X 1.0 server implementations, built for the CESMII i3X working group. Community implementers use it via a hosted web page, a self-hosted web UI, or a CLI — all from this one package.

## Commands

```bash
npm start                                  # web UI on :8330 (same page as the hosted version)
npm run mock                               # compliant reference server on :8331 (/v1 prefix)
npm test                                   # self-test: suite vs mock in 7 configs, asserts each verdict
node bin/i3x-test.js run <endpoint> [...]  # CLI runner (see --help)
```

There is no build step, linter config, or test framework — plain Node, run directly.

## Hard invariants (do not change casually)

- **Zero runtime dependencies, Node ≥ 18.17.** This is deliberate so community members can run it with nothing but Node. Don't add packages; built-in `fetch`, `node:http`, `node:zlib` cover everything.
- **Verdict strings are working-group-approved wording** and are string-matched in `bin/i3x-test.js`, `server/public/index.html`, and `test/selftest.js`:
  - `Full 1.0 Compliance` (green)
  - `1.0 Compliance, Immature Type System` (green) — all passed but every ObjectType schema is a primitive scalar
  - `1.0 Compatible` (teal/cyan — deliberately not orange; orange is reserved for warnings)
  - `Not Compliant` (red)
- **MAY features omitted ⇒ never a failure** (verdict caps at "1.0 Compatible"). A *declared* capability that misbehaves ⇒ failure.
- **SHOULD-level findings are warnings only** and never affect the verdict (e.g. plain HTTP, accepting unauthenticated requests, 501-honesty). The working group explicitly does not want to block people who disable auth for testing.
- **Write tests are non-destructive**: they write each object's current value back to itself. UPD-02 read-after-write does NOT require equality — live data sources legitimately move between write and read; a mismatch is a pass with a "Note:" message.
- **CLI exit code**: 0 for any compliance/compatible verdict, 1 only for Not Compliant/Error (CI-friendly).

## Architecture

```
lib/engine.js        orchestrator: resolves base URL (auto-probes <url>/v1 as fallback),
                     runs phases sequentially, emits events, feature-gates MAY tests
lib/report.js        verdict computation + isRichTypeSystem()
lib/validators.js    mini JSON Schema validator + SHAPES registry mirroring the OpenAPI
                     components + envelope/VQT semantic checks
lib/client.js        fetch wrapper (auth, timeout); rawGzipProbe uses node:http because
                     fetch hides Content-Encoding
lib/specrefs.js      REFS map: every test's `ref` key → Implementation Guide anchor URL
lib/tests/*.js       test definitions per phase (transport, exploratory, query, update, subscribe)
bin/i3x-test.js      CLI (run / serve / mock)
server/serve.js      web server: static UI + POST /api/run → SSE event stream
server/public/       single-file UI (inline CSS/JS, no framework) + logo/favicon assets
mock/server.js       compliant reference server (demo pump-station model)
test/selftest.js     asserts the verdict for 6 mock configurations
spec/                snapshot of the OpenAPI definition (see below); the normative
                     markdown documents live in the repo's top-level spec/
```

### Test definition shape

```js
{ id: 'QRY-01', name: '…', level: 'MUST'|'MAY'|'SHOULD',
  feature: 'update.current',   // MAY only: dotted path into /info capabilities; engine
                               // auto-skips (reason 'omitted') when declared false
  ref: 'queryMethods',         // key into lib/specrefs.js REFS
  async run(ctx) { return pass/fail/warn/skip(message) } }   // helpers in lib/results.js
```

Tests run sequentially and share `ctx` (client, config, namespaces, objectTypes/typesById, relationshipTypes/relById, objects/objectsById, currentValues, subscriptionId/clientId, …). Missing prerequisites ⇒ `skip(…, 'blocked')`. Test IDs are referenced in the README table — keep numbering stable, append new ones.

### Display conventions

- `pass()` messages are normally hidden; a pass message starting with **`Note:`** is rendered (muted gray) in both CLI and web UI — used when a pass needs an honest caveat.
- Warnings are itemized in `summary.warnings` and repeated in the final CLI summary and web verdict banner.
- Web UI consumes `POST /api/run` as SSE (`fetch` + reader, since EventSource can't POST). Event types: `start`, `note`, `phase`, `test:start`, `test:end`, `done`.

## Normative sources & spec drift

The canonical IMPLEMENTATION_GUIDE.md and UNDERSTANDING_RELATIONSHIPS.md live in the repo's top-level `spec/` — do not keep copies here; the suite versions together with the spec on this branch. This folder's `spec/` holds only a snapshot of https://api.i3x.dev/v1/openapi.json (response shapes — mirrored by hand in `lib/validators.js` SHAPES).

If the spec changes: re-derive SHAPES and any quoted requirement text in test messages, refresh the openapi snapshot, and check the anchors in `lib/specrefs.js` still resolve against `../spec/IMPLEMENTATION_GUIDE.md` headings. Jon edits the Implementation Guide too — e.g. the "production implementations MUST require authentication" wording (auth note in the UI + CORE-07) was added to the guide *after* this suite referenced it.

npm publish note: `package.json` `files` includes `spec/`, which no longer contains the guides. Before publishing to npm, add a `prepack` step that copies `../spec/IMPLEMENTATION_GUIDE.md` and `../spec/UNDERSTANDING_RELATIONSHIPS.md` in (and ignore the copies), so the tarball stays self-contained.

## Mock server switches

`MOCK_TOKEN=secret` — require bearer auth (except `/info`, which the spec keeps open).
`MOCK_BREAK=` comma list: `reverseof` | `nullgood` | `nogzip` | `badbulk` | `noclearall` | `nosinglestream` | `noscope` (→ Not Compliant), `omit-updates` (→ 1.0 Compatible), `primitive` (→ Immature Type System). `test/selftest.js` depends on these.

## History / open threads

- 2026-06-10 (clientId scoping): community issue confirmed valid — guide mandates required `clientId` + client-scoped subscriptions, but the OpenAPI had it optional and demo/mock were lenient. Demo server and mock made strict per the guide (missing `clientId` → 400, cross-client access → 404, indistinguishable from nonexistent); added SUB-15/16 and the `noscope` break switch. The demo's OpenAPI regenerates from its Pydantic models, so refresh `spec/openapi.json` once the deployed demo is updated. SDK docs "Pattern 7" still needs its repository ops keyed by (clientId, subscriptionId) — maintained outside this repo.

- 2026-06-10: full audit against the current Implementation Guide and CHANGELOG (all entries through #313). Existing tests already matched (history-as-MUST with GoodNoData, sync batches, POST-style subscription endpoints, UTC-only timestamps); added SUB-13 (`lastSequenceNumber=-1` clear-all, #311) and SUB-14 (single-stream takeover with clean close, #313). SUB-13/14 run mid-phase (after SUB-07/SUB-09) while the suite's subscription is still alive — array order ≠ id order there, deliberately.
- An independent server implementation was validated against this suite (2026-06-10); the suite's findings were confirmed correct.
- The project was moved into the main i3X repo from a standalone folder; it was never published to npm under `i3x-test-suite` (README `npx` forms are aspirational until published).
- Hosted instance deployed 2026-06-10: systemd unit (`i3x-compliance.service`) running `node bin/i3x-test.js serve` bound to 127.0.0.1:8330, behind nginx at the `/compliance/` path prefix (trailing-slash `proxy_pass` strips the prefix; UI uses relative URLs to support this).
