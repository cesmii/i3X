from typing import Any
from datetime import datetime, timezone


def success_response(result):
    return {"success": True, "result": result}


def error_response(message):
    return {"success": False, "error": {"message": message}}


def bulk_response(succeeded, failed):
    overall_success = len(failed) == 0
    return {"success": overall_success, "result": {"succeeded": succeeded, "failed": failed}}


def getObject(instance: Any, includeMetadata: bool) -> Any:
    """Helper to format object with or without metadata"""
    if includeMetadata:
        return instance

    noMetadataObject = {
        "elementId": instance["elementId"],
        "displayName": instance["displayName"],
        "typeId": instance["typeId"],
        "namespaceUri": instance["namespaceUri"],
        "parentId": instance.get("parentId"),
        "isComposition": instance["isComposition"]
    }
    return noMetadataObject


def getValue(value: Any, includeMetadata: bool) -> Any:
    """Helper to format value with or without metadata"""
    if not includeMetadata:
        return value

    metadataValue = {
        "dataType": "object",
        "quality": "GoodNoData" if not value else "Good",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "value": value
    }

    return metadataValue


def getValueMetadata(value: Any) -> Any:
    """Helper to extract metadata from value"""
    metadata = {
        "dataType": "object",
        "quality": "GoodNoData" if not value else "Good",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return metadata


def transform_value_result(element_id: str, ds_result: Any, instance: Any, is_history: bool = False) -> Any:
    """
    Converts data source {elementId: {data: [VQT...], childId: {...}}}
    to guide format {isComposition, value, quality, timestamp}.

    Returns the 'result' value for a bulk succeeded item.
    For is_history=True, returns a list of VQT dicts.
    """
    if element_id not in ds_result:
        return None

    element_data = ds_result[element_id]
    is_composition = instance.get("isComposition", False) if instance else False

    # Check if there are child keys (composition structure with children)
    child_keys = [k for k in element_data.keys() if k != "data"]

    if is_history:
        data_list = element_data.get("data", [])
        result = []
        for vqt in data_list:
            result.append({
                "isComposition": is_composition,
                "value": vqt.get("value"),
                "quality": vqt.get("quality"),
                "timestamp": vqt.get("timestamp")
            })
        return result
    elif child_keys:
        # Composition with children: build nested value
        parent_data = element_data.get("data", [{}])
        parent_vqt = parent_data[0] if parent_data else {}

        value_dict = {"_value": parent_vqt}
        for child_key in child_keys:
            child_data = element_data[child_key]
            if isinstance(child_data, dict) and "data" in child_data:
                child_vqt = child_data["data"][0] if child_data["data"] else {}
                value_dict[child_key] = child_vqt
            else:
                value_dict[child_key] = child_data

        return {
            "isComposition": True,
            "value": value_dict,
            "quality": parent_vqt.get("quality"),
            "timestamp": parent_vqt.get("timestamp")
        }
    else:
        # Simple (no children): flat VQT
        data_list = element_data.get("data", [{}])
        vqt = data_list[0] if data_list else {}

        return {
            "isComposition": is_composition,
            "value": vqt.get("value"),
            "quality": vqt.get("quality"),
            "timestamp": vqt.get("timestamp")
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
                result = {"elementId": element_id, "value": transformed.get("value")}
                if transformed.get("isComposition") and isinstance(transformed.get("value"), dict):
                    parent_vqt = transformed["value"].get("_value", {})
                    result["quality"] = parent_vqt.get("quality") if isinstance(parent_vqt, dict) else None
                    result["timestamp"] = parent_vqt.get("timestamp") if isinstance(parent_vqt, dict) else None
                else:
                    result["quality"] = transformed.get("quality")
                    result["timestamp"] = transformed.get("timestamp")
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
