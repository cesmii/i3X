from fastapi import APIRouter, Depends
from .utils import success_response, get_data_source
import logging

logger = logging.getLogger("uvicorn.error")
ns = APIRouter(prefix="", tags=["Explore"])


# RFC 4.1.1 - Namespaces
@ns.get("/namespaces", summary="Get Namespaces", operation_id="getNamespaces")
def get_namespaces(data_source=Depends(get_data_source)):
    """Get all Namespaces"""
    return success_response(data_source.get_namespaces())
