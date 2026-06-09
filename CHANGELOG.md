# Changelog

Changes accepted between 1.0 Beta and the 1.0 Release.

All notable changes to the i3X RFC, Implementation Guide, and demo are documented here so that implementers can identify the exact deltas they need to adopt.

## Summary
- 2026-06-09 — Opening a new `/stream` connection while one is already active now closes the existing stream and opens the new one. The previously connected client receives a clean SSE stream close. | [#313](https://github.com/cesmii/i3X/issues/313)
- 2026-05-26 — Clients may send `lastSequenceNumber=-1` in a `/sync` call to acknowledge and clear all pending updates in a single round trip | [#311](https://github.com/cesmii/i3X/issues/311)
- 2026-05-22 — `/subscriptions/sync` response restructured: updates are now grouped into batches — `[{"sequenceNumber": N, "updates": [...]}]` — rather than a flat list where each update carried its own `sequenceNumber` | [#295](https://github.com/cesmii/i3X/issues/295)
- 2026-05-22 — Subscription management endpoints restructured: `GET /subscriptions` and `GET /subscriptions/{id}` replaced by `POST /subscriptions/list`; `DELETE /subscriptions/{id}` replaced by `POST /subscriptions/delete`; `GET /subscriptions/stream` changed to `POST`. All subscription operations now require `clientId` in the request body for client scoping | [#295](https://github.com/cesmii/i3X/issues/295)
- 2026-05-22 — `POST /objects/history` conformance level raised from MAY to MUST; servers with no historical data SHOULD implement the endpoint and return quality `GoodNoData` rather than 404 or 501 | [#308](https://github.com/cesmii/i3X/issues/308)
- 2026-05-22 — Stream delivery (`/subscriptions/stream`) conformance downgraded from SHOULD to MAY; servers backed by non-push data sources MAY satisfy `/sync` by reading the current value at poll time and SHOULD return HTTP 501 for `/subscriptions/stream` | [#310](https://github.com/cesmii/i3X/issues/310)
- 2026-05-22 — `timestamp` values MUST be UTC with no timezone offset; fractional seconds are explicitly supported (e.g., `"2025-01-08T10:30:00.123456Z"`) | [#310](https://github.com/cesmii/i3X/issues/310)
- 2026-05-04 — Sync `sequenceNumber` MUST be a 64-bit unsigned integer to avoid rollover | [#257](https://github.com/cesmii/i3X/issues/257)
- 2026-04-29 — `responseDetail` replaces `problemDetail` as the response envelope field for error and partial-success details | [#294](https://github.com/cesmii/i3X/issues/294)
- 2026-04-28 — `PUT /objects/{elementId}/value` and `PUT /objects/{elementId}/history` replaced by `PUT /objects/value` and `PUT /objects/history`, accepting elementIds in the request body as `{"updates": [{"elementId": "...", "value": {...}}, ...]}` and returning bulk responses. `GET /objects/{elementId}/history` removed — use `POST /objects/history` instead. (RFC §4.2.2, Implementation Guide, demo server)
- 2026-04-28 — `extendedAttributes` renamed to `schemaExtensions` in the object metadata response (RFC §3.1.1, Implementation Guide, and demo server)
- 2026-04-23 — `/sync` returns HTTP 206 when subscription queue overflow causes updates to be dropped | [#258](https://github.com/cesmii/i3X/issues/258) [#288](https://github.com/cesmii/i3X/issues/288) 
- 2026-04-23 — Error responses now use a `problemDetail` object (`title`, `status`, `detail`) in place of the previous `error` object (`code`, `message`). Applied to all endpoints and the demo server | [#294](https://github.com/cesmii/i3X/issues/294) 
