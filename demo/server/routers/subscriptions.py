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
    CreateSubscriptionRequest, CreateSubscriptionResponse,
    ListSubscriptionsRequest, SubscriptionDetail,
    RegisterMonitoredItemsRequest,
    StreamRequest, SyncRequest,
    DeleteSubscriptionsRequest,
)
from data_sources.data_interface import I3XDataSource
from .utils import getSubscriptionValue


# Not required, but showing what information is stored for simulated subscriptions
class Subscription(BaseModel):
    subscriptionId: str
    displayName: Optional[str] = None
    created: str
    maxDepth: int = 1  # Depth to follow HasComponent relationships (0=infinite, 1=no recursion, N=recurse N levels)
    monitoredItems: List[str] = []
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


def get_data_source(request: Request) -> I3XDataSource:
    """Dependency to inject data source"""
    return request.app.state.data_source


def _find_sub(request: Request, subscription_id: str) -> Optional[Subscription]:
    """Locate a subscription by ID"""
    return next(
        (s for s in request.app.state.I3X_DATA_SUBSCRIPTIONS if s.subscriptionId == subscription_id),
        None,
    )


# RFC 4.2.3.1 - Create Subscription
@subs.post(
    "/subscriptions",
    summary="Create Subscription",
    response_model=CreateSubscriptionResponse,
    operation_id="createSubscription",
)
def create_subscription(request: Request, subscription: CreateSubscriptionRequest):
    """Create a new subscription. Returns a unique subscriptionId the client must cache.
    There is no way to list all subscriptions; the client must track the returned ID."""

    subscription_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ttl = getattr(request.app.state, "subscription_ttl_seconds", 300)
    new_sub = Subscription(
        subscriptionId=subscription_id,
        displayName=subscription.displayName,
        created=now,
        last_activity=now,
        ttl_seconds=ttl,
    )
    request.app.state.I3X_DATA_SUBSCRIPTIONS.append(new_sub)

    return CreateSubscriptionResponse(
        subscriptionId=subscription_id,
        displayName=subscription.displayName,
    )


# POST /subscriptions/list - Retrieve details for one or more subscriptions
@subs.post(
    "/subscriptions/list",
    summary="List Subscriptions",
    operation_id="listSubscriptions",
)
def list_subscriptions(request: Request, req: ListSubscriptionsRequest):
    """Return details for the specified subscriptions, including registered elementIds."""
    result = []
    for sub_id in req.subscriptionIds:
        sub = _find_sub(request, sub_id)
        if sub:
            result.append(SubscriptionDetail(
                subscriptionId=sub.subscriptionId,
                displayName=sub.displayName,
                elementIds=sub.monitoredItems,
            ))
    return result


# RFC 4.2.3.2 - Register Monitored Items
@subs.post(
    "/subscriptions/register",
    summary="Register Monitored Items",
    operation_id="registerMonitoredItems",
)
def register_objects(request: Request, req: RegisterMonitoredItemsRequest):
    """Add objects to the subscription. subscriptionId is passed in the request body."""
    sub = _find_sub(request, req.subscriptionId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Get data source
    data_source = request.app.state.data_source

    # Validate that root elementIds exist
    invalid = [eid for eid in req.elementIds if not data_source.get_instance_by_id(eid)]
    if invalid:
        raise HTTPException(
            status_code=404, detail=f"Invalid elementIds: {', '.join(invalid)}"
        )

    # Collect all monitored elementIds including descendants
    all_element_ids = set()
    for eid in req.elementIds:
        tree = collect_instance_tree(
            eid, req.maxDepth, 0, data_source.get_all_instances()
        )
        all_element_ids.update([i["elementId"] for i in tree])

    # Update the subscription (additive - adds to existing monitored items)
    added_count = 0
    for eid in all_element_ids:
        if eid not in sub.monitoredItems:
            sub.monitoredItems.append(eid)
            added_count += 1

    return {
        "message": f"Registered {added_count} objects to subscription.",
        "totalObjects": len(sub.monitoredItems)
    }


# RFC 4.2.3.2 - Unregister Monitored Items
@subs.post(
    "/subscriptions/unregister",
    summary="Remove Monitored Items",
    operation_id="removeMonitoredItems",
)
def unregister_objects(request: Request, req: RegisterMonitoredItemsRequest):
    """Remove objects from the subscription. subscriptionId is passed in the request body."""
    sub = _find_sub(request, req.subscriptionId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Get data source
    data_source = request.app.state.data_source

    # Collect all elementIds including descendants (same logic as register)
    all_element_ids = set()
    for eid in req.elementIds:
        # Only process IDs that exist
        if data_source.get_instance_by_id(eid):
            tree = collect_instance_tree(
                eid, req.maxDepth, 0, data_source.get_all_instances()
            )
            all_element_ids.update([i["elementId"] for i in tree])

    # Remove from subscription (silently ignore IDs that aren't registered)
    removed_count = 0
    for eid in all_element_ids:
        if eid in sub.monitoredItems:
            sub.monitoredItems.remove(eid)
            removed_count += 1

    return {
        "message": f"Unregistered {removed_count} objects from subscription."
    }


# POST /subscriptions/stream - Open SSE stream
@subs.post(
    "/subscriptions/stream",
    summary="Stream Values (SSE)",
    operation_id="streamSubscription",
)
async def stream_subscription(request: Request, req: StreamRequest):
    """Open a Server-Sent Events (SSE) stream. subscriptionId is passed in the request body."""
    sub = _find_sub(request, req.subscriptionId)
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

    If `through` is provided, all queued updates with sequenceNumber <= through are removed first,
    then the remaining (newer) updates are returned. subscriptionId is passed in the request body.
    """
    sub = _find_sub(request, req.subscriptionId)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if req.through is not None:
        sub.pendingUpdates = [u for u in sub.pendingUpdates if u.get("sequenceNumber", 0) > req.through]
        sub.lastAckedSequence = max(sub.lastAckedSequence, req.through)

    sub.last_activity = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"success": True, "result": list(sub.pendingUpdates)}


# POST /subscriptions/delete - Delete one or more subscriptions
@subs.post(
    "/subscriptions/delete",
    summary="Delete Subscriptions",
    operation_id="deleteSubscriptions",
)
def delete_subscriptions(request: Request, req: DeleteSubscriptionsRequest):
    """Delete one or more subscriptions by ID. subscriptionIds are passed in the request body."""
    removed = []
    not_found = []

    for sub_id in req.subscriptionIds:
        index = next(
            (
                i
                for i, s in enumerate(request.app.state.I3X_DATA_SUBSCRIPTIONS)
                if s.subscriptionId == sub_id
            ),
            None,
        )
        if index is not None:
            removed.append(request.app.state.I3X_DATA_SUBSCRIPTIONS[index].subscriptionId)
            request.app.state.I3X_DATA_SUBSCRIPTIONS.pop(index)
        else:
            not_found.append(sub_id)

    return {
        "message": "Delete processed.",
        "deleted": removed,
        "not_found": not_found,
    }


# Subscription thread responsible for creating updates for items being monitored.
# If SSE is active (is_streaming=True), stream updates via handler (streaming mode)
# Otherwise, queue updates for retrieval via /sync (sync mode, max 1000, FIFO)
def handle_data_source_update(instance, value, I3X_DATA_SUBSCRIPTIONS, data_source):
    """Route updates from data sources to active subscriptions"""
    try:
        # Iterate through all active subscriptions
        for sub in I3X_DATA_SUBSCRIPTIONS:
            if not sub.monitoredItems:
                continue

            # Check if this update is for a monitored element
            element_id = instance.get("elementId")
            if element_id and element_id in sub.monitoredItems:

                if sub.is_streaming and sub.handler:
                    # Stream mode: immediate delivery via SSE handler
                    updateValue = getSubscriptionValue(instance, value, maxDepth=sub.maxDepth, data_source=data_source)
                    try:
                        sub.handler(updateValue)
                    except Exception as e:
                        print(f"[SSE] Handler error: {e}")
                        # On error, switch back to queue mode
                        sub.is_streaming = False
                        sub.handler = None
                else:
                    # Queue mode: store for later /sync retrieval in flat format with sequence number
                    actual_value = value.get("value") if isinstance(value, dict) else value
                    quality = value.get("quality", "Good") if isinstance(value, dict) else "Good"
                    timestamp = value.get("timestamp") if isinstance(value, dict) else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    queued_item = {
                        "sequenceNumber": sub.nextSequence,
                        "elementId": element_id,
                        "value": actual_value,
                        "quality": quality,
                        "timestamp": timestamp,
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
