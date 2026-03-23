from typing import Any


def success_response(result):
    return {"success": True, "result": result}


def error_response(message):
    return {"success": False, "error": {"message": message}}


def bulk_response(succeeded, failed):
    overall_success = len(failed) == 0
    return {"success": overall_success, "result": {"succeeded": succeeded, "failed": failed}}


def getObject(instance: Any, includeMetadata: bool, type_info: Any = None) -> Any:
    """Helper to format object with or without metadata"""
    STANDARD_FIELDS = {"elementId", "displayName", "typeElementId", "parentId", "isComposition", "namespaceUri", "relationships", "records"}

    base = {
        "elementId": instance["elementId"],
        "displayName": instance["displayName"],
        "typeElementId": instance["typeElementId"],
        "parentId": instance.get("parentId"),
        "isComposition": instance["isComposition"],
        "namespaceUri": instance.get("namespaceUri"),
    }
    if not includeMetadata:
        return base

    metadata_object = dict(base)
    if type_info:
        metadata_object["typeNamespaceUri"] = type_info.get("namespaceUri")
        metadata_object["typeId"] = type_info.get("typeId")
    metadata_object["relationships"] = instance.get("relationships", {})

    # Include any extra instance-level properties (RFC 3.1.2 optional metadata)
    for key, value in instance.items():
        if key not in STANDARD_FIELDS:
            metadata_object[key] = value

    return metadata_object



def transform_value_result(element_id: str, ds_result: Any, instance: Any, is_history: bool = False) -> Any:
    """
    Converts data source {elementId: {data: [VQT...], childId: {...}}}
    to the response format described in the Implementation Guide.

    For current value (is_history=False):
      Simple:      {isComposition, value, quality, timestamp}
      Composition: {isComposition, value, quality, timestamp, components: {childId: {value, quality, timestamp}}}

    For history (is_history=True):
      {isComposition, values: [{value, quality, timestamp}, ...]}
    """
    if element_id not in ds_result:
        return None

    element_data = ds_result[element_id]
    is_composition = instance.get("isComposition", False) if instance else False
    child_keys = [k for k in element_data.keys() if k != "data"]

    if is_history:
        data_list = element_data.get("data", [])
        return {
            "isComposition": is_composition,
            "values": [
                {"value": vqt.get("value"), "quality": vqt.get("quality"), "timestamp": vqt.get("timestamp")}
                for vqt in data_list
            ]
        }
    elif child_keys:
        # Composition with children: parent's own VQT at top level, children under 'components'
        parent_data = element_data.get("data", [{}])
        parent_vqt = parent_data[0] if parent_data else {}

        components = {}
        for child_key in child_keys:
            child_data = element_data[child_key]
            if isinstance(child_data, dict) and "data" in child_data:
                child_vqt = child_data["data"][0] if child_data["data"] else {}
                components[child_key] = {
                    "value": child_vqt.get("value"),
                    "quality": child_vqt.get("quality"),
                    "timestamp": child_vqt.get("timestamp"),
                }
            else:
                components[child_key] = child_data

        return {
            "isComposition": True,
            "value": parent_vqt.get("value"),
            "quality": parent_vqt.get("quality"),
            "timestamp": parent_vqt.get("timestamp"),
            "components": components,
        }
    else:
        # Simple leaf element
        data_list = element_data.get("data", [{}])
        vqt = data_list[0] if data_list else {}

        return {
            "isComposition": is_composition,
            "value": vqt.get("value"),
            "quality": vqt.get("quality"),
            "timestamp": vqt.get("timestamp"),
        }


def getSubscriptionValue(instance: Any, record: Any, maxDepth: int = 1, data_source: Any = None) -> Any:
    """
    Helper to get subscription value in flat {elementId, value, quality, timestamp} format.

    Args:
        instance: The instance object with elementId
        record: The record object with structure {value: ..., quality: ..., timestamp: ..., etc}
        maxDepth: Controls recursion (0=infinite, 1=no recursion, N=recurse N levels). Requires data_source if not 1.
        data_source: Data source to fetch recursive values (required if maxDepth != 1)

    Returns:
        Dictionary with format: {elementId, value, quality, timestamp}
    """
    element_id = instance["elementId"]

    # If maxDepth != 1 (i.e., recursion is needed) and we have a data_source, fetch the full recursive structure
    should_recurse = (maxDepth == 0 or maxDepth > 1)
    if should_recurse and data_source is not None:
        ds_result = data_source.get_instance_values_by_id(
            element_id, maxDepth=maxDepth, returnHistory=False
        )
        if ds_result and element_id in ds_result:
            transformed = transform_value_result(element_id, ds_result, instance, is_history=False)
            if isinstance(transformed, dict):
                result = {
                    "elementId": element_id,
                    "value": transformed.get("value"),
                    "quality": transformed.get("quality"),
                    "timestamp": transformed.get("timestamp"),
                }
                if transformed.get("components"):
                    result["components"] = transformed["components"]
                return result

    # Build flat VQT from record
    actual_value = record.get("value") if isinstance(record, dict) else record
    quality = record.get("quality") if isinstance(record, dict) else None
    timestamp = record.get("timestamp") if isinstance(record, dict) else None

    return {
        "elementId": element_id,
        "value": actual_value,
        "quality": quality,
        "timestamp": timestamp
    }
