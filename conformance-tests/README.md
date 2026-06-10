# i3X 1.0 Conformance Test Suite

Validates an [i3X](https://github.com/cesmii/i3X) server implementation against the **1.0 specification** and reports a compliance level. Built for the i3X working group and community server implementers.

> This suite is part of the i3X repository but is fully self-contained: all commands below are run **from this folder** (`cd` into it from the repo root first). It has zero runtime dependencies and needs only Node.js ≥ 18.17.

- **59 conformance tests** covering every required (MUST) behavior — transport & encoding, the `/info` capabilities contract, all Exploratory methods, current/historical value queries, the Subscribe lifecycle and sync acknowledgement — plus every optional (MAY) feature the server declares (updates, SSE streaming).
- **Optional features are never penalized for being omitted.** If a server *declares* a capability in `GET /info` but implements it incorrectly, that is a failure.
- Every failure explains **what's wrong** and links to the **exact section of the Implementation Guide** to consult.
- Zero runtime dependencies. Requires only **Node.js ≥ 18.17**.

## Quick start (from this folder)

```bash
npm start            # web UI → open http://localhost:8330
npm run mock         # (optional) known-good reference server at http://localhost:8331
```

Open http://localhost:8330, enter your server's versioned endpoint — e.g. `https://your-server.example.com/i3x/v1`, or `http://localhost:8331/v1` to try the bundled mock — and click **Run conformance tests**.

No browser needed? Use the CLI directly:

```bash
node bin/i3x-test.js run https://your-server.example.com/v1 --token <token>
```

> ⚠️ `npx serve` is **not** this tool — that's an unrelated npm package that serves static files. Until this package is published to npm, always run it via `npm start` / `npm run mock` / `node bin/i3x-test.js …` from this folder.

## Compliance levels

| Verdict | Meaning |
|---|---|
| **Full 1.0 Compliance** | All MUST and all declared MAY behavior passed, and the type system exposes rich structured Object Types. |
| **1.0 Compliance, Immature Type System** | Everything passed, but every Object Type schema is a primitive scalar (`number`/`string`/…). i3X expects schema-aware structured types. |
| **1.0 Compatible** | All MUST behavior passed; one or more optional features (updates, streaming) were omitted. |
| **Not Compliant** | One or more MUST tests failed, or a declared optional feature behaves incorrectly. Failures are listed with spec links. |

Advisory **SHOULD**-level findings (e.g. plain-HTTP endpoints, capability/behavior mismatches) appear as warnings and never affect the verdict.

## Using the hosted web page (public endpoints)

Open the test suite site, enter your server's full versioned endpoint (including the `/v1` prefix the spec requires, e.g. `https://your-server.example.com/i3x/v1`), choose your authentication (none / Bearer token / Basic / custom header), and click **Run conformance tests**. Progress streams live, test by test, and finishes with a verdict banner, per-failure spec links, and a downloadable JSON report.

> **Note on write tests:** if your server declares `update` capabilities, the suite verifies them by writing each sampled object's **current value back to itself** (non-destructive). Untick the write checkbox to skip writes entirely; update features are then reported as unverified.

## Running inside your own network (private endpoints)

If your endpoint isn't reachable from the public internet, run the identical experience locally. Clone or download this repository and:

```bash
npm start                             # local web UI (same page as the hosted version)
node bin/i3x-test.js run <endpoint>   # or pure CLI with live progress + summary
```

Once the package is published to npm, the no-install form also works:

```bash
npx i3x-test-suite serve
npx i3x-test-suite run https://i3x.intranet.example.com/v1 --token <token>
```

### CLI options

```
i3x-test run <endpoint> [options]
  --token <token>            Bearer token authentication
  --basic <user:pass>        HTTP Basic authentication
  --header "<Name: value>"   Custom header (e.g. API keys); repeatable
  --no-writes                Skip write tests even if update capabilities are declared
  --timeout <ms>             Per-request timeout (default 20000)
  --insecure                 Accept self-signed TLS certificates (development only)
  --json <file>              Write the full machine-readable report to a file
  --quiet                    Print only failures and the final summary
```

Exit code is `0` for any compliance/compatibility verdict and `1` for *Not Compliant*, so the CLI drops straight into CI pipelines:

```bash
i3x-test run https://staging.example.com/v1 --token "$I3X_TOKEN" --json report.json
```

## Reference mock server

A fully compliant in-memory reference server (the spec's demo pump-station model) ships with the suite — useful for seeing what *Full 1.0 Compliance* looks like, demoing the suite, and developing against a known-good peer:

```bash
i3x-test mock                  # http://localhost:8331/v1
i3x-test run http://localhost:8331/v1
```

It can also simulate spec violations to exercise the failure reporting (`MOCK_BREAK=reverseof,nullgood,nogzip,badbulk,noclearall,nosinglestream,noscope`), require auth (`MOCK_TOKEN=secret`), omit optional features (`MOCK_BREAK=omit-updates` → *1.0 Compatible*), or serve a primitive-only type registry (`MOCK_BREAK=primitive` → *Immature Type System*).

## Deploying the public instance

The web version is a single self-contained Node process (static UI + an SSE endpoint that runs the suite server-side, avoiding browser CORS restrictions against target servers):

```bash
PORT=8330 node server/serve.js
# or: npx i3x-test-suite serve -p 8330
```

Put it behind any TLS-terminating reverse proxy — either at the root of a (sub)domain or under a path prefix. The UI uses only relative URLs, so prefix-stripping proxies work; with nginx the trailing slash on `proxy_pass` is what strips the prefix:

```nginx
location /i3x-test/ {
    proxy_pass http://127.0.0.1:8330/;   # trailing slash: /i3x-test/foo → /foo
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;                  # required for the SSE progress stream
    proxy_read_timeout 1h;                # test runs stream for minutes
}
```

Operational notes:

- `I3X_MAX_RUNS` caps concurrent test runs (default 4).
- The runner makes outbound requests to user-supplied URLs by design. On a public deployment, isolate the process from internal networks (container/egress policy) as you would any URL-fetching service.
- No state is stored; reports exist only in the user's browser.

## What exactly is tested?

| Area | Tests | Notes |
|---|---|---|
| Transport & `/info` | CORE-01…07 | unauthenticated `/info`, success envelope, capabilities matrix, gzip; advisories for HTTPS and for accepting unauthenticated requests |
| Exploratory | EXP-01…22 | namespaces, object/relationship types, `reverseOf` symmetry, objects, roots, filters, metadata, bulk order/size, per-item 404s, bidirectional relationship traversal, hierarchy reachability |
| Query | QRY-01…09 | VQT shape, quality/null pairing, **value-vs-type-schema conformance**, `maxDepth`/components semantics, history range & shapes |
| Update (MAY) | UPD-01…05 | write-back of current values, read-after-write, partial failure, historical writes, 501 honesty |
| Subscribe | SUB-01…16 | create/list/client scoping (`clientId` required → 400, cross-client access → 404)/register (idempotent, partial failure)/sync (batch shape, sequence acknowledgement, `lastSequenceNumber=-1` clear-all)/unregister/SSE stream (MAY, incl. single-stream takeover)/delete/404 after delete |

Normative sources: the [Implementation Guide](../spec/IMPLEMENTATION_GUIDE.md) and [Understanding Relationships](../spec/UNDERSTANDING_RELATIONSHIPS.md) in this repository's `spec/` directory, and the [OpenAPI definition](https://api.i3x.dev/v1/openapi.json) generated by this repository's demo server (response shapes mirrored in `lib/validators.js`). The suite and the specification version together on this branch; if the specification is revised, re-check the validators and test messages against it. Implementer help: [i3X Server Developer SDK docs](https://www.i3x.dev/sdk/category/server-developers).

## Development

```bash
npm test     # self-test: runs the suite against the mock in 7 configurations
             # (compliant, updates-omitted, primitive types, broken, broken
             # subscriptions, auth ok, auth wrong) and asserts each verdict
```

Layout:

```
bin/i3x-test.js        CLI entry (run / serve / mock)
lib/engine.js          orchestrator: resolves base URL, runs tests, emits progress events
lib/report.js          verdict computation
lib/validators.js      envelope/shape/VQT validators mirroring the OpenAPI components
lib/client.js          HTTP client (auth, timeouts, raw gzip probe)
lib/specrefs.js        spec section links cited by every test
lib/tests/*.js         test definitions (transport, exploratory, query, update, subscribe)
server/                web UI + SSE API
mock/server.js         compliant reference server with optional break switches
test/selftest.js       end-to-end self-verification
```

---

*Copyright (C) CESMII, the Smart Manufacturing Institute. Test suite for the i3X 1.0 specification.*
