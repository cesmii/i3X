from fastapi import APIRouter, Path, Query, HTTPException, Request, Body, Depends
from typing import Optional, Any
from urllib.parse import unquote
from models import (
    ObjectInstanceMinimal,
    ObjectInstance,
    GetObjectsRequest,
    GetRelatedObjectsRequest,
    GetObjectValueRequest,
    GetObjectHistoryRequest,
)
from data_sources.data_interface import I3XDataSource
from .utils import getObject, success_response, error_response, bulk_response, transform_value_result

explore = APIRouter(prefix="", tags=["Explore"])
query = APIRouter(prefix="", tags=["Query"])
update = APIRouter(prefix="", tags=["Update"])


def get_data_source(request: Request) -> I3XDataSource:
    """Dependency to inject data source"""
    return request.app.state.data_source


# RFC 4.1.5 - Instances of an Object Type
@explore.get("/objects", summary="Get Objects", operation_id="getObjects")
def get_objects(
    typeId: Optional[str] = Query(default=None),
    includeMetadata: bool = Query(default=False),
    data_source: I3XDataSource = Depends(get_data_source),
):
    """Return all Objects. Optionally filter by TypeId"""
    instances = [getObject(i, includeMetadata) for i in data_source.get_instances(typeId)]
    return success_response(instances)


# RFC 4.1.5 - Query Objects by ElementId
@explore.post("/objects/list", summary="List Objects by ElementId", operation_id="listObjectsById")
def query_objects_by_id(
    request_body: GetObjectsRequest,
    data_source: I3XDataSource = Depends(get_data_source),
):
    """
    Return one or more Objects by elementId.

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    succeeded = []
    failed = []

    for eid in element_ids:
        instance = data_source.get_instance_by_id(eid)
        if instance:
            succeeded.append({"elementId": eid, "result": getObject(instance, request_body.includeMetadata)})
        else:
            failed.append({"elementId": eid, "error": {"message": f"Element not found: {eid}"}})

    return bulk_response(succeeded, failed)


# RFC 4.1.6 - Objects linked by Relationship Type
@explore.post("/objects/related", summary="Query Related Objects", operation_id="queryRelatedObjects")
def query_related_objects(
    request_body: GetRelatedObjectsRequest,
    data_source: I3XDataSource = Depends(get_data_source),
):
    """
    Return related objects for one or more elementIds.

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    succeeded = []
    failed = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            related_objects = data_source.get_related_instances(
                eid_decoded,
                request_body.relationshipType
            )
            result = []
            for obj in related_objects:
                obj_data = getObject(obj, request_body.includeMetadata)
                # Always include relationship fields to support graph traversal
                for field in ("relationships", "sourceRelationship"):
                    if field in obj:
                        obj_data[field] = obj[field]
                result.append(obj_data)
            succeeded.append({"elementId": eid_decoded, "result": result})
        else:
            failed.append({"elementId": eid_decoded, "error": {"message": f"Element not found: {eid_decoded}"}})

    return bulk_response(succeeded, failed)


# RFC 4.2.1.1 - Object Element LastKnown Value
@query.post("/objects/value", summary="Query Last Known Values", operation_id="queryLastKnownValues")
def query_last_known_values(
    request_body: GetObjectValueRequest,
    data_source: I3XDataSource = Depends(get_data_source),
):
    """
    Return last known value for one or more Objects.

    If maxDepth=0, recursively includes all values from HasComponent children (infinite depth).
    Otherwise, recurses only to the specified depth (1=no recursion, just this element).

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    succeeded = []
    failed = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            value = data_source.get_instance_values_by_id(
                eid_decoded,
                maxDepth=request_body.maxDepth,
                returnHistory=False
            )
            if value:
                transformed = transform_value_result(eid_decoded, value, instance, is_history=False)
                succeeded.append({"elementId": eid_decoded, "result": transformed})
            else:
                failed.append({"elementId": eid_decoded, "error": {"message": "No value available"}})
        else:
            failed.append({"elementId": eid_decoded, "error": {"message": f"Element not found: {eid_decoded}"}})

    return bulk_response(succeeded, failed)


# RFC 4.2.1.2 - Object Element HistoricalValue
@query.post("/objects/history", summary="Query Historical Values", operation_id="queryHistoricalValues")
def query_historical_values(
    request_body: GetObjectHistoryRequest,
    data_source: I3XDataSource = Depends(get_data_source),
):
    """
    Get the historical values for one or more Objects.

    If maxDepth=0, recursively includes all values from HasComponent children (infinite depth).
    Otherwise, recurses only to the specified depth (1=no recursion, just this element).

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    succeeded = []
    failed = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        instance = data_source.get_instance_by_id(eid_decoded)
        if instance:
            historical_values = data_source.get_instance_values_by_id(
                eid_decoded,
                request_body.startTime,
                request_body.endTime,
                request_body.maxDepth,
                returnHistory=True
            )
            if historical_values:
                transformed = transform_value_result(eid_decoded, historical_values, instance, is_history=True)
                succeeded.append({"elementId": eid_decoded, "result": transformed})
            else:
                failed.append({"elementId": eid_decoded, "error": {"message": "No historical data available"}})
        else:
            failed.append({"elementId": eid_decoded, "error": {"message": f"Element not found: {eid_decoded}"}})

    return bulk_response(succeeded, failed)


# RFC 4.2.2.1 - Object Element LastKnownValue update
@update.put(
    "/objects/{elementId}/value",
    summary="Update Value of Object",
    operation_id="updateObjectValue",
)
def update_object(
    elementId: str = Path(...),
    body: Any = Body(...),
    data_source: I3XDataSource = Depends(get_data_source),
):
    """Update the value of an Object"""
    try:
        data_source.update_instance_value(elementId, body)
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
    data_source: I3XDataSource = Depends(get_data_source),
):
    """Update the historical values for one or more Objects"""
    raise HTTPException(status_code=501, detail="Operation not implemented")
