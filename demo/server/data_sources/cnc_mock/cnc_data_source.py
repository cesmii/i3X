"""
CNC Mock Data Source - Implements I3XDataSource interface for CNC machine data.

This data source provides simulated CNC machine data based on the CESMII CNC profile
(OPC UA NodeSet2 information model).
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from ..data_interface import I3XDataSource
from .cnc_data import CNC_DATA
from .cnc_updater import CNCDataUpdater


class CNCDataSource(I3XDataSource):
    """CNC Mock data implementation of I3XDataSource"""

    def __init__(self):
        self.data = CNC_DATA
        self.updater = CNCDataUpdater(self)
        self.update_callback = None

    def start(
        self, update_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        """Initialize CNC data source and start background updates"""
        self.update_callback = update_callback
        self.updater.start(self.update_callback)

    def stop(self) -> None:
        """Stop CNC data source and cleanup background updates"""
        self.updater.stop()

    def get_namespaces(self) -> List[Dict[str, Any]]:
        return self.data["namespaces"]

    def get_object_types(
        self, namespace_uri: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        type_definition_list = self.data["objectTypes"]
        if namespace_uri:
            type_definition_list = [
                t
                for t in type_definition_list
                if t["namespaceUri"] == namespace_uri
            ]
        return type_definition_list

    def get_object_type_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        for type_definition in self.data["objectTypes"]:
            if type_definition["elementId"] == element_id:
                return type_definition
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
        for rel_type in self.data["relationshipTypes"]:
            if rel_type["elementId"] == element_id:
                return rel_type
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

        # Filter out records member from each instance before returning
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

        if startTime and endTime:
            start_dt = datetime.fromisoformat(startTime.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(endTime.replace("Z", "+00:00"))

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
            if returnHistory:
                returned_records = records_array
            else:
                # Return only most recent value
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

        if isinstance(returned_records, list):
            return [{"value": record.get("value"), "quality": record.get("quality"), "timestamp": record.get("timestamp")}
                   for record in returned_records if "value" in record]
        elif isinstance(returned_records, dict) and "value" in returned_records:
            return {
                "value": returned_records["value"],
                "quality": returned_records.get("quality"),
                "timestamp": returned_records.get("timestamp")
            }
        else:
            return None

    def get_instance_by_id(
        self, element_id: str, values: bool = False
    ) -> Optional[Dict[str, Any]]:
        for instance in self.data["instances"]:
            if instance["elementId"] == element_id:
                if values:
                    return instance
                else:
                    filtered_instance = {
                        k: v for k, v in instance.items() if k != "records"
                    }
                    return filtered_instance
        return None

    def get_related_instances(
        self, element_id: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        related_objects = []

        source_instance = None
        for instance in self.data["instances"]:
            if instance["elementId"] == element_id:
                source_instance = instance
                break

        if not source_instance:
            return related_objects

        relationships_metadata = source_instance.get("relationships", {})

        if relationship_type is None:
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

        return related_objects

    def update_instance_value(
        self, element_id: str, value: Any
    ) -> Dict[str, Any]:
        from datetime import datetime, timezone

        instance = self.get_instance_by_id(element_id, values=True)
        if not instance:
            return {
                "elementId": element_id,
                "success": False,
                "message": "Element not found",
            }

        try:
            records = instance.get("records")
            if not records or len(records) == 0:
                return {
                    "elementId": element_id,
                    "success": False,
                    "message": "Element has no records to update",
                }

            current_timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            records[0]["value"] = value
            records[0]["timestamp"] = current_timestamp

            return {
                "elementId": element_id,
                "success": True,
                "message": "Updated successfully",
            }
        except Exception as e:
            return {
                "elementId": element_id,
                "success": False,
                "message": f"Update failed: {str(e)}",
            }

    def get_all_instances(self) -> List[Dict[str, Any]]:
        filtered_results = []
        for instance in self.data["instances"]:
            filtered_instance = {k: v for k, v in instance.items() if k != "records"}
            filtered_results.append(filtered_instance)
        return filtered_results
