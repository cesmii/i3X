from fastapi import APIRouter, Request
from models import SuccessResponse, ServerInfo
from .utils import success_response, capability_enabled, BASE_ERROR_RESPONSES

info = APIRouter(prefix="", tags=["Info"])

I3X_SPEC_VERSION = "1.0"


# RFC - Server Capabilities
@info.get("/info", summary="Server Info", operation_id="getInfo", response_model=SuccessResponse[ServerInfo], responses={**BASE_ERROR_RESPONSES})
def get_info(request: Request):
    """Returns the server version and capabilities. May be used as a health check.
    This endpoint does not require authentication."""
    app_config = getattr(request.app.state, "app_config", {})

    return success_response({
        "specVersion": I3X_SPEC_VERSION,
        "serverVersion": app_config.get("version"),
        "serverName": app_config.get("title"),
        "capabilities": {
            "query": {
                "history": capability_enabled(request, "query", "history", True),
            },
            "update": {
                "current": capability_enabled(request, "update", "current", True),
                "history": capability_enabled(request, "update", "history", False),
            },
            "subscribe": {
                "stream": capability_enabled(request, "subscribe", "stream", True),
            },
        },
    })
