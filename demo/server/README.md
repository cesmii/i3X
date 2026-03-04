# I3X API Server

This is a FastAPI-based HTTP server that implements the RFC 001 compliant I3X (Industrial Information Interface eXchange) API for Contextualized Manufacturing Information. The server provides endpoints for browsing equipment, sensors, and process data in a manufacturing environment. The server port is configurable via a config file.

### Core Structure
- **app.py**: Main FastAPI application with startup/shutdown lifecycle and configurable data source initialization
- **models.py**: Pydantic models for all I3X RFC-compliant data structures
- **data_sources/**: Abstraction layer for data access
  - `data_interface.py`: Abstract I3XDataSource interface
  - `factory.py`: Factory pattern for creating single or multiple data sources from config
  - `manager.py`: DataSourceManager for routing operations across multiple data sources
  - `mock/`: Mock data source implementation with random value generation
    - `mock_data.py`: I3X-compliant simulated manufacturing data
    - `mock_data_source.py`: Mock implementation using mock_data.py
    - `mock_updater.py`: Background thread for generating random value updates
  - `mqtt/`: MQTT data source implementation with real-time updates, subscribes to one or more topics on a single broker
    - `mqtt_data_source.py`: Holds the paho client, topic cache, and all the interface handlers
- **routers/**: API endpoint implementations organized by functionality (use dependency injection for data access)
  - `namespaces.py`: Namespace operations (RFC 4.1.1)
  - `typeDefinitions.py`: Type and relationship type definitions (RFC 4.1.2-4.1.5)
  - `objects.py`: Three router instances (explore, query, update) handling object operations:
    - Explore: Object instance queries (RFC 4.1.6-4.1.8)
    - Query: Current and historical values (RFC 4.2.1.x)
    - Update: Value updates (RFC 4.2.2.x)
  - `subscriptions.py`: Real-time data streaming with streaming/sync support (RFC 4.2.3.x)
  - `utils.py`: Helper functions for formatting responses (getObject, getValue, getValueMetadata, getSubscriptionValue)

## Docker Deployment

### Building and running your application

#### Build:
> docker build -t cesmii/api:dev . 

#### Run:
> docker run --rm -it -p 8080:8080 cesmii/api:dev

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)

## Setting Up the Virtual Environment

### Prerequisites
- Python 3 versions between 3.7 and 3.14 have been tested to work
- pip

### Setup Instructions

1. **Create a virtual environment**:

Windows:
```powershell
# Navigate to the project directory
cd c:\Users\<user>\i3x

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate
```

Linux/Mac
```bash
# Navigate to the project directory
cd ~/i3x

# Create a virtual environemnt
python -m venv venv

# Activate the virtual environment
chmod +x ./venv/bin/activate
./venv/bin/activate
```

2. **Install dependencies**:

```
pip install -r requirements.txt
```

3. **Configure the server** (optional):

Create `config.json` from the provided `config-example.json` template and customize as needed:

**Mock Data Source (simulated data with random updates):**
```json
{
    "port": 8080,
    "host": "0.0.0.0", 
    "debug": true,
    "data_source": {
        "type": "mock",
        "config": {}
    }
}
```

**MQTT Data Source (real-time MQTT data):**
```json
{
    "port": 8080,
    "host": "0.0.0.0",
    "debug": true,
    "data_source": {
        "type": "mqtt",
        "config": {
            "mqtt_endpoint": "mqtt://localhost:1883",
            "topics": ["#"],
            "username": "optional_username",
            "password": "optional_password",
            "excluded_topics": []
        }
    }
}
```
Note: `username`, `password`, and `excluded_topics` are optional.

**MQTT with TLS (secure connection):**
```json
{
    "port": 8080,
    "host": "0.0.0.0",
    "debug": true,
    "data_source": {
        "type": "mqtt",
        "config": {
            "mqtt_endpoint": "mqtts://broker.example.com:8883",
            "topics": ["sensors/#", "equipment/#"]
        }
    }
}
```

**Multi Data Source Configuration:**
```json
{
    "port": 8080,
    "host": "0.0.0.0",
    "debug": true,
    "app": {
        "title": "I3X API Prototype",
        "description": "Industrial Information Interface eXchange API - RFC 001 Compliant",
        "version": "0.0.1"
    },
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
        "get_object_type_by_id": "exploratory",
        "get_instances": "exploratory",
        "get_instance_by_id": "values",
        "get_relationship_types": "exploratory",
        "get_related_instances": "exploratory",
        "update_instance_value": "updates",
        "get_all_instances": "subscriptions"
    }
}
```
Note: This example uses mock data sources for all operations. In production, different sources could be different types (e.g., database for values, cache for updates, streaming broker for subscriptions). See `config-example.json` for reference.

4. **Run the server**:

```
python app.py
```

Alternatively, you can run with uvicorn directly:

```
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

The server will start on the configured port (default: 8080).

### Quick Setup with PowerShell Script

For convenience, you can use the included scripts to set up and run the server with a single command:

Windows:
```powershell
# Run the setup script
.\setup.ps1
```

Linux/Mac:
```bash
# Run the setup script
chmod +x ./setup.sh
./setup.sh
```

This script will:
- Create a virtual environment (if it doesn't exist)
- Activate the virtual environment
- Install dependencies
- Start the server

## API Endpoints

The I3X server implements RFC 001 - Common API for Industrial Information Interface eXchange (I3X). The available endpoints follow the specification exactly. Check the interactive document to explore the API.

### Interactive Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## Running Tests

To run the unit tests, make sure your virtual environment is activated and dependencies are installed:

```powershell
# Activate the virtual environment if not already activated
.\venv\Scripts\Activate

# Run the tests
python -m unittest test_app.py
```

### Troubleshooting

If you encounter the error `ModuleNotFoundError: No module named 'flask'`, make sure you:

1. Have activated the virtual environment
2. Have installed the dependencies with `pip install -r requirements.txt`

## Advanced Usage

### Data Source Architecture

The server supports both single and multi-data source configurations:

**Single Data Source**: Traditional approach where one data source handles all operations.

**Multi-Data Source**: Advanced configuration that allows different operations to use different data sources for optimal performance:

- **Exploratory operations** (browsing namespaces, object types): Use metadata-optimized source
- **Value operations** (reading current/historical values): Use read-optimized source  
- **Update operations** (writing values): Use write-optimized source
- **Subscription operations** (real-time streaming): Use streaming-optimized source

**Benefits of Multi-Data Source Configuration:**
- **Performance optimization**: Route operations to specialized data sources
- **Scalability**: Distribute load across multiple backend systems
- **Flexibility**: Mix different data source types (databases, caches, message queues)
- **Backward compatibility**: Single-source configuration still fully supported

### Changing the Port

To run on a different port, modify the `port` field in `config.json`:

```json
{
    "port": 9000,
    "host": "0.0.0.0",
    "debug": true
}
```

### Data Sources

**Mock Data Source**
The server includes a mock data source stored in `mock_data.py` that simulates an I3X-compliant manufacturing environment with:
- Namespaces (equipment, process, quality)
- Object Types (machines, sensors, processes)  
- Object Instances (specific machines, sensors, and processes)
- Relationship definitions (hierarchical and non-hierarchical)
- Random value updates for real-time simulation

**MQTT Data Source**
The server supports connecting to MQTT brokers for real-time industrial data:
- **Connection Support**:
  - `mqtt://` (plain connection, default port 1883)
  - `mqtts://` (TLS encrypted, default port 8883, accepts any certificate)
  - Optional username/password authentication
- **Topic Subscription**: Subscribe to specific topics or use wildcards (`#` for multi-level, `+` for single-level)
- **Topic Filtering**: Exclude specific topics via `excluded_topics` configuration
- **Real-time Updates**: Automatic cache updates and subscription notifications when messages arrive
- **Dynamic Types**: Automatically generates I3X object types from JSON message structure
- **URL Path Safe**: Converts topic `/` to `_` for API element IDs (e.g., `sensors/temp` becomes `sensors_temp`)
- **Limitations**: Read-only (no write operations), limited exploratory support

### RFC 001 Compliance

This implementation follows RFC 001 - Common API for Industrial Information Interface eXchange (I3X) which provides a common API that Contextualized Manufacturing Information Platforms (CMIPs) can implement. The specification defines:

- **Address Space Organization** (RFC 3) - Complete collection of contextualized information
- **Object Elements** (RFC 3.1) - Objects with attributes and required metadata
- **Object Relationships** (RFC 3.2) - Hierarchical and non-hierarchical relationships
- **Exploratory Methods** (RFC 4.1) - Read-only operations for browsing data
- **Value Methods** (RFC 4.2.1) - Reading current and historical values
- **Update Methods** (RFC 4.2.2) - Writing values (4.2.2.1 implemented, 4.2.2.2 returns 501)
- **Subscription Methods** (RFC 4.2.3) - Real-time data streaming with streaming/sync support

This implementation provides comprehensive RFC-compliant endpoints with proper metadata handling and JSON serialization. See the interactive Swagger UI documentation at http://localhost:8080/docs for complete API details.

