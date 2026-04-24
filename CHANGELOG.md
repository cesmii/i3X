# Changelog

Changes accepted between Beta and the 1.0 release.

All notable changes to the i3X RFC, Implementation Guide, and demo are documented here so that implementers can identify the exact deltas they need to adopt.

## Summary

- 2026-04-23 — `/sync` returns HTTP 206 when subscription queue overflow causes updates to be dropped | #258 #288
- 2026-04-23 — Error responses now use a `problemDetail` object (`title`, `status`, `detail`) in place of the previous `error` object (`code`, `message`). Applied to all endpoints and the demo server | #294 
