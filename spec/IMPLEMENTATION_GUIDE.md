# i3X Implementation Guide

This document provides guidance for implementing i3X (Industrial Information Interface eXchange), and is intended to be used by developers creating i3X servers and clients.

## Status of This Document

This document is a working draft, and should not be considered complete or normative. This guide is derived from RFC 001 "Common API for Industrial Information Interface eXchange (i3X)". All contents are subject to change.

## Table of Contents

- [Introduction](#introduction)
- [Compliance](#compliance)
- [Transport & Encoding](#transport--encoding)
  - [Security & Authentication](#security--authentication)
  - [Versioning](#versioning)
- [Response Format](#response-format)
  - [Bulk Response](#bulk-response)
- [Address Space](#address-space)
  - [ElementId and DisplayName](#elementid-and-displayname)
  - [Namespaces](#namespaces)
  - [Object Types](#object-types)
  - [Relationship Types](#relationship-types)
  - [Objects](#objects)
- [Exploratory Methods](#exploratory-methods)
  - [Server Capabilities Endpoints](#server-capabilities-endpoints)
  - [Namespace Endpoints](#namespace-endpoints)
  - [Object Type Endpoints](#object-type-endpoints)
  - [Relationship Type Endpoints](#relationship-type-endpoints)
  - [Object Endpoints](#object-endpoints)
- [Query Methods](#query-methods)
- [Update Methods](#update-methods)
- [Subscribe Methods](#subscribe-methods)
  - [Subscriptions](#subscriptions)
  - [Registering and Unregistering Objects](#registering-and-unregistering-objects)
  - [Streaming](#streaming)
  - [Sync](#sync)
  - [Subscription Life Cycle](#subscription-life-cycle)
- [Appendix](#appendix-for-now)
  - [Relationship Semantics](#relationship-semantics)
    - [HasParent / HasChildren](#hasparent--haschildren)
    - [HasComponent / ComponentOf (Composition)](#hascomponent--componentof-composition)
  - [maxDepth Parameter Semantics](#maxdepth-parameter-semantics)
  - [Error Handling](#error-handling)
  - [Pagination](#pagination)

## Introduction
i3X is an HTTP-based API for interacting with industrial systems. It defines a standard interface between clients and servers for discovery, browsing, reading, writing, and subscribing to industrial data.

i3X exposes industrial systems through schema-aware information models. Data is represented as typed objects with attributes, metadata, and relationships, allowing clients to interact with both values and structure in a consistent way.

## Compliance
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are interpreted as described in Internet RFC 2119.

i3X consists of the following high level capabilities.

- **Exploratory** browse and discover the address space
- **Query** read the current or historical values of Objects
- **Update** write current or historical data to Objects
- **Subscribe** subscribe to data changes for Objects

Below are the required capabilities for all i3X compliant Clients and Servers.

**Requirements**
* Exploratory
  * MUST support all [Exploratory Methods](#exploratory-methods)
* Query
  * MUST support Current Value (`objects/value`) as defined in [Query Methods](#query-methods)
  * MAY support History Value (`objects/history`)
* Update
  * MAY support [Update Methods](#update-methods)
* Subscribe
  * MUST support base [Subscribe Methods](#subscribe-methods) (create, delete, list, register objects, unregister objects)
  * MUST support Sync (`/subscriptions/sync`)
  * SHOULD support Stream (`/subscriptions/stream`)
  
## Transport & Encoding

i3X is RESTful HTTP-based API and relies on HTTP for transport. It includes typical request/response patterns as well as SSE (Server Sent Events) for Subscribe capabilities.

In addition to an HTTP based transport, i3X uses JSON encoding to exchange data between the client and the server and clients may request compression through gzip.

- All i3X requests MUST include `Content-Type: application/json` and `Accept: application/json` in the HTTP header.
- When i3x requests include `Accept-Encoding: gzip`, servers MUST respond with `Content-Encoding: gzip` where the response is compressed using gzip.

### Security & Authentication

i3X relies on HTTP security best practices to secure communication between the client and server. This includes the use of HTTPs.

- Implementations MUST support encrypted transport (HTTPS) in production
- TLS 1.2 or higher SHOULD be used
- Self-signed certificates MAY be used for development
- Servers SHOULD limit client access based on the token

### Versioning

The i3X specification uses **semantic versioning** (`MAJOR.MINOR`):

All servers MUST implement a `GET /info` endpoint that returns information about the server's capabilities. This endpoint can also be used for health checks, as it is assumed the server will respond to this request when running. See the [Server Capabilities Endpoints](#server-capabilities-endpoints) section for details.

Clients SHOULD use `GET /info` to discover the `specVersion` and `capabilities` supported by a server before making other API calls.

The server MUST prefix API endpoints with `baseURL/v1/namespaces` where the `v1` is the version number. This version will only be incremented (ex. v2) if there is a future
version of the API with a breaking change. `baseURL` is server dependent.

## Response Format

All i3X responses follow a consistent response shape.

Successful responses return an HTTP 200 with the following response shape. The result shape is specific to the endpoint.

```json
{
  "success": true,
  "result": <data>
}
```

Error responses return HTTP 4xx/5xx (see [Error Handling](#error-handling)) with the following shape. The message contains Server specific details on the cause of the failure.

```json
{
  "success": false,
  "error": {
    "message": "failure message"
  }
}
```

Examples:

```json
// GET /namespaces
{ "success": true, "result": [{ "uri": "https://cesmii.org/i3x", "displayName": "I3X" }] }

// POST /subscriptions
{ "success": true, "result": { "subscriptionId": "Xf9q8wL1...", "displayName": "mySubscription" } }

// PUT /objects/{elementId}/value (write succeeded)
{ "success": true, "result": null }
```

### Bulk Response

POST query endpoints that accept an array of `elementIds` return a bulk shape. Each element is independently succeeded or failed. The top-level `success` is `false` if **any** element failed.

The Server's response MUST be in the same order and the same size as the request, allowing clients to quickly index results.

```json
{
  "success": false,
  "results": [
    {
      "success": true,
      "elementId": "pump-101",
      "result": { ... }
    },
    {
      "success": false,
      "elementId": "non-existent",
      "error": { "message": "Element not found: non-existent" }
    }
  ]
}
```

### Design Rationale

**Why a consistent `{success, result}` envelope?**
- Clients can always check `success` before reading `result`
- Error shape is predictable regardless of which endpoint failed
- Bulk operations surface partial failures without using HTTP error codes

**Why return bulk results in a flat array with succes/failure included in each row?**
- `success: false` at the top level signals that action is needed without forcing clients to iterate all items first
- Clients rely on the results being in the same order as the request, making lookups for a specific elementid faster

---

## Address Space
The i3X server address space consists of the following elements.

- **Namespaces**
  - A logical way to group elements in an i3X server. Object Types, Objects, and Relationship Types all belong to a namespace.
- **Object Types** 
  - Schema definitions that describe the shape of an Object's value. For example a Boiler might have a schema with temperature and pressure attributes.
- **Objects** 
  - Instantiations or instances of an Object Type. Objects can be read, written and subscribed to. For example, a server might have Boiler1 and Boiler2 Objects that represent two boilers at a facility, and both are backed by a Boiler Object Type. When the Boiler1 value is read, it returns data that conforms to the Boiler Object Type schema.
- **Relationship Types** 
  - Objects can be related to one another via Relationship Types. The simplest example is parent and child relationship, but graph and other relationship types are supported.

The example response payloads used in this section are meant to be representative but not exhaustive, and are used to provide a general overview of the address space. See the corresponding Method sections below for full descriptions of request/response.

### ElementId and DisplayName
All elements in the namespace must have an ElementId and DisplayName.

An ElementId is a platform-specific unique string identifier. Each element in the address space must have a unique elementId. The following are requirements for ElementIds.

**Requirements:**
- ElementIds MUST be strings with the following constraints
  - MUST be case-insensitive
  - MUST not contain leading or trailing white spaces
  - MUST not contain non-printable characters
- ElementIds MUST be unique within the scope of the platform
- ElementIds SHOULD be persistent (the same element always has the same ID)
- ElementIds SHOULD be human-readable when practical

Below are examples of ElementIds.
```
machine-001
sensor_temperature_01
urn:example:equipment:pump:123
MachineType
HasParent
```

DisplayName is the human readable name often used when displaying the Namespace, Object, etc to a user. For example a Boiler Object might have the following definition, where the elementId makes it unique in the server, and the displayName makes it easy to display to a user.

```json
{
  "elementId": "site-area-line-boiler1",
  "displayName": "Boiler1",
  "namespaceUri": "https://example.com/ns/sensors"
}
```

### Namespaces

A Namespace provides a logical grouping of *types* within the i3X address space — specifically ObjectTypes and Relationship Types. Object instances do not belong to a Namespace; they exist in the server's implicit address space. The namespace of an instance's type is accessible via `typeNamespaceUri` on the instance response when `includeMetadata=true`.

When used to reference an external Namespace definition (eg: an OPC UA Companion Specification), the URI should match that of the external Namespace.

When an implementation of an external Namespace is in-exact, by convention, the Namespace URI SHOULD be suffixed with a `projection` query string indicating the source of the adaption.

For example, by default the project MAY be called i3X: http://opcfoundation.org/UA/Robotics/?projection=i3X

The following is an example of a Namespace definition.

[TODO] - should a namespace also have an elementId to make it consistent with everything else? What if we add a GET /namesapce/{id} route?

```json
  {
    "uri": "https://cesmii.org/i3X",
    "displayName": "I3X"
  }
```

**Requirements**
- A server MUST have at least one Namespace
- Each Namespace MUST have a unique URI
- Each ObjectType and Relationship Type MUST belong to one and only one Namespace

Below are example URI patterns:

```
https://www.company.com/ns/equipment
https://www.isa.org/isa95
urn:i3x:relationships
```

### Object Types

Object Types define the schema (structure, attributes) for a class of Objects. They are analogous to classes in object-oriented programming. When an Object is read, the value returned conforms to the schema defined by the Object Type.

Below is an example of an Object Type in an i3X server. Note the `schema` attribute contains the JSON Schema definition of the object. For more information on JSON Schema see https://json-schema.org/. i3X used JSON Schema to define Object Types.

```json
{
  "elementId": "TemperatureSensorType",
  "displayName": "Temperature Sensor",
  "namespaceUri": "https://example.com/ns/sensors",
  "version": "1.0.0",
  "schema": {
    "type": "object",
    "properties": {
      "temperature": { "type": "number" },
      "unit": { "type": "string", "enum": ["C", "F", "K"] }
    }
  }
}
```

**Unknown types: `UnknownType`**

When an instance's type cannot be determined at discovery or import time, implementations SHOULD register a placeholder type named `UnknownType` in their type registry and use its `elementId` as the `typeElementId` on all affected instances. This ensures the Types response always contains an entry for every `typeElementId` referenced by instances. The `UnknownType` schema should be `{"type": "object"}`. The choice of `elementId` is implementation-specific.

**Requirements**
- An Object Type MUST have a JSON Schema definition
- An Object Type MUST belong to one Namespace
- An Object Type SHOULD have a version in Semantic Versioning format (e.g. `"1.0.0"`)

The standard creates the necessary hooks to identify the version of an object type, but it is up to implementations to manage multiple versions if necessary.

### Relationship Types

Relationship Types define the relationships between Objects. The most common relationship type is often parent/child, but relationship types can can include composition, inheritance, graph, etc.
Every Relationship Type MUST define a `reverseOf` that is also registered in the address space.

Below is an example of two Relationship Type definitions.

```json
[
 {
    "elementId": "HasParent",
    "displayName": "HasParent",
    "namespaceUri": "https://cesmii.org/i3x",
    "reverseOf": "HasChildren"
  },
  {
    "elementId": "HasChildren",
    "displayName": "HasChildren",
    "namespaceUri": "https://cesmii.org/i3x",
    "reverseOf": "HasParent"
  },
  {
    "elementId": "HasComponent",
    "displayName": "HasComponent",
    "namespaceUri": "https://cesmii.org/i3x",
    "reverseOf": "ComponentOf"
  },
  {
    "elementId": "ComponentOf",
    "displayName": "ComponentOf",
    "namespaceUri": "https://cesmii.org/i3x",
    "reverseOf": "HasComponent"
  }
]
```

**Expressing type inheritance with `allOf`**

When one Object Type is a specialization of another (i.e., it `InheritsFrom` a base type), express this in the JSON Schema using `allOf`. The derived type references the base type within the same namespace schema file and adds its own properties:

```json
"temperature-sensor-type": {
    "type": "object",
    "properties": {
        "temperature": { "type": "number" },
        "unit": { "type": "string" }
    }
},
"precision-temperature-sensor-type": {
    "description": "Temperature sensor extended with accuracy and calibration metadata",
    "allOf": [
        { "$ref": "#/types/temperature-sensor-type" },
        {
            "type": "object",
            "properties": {
                "accuracy": { "type": "number" },
                "calibrationDate": { "type": "string" }
            },
            "required": ["accuracy", "calibrationDate"]
        }
    ]
}
```

Both types are independent entries in the flat `types` map. The server resolves the `$ref` and inlines the base type's properties when serving the schema, so clients receive the fully expanded shape.

The corresponding Object Type entries in the address space record the relationship:

```json
{ "elementId": "temperature-sensor-type", ... },
{
  "elementId": "precision-temperature-sensor-type",
  ...
  "related": { "relationshipType": "InheritsFrom", "types": ["temperature-sensor-type"] }
}
```

An instance typed as `precision-temperature-sensor-type` simply sets `typeElementId` to that type's `elementId` — no other change is needed on the instance:

```json
{
  "elementId": "sensor-302",
  "typeElementId": "precision-temperature-sensor-type",
  ...
}
```

Distinguish inheritance from composition: `allOf` with `$ref` means "is a kind of" (`InheritsFrom`); a `$ref` inside `properties` means "is made up of" (`HasComponent`).

### Objects

Objects are actual equipment, sensors, or processes with values. Their values are defined by Object Types and they can be related via Relationship Types. For example, we may have the following Objects in the server.

```
Production Line A (Line) [parent]
├── Machine 1 (CNCType) [child]
├── Machine 2 (PressType) [child]
└── Machine 3 (PackagingType) [child]
```
Here `Production Line A` is the parent object of type `Line`, and the machines are child objects of different types.

The definition of an Object looks as follows.

```json
{
  "elementId": "string",
  "displayName": "string",
  "typeElementId": "string",
  "parentId": "string",
  "isComposition": false,
  "isExtended": false
}
```

**Requirements:**

- The Object's value, which is queried in the `objects/value` endpoint MUST conform to the ObjectType schema set by the `typeElementId` attribute. 
- If `isExtended=true` the Object may have additional attributes not included in the `typeElementId` schema. Use `includeMetadata=true` to see the additional attributes.
- Objects whose type cannot be determined SHOULD set `typeElementId` to the `elementId` of the `UnknownType` placeholder registered in the type registry.
- The Server MUST have at least one root Object which is queried using the `/objects?root=true` endpoint. This allows clients to progressively browse the address space from one or more root objects.

## Exploratory Methods

i3X Servers exposes exploratory methods to browse the i3X address space. This includes the ability to browse Namespaces, Types, Objects, and Object relationships. This section covers the API calls included in Exploratory methods.

### Server Capabilities Endpoints

#### `GET` /info

Returns the server version and capabilities. Clients SHOULD call this endpoint before making other API calls to confirm the server supports the features they require. This endpoint also serves as a health check.

- This endpoint MUST NOT require authentication

**Parameters:** None

**Response:**

```json
{
  "specVersion": "1.0",
  "serverVersion": "2.3.1",
  "serverName": "myi3XServer",
  "capabilities": {
    "query": {
      "history": false
    },
    "update": {
      "current": false,
      "history": false
    },
    "subscribe": {
      "stream": true
    }
  }
}
```

| Field                           | Type | Required | Description                                                        |
|---------------------------------|------|----------|--------------------------------------------------------------------|
| `specVersion`                   | string | Yes | The i3X specification version implemented, e.g., `"1.0"`           |
| `serverVersion`                 | string | No | The server implementation's own version. Format is vendor-defined. |
| `serverName`                    | string | No | Human-readable name for this server or deployment                  |
| `capabilities`                  | object | Yes | Declares which optional features this server supports              |
| `capabilities.query.history`    | boolean | Yes | True if `POST /objects/history` is supported                       |
| `capabilities.update.current`   | boolean | Yes | True if `PUT /objects/{elementId}/value` is supported              |
| `capabilities.update.history`   | boolean | Yes | True if `PUT /objects/{elementId}/history` is supported            |
| `capabilities.subscribe.stream` | boolean | Yes | True if `POST /subscriptions/stream` is supported                  |


### Namespace Endpoints

#### `GET` /namespaces

Returns all the Namespaces for the server.

**Parameters:** None

**Response:**

```json
{
  "success": true,
  "result": [
    {
      "uri": "string",
      "displayName": "string"
    }
  ]
}
```

---

### Object Type Endpoints

#### `GET` /objecttypes

Returns a list of all Object Types, optionally filtered by Namespace.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `namespaceUri` | string | No | When set, returns Object Types that belong to the Namespace. If not set, all Object Types are returned. |

**Response:**

Note the JSON Schema definition for the Object Type is placed under the `schema` attribute.

```json
{
  "success": true,
  "result": [
    {
      "elementId": "string",
      "displayName": "string",
      "namespaceUri": "string",
      "sourceTypeId": "string",
      "version": "1.0.0",
      "schema": {...}
    }
  ]
}
```

| Field          | Type        | Required | Description                                                                    |
|----------------|-------------|----------|--------------------------------------------------------------------------------|
| `elementId`    | string      | Yes      | Unique identifier                                                              |
| `displayName`  | string      | Yes      | Friendly name                                                                  |
| `namespaceUri` | string      | Yes      | Namespace that the type is associated with                                     |
| `sourceTypeId`       | string      | Yes      | Class or member of the Namespace that defines this type                        |
| `version`      | string      | No       | Optional type version in Semantic Versioning format (e.g. `"1.0.0"`)           |
| `schema`       | json schema | Yes      | The JSON Schema definition for the type                                        |

---

#### `POST` /objecttypes/query

Returns one or more Object Types given a collection of elementIds.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elementIds` | string[] | Yes | One or more elementIds to query |

```json
{
  "elementIds": [
    "string"
  ]
}
```

**Response:**

```json
{
  "success": false,
  "results": [
    {
      "success": true,
      "elementId": "string",
      "result": {
        "elementId": "string",
        "displayName": "string",
        "namespaceUri": "string",
        "sourceTypeId": "string",
        "version": "1.0.0",
        "schema": {}
      }
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Object type not found: string" }
    }
  ]
}
```

---

### Relationship Type Endpoints

#### `GET` /relationshiptypes

Returns a list of all Relationship Types, optionally filtered by Namespace.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `namespaceUri` | string | No | When set, returns types that belong to the Namespace. If not set, all types are returned. |

**Response:**

```json
{
  "success": true,
  "result": [
    {
      "elementId": "string",
      "displayName": "string",
      "namespaceUri": "string",
      "relationshipId": "string",
      "reverseOf": "string"
    }
  ]
}
```

| Field            | Type        | Required | Description                                                                    |
|------------------|-------------|----------|--------------------------------------------------------------------------------|
| `elementId`      | string      | Yes      | Unique identifier                                                              |
| `displayName`    | string      | Yes      | Friendly name                                                                  |
| `namespaceUri`   | string      | Yes      | Namespace that the type is associated with                                     |
| `relationshipId` | string      | Yes      | Class or member of the Namespace that defines this relationshipType            |
| `reverseOf `     | string      | Yes      | The elementId of the reverse relationship. All relationships MUST have a reverse |

---

#### `POST` /relationshiptypes/query

Returns one or more Relationship Types given a collection of elementIds.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elementIds` | string[] | Yes | One or more elementIds to query |

```json
{
  "elementIds": [
    "string"
  ]
}
```

**Response:**

```json
{
  "success": false,
  "results": [
    {
      "success": true,
      "elementId": "string",
      "result": {
        "elementId": "string",
        "displayName": "string",
        "namespaceUri": "string",
        "relationshipId": "string",
        "reverseOf": "string"
      }
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Relationship type not found: string" }
    }
  ]
}
```

---

### Object Endpoints

#### `GET` /objects

Returns a list of all Objects, optionally filtered by `typeElementId`. This allows a client to ask for all Objects of a given type.

**Parameters:**

| Name              | Type | Required | Description                                                                                 |
|-------------------|------|----------|---------------------------------------------------------------------------------------------|
| `typeElementId`   | string | No | When set, returns Objects of the given typeElementId. If not set, all Objects are returned. |
| `includeMetadata` | boolean | No | Optionally include metadata in the response.                                                |
| `root`            | boolean | No | Returns the root Objects for the server when set to true.                                   |

**Response:**

```json
{
  "success": true,
  "result": [
    {
      "elementId": "string",
      "displayName": "string",
      "typeElementId": "string",
      "parentId": "",
      "isComposition": false,
      "isExtended": true,
      "metadata": {
        "description": "A human-readable description of this Object.",
        "typeNamespaceUri": "string",
        "sourceTypeId": "string",
        "relationships": {
          "HasParent": "/",
          "HasChildren": ["child1", "child2"]
        },
        "extendedAttributes": {
          "serial_number": { "type": "string" },
          "firmware_version": { "type": "string" }
        },
        "system": {
          "<vendor-key-1>": "string",
          "<vendor-key-2>": 123,
          "<vendor-key-3>": true
        }
      }
    }
  ]
}
```

| Field           | Type    | Required | Description                                                                                                                                                                                                            |
|-----------------|---------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `elementId`     | string  | Yes      | Unique identifier for this Object within the i3X address space                                                                                                                                                         |
| `displayName`   | string  | Yes      | Human-friendly name for display                                                                                                                                                                                        |
| `typeElementId` | string  | Yes      | ElementId of the Object Type that defines this Object's schema                                                                                                                                                         |
| `parentId`      | string? | Yes      | ElementId of the parent Object in the organizational hierarchy; `null` if this is a root Object                                                                                                                        |
| `isComposition` | boolean | Yes      | `true` if this Object encapsulates composed child elements (HasComponent). Composition children contribute to the parent's value and are returned together under `components` when reading values with `maxDepth > 1`. |
| `isExtended`    | boolean | Yes      | `true` if the Object's current value contains attributes not declared in its ObjectType schema. The Object carries data the type doesn't describe. See `extendedAttributes` below in the `metadata`.                   |

The `metadata` key is included if `includeMetadata=true` in the request.

| Field                         | Type    | Required                 | Description |
|-------------------------------|---------|--------------------------|-------------|
| `metadata.description`        | string | No | A human-readable description of this Object. SHOULD be used to convey context or intent beyond what `displayName` communicates. |
| `metadata.typeNamespaceUri`   | string  | Yes                      | The namespace the ObjectType *definition* belongs to — identifies which namespace's schema this Object conforms to (e.g., an ISA-95 or OPC UA standard namespace, or a vendor namespace). An Object instance's type may come from any namespace; this field makes that provenance explicit. For example, if the external Namespace was the OPC UA for Machinery Companion spec, the typeNamespaceUri would be `http://opcfoundation.org/UA/Machinery/`. |
| `metadata.sourceTypeId`       | string  | Yes                      | An identifier of this type within its *source namespace*. Provided so clients can correlate back to the originating definition. Distinct from `typeElementId`, which is the i3X address space identifier. For example, if the external Type was JobOrderControl from the OPC UA for Machinery Companion spec, the typeElementId may be the BrowseName, `JobOrderControl` OR the NodeId `ns=1;i=5058`. |
| `metadata.relationships`      | object  | No                       | The Object's outgoing relationship edges, keyed by relationship type. Enables clients to plan graph traversal without an additional `/objects/related` call. Only elementIds are returned here; use `/objects/related` to get the full related Object records. |
| `metadata.extendedAttributes` | object  | No                       | Present only when `isExtended=true`. Contains the non-conformant attributes and their inferred JSON Schema fragments, keyed by attribute name. Declared (conformant) attributes are omitted — they can be looked up from the `typeElementId`. |
|  `metadata.system`            | object | Yes if `isExtended=true` | Vendor-defined key/value pairs for platform-specific metadata not covered by the standard fields. Keys are vendor-defined strings; values are limited to strings, numbers, and booleans.|


- Note on `parentId` vs `relationships`: `parentId` always travels with the Object so a tree can be constructed from a flat list. `relationships` is returned only when `includeMetadata=true` and lets clients traverse the full graph without an additional `/objects/related` call. `/objects/related` returns the full related Object records; `relationships` returns only the elementIds.

---

#### `POST` /objects/list

Returns one or more Objects without data/values given a collection of elementIds.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elementIds` | string[] | Yes | One or more elementIds to query |
| `includeMetadata` | boolean | No | Optionally include metadata in the response. |

```json
{
  "elementIds": [
    "string"
  ],
  "includeMetadata": false
}
```

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "success": true,
      "elementId": "string",
      "result": {
        "elementId": "string",
        "displayName": "string",
        "typeElementId": "string",
        "parentId": "",
        "isComposition": false,
        "isExtended": false
      }
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Element not found: string" }
    }
  ]
}
```

**Response (with `includeMetadata=true`):**

```json
{
  "success": true,
  "results": [
    {
      "success": true,
      "elementId": "string",
      "result": {
        "elementId": "string",
        "displayName": "string",
        "typeElementId": "string",
        "parentId": "",
        "isComposition": false,
        "isExtended": false,
        "metadata": {
          "description": "A human-readable description of this Object.",
          "typeNamespaceUri": "string",
          "sourceTypeId": "string",
          "relationships": {
            "HasParent": "/",
            "HasChildren": ["child1", "child2"]
          }
        }
      }
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Element not found: string" }
    }
  ]
}
```
| Field              | Type    | Required | Description                                                                                                   |
|--------------------|---------|----------|---------------------------------------------------------------------------------------------------------------|
| `results[].result` | Object  | Yes | See the [Objects](#objects) section for a full description of the Object response fields including `metadata`. |

---

#### `POST` /objects/related

Returns related Objects, with the option to filter on a Relationship Type.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elementIds` | string[] | Yes | List of elementIds to browse for relationships |
| `relationshipType` | string | No | The elementId of the Relationship Type to filter on. Leave out or set to null to get all related Objects. |
| `includeMetadata` | boolean | No | When true, includes all extended metadata fields on each returned Object. |

```json
{
  "elementIds": [
    "string"
  ],
  "relationshipType": "string",
  "includeMetadata": false
}
```

**Response:**

Returns a bulk response with the related Objects for each queried elementId.

```json
{
  "success": false,
  "results": [
    {
      "success": true,
      "elementId": "string",
      "result": [
        {
          "sourceRelationship": "string",
          "object": {
            "elementId": "string",
            "displayName": "string",
            "typeElementId": "string",
            "parentId": "",
            "isComposition": false,
            "isExtended": false
          }
        }
      ]
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Element not found: string" }
    }
  ]
}
```

| Field                          | Type   | Required | Description                                                                                                                                                                                                                                    |
|--------------------------------|--------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `elementId`                    | string | Yes      | The elementId from the request                                                                                                                                                                                                                 |
| `results[].sourceRelationship` | string | Yes      | The name of the relationship that links this Object to the Object in the request, or inbound edge. For example, if it's a parent/child relationship this would be `hasChild`. This helps support graph traversal without additional API calls. |
| `results[].object`            | object | Yes      | See the [Objects](#objects) section for a full description of the Object response fields.                                                                                                                                                      |


- **Note** Servers MUST ensure that all relationship types used in Object `metadata.relationships` fields are registered in `/relationshiptypes` and have a defined `reverseOf`. This guarantees that clients can traverse the graph in both directions from any returned Object without additional discovery calls.

---

## Query Methods

Query methods are used to read the current and historical value for an Object.

Values in i3X have the following definition.

```json
{
  "value": <any>,
  "quality": "Good" | "GoodNoData" | "Bad" | "Uncertain",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | any | Yes | The actual data value (any JSON type) |
| `quality` | string | Yes | Data quality indicator |
| `timestamp` | string | Yes | RFC 3339 timestamp when data was recorded. Times must be UTC with no timezone offset. |


| Quality | Description | When to Use |
|---------|-------------|-------------|
| `Good` | Value is valid and current | Normal operation, value is reliable |
| `GoodNoData` | No data available but connection is good | Sensor connected but hasn't reported yet |
| `Bad` | Value is invalid or connection failed | Communication failure, sensor malfunction |
| `Uncertain` | Value quality cannot be determined | Sensor in calibration, stale data |

Below is an example of a temperature sensor value return.

```json
// Object Value read for tempSensor1
{
  "value": {
    "temperature": 20,
    "unit": "C"
  },
  "quality": "Good",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

#### `POST` /objects/value

Returns the last known value for one or more Objects.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elementIds` | string[] | Yes | One or more elementIds to query |
| `maxDepth` | integer | No | [TODO] - need to define this with clear examples. Can you filter this on a relationship type or does it traverse all relationships? MGP: I believe it only traverses hasComponent relationships.  vNext could add a relationship type parameter to deviate from default of hasComponent |

```json
{
  "elementIds": [
    "string"
  ],
  "maxDepth": 1
}
```

**Response:**

```json
{
  "success": false,
  "results": [
    {
      "success": true,
      "elementId": "string",
      "result": {
        "isComposition": false,
        "value": {
          "temperature": 1,
          "inletPressure": "2",
          "outletPressure": 0.11
        },
        "quality": "Good",
        "timestamp": "2026-01-29T16:37:41Z"
      }
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Element not found: string" }
    }
  ]
}
```

**Result shape — simple (leaf) element:**

```json
{ "success": true, "elementId": "sensor-001", "result": { "isComposition": false, "value": 67.1, "quality": "Good", "timestamp": "2025-10-28T10:15:30Z" } }
```

**Result shape — composition element** (when `maxDepth > 1`):

```json
{
  "success": true,
  "elementId": "pump-101-measurements",
  "result": {
    "isComposition": true,
    "value": null,
    "quality": "GoodNoData",
    "timestamp": "...",
    "components": {
      "pump-101-bearing-temperature": { "value": 70.34, "quality": "Good", "timestamp": "..." }
    }
  }
}
```

- The top-level `value`, `quality`, and `timestamp` always reflect the parent element's own VQT
- `components` is present only on composition elements and contains child values keyed by `elementId`
- See [maxDepth Parameter Semantics](#maxdepth-parameter-semantics) for full recursion behavior

---

#### `POST` /objects/history

Returns the historical values for one or more Objects between a start and end time.

[TODO] - Sync reponse with v0.1.2

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elementIds` | string[] | No | One or more elementIds to query |
| `startTime` | string | Yes | RFC 3339 timestamp for range start |
| `endTime` | string | Yes | RFC 3339 timestamp for range end |
| `maxDepth` | integer | No | Controls recursion depth |

```json
{
  "elementIds": [
    "string"
  ],
  "startTime": "string",
  "endTime": "string",
  "maxDepth": 1
}
```

**Response:**

```json
{
  "success": false,
  "results": [
    {
      "success": true,
      "elementId": "object-elementid-1",
      "result": {
        "isComposition": false,
        "values": [
          { "value": { "temperature": 1, "inletPressure": "2", "outletPressure": 0.11 }, "quality": "Good", "timestamp": "2026-01-29T16:00:00Z" },
          { "value": { "temperature": 3, "inletPressure": "4", "outletPressure": 0.22 }, "quality": "Good", "timestamp": "2026-01-29T15:00:00Z" }
        ]
      }
    },
    {
      "success": false,
      "elementId": "string",
      "error": { "message": "Element not found: string" }
    }
  ]
}
```

- `isComposition` is at the `result` envelope level, not per value entry
- `values` is an ordered array of VQT objects for the requested time range

---

## Update Methods

Update methods allow clients to write current and historical values to an Object. Update methods have the following limitations.

- Clients MUST write the full value to the Object. Partial updates are currently not supported.

It is the responsibility of the implementing platform to validate the input, including verification of the schema, and return the appropriate error if the input fails.

---

#### `PUT` /objects/{elementId}/value

Update the value of an Object.

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `elementId` | string | Yes | The elementId of the Object to update |

**Request Body:**

The value to write in VQT format. The value will replace the current Object value in its entirety. Partial writes of attributes are not currently supported.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | any | Yes | The data value to write. Must conform to the Object's type schema. |
| `quality` | string | No | Quality indicator. Defaults to `"Good"` if omitted. |
| `timestamp` | string | No | RFC 3339 timestamp. Defaults to server time if omitted. |

```json
{
  "value": { "temperature": 20, "unit": "C" },
  "quality": "Good",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Response:**

```json
{
  "success": true,
  "result": null
}
```

---

#### `PUT` /objects/{elementId}/history

Update historical values of an Object.

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `elementId` | string | Yes | The elementId of the Object to update |

**Request Body:**

```json
// TODO document this
```

**Response:**

```json
// TODO document this
```

---

## Subscribe Methods

Subscriptions allow clients to receive value changes in real-time for objects they are interested in. Subscriptions support two delivery modes:

| Mode | Description |
|------|-------------|
| **streaming** | Value changes are sent as fast as possible using SSE (Server Sent Events). |
| **sync** | Value changes are queued and delivered when the client calls the sync API. |

Streaming provides data as fast as possible, where Sync allows the client to control when data is delivered and acknowledge delivery. The following
sections describe common methods to setup and configure a subscription, followed by more details on the stream and sync modes.

### Subscriptions

Clients must first create a subscription in the server. Subscriptions have the following requirements:

- The client must provide a unique `clientId` to scope subscriptions to the client
- The server MUST provide a unique `subscriptionId` to the client
- The `subscriptionId` MUST be scoped to the `clientId` to ensure that only the client has access to a subscription
- Servers SHOULD NOT make subscriptions shareable across clients, but the standard doesn't enforce that
- `subscriptionId` and `clientId` SHOULD be unique enough that the server can reasonably assume other clients cannot guess the identifiers

---

#### `POST` /subscriptions

Creates a subscription scoped to a client.

The client MUST pass in a `clientId` unique to the client to scope the subscription to the client. The `clientId` SHOULD be reasonably complex and difficult for other clients to guess. Examples are authentication tokens or other unique client identifiers.

The server returns a unique `subscriptionId` for the subscription. This SHOULD also be reasonably complex. Both the server and the client MUST cache the `clientId` and `subscriptionId` for future requests on the subscription.

The client can optionally pass in a friendly name for the subscription. This is intended to assist clients and servers in logging and tracking subscriptions.

**Parameters:**
```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "displayName": "mySubscription"
}
```

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `clientId` | string | Yes | Unique identifier for the client. |
| `displayName` | string | No | Optional name to associate with the subscription. |

**Response:**

```json
{
  "success": true,
  "result": {
    "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt",
    "displayName": "mySubscription"
  }
}
```

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `clientId` | string | Yes | The clientId passed in the request. |
| `subscriptionId` | string | Yes | Unique ID for the subscription. |
| `displayName` | string | Yes | Friendly name for the subscription. |

---

#### `POST` /subscriptions/list

Get one or more subscriptions by ID. Used to check if subscriptions exist and inspect their current configuration.

**Body Parameters:**
```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionIds": ["Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt"]
}
```

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `clientId` | string | Yes | The clientId for the subscriptions. |
| `subscriptionIds` | string array | Yes | List of subscription IDs to retrieve. |

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "success": true,
      "elementId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt",
      "result": {
        "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt",
        "displayName": "mySubscription",
        "monitoredObjects": [
          { "elementId": "object-elementid-1", "maxDepth": 1 }
        ]
      }
    }
  ]
}
```
---

#### `POST` /subscriptions/delete

Delete one or more subscriptions.

- Servers SHOULD stop collecting data for Objects being monitored by the Subscription when it's deleted.

**Body Parameters:**
```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionIds": ["Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt"]
}
```

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `clientId` | string | Yes | The clientId for the subscriptions. |
| `subscriptionIds` | string array | Yes | List of subscription IDs to delete. |

**Response:**

```json
{
  "success": true,
  "results": [
    { "success": true, "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt", "result": null }
  ]
}
```

---

### Registering and Unregistering Objects

Once a Subscription is created, a client can add and remove Objects to the Subscription to start collecting data changes.

- Once an Object is registered the server MUST start collecting data changes for the Object
- Servers SHOULD queue the updates and deliver them FIFO to clients
- Servers SHOULD have a limit on how many updates they can queue, and when reached, start dropping older updates first

[TODO] - how does a server signal a client that data has been dropped?  MGP- Maybe through some additional data in the `GET` /subscription.  Add some timestamp for when data was last dropped?  Maybe something more creative, also?

---

#### `POST` /subscriptions/register

Register one or more Objects with a Subscription.

- If an Object is registered more than once the Server MUST return success and ignore the subsequent registration
- The Server MUST support partial failures (e.g. bad elementId) and not fail the full request

**Request Body:**

```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt",
  "elementIds": [
    "object-elementid-1",
    "object-elementid-2"
  ],
  "maxDepth": 1
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `clientId` | string | Yes | The clientId for the subscription. |
| `subscriptionId` | string | Yes | The subscriptionId to register items with. |
| `elementIds` | string[] | Yes | One or more elementIds to register. |
| `maxDepth` | integer | No | Controls recursion depth. [TODO] - MGP explain how maxDepth works. Similar to values, where it only follows hasComponent relationships? |

**Response:**

```json
{
  "success": true,
  "results": [
    { "success": true, "elementId": "object-elementid-1", "result": null },
    { "success": true, "elementId": "object-elementid-2", "result": null }
  ]
}
```

---

#### `POST` /subscriptions/unregister

Unregister one or more Objects from a Subscription.

- Once an Object is unregistered the server SHOULD stop queuing new values for the Object on the Subscription
- The server SHOULD NOT delete any prior queued values for the Object
- The Server MUST support partial failures (e.g. bad elementId) and not fail the full request

**Request Body:**

```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt",
  "elementIds": [
    "object-elementid-1",
    "object-elementid-2"
  ],
  "maxDepth": 1
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `clientId` | string | Yes | The clientId for the subscription. |
| `subscriptionId` | string | Yes | The subscriptionId to unregister items from. |
| `elementIds` | string[] | Yes | One or more elementIds to unregister. |
| `maxDepth` | integer | No | Controls recursion depth. |

**Response:**

```json
{
  "success": true,
  "results": [
    { "success": true, "elementId": "object-elementid-1", "result": null },
    { "success": true, "elementId": "object-elementid-2", "result": null }
  ]
}
```

---

### Streaming

Streaming sends values on the subscription to the client as they occur using SSE (Server Sent Events) for a low Quality of Service.

**How it works:**

1. Client creates subscription via `POST /subscriptions`
2. Client registers items via `POST /subscriptions/register`
   - The server starts queuing value changes for Objects
3. Client opens SSE stream via `POST /subscriptions/stream`
   - The server sends any values queued while the stream was closed
4. Server sends values as they occur, with "at most once" delivery. If a client misses a message, it cannot be retrieved.

If the SSE connection is lost, the client can call the /stream endpoint again to re-open it.

---

#### `POST` /subscriptions/stream

Opens an SSE stream on the subscription to stream value changes from the server.

- Server MUST only allow a single SSE stream per subscription
  - [TODO] is this enough or should we spec what happens if you spam the /stream endpoint? Ignore? Close the old and open new?
  - MGP - should multiple clients be allowed to connect in a multicast-type pattern?
- The Server MUST send queued updates when the stream is open
- Clients MAY not receive updates if there are no value changes
  - [TODO] should register require queuing the current value of the Object?

**Body Parameters:**
```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt"
}
```

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `clientId` | string | Yes | The clientId for the subscription. |
| `subscriptionId` | string | Yes | The subscriptionId for the Subscription to stream. |

**Response:**

The response includes value updates over SSE in the following format:

```json
[{"elementId": "sensor-001", "value": 72.5, "quality": "Good", "timestamp": "2025-01-08T10:30:00Z"}]
```

---

### Sync

Sync allows the client to control when value changes are received, and to explicitly acknowledge receipt for a high Quality of Service.

**How it works:**

1. Client creates subscription via `POST /subscriptions`
2. Client registers items via `POST /subscriptions/register`
3. Server queues updates as they occur, each assigned a monotonically increasing `sequenceNumber`.  Each subscription uses a different `sequenceNumber` where the first update within a new subscription sets `sequenceNumber=1`.  `sequenceNumber` is a 64-bit unsigned integer so rollover happens after 2⁶⁴ − 1
4. Client polls via `POST /subscriptions/sync` (no `lastSequenceNumber` on first call)
5. Server returns all pending updates
6. Client processes the updates
7. Client calls `POST /subscriptions/sync` again with `{"clientId": "...", "subscriptionId": "...", "lastSequenceNumber": <lastSequenceNumber>}` to acknowledge the previous batch and receive any new updates in a single round trip
8. Server removes acknowledged updates (sequenceNumber ≤ `lastSequenceNumber`) then returns the remaining queue
9. Continue this process

This approach ensures updates are not lost if the client crashes between receiving and processing data, while keeping acknowledgement and polling as a single call.

---

#### `POST` /subscriptions/sync

Returns all pending updates, acknowledging a previously received batch in the same call.

- Each queued update includes a `sequenceNumber`
- If `lastSequenceNumber` is provided, the server removes all updates with sequenceNumber ≤ `lastSequenceNumber` before returning the remaining queue
- Server MUST NOT clear the queue if `lastSequenceNumber` is omitted
- Clients SHOULD omit `lastSequenceNumber` only on the first call, when there is nothing yet to acknowledge
- Clients SHOULD provide `lastSequenceNumber` on every subsequent call, set to the highest `sequenceNumber` received in the previous response

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `clientId` | string | Yes | The clientId for the subscription. |
| `subscriptionId` | string | Yes | The subscriptionId for the Subscription to sync. |
| `lastSequenceNumber` | 64-bit unsigned integer | No — omit only on first call | Acknowledge all updates with sequenceNumber ≤ this value before returning new ones. |

First call (nothing to acknowledge yet):
```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt"
}
```

All subsequent calls (ack previous batch, fetch new):
```json
{
  "clientId": "myClient.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "subscriptionId": "Xf9q8wL1b3YpQjV2Z7nRmK6sH4v0TgNd5eP2jF8hB1cQvLkS0UoMxZwA3yE6RrJt",
  "lastSequenceNumber": 2
}
```

**Response:**

```json
{
  "success": true,
  "result": [
    {"sequenceNumber": 1, "elementId": "sensor-001", "value": 72.5, "quality": "Good", "timestamp": "2025-01-08T10:30:00Z"},
    {"sequenceNumber": 2, "elementId": "sensor-002", "value": 18.3, "quality": "Good", "timestamp": "2025-01-08T10:30:01Z"}
  ]
}
```

---

### Subscription Life Cycle

Once a Subscription has been created and one or more Objects have been registered, the Server SHALL begin queuing data change events for those Objects.

If neither an active SSE stream nor a call to `/sync` is received within the configured Time-To-Live (TTL) interval, the Server MUST delete the Subscription. Deletion MUST include:

- All queued Object values associated with the Subscription
- Any internal resources allocated to maintain the Subscription

This requirement prevents abandoned Subscriptions from consuming Server resources.

Once deleted, the Subscription SHALL NOT be returned by any API endpoint and MUST be re-created by the Client. Subsequent calls to `/sync` or `/stream` for a deleted or non-existent Subscription MUST return 404 Not Found.

---


## Appendix (for now)

[TODO] This is useful stuff that I can't figure out yet whereto put

### Relationship Semantics

All relationships MUST be stored bidirectionally. If object A has a relationship of type X to object B, then B MUST store the inverse relationship back to A. This guarantee allows clients to discover the complete graph starting from any known node using `POST /objects/related`, without needing prior knowledge of which objects reference a given element.

#### HasParent / HasChildren

These represent topological or organizational hierarchy where child objects are separate entities organized under a parent.

```
Production Line A (parent)
├── Machine 1 (child)
├── Machine 2 (child)
└── Machine 3 (child)
```

**Requirements:**

- If object A `HasParent` B, then B `HasChildren` A
- `parentId` on instances MUST match the `HasParent` relationship
- Traversing `HasChildren` returns distinct, independently-valued objects

#### HasComponent / ComponentOf (Composition)

These indicate when child data IS part of the parent's definition. The parent's value is composed of its children's values.

```
CNC Machine (parent, isComposition: true)
├── Spindle (component)
├── Coolant System (component)
└── Control Panel (component)
```

**Requirements:**

- If object A `HasComponent` B, then B `ComponentOf` A
- Parent MUST have `isComposition: true`
- Querying parent value with `maxDepth > 1` returns nested child values
- Component children's values are part of the parent's logical value

### maxDepth Parameter Semantics

The `maxDepth` parameter controls recursion through HasComponent relationships:

| Value | Behavior |
|-------|----------|
| `0` | Infinite recursion - include all nested composed elements |
| `1` | No recursion - return only this element's direct value (default) |
| `N` | Recurse up to N levels deep through HasComponent relationships |

**Response Structure with maxDepth:**

When `maxDepth > 1` and the element has components, the full `POST /objects/value` response looks like:

```json
{
  "success": true,
  "results": [
    {
      "success": true,
      "elementId": "machine-001",
      "result": {
        "isComposition": true,
        "value": { "status": "running" },
        "quality": "Good",
        "timestamp": "2025-01-08T10:30:00Z",
        "components": {
          "spindle-001": {
            "value": { "rpm": 12000 },
            "quality": "Good",
            "timestamp": "2025-01-08T10:30:00Z"
          },
          "coolant-001": {
            "value": { "flow_rate": 5.2, "temp": 22.1 },
            "quality": "Good",
            "timestamp": "2025-01-08T10:30:00Z"
          }
        }
      }
    }
  ]
}
```

**Key Points:**

- The top-level `value`, `quality`, and `timestamp` always reflect the parent element's own VQT
- `components` is present only on composition elements and contains child values keyed by their `elementId`
- Each child value is in VQT format (`value`, `quality`, `timestamp`)
- Recursion only follows `HasComponent` relationships, not `HasChildren`

---

### Error Handling

**HTTP Status Codes:**

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters, malformed request body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | ElementId or resource doesn't exist |
| 500 | Internal Server Error | Server-side error |
| 501 | Not Implemented | Optional feature not supported |

See [Error Response](#error-response) for the error response body format.

---

### Pagination

For endpoints returning arrays, implementations SHOULD support pagination.

**Offset/Limit (Simple):**

```
GET /objects?offset=100&limit=50
```

**Response with pagination metadata:**

```json
{
  "items": [...],
  "total": 500,
  "offset": 100,
  "limit": 50
}
```

---

*Copyright (C) CESMII, the Smart Manufacturing Institute, 2024-2025. All Rights Reserved.*
