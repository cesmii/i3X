from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, Any, Callable
from datetime import datetime, timezone
import asyncio
import json
import time
import uuid
from pydantic import BaseModel, Field, ConfigDict
from models import (
    CreateSubscriptionRequest,
    RegisterMonitoredItemsRequest,
    StreamRequest, SyncRequest,
    DeleteSubscriptionsRequest,
    ListSubscriptionsRequest,
)
from .utils import getSubscriptionValue, success_response, bulk_response, get_data_source


# Not required, but showing what information is stored for simulated subscriptions
class Subscription(BaseModel):
    clientId: Optional[str] = None
    subscriptionId: str
    displayName: Optional[str] = None
    created: str
    monitoredObjects: List[dict] = []  # Each entry: {"elementId": str, "maxDepth": int}
    pendingUpdates: List[Any] = []  # Queue for updates (max 1000, FIFO). Each item: {sequenceNumber, elementId, value, quality, timestamp}
    max_queue_size: int = 1000
    nextSequence: int = 1           # Sequence number for the next queued update
    lastAckedSequence: int = 0      # Highest sequence number acknowledged by the client
    ttl_seconds: int = 300          # Idle TTL: subscription auto-deleted if no /sync or active stream within this window
    last_activity: str = ""         # ISO timestamp of last /sync, /ack, or stream open
    is_streaming: bool = False  # True when SSE connection is active
    # Exclude these fields from JSON serialization/schema
    handler: Callable[[Any], None] | None = Field(exclude=True, default=None)
    event_loop: Any | None = Field(exclude=True, default=None)
    streaming_response: StreamingResponse | None = Field(exclude=True, default=None)
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )  # Needed to allow for StreamingResponse in the model


subs = APIRouter(prefix="", tags=["Subscribe"])


def _find_sub(request: Request, subscription_id: str, client_id: Optional[str] = None) -> Optional[Subscription]:
    """Locate a subscription by ID, optionally validating clientId scoping."""
    return next(
        (
            s for s in request.app.state.I3X_DATA_SUBSCRIPTIONS
            if s.subscriptionId == subscription_id
            and (client_id is None or s.clientId is None or s.clientId == client_id)
        ),
        None,
    )


# RFC 4.2.3.1 - Create Subscription
@subs.post(
    "/subscriptions",
    summary="Create Subscription",
    operation_id="createSubscription",
)
def create_subscription(request: Request, subscription: CreateSubscriptionRequest):
    """Create a new subscription. Returns a unique subscriptionId the client must cache.
    There is no way to list all subscriptions; the client must track the returned ID."""

    subscription_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ttl = getattr(request.app.state, "subscription_ttl_seconds", 300)
    new_sub = Subscription(
        clientId=subscription.clientId,
        subscriptionId=subscription_id,
        displayName=subscription.displayName,
        created=now,
        last_activity=now,
        ttl_seconds=ttl,
    )
    request.app.state.I3X_DATA_SUBSCRIPTIONS.append(new_sub)

    return success_response({"clientId": subscription.clientId, "subscriptionId": subscription_id, "displayName": subscription.displayName})



# RFC 4.2.3.2 - Register Monitored Items
@subs.post(
    "/subscriptions/register",
    summary="Register Monitored Items",
    operation_id="registerMonitoredItems",
)
def register_objects(request: Request, req: RegisterMonitoredItemsRequest):
    """Add objects to the subscription. subscriptionId is passed in the request body."""
    sub = _find_sub(request, req.subscriptionId, req.clientId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    data_source = request.app.state.data_source
    results = []

    for eid in req.elementIds:
        if not data_source.get_instance_by_id(eid):
            results.append({"success": False, "elementId": eid, "error": {"code": 404, "message": f"Element not found: {eid}"}})
            continue
        tree = collect_instance_tree(eid, req.maxDepth, 0, data_source.get_all_instances())
        for item in tree:
            item_id = item["elementId"]
            if not any(m["elementId"] == item_id for m in sub.monitoredObjects):
                sub.monitoredObjects.append({"elementId": item_id, "maxDepth": req.maxDepth})
        results.append({"success": True, "elementId": eid, "result": None})

    return bulk_response(results)


# RFC 4.2.3.2 - Unregister Monitored Items
@subs.post(
    "/subscriptions/unregister",
    summary="Remove Monitored Items",
    operation_id="removeMonitoredItems",
)
def unregister_objects(request: Request, req: RegisterMonitoredItemsRequest):
    """Remove objects from the subscription. subscriptionId is passed in the request body."""
    sub = _find_sub(request, req.subscriptionId, req.clientId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    data_source = request.app.state.data_source
    results = []

    for eid in req.elementIds:
        if not data_source.get_instance_by_id(eid):
            results.append({"success": False, "elementId": eid, "error": {"code": 404, "message": f"Element not found: {eid}"}})
            continue
        tree = collect_instance_tree(eid, req.maxDepth, 0, data_source.get_all_instances())
        for item in tree:
            item_id = item["elementId"]
            sub.monitoredObjects = [m for m in sub.monitoredObjects if m["elementId"] != item_id]
        results.append({"success": True, "elementId": eid, "result": None})

    return bulk_response(results)


# POST /subscriptions/stream - Open SSE stream
@subs.post(
    "/subscriptions/stream",
    summary="Stream Values (SSE)",
    operation_id="streamSubscription",
)
async def stream_subscription(request: Request, req: StreamRequest):
    """Open a Server-Sent Events (SSE) stream. subscriptionId is passed in the request body."""
    sub = _find_sub(request, req.subscriptionId, req.clientId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # If handler and streaming_response already exist, reuse them
    if sub.handler is not None and sub.streaming_response is not None:
        return sub.streaming_response

    # Otherwise create queue, loop, handler, and streaming response once
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    async def event_stream():
        try:
            while True:
                update = await queue.get()
                yield f"data: {json.dumps([update])}\n\n"
        except Exception as e:
            print(f"[SSE] Stream ended: {e}")
        finally:
            # When stream disconnects, switch back to queue mode
            sub.is_streaming = False
            sub.handler = None
            sub.event_loop = None
            sub.streaming_response = None
            print(f"[SSE] Subscription {req.subscriptionId} switched back to queue mode")

    def push_update_to_client(update):
        asyncio.run_coroutine_threadsafe(queue.put(update), loop)

    # Switch to streaming mode
    sub.last_activity = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sub.is_streaming = True
    sub.handler = push_update_to_client
    sub.event_loop = loop
    sub.streaming_response = StreamingResponse(
        event_stream(), media_type="text/event-stream"
    )

    # Clear the queue when switching to streaming (per requirements)
    sub.pendingUpdates.clear()

    return sub.streaming_response


# RFC 4.2.3.3 - Sync
@subs.post(
    "/subscriptions/sync",
    summary="Sync Values",
    operation_id="syncSubscription",
)
def sync_subscription(request: Request, req: SyncRequest):
    """Acknowledge previously received updates and return all pending updates in one call.

    If `lastSequenceNumber` is provided, all queued updates with sequenceNumber <= lastSequenceNumber are removed first,
    then the remaining (newer) updates are returned. subscriptionId is passed in the request body.
    """
    sub = _find_sub(request, req.subscriptionId, req.clientId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if req.lastSequenceNumber is not None:
        sub.pendingUpdates = [u for u in sub.pendingUpdates if u.get("sequenceNumber", 0) > req.lastSequenceNumber]
        sub.lastAckedSequence = max(sub.lastAckedSequence, req.lastSequenceNumber)

    sub.last_activity = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return success_response(list(sub.pendingUpdates))


# POST /subscriptions/delete - Delete one or more subscriptions
@subs.post(
    "/subscriptions/delete",
    summary="Delete Subscriptions",
    operation_id="deleteSubscriptions",
)
def delete_subscriptions(request: Request, req: DeleteSubscriptionsRequest):
    """Delete one or more subscriptions by ID. subscriptionIds are passed in the request body."""
    results = []

    for sub_id in req.subscriptionIds:
        index = next(
            (
                i
                for i, s in enumerate(request.app.state.I3X_DATA_SUBSCRIPTIONS)
                if s.subscriptionId == sub_id
                and (req.clientId is None or s.clientId is None or s.clientId == req.clientId)
            ),
            None,
        )
        if index is not None:
            request.app.state.I3X_DATA_SUBSCRIPTIONS.pop(index)
            results.append({"success": True, "subscriptionId": sub_id, "result": None})
        else:
            results.append({"success": False, "subscriptionId": sub_id, "error": {"code": 404, "message": f"Subscription not found: {sub_id}"}})

    return bulk_response(results)


# POST /subscriptions/list - Get one or more subscriptions by ID
@subs.post(
    "/subscriptions/list",
    summary="List Subscriptions",
    operation_id="listSubscriptions",
)
def list_subscriptions(request: Request, req: ListSubscriptionsRequest):
    """Get one or more subscriptions by ID to check their existence and current configuration."""
    results = []

    for sub_id in req.subscriptionIds:
        sub = _find_sub(request, sub_id, req.clientId)
        if sub:
            results.append({
                "success": True,
                "subscriptionId": sub_id,
                "result": {
                    "subscriptionId": sub.subscriptionId,
                    "displayName": sub.displayName,
                    "monitoredObjects": sub.monitoredObjects,
                },
            })
        else:
            results.append({"success": False, "subscriptionId": sub_id, "error": {"code": 404, "message": f"Subscription not found: {sub_id}"}})

    return bulk_response(results)


# Subscription thread responsible for creating updates for items being monitored.
# If SSE is active (is_streaming=True), stream updates via handler (streaming mode)
# Otherwise, queue updates for retrieval via /sync (sync mode, max 1000, FIFO)
def handle_data_source_update(instance, value, I3X_DATA_SUBSCRIPTIONS, data_source):
    """Route updates from data sources to active subscriptions"""
    try:
        # Iterate through all active subscriptions
        for sub in I3X_DATA_SUBSCRIPTIONS:
            if not sub.monitoredObjects:
                continue

            # Check if this update is for a monitored element
            element_id = instance.get("elementId")
            monitored = next((m for m in sub.monitoredObjects if m["elementId"] == element_id), None)
            if element_id and monitored:

                if sub.is_streaming and sub.handler:
                    # Stream mode: immediate delivery via SSE handler
                    updateValue = getSubscriptionValue(instance, value, maxDepth=monitored["maxDepth"], data_source=data_source)
                    try:
                        sub.handler(updateValue)
                    except Exception as e:
                        print(f"[SSE] Handler error: {e}")
                        # On error, switch back to queue mode
                        sub.is_streaming = False
                        sub.handler = None
                else:
                    # Queue mode: store for later /sync retrieval
                    update_value = getSubscriptionValue(instance, value, maxDepth=monitored["maxDepth"], data_source=data_source)
                    queued_item = {
                        "sequenceNumber": sub.nextSequence,
                        **update_value,
                    }
                    sub.nextSequence += 1
                    # Enforce FIFO with max queue size
                    if len(sub.pendingUpdates) >= sub.max_queue_size:
                        sub.pendingUpdates.pop(0)
                    sub.pendingUpdates.append(queued_item)
    except Exception as e:
        import traceback
        print(f"Error routing data source update: {e}\n{traceback.format_exc()}")


def subscription_worker(I3X_DATA_SUBSCRIPTIONS, running_flag):
    """Subscription worker thread - handles TTL cleanup of abandoned subscriptions"""
    TTL_CHECK_INTERVAL = 60  # seconds between cleanup passes
    elapsed = 0
    while running_flag["running"]:
        time.sleep(1)
        elapsed += 1
        if elapsed < TTL_CHECK_INTERVAL:
            continue
        elapsed = 0

        now = datetime.now(timezone.utc)
        expired = [
            s for s in I3X_DATA_SUBSCRIPTIONS
            if not s.is_streaming and s.last_activity and
            (now - datetime.fromisoformat(s.last_activity)).total_seconds() > s.ttl_seconds
        ]
        for sub in expired:
            I3X_DATA_SUBSCRIPTIONS.remove(sub)
            print(f"[TTL] Subscription {sub.subscriptionId} expired and was deleted")


# Recursively collect an instance tree starting from root_id
## TODO this should probably be a utility used by exploratory/browse as well?
def collect_instance_tree(
    root_id: str, max_depth: int = 0, depth: int = 0, instances=[]
):
    collected = []
    for inst in instances:
        if inst["elementId"] == root_id:
            collected.append(inst)
            if inst.get("isComposition") and (max_depth == 0 or depth < max_depth):
                children = [i for i in instances if i.get("parentId") == root_id]
                for child in children:
                    collected.extend(
                        collect_instance_tree(
                            child["elementId"], max_depth, depth + 1, instances
                        )
                    )
    return collected
