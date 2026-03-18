# Mock Data Source

This directory contains the mock data source for the I3X demo server. It serves static manufacturing data to exercise the full I3X API surface without requiring a real platform connection.

## Namespace Schema Files (`Namespaces/`)

Each namespace has a JSON file defining its object types using [JSON Schema Draft 4](https://json-schema.org/draft-04/schema). The files follow this structure:

```json
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "$id": "<namespace-uri>",
    "types": {
        "some-type": { ... },
        "another-type": { ... }
    }
}
```

The `types` map is a flat registry — every type in the namespace is a top-level entry, including component types. There is no nesting of type definitions.

## Expressing Composition in JSON Schema

I3X supports composite objects whose values are composed of child component values (via `HasComponent` relationships). JSON Schema has no built-in concept of "this type is composed of instances of these other types" — that relationship is an I3X concept, not a schema concept.

Within JSON Schema's constraints, component types are expressed using same-document `$ref` pointers:

```json
"measurement-type": {
    "type": "object",
    "properties": {
        "tolerance": { "type": "number" },
        "inTolerance": { "type": "boolean" },
        "value": { "$ref": "#/types/measurement-value-type" },
        "health": { "$ref": "#/types/measurement-health-type" }
    }
},
"measurement-value-type": { "type": "number" },
"measurement-health-type": { "type": "integer" }
```

This means:
- Every component type exists independently in the `types` map and is served as its own entry by the API.
- A composite type uses `$ref` to point at its component types within the same file, describing the full shape of its composed value.
- When the server loads a schema, it resolves `$ref` pointers and inlines them, so API consumers receive fully expanded schemas without needing to chase references.

## Type Extension with `allOf`

A common need is an instance that is *almost like* an existing type but has a couple of extra properties. JSON Schema's `allOf` handles this: it means "valid against all of these schemas simultaneously", which in practice expresses inheritance — the extended type satisfies the base type's shape plus adds its own properties.

```json
"temperature-sensor-type": {
    "type": "object",
    "properties": {
        "temperature": { "type": "number" },
        "unit": { "type": "string" }
    }
},
"precision-temperature-sensor-type": {
    "allOf": [
        { "$ref": "#/types/temperature-sensor-type" },
        {
            "type": "object",
            "properties": {
                "accuracy": { "type": "number" },
                "calibrationDate": { "type": "string" }
            }
        }
    ]
}
```

Both types are independent entries in the flat `types` map. The base type is fully usable on its own. The extended type composes the base via `$ref` inside `allOf`, and the server inlines that reference when serving the schema so API consumers receive the fully resolved shape.

This maps to the `InheritsFrom`/`InheritedBy` relationship types in the I3X relationship vocabulary. The `related` field on the extended type's entry in `mock_data.py` records this topology for use by the instance graph.

Note the distinction from composition:
- `allOf` / `$ref` in properties → `HasComponent` — the value *is made up of* child objects that exist independently in the graph
- `allOf` in `allOf` → `InheritsFrom` — the type *is a kind of* the base type, with the same value shape plus extensions

## UnknownType

When an instance is discovered at runtime and its type cannot be determined (e.g. during MQTT topic discovery or OPC UA browsing), the implementation should register a placeholder type called `UnknownType` in its type registry and use its `elementId` as the `typeElementId` on affected instances. This ensures the Types response always contains an entry for every `typeElementId` referenced by instances. See the Implementation Guide for guidance.

## Relationship Metadata

The `related` field on object type entries in `mock_data.py` captures I3X-specific relationship topology (e.g. which types a given type has `HasComponent` or `HasChildren` relationships with). This is internal mock data configuration — it is not part of the JSON Schema definition and does not appear in the API response. The I3X instance graph (the `/objects` endpoints) is the authoritative source for relationship information at runtime.
