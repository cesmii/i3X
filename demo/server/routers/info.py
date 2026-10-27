from fastapi import APIRouter, Request
from models import SuccessResponse, ServerInfo
from .utils import success_response, BASE_ERROR_RESPONSES

info = APIRouter(prefix="", tags=["Info"])

I3X_SPEC_VERSION = "1.0"


def _capability(capabilities_config, group, name, default):
    """Read a capability flag; a bare boolean for the group applies to all its flags."""
    value = capabilities_config.get(group, {})
    if isinstance(value, bool):
        return value
    return value.get(name, default)


# RFC - Server Capabilities
@info.get("/info", summary="Server Info", operation_id="getInfo", response_model=SuccessResponse[ServerInfo], responses={**BASE_ERROR_RESPONSES})
def get_info(request: Request):
    """Returns the server version and capabilities. May be used as a health check.
    This endpoint does not require authentication."""
    app_config = getattr(request.app.state, "app_config", {})
    capabilities_config = getattr(request.app.state, "capabilities_config", {})

    return success_response({
        "specVersion": I3X_SPEC_VERSION,
        "serverVersion": app_config.get("version"),
        "serverName": app_config.get("title"),
        "capabilities": {
            "query": {
                "history": _capability(capabilities_config, "query", "history", True),
            },
            "update": {
                "current": _capability(capabilities_config, "update", "current", True),
                "history": _capability(capabilities_config, "update", "history", False),
            },
            "subscribe": {
                "stream": _capability(capabilities_config, "subscribe", "stream", True),
            },
        },
    })
