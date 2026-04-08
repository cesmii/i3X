from fastapi import APIRouter, Path, Query, HTTPException, Body, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Any
from urllib.parse import unquote
from models import (
    GetObjectsRequest,
    GetRelatedObjectsRequest,
    GetObjectValueRequest,
    GetObjectHistoryRequest,
)
from .utils import getObject, success_response, error_response, bulk_response, transform_value_result, get_data_source

explore = APIRouter(prefix="", tags=["Explore"])
query = APIRouter(prefix="", tags=["Query"])
update = APIRouter(prefix="", tags=["Update"])


# RFC 4.1.5 - Instances of an Object Type
@explore.get("/objects", summary="Get Objects", operation_id="getObjects")
def get_objects(
    typeElementId: Optional[str] = Query(default=None),
    includeMetadata: bool = Query(default=False),
    root: Optional[bool] = Query(default=None),
    data_source=Depends(get_data_source),
):
    """Return all Objects. Optionally filter by typeElementId or set root=true to get root Objects."""
    result = []
    for i in data_source.get_instances(typeElementId, root=bool(root)):
        type_info = data_source.get_object_type_by_id(i["typeElementId"]) if includeMetadata and i.get("typeElementId") else None
        extra_attrs = data_source.get_instance_extra_attributes(i["elementId"])
        result.append(getObject(i, includeMetadata, type_info, extra_attrs))
    return success_response(result)


# RFC 4.1.5 - Query Objects by ElementId
@explore.post("/objects/list", summary="List Objects by ElementId", operation_id="listObjectsById")
def query_objects_by_id(
    request_body: GetObjectsRequest,
    data_source=Depends(get_data_source),
):
    """
    Return one or more Objects by elementId.

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    results = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            type_info = data_source.get_object_type_by_id(instance["typeElementId"]) if request_body.includeMetadata and instance.get("typeElementId") else None
            extra_attrs = data_source.get_instance_extra_attributes(eid_decoded)
            results.append({"success": True, "elementId": eid_decoded, "result": getObject(instance, request_body.includeMetadata, type_info, extra_attrs)})
        else:
            results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": f"Element not found: {eid_decoded}"}})

    return bulk_response(results)


# RFC 4.1.6 - Objects linked by Relationship Type
@explore.post("/objects/related", summary="Query Related Objects", operation_id="queryRelatedObjects")
def query_related_objects(
    request_body: GetRelatedObjectsRequest,
    data_source=Depends(get_data_source),
):
    """
    Return related objects for one or more elementIds.

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    results = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            related_objects = data_source.get_related_instances(
                eid_decoded,
                request_body.relationshipType
            )
            related_result = []
            for obj in related_objects:
                type_info = data_source.get_object_type_by_id(obj["typeElementId"]) if request_body.includeMetadata and obj.get("typeElementId") else None
                extra_attrs = data_source.get_instance_extra_attributes(obj["elementId"])
                formatted = getObject(obj, request_body.includeMetadata, type_info, extra_attrs)
                related_result.append({
                    "sourceRelationship": obj.get("sourceRelationship", ""),
                    "object": formatted,
                })
            results.append({"success": True, "elementId": eid_decoded, "result": related_result})
        else:
            results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": f"Element not found: {eid_decoded}"}})

    return bulk_response(results)


# RFC 4.2.1.1 - Object Element LastKnown Value
@query.post("/objects/value", summary="Query Last Known Values", operation_id="queryLastKnownValues")
def query_last_known_values(
    request_body: GetObjectValueRequest,
    data_source=Depends(get_data_source),
):
    """
    Return last known value for one or more Objects.

    If maxDepth=0, recursively includes all values from HasComponent children (infinite depth).
    Otherwise, recurses only to the specified depth (1=no recursion, just this element).

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    results = []
    any_truncated = False

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            value = data_source.get_instance_values_by_id(
                eid_decoded,
                maxDepth=request_body.maxDepth,
                returnHistory=False,
            )
            if value:
                transformed, was_truncated = transform_value_result(eid_decoded, value, instance, is_history=False)
                if was_truncated:
                    any_truncated = True
                results.append({"success": True, "elementId": eid_decoded, "result": transformed})
            else:
                results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": "No value available"}})
        else:
            results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": f"Element not found: {eid_decoded}"}})

    response_body = bulk_response(results)
    if any_truncated:
        return JSONResponse(content=response_body, status_code=206)
    return response_body


# RFC 4.2.1.2 - Object Element HistoricalValue
@query.post("/objects/history", summary="Query Historical Values", operation_id="queryHistoricalValues")
def query_historical_values(
    request_body: GetObjectHistoryRequest,
    data_source=Depends(get_data_source),
):
    """
    Get the historical values for one or more Objects.

    If maxDepth=0, recursively includes all values from HasComponent children (infinite depth).
    Otherwise, recurses only to the specified depth (1=no recursion, just this element).

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    results = []
    any_truncated = False

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            historical_values = data_source.get_instance_values_by_id(
                eid_decoded,
                request_body.startTime,
                request_body.endTime,
                request_body.maxDepth,
                returnHistory=True,
            )
            if historical_values:
                transformed, was_truncated = transform_value_result(eid_decoded, historical_values, instance, is_history=True)
                if was_truncated:
                    any_truncated = True
                results.append({"success": True, "elementId": eid_decoded, "result": transformed})
            else:
                results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": "No historical data available"}})
        else:
            results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": f"Element not found: {eid_decoded}"}})

    response_body = bulk_response(results)
    if any_truncated:
        return JSONResponse(content=response_body, status_code=206)
    return response_body


# RFC 4.2.2.1 - Object Element LastKnownValue update
@update.put(
    "/objects/{elementId}/value",
    summary="Update Value of Object",
    operation_id="updateObjectValue",
)
def update_object(
    elementId: str = Path(...),
    body: Any = Body(...),
    data_source=Depends(get_data_source),
):
    """Update the value of an Object"""
    if not data_source.get_instance_by_id(elementId):
        raise HTTPException(status_code=404, detail=f"Element not found: {elementId}")
    try:
        # Unwrap VQT body: {value, quality, timestamp} -> extract inner value
        if isinstance(body, dict) and "value" in body:
            value = body["value"]
        else:
            value = body
        data_source.update_instance_value(elementId, value)
        return success_response(None)
    except Exception as e:
        return error_response(str(e))


# RFC 4.2.2.2 - Object Element HistoricalValue
@update.put(
    "/objects/{elementId}/history",
    summary="Update Historical Values of Object",
    operation_id="updateObjectHistory",
)
def update_object_history(
    elementId: str = Path(...),
    data_source=Depends(get_data_source),
):
    """Update the historical values for one or more Objects"""
    raise HTTPException(status_code=501, detail="Operation not implemented")
