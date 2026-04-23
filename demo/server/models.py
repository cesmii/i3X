from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict, Any, Union, Callable, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar('T')


# RFC 4.1.1 - Namespace Model
class Namespace(BaseModel):
    uri: str = Field(..., description="Namespace URI")
    displayName: str = Field(..., description="Namespace name")


# RFC 4.1.2/4.1.3 - Object Type Model
class ObjectType(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    elementId: str = Field(..., description="Unique string identifier for the type")
    displayName: str = Field(..., description="Type name")
    namespaceUri: str = Field(..., description="Namespace URI")
    version: Optional[str] = Field(None, description="Optional type version in Semantic Versioning format (e.g. '1.0.0')")
    type_schema: Dict[str, Any] = Field(
        ..., alias="schema", description="JSON Schema definition for this object type"
    )


# RFC 4.1.4/4.1.5 - Relationship Type Model
class RelationshipTypeDirection(BaseModel):
    Subject: str = Field(..., description="Subject relationship name")
    Target: str = Field(..., description="Target relationship name")
    Cardinality: str = Field(..., description="Cardinality of the relationship")


class RelationshipType(BaseModel):
    elementId: str = Field(
        ..., description="Unique string identifier for the relationship type"
    )
    displayName: str = Field(..., description="Relationship type name")
    namespaceUri: str = Field(..., description="Namespace URI")
    relationshipId: str = Field(..., description="Class or member of the Namespace that defines this relationship type")
    reverseOf: str = Field(..., description="ElementId of the reverse relationship type")


# RFC 3.1.1 - Required Object Metadata (Minimal Instance)
class ObjectInstanceMinimal(BaseModel):
    elementId: str = Field(..., description="Unique string identifier for the element")
    displayName: str = Field(..., description="Object name")
    typeElementId: str = Field(..., description="ElementId of the object type")
    parentId: Optional[str] = Field(None, description="ElementId of the parent object")
    isComposition: bool = Field(
        ..., description="Boolean indicating if element has child objects"
    )
    namespaceUri: str = Field(..., description="Namespace URI")


class ObjectLinkedByRelationshipType(BaseModel):
    subject: Optional[str] = Field(None, description="")
    sourceRelationship: Optional[str] = Field(
        None, description="Relationship type traversed from the queried element to reach this instance"
    )
    elementId: str = Field(..., description="Unique string identifier for the element")
    displayName: str = Field(..., description="Object name")
    typeElementId: str = Field(..., description="ElementId of the object type")
    parentId: Optional[str] = Field(None, description="ElementId of the parent object")
    isComposition: bool = Field(
        ..., description="Boolean indicating if element has child objects"
    )
    namespaceUri: str = Field(..., description="Namespace URI")


# RFC 3.1.1 + 3.1.2 - Full Object Instance with Attributes
class ObjectInstance(ObjectInstanceMinimal):
    relationships: Optional[Dict[str, Any]] = Field(
        None, description="Relationships to other objects"
    )


# RFC 4.2.1.1 - Last Known Value Response
class LastKnownValue(BaseModel):
    elementId: str = Field(..., description="Unique string identifier for the element")
    value: Dict[str, Any] = Field(..., description="Current attribute values")
    parentId: Optional[str] = Field(None, description="ElementId of the parent object")
    namespaceUri: str = Field(..., description="Namespace URI")
    dataType: Optional[str] = Field(
        None, description="Data type (when includeMetadata=true)"
    )
    timestamp: Optional[str] = Field(
        None, description="ISO 8601 timestamp (when includeMetadata=true)"
    )


# RFC 4.2.1.2 - Historical Value Response
class HistoricalValue(BaseModel):
    elementId: str = Field(..., description="Unique string identifier for the element")
    value: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ...,
        description="Historical attribute values (can be a dict or array of objects)",
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp when data was recorded")
    parentId: Optional[str] = Field(None, description="ElementId of the parent object")
    namespaceUri: str = Field(..., description="Namespace URI")
    dataType: Optional[str] = Field(
        None, description="Data type (when includeMetadata=true)"
    )


# RFC 4.2.2.1 - Object Element LastKnownValue
class UpdateRequest(BaseModel):
    elementIds: List[str]
    values: List[Any]


# TODO: the RFC doesn't say what this should be
class UpdateResult(BaseModel):
    elementId: str
    success: bool
    message: str


# 4.2.2.2 Object Element HistoricalValue
class HistoricalValueUpdate(BaseModel):
    elementId: str
    timestamp: str  # ISO8601 string
    value: Any


class HistoricalUpdateResult(BaseModel):
    elementId: str
    timestamp: str
    success: bool
    message: str


class CreateSubscriptionRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="Unique identifier for the client scoping this subscription")
    displayName: Optional[str] = Field(None, description="Optional friendly name for the subscription")


class CreateSubscriptionResponse(BaseModel):
    clientId: Optional[str] = None
    subscriptionId: str
    displayName: Optional[str] = None


class RegisterMonitoredItemsRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="The clientId scoping this subscription")
    subscriptionId: str = Field(..., description="The subscription to register items with")
    elementIds: List[str]
    maxDepth: Optional[int] = 1  # 0 means infinite recursion, 1 means no recursion, >1 recurses to that depth


class StreamRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="The clientId scoping this subscription")
    subscriptionId: str = Field(..., description="The subscription to open a stream for")


class SyncRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="The clientId scoping this subscription")
    subscriptionId: str = Field(..., description="The subscription to sync")
    lastSequenceNumber: Optional[int] = Field(None, description="Acknowledge all updates through this sequence number before returning new ones")


class DeleteSubscriptionsRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="The clientId scoping these subscriptions")
    subscriptionIds: List[str] = Field(..., description="List of subscription IDs to delete")


class ListSubscriptionsRequest(BaseModel):
    clientId: Optional[str] = Field(None, description="The clientId scoping these subscriptions")
    subscriptionIds: List[str] = Field(..., description="List of subscription IDs to retrieve")


# Request models for POST endpoints (GET to POST refactor)

class ElementIdRequest(BaseModel):
    """Base request model that accepts an array of elementIds"""
    elementIds: List[str] = Field(..., description="Array of element IDs to query")

    @model_validator(mode='after')
    def validate_element_ids(self):
        """Ensure at least one elementId is provided"""
        if not self.elementIds:
            raise ValueError("'elementIds' must contain at least one element")
        return self

    def get_element_ids(self) -> List[str]:
        """Helper to get the list of element IDs"""
        return self.elementIds


class GetObjectsRequest(ElementIdRequest):
    """Request model for POST /objects/query"""
    includeMetadata: bool = Field(default=False, description="Include full metadata in response")


class GetRelatedObjectsRequest(ElementIdRequest):
    """Request model for POST /objects/related"""
    relationshipType: Optional[str] = Field(default=None, description="Filter by relationship type")
    includeMetadata: bool = Field(default=False, description="Include full metadata in response")


class GetObjectValueRequest(ElementIdRequest):
    """Request model for POST /objects/value"""
    maxDepth: int = Field(default=1, ge=0, description="Controls recursion depth. 0=infinite, 1=no recursion")


class GetObjectHistoryRequest(ElementIdRequest):
    """Request model for POST /objects/history"""
    startTime: Optional[str] = Field(default=None, description="ISO 8601 start time for filtering")
    endTime: Optional[str] = Field(default=None, description="ISO 8601 end time for filtering")
    maxDepth: int = Field(default=1, ge=0, description="Controls recursion depth. 0=infinite, 1=no recursion")


class GetObjectTypesRequest(ElementIdRequest):
    """Request model for POST /objecttypes/query"""
    pass


class GetRelationshipTypesRequest(ElementIdRequest):
    """Request model for POST /relationshiptypes/query"""
    pass


# --- Generic response wrappers ---

class ErrorDetail(BaseModel):
    title: str
    status: int
    detail: str


class ErrorResponse(BaseModel):
    success: bool = False
    problemDetail: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    result: Optional[T] = None


class BulkResultItem(BaseModel, Generic[T]):
    success: bool
    elementId: Optional[str] = None
    subscriptionId: Optional[str] = None
    result: Optional[T] = None
    problemDetail: Optional[ErrorDetail] = None


class BulkResponse(BaseModel, Generic[T]):
    success: bool
    results: List[BulkResultItem[T]]


# --- Endpoint-specific result models ---

class ObjectTypeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    elementId: str
    displayName: str
    namespaceUri: str
    sourceTypeId: str = Field(..., description="Class or member of the Namespace that defines this type")
    version: Optional[str] = None
    type_schema: Dict[str, Any] = Field(..., alias="schema", description="JSON Schema definition for this object type")
    related: Optional[Dict[str, Any]] = None


class ObjectInstanceMetadata(BaseModel):
    typeNamespaceUri: Optional[str] = None
    sourceTypeId: Optional[str] = None
    description: Optional[str] = None
    relationships: Optional[Dict[str, Any]] = None
    extendedAttributes: Optional[Dict[str, Any]] = None
    system: Optional[Dict[str, Any]] = None


class ObjectInstanceResponse(BaseModel):
    elementId: str
    displayName: str
    typeElementId: str
    parentId: Optional[str] = None
    isComposition: bool
    isExtended: bool = False
    metadata: Optional[ObjectInstanceMetadata] = None


class RelatedObjectResult(BaseModel):
    sourceRelationship: str
    object: ObjectInstanceResponse


class VQT(BaseModel):
    value: Any
    quality: str = Field(..., description="Data quality indicator: Good, GoodNoData, Bad, or Uncertain")
    timestamp: str = Field(..., description="RFC 3339 UTC timestamp when this value was recorded")


class CurrentValueResult(BaseModel):
    isComposition: bool = Field(..., description="True if this Object encapsulates composed child elements")
    value: Any
    quality: str = Field(..., description="Data quality indicator: Good, GoodNoData, Bad, or Uncertain")
    timestamp: str = Field(..., description="RFC 3339 UTC timestamp when this value was recorded")
    components: Optional[Dict[str, VQT]] = Field(None, description="Child element values, present only on composition elements when maxDepth > 1")


class HistoricalValueResult(BaseModel):
    isComposition: bool = Field(..., description="True if this Object encapsulates composed child elements")
    values: List[VQT] = Field(..., description="Ordered array of VQT objects for the requested time range")


class SyncUpdate(BaseModel):
    model_config = ConfigDict(extra='allow')
    sequenceNumber: int
    elementId: str
    value: Any
    quality: str = Field(..., description="Data quality indicator: Good, GoodNoData, Bad, or Uncertain")
    timestamp: str = Field(..., description="RFC 3339 UTC timestamp when this value was recorded")


class SubscriptionDetail(BaseModel):
    subscriptionId: str
    displayName: Optional[str] = None
    monitoredObjects: List[Dict[str, Any]]


class _QueryCapabilities(BaseModel):
    history: bool


class _UpdateCapabilities(BaseModel):
    current: bool
    history: bool


class _SubscribeCapabilities(BaseModel):
    stream: bool


class ServerCapabilities(BaseModel):
    query: _QueryCapabilities
    update: _UpdateCapabilities
    subscribe: _SubscribeCapabilities


class ServerInfo(BaseModel):
    specVersion: str
    serverVersion: Optional[str] = None
    serverName: Optional[str] = None
    capabilities: ServerCapabilities
