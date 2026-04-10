# MQTT Data Source

The MQTT data source adapter connects to an MQTT broker and exposes topics as i3X objects. It supports real-time subscriptions, automatic relationship inference from topic hierarchy, and namespace/type discovery from payload metadata.

## Configuration

```json
{
  "data_source": {
    "type": "mqtt",
    "config": {
      "mqtt_endpoint": "mqtt://localhost:1883",
      "topics": ["#"],
      "username": "optional",
      "password": "optional",
      "excluded_topics": []
    }
  }
}
```

### Configuration Options

| Option | Description |
|--------|-------------|
| `mqtt_endpoint` | Broker URL. Use `mqtt://` for plain (port 1883) or `mqtts://` for TLS (port 8883) |
| `topics` | Array of topic patterns to subscribe to. Supports MQTT wildcards: `#` (multi-level), `+` (single-level) |
| `username` | Optional authentication username |
| `password` | Optional authentication password |
| `excluded_topics` | Array of topic patterns to exclude. Supports `*` wildcard |

## Topic to Element ID Mapping

MQTT topics are converted to element IDs by replacing `/` with `_` to avoid URL path conflicts:

- Topic: `sensors/temperature/room1`
- Element ID: `sensors_temperature_room1`

## Relationship Inference

The adapter automatically infers object relationships from the MQTT topic hierarchy.

### Supported Relationship Types

| Relationship | Description |
|--------------|-------------|
| `HasParent` | Links a topic to its parent in the hierarchy |
| `HasChildren` | Links a topic to its direct children |
| `HasSibling` | Links topics that share the same parent |

### Virtual Nodes

MQTT brokers typically only publish messages to leaf topics. To support proper parent-child relationships, the adapter creates **virtual parent nodes** for intermediate path segments.

For example, when a message arrives at `abelara/site1/machine1/status`:
- Virtual nodes are created for: `abelara`, `abelara/site1`, `abelara/site1/machine1`
- A virtual root node `/` is created as the parent of all top-level topics
- The leaf topic `status` has `parentId: "abelara_site1_machine1"`

Virtual nodes have:
- `value: null` (no payload data)
- `virtual: true` marker
- Proper `parentId` linking to their parent

### Querying Relationships

```bash
# Get children of root (all top-level topics)
POST /objects/related
{"elementIds": ["/"], "relationshiptype": "HasChildren"}

# Get parent of a topic
POST /objects/related
{"elementIds": ["abelara_site1_machine1_status"], "relationshiptype": "HasParent"}

# Get siblings (topics with same parent)
POST /objects/related
{"elementIds": ["abelara_site1_machine1"], "relationshiptype": "HasSibling"}
```

## Namespace Discovery

Namespaces are automatically discovered from MQTT payloads that contain a `$namespace` field.

### Payload Format

```json
{
  "$namespace": "https://opcfoundation.org/UA/Machinery/MachineIdentification/v1.0",
  "Manufacturer": "Acme Corp",
  "SerialNumber": "12345"
}
```

When a payload contains `$namespace`:
1. The namespace is registered and returned by `GET /namespaces`
2. A single type is created for that namespace (shared by all payloads with the same `$namespace`)
3. The instance's `namespaceUri` is set to the discovered namespace

### Type Inference

Types are inferred differently based on whether `$namespace` is present:

| Payload Has `$namespace` | Type Behavior |
|--------------------------|---------------|
| Yes | One type per namespace, assigned to that namespace. Type ID derived from namespace URI (e.g., `MachineIdentification` from `.../MachineIdentification/v1.0`) |
| No | One type per unique topic name, assigned to the default MQTT namespace (`http://i3x.org/mfg/mqtt`). Type ID is `{topicName}Type` |

For topics without `$namespace`, types are deduplicated by name. For example, `machine1/state` and `machine2/state` both have the type `stateType` rather than separate types.

The default MQTT namespace is always returned by `GET /namespaces`, alongside any discovered namespaces.

The type's JSON schema is generated from the first payload structure encountered for that type.

### Example

Given these payloads on different topics:

```
Topic: factory/machine1/identity
Payload: {"$namespace": "https://example.com/MachineId/v1.0", "serial": "001"}

Topic: factory/machine2/identity
Payload: {"$namespace": "https://example.com/MachineId/v1.0", "serial": "002"}

Topic: factory/machine1/state
Payload: {"running": true}

Topic: factory/machine2/state
Payload: {"running": false}
```

Results:
- **Namespaces**:
  - `http://i3x.org/mfg/mqtt` (default, always present)
  - `https://example.com/MachineId/v1.0` (discovered)
- **Types**:
  - `MachineId` (in `https://example.com/MachineId/v1.0`, shared by both identity topics)
  - `stateType` (in default MQTT namespace, shared by both state topics)
- **Instances**:
  - `factory_machine1_identity` with `typeId: "MachineId"`
  - `factory_machine2_identity` with `typeId: "MachineId"`
  - `factory_machine1_state` with `typeId: "stateType"`
  - `factory_machine2_state` with `typeId: "stateType"`

## Limitations

- **Read-only by default**: Write operations publish to MQTT but depend on broker permissions
- **No historical data**: Only current values are cached; historical queries return current value only
- **Schema from first payload**: Type schemas are generated from the first payload seen for each type (whether discovered via `$namespace` or inferred from topic name). Subsequent payloads with different structures won't update the schema.
- **Virtual nodes have no values**: Parent nodes created for hierarchy don't have payload data
- **`isComposition` always false**: Topic hierarchy represents organizational relationships, not data composition
