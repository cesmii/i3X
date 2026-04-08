from typing import Any
from fastapi import Request


def get_data_source(request: Request) -> Any:
    """Shared FastAPI dependency — injects the configured data source into route handlers."""
    return request.app.state.data_source


OBJECT_TYPE_FIELDS = {"elementId", "displayName", "namespaceUri", "sourceTypeId", "version", "schema", "related"}


def formatObjectType(type_def: Any) -> Any:
    """Filter an ObjectType dict to the spec-defined fields, excluding implementation internals."""
    return {k: v for k, v in type_def.items() if k in OBJECT_TYPE_FIELDS}


def success_response(result):
    return {"success": True, "result": result}


def error_response(message, code=500):
    return {"success": False, "error": {"code": code, "message": message}}


def bulk_response(results):
    overall_success = all(r.get("success", False) for r in results)
    return {"success": overall_success, "results": results}


def getObject(instance: Any, includeMetadata: bool, type_info: Any = None, extra_attrs: Any = None) -> Any:
    """Helper to format object with or without metadata.

    extra_attrs: dict of {attrName: schema_fragment} for attributes present in the
    instance's value but not declared in its ObjectType. Pass None to skip the check.
    """
    STANDARD_FIELDS = {"elementId", "displayName", "description", "typeElementId", "parentId", "isComposition", "namespaceUri", "relationships", "records"}

    is_extended = bool(extra_attrs)
    base = {
        "elementId": instance["elementId"],
        "displayName": instance["displayName"],
        "typeElementId": instance["typeElementId"],
        "parentId": instance.get("parentId"),
        "isComposition": instance["isComposition"],
        "isExtended": is_extended,
    }
    if not includeMetadata:
        return base

    metadata = {}
    if type_info:
        metadata["typeNamespaceUri"] = type_info.get("namespaceUri")
        metadata["sourceTypeId"] = type_info.get("sourceTypeId")
    if instance.get("description") is not None:
        metadata["description"] = instance["description"]        
    metadata["relationships"] = instance.get("relationships", {})

    if extra_attrs:
        metadata["extendedAttributes"] = extra_attrs

    # Collect vendor/server-defined instance-level properties (RFC 3.1.2 optional metadata)
    # into metadata.system. Values are limited to primitives (string, number, boolean).
    system = {
        k: v for k, v in instance.items()
        if k not in STANDARD_FIELDS and isinstance(v, (str, int, float, bool))
    }
    if system:
        metadata["system"] = system

    return {**base, "metadata": metadata}



def transform_value_result(element_id: str, ds_result: Any, instance: Any, is_history: bool = False) -> tuple:
    """
    Converts data source {elementId: {data: [VQT...], _truncated: bool, childId: {...}}}
    to the response format described in the Implementation Guide.

    Returns (result, was_truncated) where was_truncated is True if server limits caused
    the result to be incomplete. The caller MUST return HTTP 206 when was_truncated is True.

    For current value (is_history=False):
      Simple:      {value, quality, timestamp}
      Composition: {value, quality, timestamp, components: {childId: {value, quality, timestamp}}}

    For history (is_history=True):
      {values: [{value, quality, timestamp}, ...]}
    """
    INTERNAL_KEYS = {"data", "_truncated"}

    if element_id not in ds_result:
        return None, False

    element_data = ds_result[element_id]
    child_keys = [k for k in element_data.keys() if k not in INTERNAL_KEYS]
    was_truncated = element_data.get("_truncated", False)

    if is_history:
        data_list = element_data.get("data", [])
        return {
            "values": [
                {"value": vqt.get("value"), "quality": vqt.get("quality"), "timestamp": vqt.get("timestamp")}
                for vqt in data_list
            ]
        }, was_truncated
    elif child_keys:
        # Composition with children: parent's own VQT at top level, children under 'components'
        parent_data = element_data.get("data", [{}])
        parent_vqt = parent_data[0] if parent_data else {}

        components = {}
        for child_key in child_keys:
            child_data = element_data[child_key]
            if isinstance(child_data, dict) and "data" in child_data:
                child_vqt = child_data["data"][0] if child_data["data"] else {}
                child_entry = {
                    "value": child_vqt.get("value"),
                    "quality": child_vqt.get("quality"),
                    "timestamp": child_vqt.get("timestamp"),
                }
                if child_data.get("_truncated"):
                    was_truncated = True
            else:
                child_entry = child_data
            components[child_key] = child_entry

        return {
            "value": parent_vqt.get("value"),
            "quality": parent_vqt.get("quality"),
            "timestamp": parent_vqt.get("timestamp"),
            "components": components,
        }, was_truncated
    else:
        # Simple leaf element (or composition element where all children were server-truncated)
        data_list = element_data.get("data", [{}])
        vqt = data_list[0] if data_list else {}

        return {
            "value": vqt.get("value"),
            "quality": vqt.get("quality"),
            "timestamp": vqt.get("timestamp"),
        }, was_truncated


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
            transformed, _ = transform_value_result(element_id, ds_result, instance, is_history=False)
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
