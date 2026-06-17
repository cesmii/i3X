---
name: Bug report
about: Create a report to help us improve
title: 'History responses use a `components` structure that the guide never defines'
labels: ''
assignees: ''

---

**Describe the bug**
`POST /objects/history` accepts a `maxDepth` parameter (see the request table in the Query History section), which implies composition elements recurse into their `HasComponent` children just like `POST /objects/value`. However, the guide only defines the `components` block for the *current value* endpoint, where each component maps to a single VQT. The history endpoint's documented response shape is a flat `{ isComposition, values: [...] }` with no `components` key and no description of how a composition's children appear over a time range.

As a result, a server returning history for a composition element has no specified shape to follow. The demo server currently emits, by reasonable extrapolation:

```json
"result": {
  "isComposition": true,
  "values": [],
  "components": {
    "pump-101-state": { "values": [ { "value": {...}, "quality": "Good", "timestamp": "..." } ] }
  }
}
```

i.e. each component maps to its own `{ "values": [...] }` array rather than a single VQT. This is sensible but undefined — clients cannot rely on it and two compliant servers could diverge.

**Expected behavior**
The Query History section should define the response shape for composition elements when `maxDepth > 1`, parallel to the maxDepth/`components` definition given for `POST /objects/value`. Each component should map to a time-ordered `values` array, and the interaction between the parent's own `values` and its `components` should be spelled out (e.g. parent `values: []` when the parent has no own history but its components do).

**Proposed resolution**
Add a "Response Structure with maxDepth" subsection to `POST /objects/history` mirroring the one under `maxDepth Parameter Semantics`, with an explicit example showing `components` keyed by `elementId`, each containing a `values` array of VQT objects. State whether the parent's `values` and `components` can be populated simultaneously.

**Version:**
 - Alpha (`main` branch)
 - Beta (`1.0` branch)

**Additional context**
Surfaced while validating a real `/objects/history` response from the demo server (`demo/server`). The demo had to invent the `components`-of-`values` shape because the guide is silent. Related to the empty-range and ordering ambiguities filed separately.
