import json
from genson import SchemaBuilder
import logging
import re
import ssl
import threading
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from ..data_interface import I3XDataSource

class MQTTDataSource(I3XDataSource):
    """MQTT data source implementation with topic->value caching
    
    Creates an MQTT connection on start and subscribes to the topics set in config.json. 
    Keeps a cache of topic --> value to return exploratory and read interfaces. 
    Does not support Updates interface or the Exploratory hierarchy methods for now. 
    Supports Reads and Subscriptions.
    """
    
    # Define the MQTT namespace URI as a class constant
    MQTT_NAMESPACE_URI = "http://i3x.org/mfg/mqtt"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mqtt_endpoint = config.get('mqtt_endpoint', '')
        self.topics = config.get('topics', [])
        self.excluded_topics = config.get('excluded_topics', [])
        self.username = config.get('username')
        self.password = config.get('password')
        self.topic_cache = {}  # topic -> value cache
        self.discovered_namespaces = {}  # namespace_uri -> display_name
        self.discovered_types = {}  # namespace_uri -> type definition (one type per $namespace)
        self.inferred_types = {}  # type_name -> type definition (for topics without $namespace)
        self.cache_lock = threading.Lock()  # Thread-safe access to cache
        self.client = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        self.update_callback = None
        
    def start(self, update_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """Initialize and start MQTT connection"""
        self.update_callback = update_callback
        if self.client is not None:
            return  # Already started
            
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Set username/password if provided
        if self.username is not None and self.password is not None:
            self.logger.info(f"Setting MQTT authentication for user: {self.username}")
            self.client.username_pw_set(self.username, self.password)
        
        # Parse MQTT endpoint (supports mqtt:// and mqtts:// for TLS)
        use_tls = False
        if self.mqtt_endpoint.startswith('mqtts://'):
            endpoint = self.mqtt_endpoint[8:]  # Remove mqtts:// prefix
            use_tls = True
            default_port = 8883
        elif self.mqtt_endpoint.startswith('mqtt://'):
            endpoint = self.mqtt_endpoint[7:]  # Remove mqtt:// prefix
            default_port = 1883
        else:
            raise ValueError(f"Invalid MQTT endpoint format: {self.mqtt_endpoint}. Use mqtt:// or mqtts://")
        
        # Extract host and port
        if ':' in endpoint:
            host, port = endpoint.split(':', 1)
            port = int(port)
        else:
            host = endpoint
            port = default_port
        
        # Configure TLS if needed
        if use_tls:
            self.logger.info(f"Configuring TLS for MQTT connection")
            # Create SSL context that accepts any certificate (insecure but simple)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.client.tls_set_context(context)
            
        self.logger.info(f"Connecting to MQTT broker at {host}:{port} (TLS: {use_tls})")

        try:
            self.client.connect(host, port, 60)
            self.client.loop_start()  # Start background thread
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker at {host}:{port}: {e}")
            raise
        
    def stop(self) -> None:
        """Stop and cleanup MQTT connection"""
        if self.client is not None:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
        self.is_connected = False
        with self.cache_lock:
            self.topic_cache.clear()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when MQTT client connects"""
        if rc == 0:
            self.is_connected = True
            self.logger.info("Successfully connected to MQTT broker")

            # Create virtual root node
            self._create_root_node()

            # Subscribe to all configured topics
            for topic in self.topics:
                self.logger.info(f"Subscribing to MQTT topic: {topic}")
                client.subscribe(topic)
            if self.topics:
                self.logger.info(f"Subscribed to {len(self.topics)} MQTT topics")
            else:
                self.logger.warning("No topics configured for MQTT subscription")

            # Clean up any excluded topics from existing cache after successful connection
            self._clean_excluded_topics_from_cache()
        else:
            self.logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when MQTT message is received"""
        try:
            # Check if topic should be excluded
            if self._is_topic_excluded(msg.topic):
                self.logger.debug(f"Skipping excluded topic: {msg.topic}")
                return
                
            # Try to parse as JSON, fallback to string, skip binary
            try:
                payload_str = msg.payload.decode('utf-8')
            except UnicodeDecodeError:
                # Skip binary payloads that can't be decoded as UTF-8
                self.logger.debug(f"Skipping binary payload on topic: {msg.topic}")
                return

            try:
                value = json.loads(payload_str)
            except json.JSONDecodeError:
                value = payload_str

            # Determine namespace and type for this payload
            namespace_uri = None
            type_id = None

            if isinstance(value, dict) and '$namespace' in value:
                # Payload has explicit $namespace - use discovered type
                namespace_uri = value['$namespace']
                type_id = self._namespace_to_type_id(namespace_uri)
                # Only add namespace and type if not already discovered
                if namespace_uri not in self.discovered_namespaces:
                    self.discovered_namespaces[namespace_uri] = namespace_uri
                    self.discovered_types[namespace_uri] = {
                        "elementId": type_id,
                        "displayName": type_id,
                        "namespaceUri": namespace_uri,
                        "schema": self._get_json_schema(value)
                    }
                    self.logger.info(f"Discovered new namespace and type from payload: {namespace_uri} -> {type_id}")
            else:
                # No $namespace - use inferred type based on topic name
                type_name = self._get_name_from_topic(msg.topic)
                type_id = f"{type_name}Type"
                # Only create inferred type if not already exists
                if type_id not in self.inferred_types:
                    self.inferred_types[type_id] = {
                        "elementId": type_id,
                        "displayName": type_id,
                        "namespaceUri": self.MQTT_NAMESPACE_URI,
                        "schema": self._get_json_schema(value)
                    }
                    self.logger.info(f"Created inferred type: {type_id}")

            # Update cache thread-safely
            with self.cache_lock:
                # Convert / to _ in topic for elementId to avoid URL path issues
                element_id = self._topic_to_element_id(msg.topic)
                timestamp = datetime.now(timezone.utc).isoformat()

                # Create virtual parent nodes for all intermediate path segments
                self._ensure_parent_chain(msg.topic, timestamp)

                self.topic_cache[element_id] = {
                    'value': value,
                    'timestamp': timestamp,
                    'topic': msg.topic,  # Keep original topic for reference
                    'namespaceUri': namespace_uri,  # Store discovered namespace (or None)
                    'typeElementId': type_id  # Store namespace-based type ID (or None for topic-based)
                }
                
                # If callback is set, notify subscription system of update
                if self.update_callback:
                    # Extract name from original topic
                    name = self._get_name_from_topic(msg.topic)

                    # Infer parentId from topic hierarchy
                    if '/' in msg.topic:
                        parent_topic = '/'.join(msg.topic.split('/')[:-1])
                        parent_element_id = self._topic_to_element_id(parent_topic)
                        if parent_element_id in self.topic_cache:
                            parent_id = parent_element_id
                        else:
                            parent_id = None
                    else:
                        # Top-level topic - parent is root
                        parent_id = '/'

                    instance = {
                        "elementId": element_id,
                        "displayName": name,
                        "typeElementId": type_id or (element_id + "_TYPE"),
                        "parentId": parent_id,
                        "isComposition": False,  # MQTT topic hierarchy is organizational, not composition
                        "namespaceUri": namespace_uri or self.MQTT_NAMESPACE_URI,
                        "timestamp": timestamp
                    }

                    # Pass full record with value, timestamp, and quality for subscription system
                    record = {
                        "value": value,
                        "timestamp": timestamp,
                        "quality": "Good"
                    }

                    try:
                        self.update_callback(instance, record)
                    except Exception as e:
                        self.logger.error(f"Error calling update callback: {e}")

        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when MQTT client disconnects"""
        self.is_connected = False
        if rc != 0:
            self.logger.warning(f"MQTT client disconnected unexpectedly with code {rc}")
        else:
            self.logger.info("MQTT client disconnected normally")
    
    def get_topic_value(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get cached value for a specific topic"""
        with self.cache_lock:
            return self.topic_cache.get(topic)
    
    def get_all_topic_values(self) -> Dict[str, Any]:
        """Get all cached topic values"""
        with self.cache_lock:
            return dict(self.topic_cache)

    # I3X Interface

    def get_namespaces(self) -> List[Dict[str, Any]]:
        """Return namespaces: default MQTT namespace plus any discovered from $namespace in payloads."""
        namespaces = []

        # Always include the default MQTT namespace (for inferred types without $namespace)
        namespaces.append({"uri": self.MQTT_NAMESPACE_URI, "displayName": "MQTT"})

        # Add discovered namespaces from payloads with $namespace
        for uri, display_name in self.discovered_namespaces.items():
            namespaces.append({"uri": uri, "displayName": display_name})

        return namespaces

    def get_object_types(self, namespace_uri: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return array of Type definitions.

        Returns:
        - Discovered types (one per $namespace found in payloads)
        - Inferred types (one per unique topic name, in default MQTT namespace)
        """
        types = []

        # Add discovered types (one per $namespace)
        for ns_uri, type_def in self.discovered_types.items():
            if namespace_uri is None or ns_uri == namespace_uri:
                types.append(type_def)

        # Add inferred types (for topics without $namespace)
        if namespace_uri is None or namespace_uri == self.MQTT_NAMESPACE_URI:
            for type_def in self.inferred_types.values():
                types.append(type_def)

        self.logger.info(f"Returning {len(types)} type definitions")
        return types
    
    def get_object_type_by_id(self, type_id: str) -> Optional[Dict[str, Any]]:
        """Return JSON structure defining a Type by its ID.

        Checks discovered types ($namespace-based) and inferred types (name-based).
        """
        # Check discovered types (from $namespace)
        for ns_uri, type_def in self.discovered_types.items():
            if type_def['elementId'] == type_id:
                return type_def

        # Check inferred types (from topic names)
        if type_id in self.inferred_types:
            return self.inferred_types[type_id]

        self.logger.warning(f"Type not found: {type_id}")
        return None

    def get_instances(self, type_id: Optional[str] = None, root: bool = False) -> List[Dict[str, Any]]:
        """Return array of instance objects, optionally filtered by type"""
        all_instances = self.get_all_instances()

        if root:
            all_instances = [i for i in all_instances if i.get("parentId") == "/"]

        # If no type filter specified, return all instances
        if type_id is None:
            return all_instances

        # Filter by typeElementId
        filtered_instances = [instance for instance in all_instances if instance["typeElementId"] == type_id]
        self.logger.info(f"Filtered {len(all_instances)} instances to {len(filtered_instances)} matching typeElementId: {type_id}")
        return filtered_instances
    
    def get_instance_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Return instance object by ElementId (topic)"""
        self.logger.info(f"Looking up instance by ID: {element_id}")

        with self.cache_lock:
            self.logger.info(f"Available topics in cache: {list(self.topic_cache.keys())}")
            topic_data = self.topic_cache.get(element_id)

            if topic_data is None:
                self.logger.warning(f"No data found for topic: {element_id}")
                return None

            self.logger.info(f"Found data for topic '{element_id}': {topic_data}")

            instance = self._build_instance(element_id, topic_data)

            self.logger.info(f"Returning instance: {instance}")
            return instance
    
    def get_instance_values_by_id(
        self,
        element_id: str,
        startTime: Optional[str] = None,
        endTime: Optional[str] = None,
        maxDepth: int = 1,
        returnHistory: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Return instance values by ElementId.

        Returns nested structure: {elementId: {data: [VQT]}}
        - 'data' is the reserved key for this element's VQT array
        - MQTT topics don't support composition, so no children are included

        Note: MQTT data source does not support historical values.
        startTime, endTime, and returnHistory parameters are accepted but ignored.
        """
        topic_data = self.get_topic_value(element_id)
        if topic_data is None:
            return None

        # Build VQT from cached topic data
        vqt = {
            "value": topic_data.get("value"),
            "quality": "GOOD",
            "timestamp": topic_data.get("timestamp")
        }

        # Return in new format: {elementId: {data: [VQT]}}
        return {element_id: {"data": [vqt]}}

    def get_relationship_types(self, namespace_uri: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return relationship types inferred from MQTT topic hierarchy"""
        if namespace_uri is not None and namespace_uri != self.MQTT_NAMESPACE_URI:
            return []

        return [
            {
                "elementId": "HasParent",
                "displayName": "Has Parent",
                "namespaceUri": self.MQTT_NAMESPACE_URI,
                "reverseOf": "HasChildren"
            },
            {
                "elementId": "HasChildren",
                "displayName": "Has Children",
                "namespaceUri": self.MQTT_NAMESPACE_URI,
                "reverseOf": "HasParent"
            },
            {
                "elementId": "HasSibling",
                "displayName": "Has Sibling",
                "namespaceUri": self.MQTT_NAMESPACE_URI,
                "reverseOf": "HasSibling"
            }
        ]

    def get_relationship_type_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Return a specific relationship type by ID"""
        relationship_types = self.get_relationship_types()
        for rel_type in relationship_types:
            if rel_type["elementId"].lower() == element_id.lower():
                return rel_type
        return None

    def get_related_instances(self, element_id: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return related instances based on MQTT topic hierarchy.

        Supports:
        - HasChildren/Children: Direct child topics
        - HasParent/Parent: Direct parent topic
        - HasSibling/Sibling: Topics with the same parent
        - None: Returns all related instances (parent, children, siblings)
        """
        if relationship_type is None:
            # Return all relationships
            all_related = []
            all_related.extend(self.get_related_instances(element_id, "HasParent"))
            all_related.extend(self.get_related_instances(element_id, "HasChildren"))
            all_related.extend(self.get_related_instances(element_id, "HasSibling"))
            return all_related

        rel_type_lower = relationship_type.lower()

        if rel_type_lower in ("haschildren", "children"):
            return self._get_children(element_id)
        elif rel_type_lower in ("hasparent", "parent"):
            return self._get_parent(element_id)
        elif rel_type_lower in ("hassibling", "sibling", "siblings"):
            return self._get_siblings(element_id)

        # Other relationship types not supported
        return []

    def _get_children(self, element_id: str) -> List[Dict[str, Any]]:
        """Return direct child topics for the given parent element_id"""
        children = []

        with self.cache_lock:
            # Root node - children are all top-level topics
            if element_id == '/':
                for cached_element_id, topic_data in self.topic_cache.items():
                    if cached_element_id == '/':
                        continue  # Skip root itself
                    original_topic = topic_data['topic']
                    # Top-level topic has no '/' in it
                    if '/' not in original_topic:
                        instance = self._build_instance(cached_element_id, topic_data)
                        children.append(instance)
                return children

            # Convert element_id back to topic path format
            parent_topic = element_id.replace('_', '/')

            for cached_element_id, topic_data in self.topic_cache.items():
                original_topic = topic_data['topic']

                # Check if this topic is a direct child of the parent
                # Child must start with parent path followed by '/'
                if original_topic.startswith(parent_topic + '/'):
                    # Get the remaining path after the parent
                    remaining_path = original_topic[len(parent_topic) + 1:]

                    # Direct child means no more '/' separators in remaining path
                    if '/' not in remaining_path:
                        instance = self._build_instance(cached_element_id, topic_data)
                        children.append(instance)

        return children

    def _get_parent(self, element_id: str) -> List[Dict[str, Any]]:
        """Return the direct parent topic for the given child element_id"""
        with self.cache_lock:
            # Root node has no parent
            if element_id == '/':
                return []

            topic_data = self.topic_cache.get(element_id)
            if topic_data is None:
                return []

            original_topic = topic_data['topic']

            if '/' not in original_topic:
                # Top-level topic - parent is root
                if '/' in self.topic_cache:
                    root_topic_data = self.topic_cache['/']
                    root_instance = self._build_instance('/', root_topic_data)
                    return [root_instance]
                return []

            # Get parent topic by removing last segment
            parent_topic = '/'.join(original_topic.split('/')[:-1])
            parent_element_id = self._topic_to_element_id(parent_topic)

            # Check if parent exists in cache
            if parent_element_id in self.topic_cache:
                parent_topic_data = self.topic_cache[parent_element_id]
                parent_instance = self._build_instance(parent_element_id, parent_topic_data)
                return [parent_instance]

        return []

    def _get_siblings(self, element_id: str) -> List[Dict[str, Any]]:
        """Return sibling topics (topics with the same parent) for the given element_id"""
        siblings = []

        # Root node has no siblings
        if element_id == '/':
            return []

        with self.cache_lock:
            topic_data = self.topic_cache.get(element_id)
            if topic_data is None:
                return []

            original_topic = topic_data['topic']
            if '/' not in original_topic:
                # Top-level topics are siblings (they share root as parent)
                for cached_element_id, cached_topic_data in self.topic_cache.items():
                    if cached_element_id == '/' or cached_element_id == element_id:
                        continue  # Skip root and self
                    cached_topic = cached_topic_data['topic']
                    # Top-level sibling: no '/' in topic
                    if '/' not in cached_topic:
                        instance = self._build_instance(cached_element_id, cached_topic_data)
                        siblings.append(instance)
                return siblings

            # Get parent topic by removing last segment
            parent_topic = '/'.join(original_topic.split('/')[:-1])

            for cached_element_id, cached_topic_data in self.topic_cache.items():
                if cached_element_id == element_id:
                    continue  # Skip self

                cached_topic = cached_topic_data['topic']

                # Check if this topic has the same parent
                if '/' in cached_topic:
                    cached_parent = '/'.join(cached_topic.split('/')[:-1])
                    if cached_parent == parent_topic:
                        instance = self._build_instance(cached_element_id, cached_topic_data)
                        siblings.append(instance)

        return siblings

    def update_instance_value(self, element_id: str, value: Any) -> Dict[str, Any]:
        """Update values for specified element IDs by publishing to MQTT topics"""
        if not self.is_connected or self.client is None:
            self.logger.error("MQTT client is not connected, cannot publish updates")
            return []

        result = {}

        try:
            # Convert element_id back to topic path
            topic = element_id.replace('_', '/')

            # Serialize value to JSON if it's not already a string
            if isinstance(value, str):
                payload = value
            else:
                payload = json.dumps(value)

            # Publish to MQTT topic
            mqtt_result = self.client.publish(topic, payload)

            if mqtt_result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Successfully published to topic '{topic}': {payload}")
                result = {
                    "elementId": element_id,
                    "success": True,
                    "message": "Published successfully"
                }
            else:
                self.logger.error(f"Failed to publish to topic '{topic}', error code: {mqtt_result.rc}")
                result = {
                    "elementId": element_id,
                    "success": False,
                    "message": f"Publish failed with error code {result.rc}"
                }

        except Exception as e:
            self.logger.error(f"Error publishing to element_id '{element_id}': {e}")
            result = {
                "elementId": element_id,
                "success": False,
                "message": f"Exception: {str(e)}"
            }

        return result
    
    def get_all_instances(self) -> List[Dict[str, Any]]:
        """Return all instances from MQTT topics"""
        instances = []

        with self.cache_lock:
            for element_id, topic_data in self.topic_cache.items():
                instance = self._build_instance(element_id, topic_data)
                instances.append(instance)

        return instances
    

    # Helpers to respond to data source method calls above

    # Create a "type" definition based on the value on a payload
    def _get_json_schema(self, value: Any) -> List[Dict[str, Any]]:
        builder = SchemaBuilder()
        builder.add_object(value)
        schema = builder.to_schema()
        return (schema)

    # Convert value type to type definition. Do not traverse objects or arrays
    def _get_data_type(self, value: Any) -> str:
        """Map Python types to I3X data types"""
        if isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, (dict, list)):
            return "object"
        else:
            return "string"  # Default fallback
    
    def _get_name_from_topic(self, topic: str) -> str:
        """Extract name from last part of topic path"""
        return topic.split('/')[-1] if '/' in topic else topic
    
    def _topic_to_element_id(self, topic: str) -> str:
        """Convert / to _ in topic for elementId to avoid URL path issues"""
        return topic.replace('/', '_')

    def _namespace_to_type_id(self, namespace_uri: str) -> str:
        """Convert namespace URI to a type ID.

        Uses the last meaningful path segment of the URI as the type name.
        E.g., 'https://opcfoundation.org/UA/Machinery/MachineIdentification/v1.0'
              -> 'MachineIdentification'
        """
        # Remove trailing slash and split
        parts = namespace_uri.rstrip('/').split('/')
        # Skip version-like segments (v1.0, v2, etc.) and find last meaningful name
        for part in reversed(parts):
            if not re.match(r'^v?\d+(\.\d+)*$', part, re.IGNORECASE):
                return part
        # Fallback to last segment if all are version-like
        return parts[-1] if parts else namespace_uri

    def _is_topic_excluded(self, topic: str) -> bool:
        """Check if a topic should be excluded based on excluded_topics config.
        Supports wildcards using * character.
        Returns True if the topic matches any exclusion pattern.
        """
        for excluded in self.excluded_topics:
            if self._topic_matches_pattern(topic, excluded):
                return True
                
        return False
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if a topic matches a pattern with wildcard support.
        * matches any sequence of characters within a topic level
        """
        try:
            # If no wildcards, use exact matching and hierarchical matching
            if '*' not in pattern:
                # Check exact match
                if topic == pattern:
                    return True
                # Check if topic is a child of pattern (starts with pattern + '/')
                if topic.startswith(pattern + '/'):
                    return True
                return False
            
            # Split both topic and pattern by '/' to handle wildcards per level
            topic_parts = topic.split('/')
            pattern_parts = pattern.split('/')
            
            # For hierarchical matching, the pattern can match if:
            # 1. All pattern parts match the beginning of topic parts (exact match)
            # 2. Topic has more parts than pattern (hierarchical child match)
            
            # Check exact match first
            if self._match_parts_exact(topic_parts, pattern_parts):
                return True
                
            # Check hierarchical match - pattern matches prefix of topic
            if len(topic_parts) > len(pattern_parts):
                return self._match_parts_exact(topic_parts[:len(pattern_parts)], pattern_parts)
                
            return False
        except Exception as e:
            self.logger.error(f"Error matching topic '{topic}' against pattern '{pattern}': {e}")
            return False
    
    def _match_parts_exact(self, topic_parts: list, pattern_parts: list) -> bool:
        """Match topic parts against pattern parts exactly (same number of parts)"""
        if len(topic_parts) != len(pattern_parts):
            return False
            
        for i in range(len(pattern_parts)):
            if not self._match_single_part(topic_parts[i], pattern_parts[i]):
                return False
                
        return True
    
    def _match_single_part(self, topic_part: str, pattern_part: str) -> bool:
        """Match a single topic part against a pattern part with wildcard support"""
        if pattern_part == '*':
            return True
            
        if '*' not in pattern_part:
            return topic_part == pattern_part
            
        # Handle wildcards within the pattern part (like "temp*data")
        # Convert * to regex .* and escape other regex special chars
        regex_pattern = re.escape(pattern_part).replace('\\*', '.*')
        return re.match(f'^{regex_pattern}$', topic_part) is not None
    
    def _clean_excluded_topics_from_cache(self) -> None:
        """Remove any excluded topics from the existing cache"""
        if not self.excluded_topics:
            return
            
        with self.cache_lock:
            # Get list of element_ids to remove (can't modify dict while iterating)
            to_remove = []
            for element_id, topic_data in self.topic_cache.items():
                original_topic = topic_data['topic']
                if self._is_topic_excluded(original_topic):
                    to_remove.append(element_id)
            
            # Remove excluded topics from cache
            for element_id in to_remove:
                self.logger.info(f"Removing excluded topic from cache: {self.topic_cache[element_id]['topic']}")
                del self.topic_cache[element_id]
                
            if to_remove:
                self.logger.info(f"Cleaned {len(to_remove)} excluded topics from cache")

    def _build_instance(self, element_id: str, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to build an instance object from element_id and topic_data.

        Infers parentId from topic hierarchy and isComposition from presence of children.
        """
        original_topic = topic_data['topic']
        name = self._get_name_from_topic(original_topic)

        # Infer parentId from topic hierarchy
        if original_topic == '/':
            # Root node has no parent
            parent_id = None
        elif '/' in original_topic:
            # Nested topic - parent is the path minus the last segment
            parent_topic = '/'.join(original_topic.split('/')[:-1])
            parent_element_id = self._topic_to_element_id(parent_topic)
            # Only set parentId if parent exists in cache
            if parent_element_id in self.topic_cache:
                parent_id = parent_element_id
            else:
                parent_id = None
        else:
            # Top-level topic - parent is root
            parent_id = '/'

        # Use discovered namespace from payload, or fall back to default
        namespace_uri = topic_data.get('namespaceUri') or self.MQTT_NAMESPACE_URI
        # Use stored type ID, or infer from topic name for virtual nodes
        type_id = topic_data.get('typeElementId')
        if type_id is None:
            type_name = self._get_name_from_topic(original_topic)
            type_id = f"{type_name}Type"

        return {
            "elementId": element_id,
            "displayName": name,
            "typeElementId": type_id,
            "parentId": parent_id,
            "isComposition": False,  # MQTT topic hierarchy is organizational, not composition
            "namespaceUri": namespace_uri,
            "attributes": topic_data['value'],
            "timestamp": topic_data['timestamp']
        }

    def _has_children(self, topic: str) -> bool:
        """Check if a topic has any child topics in the cache.

        Note: Caller must hold cache_lock or call within a locked context.
        """
        for cached_element_id, cached_topic_data in self.topic_cache.items():
            cached_topic = cached_topic_data['topic']
            # Child must start with this topic followed by '/'
            if cached_topic.startswith(topic + '/'):
                return True
        return False

    def _create_root_node(self) -> None:
        """Create the virtual root node that all top-level topics attach to."""
        with self.cache_lock:
            if '/' not in self.topic_cache:
                timestamp = datetime.now(timezone.utc).isoformat()
                self.topic_cache['/'] = {
                    'value': None,
                    'timestamp': timestamp,
                    'topic': '/',
                    'virtual': True,
                    'namespaceUri': None,  # Virtual nodes use default namespace
                    'typeElementId': None
                }
                self.logger.info("Created virtual root node: /")

    def _ensure_parent_chain(self, topic: str, timestamp: str) -> None:
        """Create virtual parent nodes for all intermediate path segments.

        For a topic like 'a/b/c/d', creates cache entries for 'a', 'a/b', and 'a/b/c'
        if they don't already exist. Virtual nodes have None values but proper topic
        paths so parentId relationships can be resolved.

        Note: Caller must hold cache_lock.
        """
        parts = topic.split('/')

        # Build parent paths from root to immediate parent
        # For 'a/b/c/d', we create: 'a', 'a/b', 'a/b/c'
        for i in range(1, len(parts)):
            parent_topic = '/'.join(parts[:i])
            parent_element_id = self._topic_to_element_id(parent_topic)

            # Only create if not already in cache
            if parent_element_id not in self.topic_cache:
                self.topic_cache[parent_element_id] = {
                    'value': None,  # Virtual node has no value
                    'timestamp': timestamp,
                    'topic': parent_topic,
                    'virtual': True,  # Mark as virtual for debugging
                    'namespaceUri': None,  # Virtual nodes use default namespace
                    'typeElementId': None
                }
                self.logger.debug(f"Created virtual parent node: {parent_topic}")
