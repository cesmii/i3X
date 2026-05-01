# Changelog

Changes accepted between 1.0 Beta and the 1.0 Release.

All notable changes to the i3X RFC, Implementation Guide, and demo are documented here so that implementers can identify the exact deltas they need to adopt.

## Summary
- 2026-04-29 — `responseDetail` replaces `problemDetail` as the response envelope field for error and partial-success details | [#294](https://github.com/cesmii/i3X/issues/294)
- 2026-04-28 — `PUT /objects/{elementId}/value` and `PUT /objects/{elementId}/history` replaced by `PUT /objects/value` and `PUT /objects/history`, accepting elementIds in the request body as `{"updates": [{"elementId": "...", "value": {...}}, ...]}` and returning bulk responses. `GET /objects/{elementId}/history` removed — use `POST /objects/history` instead. (RFC §4.2.2, Implementation Guide, demo server)
- 2026-04-28 — `extendedAttributes` renamed to `schemaExtensions` in the object metadata response (RFC §3.1.1, Implementation Guide, and demo server)
- 2026-04-23 — `/sync` returns HTTP 206 when subscription queue overflow causes updates to be dropped | [#258](https://github.com/cesmii/i3X/issues/258) [#288](https://github.com/cesmii/i3X/issues/288) 
- 2026-04-23 — Error responses now use a `problemDetail` object (`title`, `status`, `detail`) in place of the previous `error` object (`code`, `message`). Applied to all endpoints and the demo server | [#294](https://github.com/cesmii/i3X/issues/294) 
