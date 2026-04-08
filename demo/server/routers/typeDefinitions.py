from fastapi import APIRouter, Query, Depends
from typing import Optional
from urllib.parse import unquote
from models import GetObjectTypesRequest, GetRelationshipTypesRequest
from .utils import success_response, bulk_response, get_data_source, formatObjectType

typeDefinitions = APIRouter(prefix="", tags=["Explore"])


# RFC 4.1.3 - Object Types
@typeDefinitions.get("/objecttypes", summary="Get Object Types", operation_id="getObjectTypes")
def get_object_types(
    namespaceUri: Optional[str] = Query(default=None),
    data_source=Depends(get_data_source),
):
    """Get the schemas for all Types. Optionally filter by Namespace"""
    return success_response([formatObjectType(t) for t in data_source.get_object_types(namespaceUri)])


# RFC 4.1.2 - Object Type Definition
@typeDefinitions.post(
    "/objecttypes/query",
    summary="Query Object Types by ElementId",
    operation_id="queryObjectTypesById",
)
def query_object_types_by_id(
    request_body: GetObjectTypesRequest,
    data_source=Depends(get_data_source),
):
    """
    Get the schema for one or more Types by ElementID.

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    results = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        obj_type = data_source.get_object_type_by_id(eid_decoded)
        if obj_type:
            results.append({"success": True, "elementId": eid_decoded, "result": formatObjectType(obj_type)})
        else:
            results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": f"Object type not found: {eid_decoded}"}})

    return bulk_response(results)


# RFC 4.1.4 - Relationship Types
@typeDefinitions.get("/relationshiptypes", summary="Get Relationship Types", operation_id="getRelationshipTypes")
def get_relationship_types(
    namespaceUri: Optional[str] = Query(default=None),
    data_source=Depends(get_data_source),
):
    """Get all Relationship Types. Optionally filtered by Namespace"""
    return success_response(data_source.get_relationship_types(namespaceUri))


# RFC 4.1.4 - Relationship Type
@typeDefinitions.post(
    "/relationshiptypes/query",
    summary="Query Relationship Types by ElementId",
    operation_id="queryRelationshipTypesById",
)
def query_relationship_types_by_id(
    request_body: GetRelationshipTypesRequest,
    data_source=Depends(get_data_source),
):
    """
    Get one or more Relationship Types by ElementID.

    Request body: {"elementIds": ["...", "..."]}

    Returns bulk response with succeeded/failed.
    """
    element_ids = request_body.get_element_ids()
    results = []

    for eid in element_ids:
        eid_decoded = unquote(eid)
        rel_type = data_source.get_relationship_type_by_id(eid_decoded)
        if rel_type:
            results.append({"success": True, "elementId": eid_decoded, "result": rel_type})
        else:
            results.append({"success": False, "elementId": eid_decoded, "error": {"code": 404, "message": f"Relationship type not found: {eid_decoded}"}})

    return bulk_response(results)
