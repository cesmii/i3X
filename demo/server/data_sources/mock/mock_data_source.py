from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
import json
import os
from ..data_interface import I3XDataSource
from .mock_data import I3X_DATA
from .mock_updater import MockDataUpdater


class MockDataSource(I3XDataSource):
    """Mock data implementation of I3XDataSource"""

    def __init__(self):
        self.data = I3X_DATA
        self.updater = MockDataUpdater(self)
        self.update_callback = None
        # Cache for loaded schema files
        self._schema_cache = {}

    def _load_schema_definition(self, type_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load the full type definition from the schema file referenced in type_definition.

        Args:
            type_definition: Dict with elementId, displayName, namespaceUri, and schema pointer

        Returns:
            Complete type definition with schema pointer replaced by actual schema dict
        """
        schema_pointer = type_definition.get("schema", "")
        if not schema_pointer:
            # If no schema pointer, return metadata as-is
            return type_definition

        # If schema is already a dict (not a string pointer), return as-is
        if isinstance(schema_pointer, dict):
            return type_definition

        # Parse schema pointer: "Namespaces/abelara.json#types/state-type"
        if "#" not in schema_pointer:
            return type_definition

        file_path, json_pointer = schema_pointer.split("#", 1)

        # Load schema file (with caching)
        if file_path not in self._schema_cache:
            # Construct full path relative to this file's directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, file_path)

            try:
                with open(full_path, 'r') as f:
                    self._schema_cache[file_path] = json.load(f)
            except Exception as e:
                print(f"Error loading schema file {full_path}: {e}")
                return type_definition

        schema_data = self._schema_cache[file_path]

        # Navigate JSON pointer: "types/state-type" -> schema_data["types"]["state-type"]
        pointer_parts = json_pointer.strip("/").split("/")
        current = schema_data
        for part in pointer_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                print(f"Could not resolve JSON pointer {json_pointer} in {file_path}")
                return type_definition

        # Resolve any $ref pointers within the schema before returning
        current = self._resolve_refs(current, schema_data)

        # Replace the schema pointer string with the actual schema definition
        result = type_definition.copy()
        result["schema"] = current

        return result

    def _resolve_refs(self, schema: Any, document: Dict[str, Any], _visiting: frozenset = frozenset()) -> Any:
        """
        Recursively resolve $ref pointers within a schema against its source document.
        Only resolves same-document refs (starting with '#/'). External refs are left as-is.
        _visiting tracks in-progress pointers to prevent infinite recursion.
        """
        if isinstance(schema, dict):
            if "$ref" in schema:
                ref = schema["$ref"]
                if ref.startswith("#/"):
                    pointer = ref[2:]  # strip leading "#/"
                    if pointer in _visiting:
                        return schema  # circular ref, leave as-is
                    parts = pointer.split("/")
                    target = document
                    for part in parts:
                        if isinstance(target, dict) and part in target:
                            target = target[part]
                        else:
                            return schema  # unresolvable, leave as-is
                    resolved = self._resolve_refs(target, document, _visiting | {pointer})
                    # Merge any sibling keys (e.g. "description") alongside the resolved schema
                    other_keys = {k: v for k, v in schema.items() if k != "$ref"}
                    if other_keys and isinstance(resolved, dict):
                        return {**resolved, **other_keys}
                    return resolved
                # External $ref — leave untouched
                return schema
            return {k: self._resolve_refs(v, document, _visiting) for k, v in schema.items()}
        if isinstance(schema, list):
            return [self._resolve_refs(item, document, _visiting) for item in schema]
        return schema

    def start(
        self, update_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        """Initialize mock data source and start background updates"""
        self.update_callback = update_callback
        self.updater.start(self.update_callback)

    def stop(self) -> None:
        """Stop mock data source and cleanup background updates"""
        self.updater.stop()

    def get_namespaces(self) -> List[Dict[str, Any]]:
        return self.data["namespaces"]

    def get_object_types(
        self, namespace_uri: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Filter by namespace if specified
        type_definition_list = self.data["objectTypes"]
        if namespace_uri:
            type_definition_list = [
                t
                for t in type_definition_list
                if t["namespaceUri"] == namespace_uri
            ]

        # Load full schema definitions for each type
        result = []
        for type_definition in type_definition_list:
            full_type_def = self._load_schema_definition(type_definition)
            result.append(full_type_def)

        return result

    def get_object_type_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        # Find the type metadata
        for type_definition in self.data["objectTypes"]:
            if type_definition["elementId"] == element_id:
                # Load and return the full schema definition
                return self._load_schema_definition(type_definition)
        return None

    def get_relationship_types(
        self, namespace_uri: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if namespace_uri:
            return [
                t
                for t in self.data["relationshipTypes"]
                if t["namespaceUri"] == namespace_uri
            ]
        return self.data["relationshipTypes"]


    def get_relationship_type_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        for obj_type in self.data["relationshipTypes"]:
            if obj_type["elementId"] == element_id:
                return obj_type
        return None

    def get_instances(self, type_id: Optional[str] = None, root: bool = False) -> List[Dict[str, Any]]:
        instances = self.data["instances"]
        results = []
        if type_id:
            for instance in instances:
                if instance["typeElementId"] == type_id:
                    results.append(instance)
        else:
            results = instances

        if root:
            results = [i for i in results if i.get("parentId") is None]

        # Filter out records member from each instance before returning (unique to mock data)
        filtered_results = []
        for instance in results:
            filtered_instance = {k: v for k, v in instance.items() if k != "records"}
            filtered_results.append(filtered_instance)

        return filtered_results

    def get_instance_values_by_id(
        self,
        element_id: str,
        startTime: Optional[str] = None,
        endTime: Optional[str] = None,
        maxDepth: int = 1,
        returnHistory: bool = False,
    ):
        """
        Returns nested structure: {elementId: {data: [VQT...], childId: {...}, ...}}
        - 'data' is the reserved key for this element's VQT array
        - Other keys are child elementIds (HasComponent relationships)
        """
        return self._get_values_recursive(element_id, startTime, endTime, returnHistory, maxDepth)

    def _get_values_recursive(self, element_id: str, startTime, endTime, returnHistory: bool, max_depth: int):
        """Recursive helper for get_instance_values_by_id."""
        instance = self.get_instance_by_id(element_id, values=True)

        if not instance:
            return None

        records_array = instance.get("records")
        relationships = instance.get("relationships", {})
        composed_of = relationships.get("HasComponent", [])

        if isinstance(composed_of, str):
            composed_of = [composed_of]

        inner_result = {}

        # Process this element's own value
        if records_array and isinstance(records_array, list):
            own_vqt = self._process_records(records_array, startTime, endTime, returnHistory)
            if own_vqt is not None:
                inner_result["data"] = own_vqt if isinstance(own_vqt, list) else [own_vqt]
            else:
                inner_result["data"] = []
        else:
            inner_result["data"] = []

        # Recurse into HasComponent children if requested
        if (max_depth == 0 or max_depth > 1) and composed_of:
            next_max_depth = 0 if max_depth == 0 else max_depth - 1
            for child_id in composed_of:
                child_result = self._get_values_recursive(child_id, startTime, endTime, returnHistory, next_max_depth)
                if child_result is not None:
                    inner_result[child_id] = child_result.get(child_id, {})

        return {element_id: inner_result}

    def _process_records(self, records_array, startTime, endTime, returnHistory):
        """Helper method to process records array and return value with metadata"""
        returned_records = None

        # Filter based on time range
        if startTime and endTime:
            # Parse time strings to datetime objects for comparison
            start_dt = datetime.fromisoformat(startTime.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(endTime.replace("Z", "+00:00"))

            # Filter records array to only include items within time range
            filtered_records = []
            for record in records_array:
                if "timestamp" in record:
                    value_dt = datetime.fromisoformat(
                        record["timestamp"].replace("Z", "+00:00")
                    )
                    if start_dt <= value_dt <= end_dt:
                        filtered_records.append(record)

            returned_records = filtered_records
        else:
            # No time range specified
            if returnHistory:
                # Return all historical values for /history endpoint
                returned_records = records_array
            else:
                # Return only most recent value for /value endpoint
                most_recent = None
                most_recent_dt = None

                for record in records_array:
                    if "timestamp" in record:
                        value_dt = datetime.fromisoformat(
                            record["timestamp"].replace("Z", "+00:00")
                        )
                        if most_recent_dt is None or value_dt > most_recent_dt:
                            most_recent_dt = value_dt
                            most_recent = record

                returned_records = most_recent

        # Extract the value(s) from the records
        if isinstance(returned_records, list):
            # For historical values (list), extract value from each record with metadata
            return [{"value": record.get("value"), "quality": record.get("quality"), "timestamp": record.get("timestamp")}
                   for record in returned_records if "value" in record]
        elif isinstance(returned_records, dict) and "value" in returned_records:
            # For single value, extract value with metadata
            return {
                "value": returned_records["value"],
                "quality": returned_records.get("quality"),
                "timestamp": returned_records.get("timestamp")
            }
        else:
            return None

    def _handle_no_recurse(self, instance, records_array, startTime, endTime, returnHistory):
        """Handle the case when recurseDepth == 0"""
        # If no records, return None
        if not records_array or not isinstance(records_array, list):
            return None

        # Process and return the records
        return self._process_records(records_array, startTime, endTime, returnHistory)

    def get_instance_by_id(
        self, element_id: str, values: bool = False
    ) -> Optional[Dict[str, Any]]:
        for instance in self.data["instances"]:
            if instance["elementId"] == element_id:
                if values:
                    # Return instance with records included
                    return instance
                else:
                    # Filter out records member from each instance before returning (unique to mock data)
                    filtered_instance = {
                        k: v for k, v in instance.items() if k != "records"
                    }
                    return filtered_instance
        return None

    def get_related_instances(
        self, element_id: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        related_objects = []

        # Get the source instance directly from data (not filtered) to preserve relationships
        source_instance = None
        for instance in self.data["instances"]:
            if instance["elementId"] == element_id:
                source_instance = instance
                break

        if not source_instance:
            return related_objects

        # Check if instance has explicit relationship metadata
        relationships_metadata = source_instance.get("relationships", {})

        # If no relationship_type specified, return all related instances
        if relationship_type is None:
            # Iterate per type to preserve edge metadata per object
            seen_ids = set()
            for rel_type, related_ids in relationships_metadata.items():
                if isinstance(related_ids, str):
                    related_ids = [related_ids]
                if isinstance(related_ids, list):
                    for rid in related_ids:
                        if rid in seen_ids:
                            continue
                        for instance in self.data["instances"]:
                            if instance["elementId"] == rid:
                                filtered = {k: v for k, v in instance.items() if k != "records"}
                                filtered["sourceRelationship"] = rel_type
                                related_objects.append(filtered)
                                seen_ids.add(rid)
                                break
        else:
            # Look for the specific relationship type (case-insensitive match)
            matching_key = None
            for key in relationships_metadata.keys():
                if key.lower() == relationship_type.lower():
                    matching_key = key
                    break

            if matching_key:
                related_ids = relationships_metadata[matching_key]
                if isinstance(related_ids, str):
                    related_ids = [related_ids]
                for instance in self.data["instances"]:
                    if instance["elementId"] in related_ids:
                        filtered = {k: v for k, v in instance.items() if k != "records"}
                        filtered["sourceRelationship"] = matching_key
                        related_objects.append(filtered)
            # Fallback: Handle non-hierarchical relationships dynamically
            else:
                related_objects = self._process_non_hierarchical_relations(
                    element_id, relationship_type.lower()
                )

        return related_objects

    def _process_non_hierarchical_relations(
        self, element_id: str, relationship_type: str
    ) -> List[Dict[str, Any]]:
        """Fallback for dynamically determining relationships not found in metadata"""
        # This method can be extended in the future for semantic pattern matching
        # For now, return empty list since relationships should be explicit
        return []

    def update_instance_value(
        self, element_id: str, value: Any
    ) -> Dict[str, Any]:
        from datetime import datetime, timezone

        # Note this is a hack for now as the code below can handle multiple updates but for now we just want one
        element_ids = [element_id]
        values = [value]

        results = []
        for element_id, value in zip(element_ids, values):
            instance = self.get_instance_by_id(element_id, values=True)
            if not instance:
                results.append(
                    {
                        "elementId": element_id,
                        "success": False,
                        "message": "Element not found",
                    }
                )
                continue

            try:
                # Validate the write schema matches the instance schema
                # Now records have structure: {value: {...}, quality: "...", timestamp: "..."}
                current_value = instance["records"][0]["value"]
                value_schema = self._get_schema(value)
                instance_schema = self._get_schema(current_value)

                print(f"Value schema: {value_schema}")
                print(f"Instance schema: {instance_schema}")

                # Try to coerce value to match instance schema for primitive types
                coerced_value = value
                if value_schema != instance_schema:
                    # Attempt type coercion for numeric types
                    if instance_schema == "int" and value_schema in ["str", "float"]:
                        try:
                            coerced_value = int(float(value))
                            print(f"Coerced {value} ({value_schema}) to int")
                        except (ValueError, TypeError):
                            raise Exception(f"Cannot coerce value to int: {value}")
                    elif instance_schema == "float" and value_schema in ["str", "int"]:
                        try:
                            coerced_value = float(value)
                            print(f"Coerced {value} ({value_schema}) to float")
                        except (ValueError, TypeError):
                            raise Exception(f"Cannot coerce value to float: {value}")
                    elif instance_schema == "str" and value_schema in ["int", "float"]:
                        coerced_value = str(value)
                        print(f"Coerced {value} ({value_schema}) to str")
                    else:
                        raise Exception(f"Value schema ({value_schema}) does not match instance schema ({instance_schema})")

                # Update the value and timestamp in the record
                current_timestamp = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                instance["records"][0]["value"] = coerced_value
                instance["records"][0]["timestamp"] = current_timestamp

                # Also update timestamp inside value if it exists
                if isinstance(coerced_value, dict):
                    if "Timestamp" in coerced_value:
                        instance["records"][0]["value"]["Timestamp"] = current_timestamp
                    elif "timestamp" in coerced_value:
                        instance["records"][0]["value"]["timestamp"] = current_timestamp

                instance["timestamp"] = current_timestamp

                results.append(
                    {
                        "elementId": element_id,
                        "success": True,
                        "message": "Updated successfully",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "elementId": element_id,
                        "success": False,
                        "message": f"Update failed: {str(e)}",
                    }
                )

        return results[0]

    def _get_schema(self, obj):
        """Helper to get the schema for dictionaries"""
        if isinstance(obj, dict):
            return {k: self._get_schema(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            if not obj:
                return ["<empty>"]
            return [self._get_schema(obj[0])]
        else:
            return type(obj).__name__

    def _load_schema_raw(self, type_definition: Dict[str, Any]) -> Any:
        """Load schema from file without resolving $ref pointers — used for inheritance chain walking."""
        schema_pointer = type_definition.get("schema", "")
        if not isinstance(schema_pointer, str) or "#" not in schema_pointer:
            return {}
        file_path, json_pointer = schema_pointer.split("#", 1)
        if file_path not in self._schema_cache:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, file_path)
            try:
                with open(full_path, 'r') as f:
                    self._schema_cache[file_path] = json.load(f)
            except Exception:
                return {}
        schema_data = self._schema_cache[file_path]
        current = schema_data
        for part in json_pointer.strip("/").split("/"):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return {}
        return current

    def _collect_type_chain(self, type_id: str, _visited: frozenset = frozenset()) -> List[Dict[str, Any]]:
        """
        Walk the allOf inheritance chain for a type, returning an ordered list of
        {typeElementId, namespaceUri} from most specific (first) to most general (last).
        """
        if type_id in _visited:
            return []
        type_def = next((t for t in self.data["objectTypes"] if t["elementId"] == type_id), None)
        if not type_def:
            return []

        chain = [{"typeElementId": type_def["elementId"], "namespaceUri": type_def.get("namespaceUri")}]

        schema_pointer = type_def.get("schema", "")
        if not isinstance(schema_pointer, str) or "#" not in schema_pointer:
            return chain
        namespace_file = schema_pointer.split("#")[0]  # e.g. "Namespaces/thinkiq.json"

        raw_schema = self._load_schema_raw(type_def)
        for allof_entry in raw_schema.get("allOf", []):
            if isinstance(allof_entry, dict) and "$ref" in allof_entry:
                ref = allof_entry["$ref"]
                if ref.startswith("#/types/"):
                    parent_key = ref[len("#/types/"):]
                    parent_schema_pointer = f"{namespace_file}#types/{parent_key}"
                    parent_type = next(
                        (t for t in self.data["objectTypes"] if t.get("schema") == parent_schema_pointer),
                        None
                    )
                    if parent_type:
                        chain.extend(self._collect_type_chain(parent_type["elementId"], _visited | {type_id}))
        return chain

    def _collect_schema_properties(self, schema: Any) -> Dict[str, Any]:
        """
        Recursively collect all property definitions from a JSON Schema,
        resolving allOf chains so inherited properties are included.
        Returns a flat {name: schema_fragment} dict.
        """
        props = {}
        if not isinstance(schema, dict):
            return props
        for k, v in schema.get("properties", {}).items():
            props[k] = v
        for sub in schema.get("allOf", []):
            props.update(self._collect_schema_properties(sub))
        return props

    def _infer_json_type(self, value: Any) -> Dict[str, Any]:
        """Infer a minimal JSON Schema type fragment from a Python value."""
        if isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, list):
            return {"type": "array"}
        elif isinstance(value, dict):
            return {"type": "object"}
        return {}

    def _compute_extra_attributes(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return a {attrName: schema_fragment} dict for attributes present in the
        instance's most recent value that are not declared in its ObjectType schema.
        Returns an empty dict if the instance is fully conformant.
        """
        type_id = instance.get("typeElementId")
        type_def = self.get_object_type_by_id(type_id) if type_id else None
        declared_schema = type_def.get("schema", {}) if type_def else {}
        declared_props = self._collect_schema_properties(declared_schema)

        # Find most recent value
        most_recent_value = None
        most_recent_dt = None
        for record in instance.get("records", []):
            ts = record.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if most_recent_dt is None or dt > most_recent_dt:
                        most_recent_dt = dt
                        most_recent_value = record.get("value")
                except ValueError:
                    pass

        extra = {}
        if isinstance(most_recent_value, dict):
            for k, v in most_recent_value.items():
                if k not in declared_props:
                    extra[k] = self._infer_json_type(v)
        return extra

    def get_instance_extra_attributes(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Return extra (non-schema) attributes for an instance, or None if not found."""
        instance = self.get_instance_by_id(element_id, values=True)
        if not instance:
            return None
        return self._compute_extra_attributes(instance)

    def get_all_instances(self) -> List[Dict[str, Any]]:
        # Filter out records member from each instance before returning (unique to mock data)
        filtered_results = []
        for instance in self.data["instances"]:
            filtered_instance = {k: v for k, v in instance.items() if k != "records"}
            filtered_results.append(filtered_instance)
        return filtered_results
