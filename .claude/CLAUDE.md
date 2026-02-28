# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the RFC 001 specification and prototype implementation for I3X (Industrial Information Interface eXchange) - a common API for Contextualized Manufacturing Information Platforms (CMIPs). The goal is to enable portable application development across different manufacturing information platforms by providing a vendor-agnostic API specification.

**Key Documents:**
- `RFC for Contextualized Manufacturing Information API.md` - Complete RFC 001 specification defining the I3X API
- `Working Group Charter.md` - Charter for the Smart Manufacturing API Working Group
- `README.md` - High-level project overview and problem statement

**Repository Structure:**
- `demo/server/` - FastAPI-based I3X API server implementation (primary active codebase)
- `demo/client/` - Test client for validating server functionality (currently basic SSE client)
- `images/` - Documentation diagrams

## Working with the Server (demo/server/)

All server development happens in `demo/server/`. This is the primary active codebase.

### Development Commands

**Environment Setup:**
- Python version: Requires Python 3.7+
- Quick setup: `cd demo/server && ./setup.sh` (Linux/Mac) or `.\setup.ps1` (Windows)
- Manual setup: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

**Running the Server:**
```bash
cd demo/server
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

**Testing:**
```bash
cd demo/server
python -m pytest test_app.py -v
```

**Docker:**
```bash
cd demo/server
docker build -t cesmii/api:dev .
docker run --rm -it -p 8080:8080 cesmii/api:dev
```

**Configuration:**
Copy `config-example.json` to `config.json` and modify as needed. Supports single or multi-data source configurations.

**API Documentation:**
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- Public demo: https://api.i3x.dev/v0/

### Server Architecture

The server implements RFC 001 I3X API using FastAPI with a pluggable data source architecture.

**Core Files:**
- `app.py` - FastAPI application with lifecycle management
- `models.py` - Pydantic models for RFC-compliant data structures
- `config.json` - Runtime configuration (port, host, data sources)

**Data Source Abstraction (`data_sources/`):**

The server uses a pluggable data source architecture that supports:
1. **Single data source** - One backend handles all operations
2. **Multi-data source** - Route different operations to specialized backends for performance optimization

Key components:
- `data_interface.py` - Abstract `I3XDataSource` interface that all data sources implement
- `factory.py` - Creates data source instances from configuration
- `manager.py` - `DataSourceManager` routes operations across multiple data sources
- `mock/` - Mock data source with simulated manufacturing data and random value updates
- `mqtt/` - MQTT data source for real-time broker integration
- `cnc_mock/` - CNC machine mock data source implementing OPC UA CNC profile

**Data Flow:**
1. Server startup reads `config.json` and creates data source(s) via `DataSourceFactory`
2. Data source injected into all router endpoints via FastAPI dependency injection
3. For multi-source configs, `DataSourceManager` routes operations based on `data_source_routing` mapping
4. Background subscription worker thread monitors data sources for real-time updates
5. Data sources call `update_callback` when values change to trigger subscription notifications

**API Routers (`routers/`):**

All routers use dependency injection to access data sources - they never import data sources directly.

- `namespaces.py` - List available namespaces (RFC 4.1.1)
- `typeDefinitions.py` - Object type and relationship type definitions (RFC 4.1.2-4.1.5)
- `objects.py` - Three router instances for object operations:
  - Explore router: Browse instances, query by type (RFC 4.1.6-4.1.8)
  - Query router: Get current/historical values (RFC 4.2.1.x)
  - Update router: Write values (RFC 4.2.2.x)
- `subscriptions.py` - Real-time data streaming with streaming (SSE) and sync (polling) (RFC 4.2.3.x)
- `utils.py` - Response formatting helpers (`getObject`, `getValue`, `getValueMetadata`, `getSubscriptionValue`)

**Key RFC Concepts:**
- **Namespaces** - Organize objects by domain (equipment, process, quality)
- **Object Types** - Define structure and metadata for classes of manufacturing objects
- **Object Instances** - Actual equipment/sensors/processes with current attribute values
- **Relationships** - Hierarchical (parent-child) and non-hierarchical (equipment trains, material flow)
- **ElementId** - Platform-specific unique string identifier for any element

### Key Architectural Patterns

**Composition vs Organization Relationships:**
- **HasComponent/ComponentOf**: Child data IS part of parent's value; parent has `isComposition: True`
- **HasChildren/HasParent**: Organizational hierarchy; children are separate entities

**maxDepth Parameter:**
Controls recursion through HasComponent relationships:
- `maxDepth=0` - Infinite recursion (include all nested composed elements)
- `maxDepth=1` - No recursion (just this element's value) - default
- `maxDepth=N` - Recurse up to N levels deep

Returns nested structure with `_value` for own data and child keys for composed data.

**VQT (Value-Quality-Timestamp) Format:**
```json
{
  "value": "<any>",
  "quality": "GOOD",
  "timestamp": "2025-01-08T..."
}
```

### Data Source Configuration

**Mock Data Source** (simulated data):
```json
{
  "data_source": {
    "type": "mock",
    "config": {}
  }
}
```

**MQTT Data Source** (real-time broker):
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
- Supports `mqtt://` (plain, port 1883) and `mqtts://` (TLS, port 8883, accepts any cert)
- Topic wildcards: `#` (multi-level), `+` (single-level)
- Converts topic `/` to `_` for API element IDs (e.g., `sensors/temp` → `sensors_temp`)
- Read-only (no write operations), limited exploratory support

**CNC Mock Data Source** (OPC UA CNC profile):
```json
{
  "data_source": {
    "type": "cnc-mock",
    "config": {}
  }
}
```
- Simulates CNC machine equipment with realistic OPC UA CNC profile data
- Based on `cesmii.net.profiles.cnc.nodeset2.xml` schema
- Includes dynamic value updates via background thread

**Multi-Data Source** (advanced):
```json
{
  "data_sources": {
    "exploratory": {"type": "mock", "config": {}},
    "values": {"type": "mock", "config": {}},
    "updates": {"type": "mock", "config": {}},
    "subscriptions": {"type": "mock", "config": {}}
  },
  "data_source_routing": {
    "primary": "exploratory",
    "get_namespaces": "exploratory",
    "get_object_types": "exploratory",
    "get_instances": "exploratory",
    "get_instance_by_id": "values",
    "update_instance_value": "updates",
    "get_all_instances": "subscriptions"
  }
}
```

Available routing operations: `get_namespaces`, `get_object_types`, `get_object_type_by_id`, `get_relationship_types`, `get_instances`, `get_instance_by_id`, `get_related_instances`, `update_instance_value`, `get_all_instances`, `primary` (fallback)

### Adding New Data Sources

To add a new data source type (e.g., database, time-series store):

1. Create `data_sources/your_source/` directory
2. Implement `I3XDataSource` interface from `data_interface.py`
   - Required methods: `start()`, `stop()`, all RFC operation methods
   - Call `update_callback(instance, value)` when values change
3. Update `DataSourceFactory._create_single_source()` in `factory.py` to handle new type
4. Add type name to `DataSourceFactory.get_supported_types()`
5. Add configuration example to `config-example.json`

No router changes needed - dependency injection handles everything transparently.

### Mock Data Source Details

**Schema Files** (`data_sources/mock/Namespaces/`):
- `abelara.json` - Equipment/manufacturing types
- `isa95.json` - ISA-95 types
- `thinkiq.json` - Sensor types

**MockDataUpdater Critical Detail:**
The updater must access raw instance data (`self.data_source.data["instances"]`) not `get_all_instances()` which filters out records needed for updates.

## Working with the Client (demo/client/)

Currently a basic test client with SSE (Server-Sent Events) support. Future work will expand this into a full I3X client library.

**Running the test client:**
```bash
cd demo/client
./setup.sh  # or setup.ps1 on Windows
python test_client.py
```

## RFC 001 Compliance

The server implements RFC 001 I3X API specification:

**Implemented:**
- RFC 4.1.x - All exploratory methods (namespaces, types, instances, relationships)
- RFC 4.2.1.x - Value query methods (current and historical values)
- RFC 4.2.2.1 - Current value updates (PUT `/objects/{elementId}/value`)
- RFC 4.2.3.x - Subscriptions with streaming (SSE) and sync (polling)

**Known Limitations:**
- RFC 4.2.2.2 - Historical updates (PUT `/objects/{elementId}/history`) returns 501 Not Implemented
- GET `/subscriptions` endpoint not implemented (model exists but no endpoint)
- MQTT data source is read-only (no `update_instance_value` support)
- MQTT exploratory operations limited to namespaces; types generated dynamically from topics

## Common Patterns

**When modifying routers:**
- Always use dependency injection: `data_source: I3XDataSource = Depends(get_data_source)`
- Never import data sources directly
- Use response formatting helpers from `utils.py`
- Follow RFC section numbers in comments (e.g., `# RFC 4.1.6`)

**When modifying data sources:**
- Implement all methods from `I3XDataSource` interface
- Call `update_callback(instance, value)` for real-time updates
- Handle both single-source and routing scenarios in `manager.py`

**When modifying models:**
- Keep strict alignment with RFC 001 specification
- Use Pydantic v2 syntax
- Include proper JSON serialization configuration

**Subscription Debugging:**
If streaming subscriptions don't receive updates:
1. Verify `MockDataUpdater` is running (check app startup logs)
2. Ensure instance has `records` in mock_data.py
3. Check instance is not marked `"static": true`
4. Verify subscription's `monitoredItems` includes the elementId

**Important:** Subscriptions do NOT work when `debug: true` in config.json because uvicorn's reload mode breaks the callback threading model. Set `debug: false` for production or when testing subscriptions.
