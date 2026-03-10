from fastapi import APIRouter, Request, Depends
from data_sources.data_interface import I3XDataSource
from .utils import success_response
import logging

logger = logging.getLogger("uvicorn.error")
ns = APIRouter(prefix="", tags=["Explore"])


def get_data_source(request: Request) -> I3XDataSource:
    """Dependency to inject data source"""
    return request.app.state.data_source


# RFC 4.1.1 - Namespaces
@ns.get("/namespaces", summary="Get Namespaces", operation_id="getNamespaces")
def get_namespaces(data_source: I3XDataSource = Depends(get_data_source)):
    """Get all Namespaces"""
    return success_response(data_source.get_namespaces())
