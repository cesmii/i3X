from typing import Any
from datetime import datetime, timezone
from fastapi import Request
from models import ErrorResponse

# Shared response schema dicts for use in route decorators
BASE_ERROR_RESPONSES = {
    "default": {"model": ErrorResponse, "description": "Error — see responseDetail.status for the HTTP status code (400, 401, 403, 404, 500, etc.)"},
}

NOT_IMPLEMENTED_RESPONSE = {
    501: {"model": ErrorResponse, "description": "Not Implemented — optional feature not supported by this server"},
}

NOT_FOUND_RESPONSE = {
    404: {"model": ErrorResponse, "description": "Not Found — ElementId or resource does not exist"},
}

PARTIAL_CONTENT_DESCRIPTION = "Partial Content — server-imposed depth limit reached; response contains available data only"

# Guide § Response Format: a 206 body MUST carry a top-level responseDetail.
DEPTH_LIMIT_DETAIL = {
    "title": "Partial results returned",
    "status": 206,
    "detail": "Result set was truncated due to server-imposed depth limits. Issue follow-up requests for the affected elementIds to retrieve the remaining composition data.",
}


def capability_enabled(request: Request, group: str, name: str, default: bool) -> bool:
    """Read a capability flag from config; a bare boolean for the group applies to all its flags.
    The same flags are advertised by GET /info, so endpoints and /info never disagree."""
    capabilities_config = getattr(request.app.state, "capabilities_config", {})
    value = capabilities_config.get(group, {})
    if isinstance(value, bool):
        return value
    return value.get(name, default)


def get_data_source(request: Request) -> Any:
    """Shared FastAPI dependency — injects the configured data source into route handlers."""
    return request.app.state.data_source


OBJECT_TYPE_FIELDS = {"elementId", "displayName", "namespaceUri", "sourceTypeId", "version", "schema", "related"}


def formatObjectType(type_def: Any) -> Any:
    """Filter an ObjectType dict to the spec-defined fields, excluding implementation internals."""
    return {k: v for k, v in type_def.items() if k in OBJECT_TYPE_FIELDS}


def utc_now_iso() -> str:
    """Current UTC time as RFC 3339 with the 'Z' suffix — the Guide forbids the '+00:00' offset form."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


_BASE_QUALITIES = {q.lower(): q for q in ("Good", "GoodNoData", "Bad", "Uncertain")}


def make_vqt(value: Any, quality: Any, timestamp: Any, now: str = None) -> dict:
    """Build a VQT enforcing the Guide's pairing rules: a null value MUST carry
    quality Bad or GoodNoData; Good/Uncertain imply a value is present.

    Quality is an open string: besides Good/GoodNoData/Bad/Uncertain, OPC UA
    StatusCode symbolic names (e.g. Bad_NotConnected, Uncertain_LastUsableValue)
    pass through unchanged. Only the case of the four base names is normalized
    (e.g. "GOOD" -> "Good"); a "Bad_*" quality counts as Bad for the null rule."""
    if isinstance(quality, str):
        quality = _BASE_QUALITIES.get(quality.lower(), quality)
    if value is None:
        is_bad = isinstance(quality, str) and (quality == "Bad" or quality.startswith("Bad_"))
        if not is_bad and quality != "GoodNoData":
            quality = "GoodNoData"
    elif not quality:
        quality = "Good"
    return {"value": value, "quality": quality, "timestamp": timestamp or now or utc_now_iso()}


def success_response(result):
    return {"success": True, "result": result}


_HTTP_TITLES = {
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not Found", 500: "Internal Server Error", 501: "Not Implemented",
}

def error_response(detail, status=500):
    title = _HTTP_TITLES.get(status, "Error")
    return {"success": False, "responseDetail": {"title": title, "status": status, "detail": detail}}


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
        metadata["schemaExtensions"] = extra_attrs

    # Collect vendor/server-defined instance-level properties (RFC 3.1.2 optional metadata)
    # into metadata.system. Values are limited to primitives (string, number, boolean).
    system = {
        k: v for k, v in instance.items()
        if k not in STANDARD_FIELDS and isinstance(v, (str, int, float, bool))
    }
    if system:
        metadata["system"] = system

    return {**base, "metadata": metadata}



def _current_component(child_data: Any, now: str) -> tuple:
    """Convert one data-source child node {data: [VQT], _truncated, grandchildId: {...}}
    to a component VQT, recursing into its own components. Returns (entry, was_truncated)."""
    INTERNAL_KEYS = {"data", "_truncated"}
    if not isinstance(child_data, dict):
        return child_data, False
    was_truncated = bool(child_data.get("_truncated"))
    data_list = child_data.get("data") or [{}]
    vqt = data_list[0] if data_list else {}
    entry = make_vqt(vqt.get("value"), vqt.get("quality"), vqt.get("timestamp"), now)
    grandchildren = {}
    for key in (k for k in child_data if k not in INTERNAL_KEYS):
        sub_entry, sub_trunc = _current_component(child_data[key], now)
        grandchildren[key] = sub_entry
        was_truncated = was_truncated or sub_trunc
    if grandchildren:
        entry["components"] = grandchildren
    return entry, was_truncated


def _history_component(child_data: Any) -> tuple:
    """History counterpart of _current_component: {values: [VQT...], components?}."""
    INTERNAL_KEYS = {"data", "_truncated"}
    if not isinstance(child_data, dict):
        return {"values": []}, False
    was_truncated = bool(child_data.get("_truncated"))
    entry = {
        "values": [
            make_vqt(vqt.get("value"), vqt.get("quality"), vqt.get("timestamp"))
            for vqt in child_data.get("data", [])
        ]
    }
    grandchildren = {}
    for key in (k for k in child_data if k not in INTERNAL_KEYS):
        sub_entry, sub_trunc = _history_component(child_data[key])
        grandchildren[key] = sub_entry
        was_truncated = was_truncated or sub_trunc
    if grandchildren:
        entry["components"] = grandchildren
    return entry, was_truncated


def transform_value_result(element_id: str, ds_result: Any, instance: Any, is_history: bool = False) -> tuple:
    """
    Converts data source {elementId: {data: [VQT...], _truncated: bool, childId: {...}}}
    to the response format described in the Implementation Guide.

    Returns (result, was_truncated) where was_truncated is True if server limits caused
    the result to be incomplete. The caller MUST return HTTP 206 when was_truncated is True.

    For current value (is_history=False):
      Simple:      {value, quality, timestamp}
      Composition: {value, quality, timestamp, components: {childId: {value, quality, timestamp, components?}}}

    For history (is_history=True):
      {values: [{value, quality, timestamp}, ...], components?: {childId: {values: [...], components?}}}

    Components nest for as many levels as maxDepth reached, so no descendant
    the data source returned is dropped (Guide § maxDepth: never truncate silently).
    """
    INTERNAL_KEYS = {"data", "_truncated"}

    if element_id not in ds_result:
        return None, False

    element_data = ds_result[element_id]
    child_keys = [k for k in element_data.keys() if k not in INTERNAL_KEYS]
    was_truncated = element_data.get("_truncated", False)

    is_composition = bool(instance.get("isComposition", False)) if instance else False

    if is_history:
        data_list = element_data.get("data", [])
        result = {
            "isComposition": is_composition,
            "values": [
                make_vqt(vqt.get("value"), vqt.get("quality"), vqt.get("timestamp"))
                for vqt in data_list
            ]
        }
        if child_keys:
            components = {}
            for child_key in child_keys:
                entry, child_trunc = _history_component(element_data[child_key])
                components[child_key] = entry
                was_truncated = was_truncated or child_trunc
            result["components"] = components
        return result, was_truncated
    elif child_keys:
        # Composition with children: parent's own VQT at top level, children under 'components'
        parent_data = element_data.get("data", [{}])
        parent_vqt = parent_data[0] if parent_data else {}
        _now = utc_now_iso()

        components = {}
        for child_key in child_keys:
            entry, child_trunc = _current_component(element_data[child_key], _now)
            components[child_key] = entry
            was_truncated = was_truncated or child_trunc

        return {
            "isComposition": is_composition,
            **make_vqt(parent_vqt.get("value"), parent_vqt.get("quality"), parent_vqt.get("timestamp"), _now),
            "components": components,
        }, was_truncated
    else:
        # Simple leaf element (or composition element where all children were server-truncated)
        data_list = element_data.get("data", [{}])
        vqt = data_list[0] if data_list else {}

        return {
            "isComposition": is_composition,
            **make_vqt(vqt.get("value"), vqt.get("quality"), vqt.get("timestamp")),
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
        **make_vqt(actual_value, quality, timestamp),
    }
