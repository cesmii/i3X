from typing import Dict, Any, List, Optional, Callable
from .data_interface import I3XDataSource


class DataSourceManager(I3XDataSource):
    """Manager for multiple data sources with routing capabilities"""

    def __init__(
        self, data_sources: Dict[str, I3XDataSource], routing_config: Dict[str, str]
    ):
        """
        Initialize the manager with multiple data sources and routing configuration

        Args:
            data_sources: Dict mapping data source names to instances
            routing_config: Dict mapping operation types to preferred data source names
        """
        self.data_sources = data_sources
        self.routing_config = routing_config
        self.primary_source = None

        # Set primary data source (first one by default, or explicitly configured)
        if data_sources:
            self.primary_source = list(data_sources.values())[0]
            if (
                "primary" in routing_config
                and routing_config["primary"] in data_sources
            ):
                self.primary_source = data_sources[routing_config["primary"]]

    def _get_source_for_operation(self, operation: str) -> I3XDataSource:
        """Get the appropriate data source for a given operation"""
        if (
            operation in self.routing_config
            and self.routing_config[operation] in self.data_sources
        ):
            return self.data_sources[self.routing_config[operation]]
        return self.primary_source or list(self.data_sources.values())[0]

    def _try_all_sources(self, operation_func, *args, **kwargs):
        """Try operation on all data sources until one succeeds"""
        last_exception = None

        # First try the configured source for this operation
        try:
            primary = self._get_source_for_operation(operation_func.__name__)
            return getattr(primary, operation_func.__name__)(*args, **kwargs)
        except Exception as e:
            last_exception = e

        # Then try other sources as fallback
        for source in self.data_sources.values():
            if source == primary:
                continue  # Already tried this one
            try:
                return getattr(source, operation_func.__name__)(*args, **kwargs)
            except Exception as e:
                last_exception = e

        # If all failed, raise the last exception
        raise last_exception

    def start(
        self, update_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        """Initialize and start all managed data sources"""
        for name, source in self.data_sources.items():
            try:
                source.start(update_callback)
                print(f"Started data source: {name}")
            except Exception as e:
                print(f"Failed to start data source {name}: {e}")

    def stop(self) -> None:
        """Stop and cleanup all managed data sources"""
        for name, source in self.data_sources.items():
            try:
                source.stop()
                print(f"Stopped data source: {name}")
            except Exception as e:
                print(f"Error stopping data source {name}: {e}")

    def get_namespaces(self) -> List[Dict[str, Any]]:
        """Return array of Namespaces registered in the CMIP"""
        source = self._get_source_for_operation("get_namespaces")
        return source.get_namespaces()

    def get_object_types(
        self, namespace_uri: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return array of Type definitions, optionally filtered by NamespaceURI"""
        source = self._get_source_for_operation("get_object_types")
        return source.get_object_types(namespace_uri)

    def get_object_type_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Return JSON structure defining a Type for the requested ElementId"""
        source = self._get_source_for_operation("get_object_type_by_id")
        return source.get_object_type_by_id(element_id)

    def get_relationship_types(
        self, namespace_uri: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return array relationship types"""
        source = self._get_source_for_operation("get_relationship_types")
        return source.get_relationship_types(namespace_uri)

    def get_relationship_type_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Return JSON structure defining a Type for the requested ElementId"""
        source = self._get_source_for_operation("get_relationship_type_by_id")
        return source.get_relationship_type_by_id(element_id)

    def get_instances(self, type_id: Optional[str] = None, root: bool = False) -> List[Dict[str, Any]]:
        """Return array of instance objects, optionally filtered by Type ElementId"""
        source = self._get_source_for_operation("get_instances")
        return source.get_instances(type_id, root=root)

    def get_instance_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Return instance object by ElementId"""
        source = self._get_source_for_operation("get_instance_by_id")
        return source.get_instance_by_id(element_id)

    def get_instance_values_by_id(self, element_id: str, startTime: Optional[str] = None, endTime: Optional[str] = None, maxDepth: int = 1, returnHistory: bool = False) -> Optional[Dict[str, Any]]:
        """Return instance values by ElementId. If maxDepth=0, follows HasComponent relationships infinitely. If maxDepth>1, recurses to that depth. If returnHistory is True and no time range specified, returns all historical values."""
        source = self._get_source_for_operation("get_instance_by_id")
        return source.get_instance_values_by_id(element_id, startTime, endTime, maxDepth, returnHistory)

    def get_related_instances(
        self, element_id: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return array of objects related by specified relationship type. If relationship_type is None, return all related objects."""
        source = self._get_source_for_operation("get_related_instances")
        return source.get_related_instances(element_id, relationship_type)

    def update_instance_value(
        self, element_id: str, value: Any
    ) -> List[Dict[str, Any]]:
        """Update values for specified element IDs"""
        source = self._get_source_for_operation("update_instance_value")
        return source.update_instance_value(element_id, value)

    def get_all_instances(self) -> List[Dict[str, Any]]:
        """Return all instances (used by subscription worker)"""
        # For subscriptions, we might want to aggregate from all sources
        # or use a specific subscription-optimized source
        source = self._get_source_for_operation("get_all_instances")
        return source.get_all_instances()

    def get_instance_extra_attributes(self, element_id: str) -> Optional[Dict[str, Any]]:
        source = self._get_source_for_operation("get_instance_by_id")
        return source.get_instance_extra_attributes(element_id)
