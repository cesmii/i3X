# I3X API Response Formats

This document describes the response formats used by the I3X API. See `response-schemas.json` for formal JSON Schema definitions.

All responses follow one of three shapes:

```
┌──────────────────┬──────────────────────────────────────────┬──────────────────────────────────────────────────┐
│      Format      │                 Endpoints                │                     Structure                    │
├──────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Success (single) │ GET /namespaces                          │ {"success": true, "result": <data>}              │
│                  │ GET /objecttypes                         │                                                  │
│                  │ GET /relationshiptypes                   │                                                  │
│                  │ GET /objects                             │                                                  │
│                  │ POST /subscriptions                      │                                                  │
│                  │ GET /subscriptions                       │                                                  │
│                  │ GET /subscriptions/{id}                  │                                                  │
│                  │ POST /subscriptions/{id}/register        │                                                  │
│                  │ POST /subscriptions/{id}/unregister      │                                                  │
│                  │ POST /subscriptions/{id}/sync            │                                                  │
│                  │ DELETE /subscriptions/{id}               │                                                  │
│                  │ PUT /objects/{elementId}/value           │                                                  │
├──────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Bulk             │ POST /objecttypes/query                  │ {"success": bool,                                │
│                  │ POST /relationshiptypes/query            │  "result": {                                     │
│                  │ POST /objects/list                       │    "succeeded": [{"elementId","result"}],        │
│                  │ POST /objects/related                    │    "failed":    [{"elementId","error"}]          │
│                  │ POST /objects/value                      │  }}                                              │
│                  │ POST /objects/history                    │ success=false if any item failed                 │
├──────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Error            │ Any endpoint (HTTP 4xx/5xx)              │ {"success": false,                               │
│                  │                                          │  "error": {"message": "..."}}                    │
├──────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ SSE Stream       │ GET /subscriptions/{id}/stream           │ data: [{"elementId","value","quality",           │
│                  │                                          │         "timestamp"}]                            │
└──────────────────┴──────────────────────────────────────────┴──────────────────────────────────────────────────┘
```

## Core Concepts

### VQT (Value-Quality-Timestamp)
The standard structure for time-series data from a data source:
```json
{
  "value": <any>,
  "quality": "Good",
  "timestamp": "2025-10-28T18:20:44Z"
}
```

---

## Response Schemas

### 1. Success Response (single result)

All GET endpoints and most action endpoints return this shape.

```json
{
  "success": true,
  "result": <data>
}
```

Example — `GET /namespaces`:
```json
{
  "success": true,
  "result": [
    { "uri": "https://cesmii.org/i3x", "displayName": "I3X" }
  ]
}
```

Example — `POST /subscriptions`:
```json
{
  "success": true,
  "result": {
    "subscriptionId": "0",
    "message": "Subscription created successfully."
  }
}
```

Example — `PUT /objects/{elementId}/value` (write succeeded):
```json
{
  "success": true,
  "result": null
}
```

---

### 2. Bulk Response

POST query endpoints that accept an array of `elementIds` return a bulk shape. Each element is independently succeeded or failed. The top-level `success` is `false` if **any** element failed.

```json
{
  "success": false,
  "result": {
    "succeeded": [
      {
        "elementId": "pump-101",
        "result": { ... }
      }
    ],
    "failed": [
      {
        "elementId": "non-existent",
        "error": { "message": "Element not found: non-existent" }
      }
    ]
  }
}
```

#### Value result shape (`POST /objects/value`)

Simple (leaf) element:
```json
{
  "elementId": "sensor-001",
  "result": {
    "isComposition": false,
    "value": 67.1,
    "quality": "Good",
    "timestamp": "2025-10-28T10:15:30Z"
  }
}
```

Composition element (when `maxDepth > 1`):
```json
{
  "elementId": "pump-101-measurements",
  "result": {
    "isComposition": true,
    "value": {
      "_value": { "value": null, "quality": "GoodNoData", "timestamp": "..." },
      "pump-101-bearing-temperature": { "value": 70.34, "quality": "Good", "timestamp": "..." }
    }
  }
}
```

- `_value` contains the parent element's own VQT
- Other keys are child `elementId`s (HasComponent children)

#### History result shape (`POST /objects/history`)

```json
{
  "elementId": "sensor-001",
  "result": [
    { "isComposition": false, "value": 67.1, "quality": "Good", "timestamp": "2025-10-28T10:15:30Z" },
    { "isComposition": false, "value": 54.9, "quality": "Good", "timestamp": "2025-10-27T10:15:30Z" }
  ]
}
```

---

### 3. Error Response

Returned for HTTP 4xx/5xx responses.

```json
{
  "success": false,
  "error": { "message": "Human-readable error message" }
}
```

---

### 4. SSE Stream Events (`GET /subscriptions/{id}/stream`)

Each SSE event is a JSON array of flat value updates:

```
data: [{"elementId": "sensor-001", "value": 72.5, "quality": "Good", "timestamp": "2025-01-08T10:30:00Z"}]
```

---

### 5. Sync Response (`POST /subscriptions/{id}/sync`)

Returns all pending queued updates, each with a sequence number for acknowledgement:

```json
{
  "success": true,
  "result": [
    { "sequenceNumber": 1, "elementId": "sensor-001", "value": 72.5, "quality": "Good", "timestamp": "2025-01-08T10:30:00Z" },
    { "sequenceNumber": 2, "elementId": "sensor-002", "value": 18.3, "quality": "Good", "timestamp": "2025-01-08T10:30:01Z" }
  ]
}
```

---

## Design Rationale

### Why a consistent `{success, result}` envelope?
- Clients can always check `success` before reading `result`
- Error shape is predictable regardless of which endpoint failed
- Bulk operations surface partial failures without using HTTP error codes

### Why `succeeded`/`failed` instead of a flat array?
- Clearly separates items that worked from items that didn't
- Clients can process successes independently without inspecting each item for a status flag
- `success: false` at the top level signals that action is needed without forcing clients to iterate all items first

### Why VQT for subscription updates?
- Consistent with query value format — same parsing logic for polling and streaming
- `sequenceNumber` on sync items enables reliable at-least-once acknowledgement
