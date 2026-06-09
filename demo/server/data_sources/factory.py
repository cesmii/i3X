from typing import Dict, Any
from .data_interface import I3XDataSource
from .mock.mock_data_source import MockDataSource
from .mqtt.mqtt_data_source import MQTTDataSource
from .manager import DataSourceManager

class DataSourceFactory:
    """Factory for creating data source instances based on configuration"""
    
    @staticmethod
    def create_data_source(config: Dict[str, Any]) -> I3XDataSource:
        """Create a data source instance from configuration
        
        Args:
            config: Dictionary with 'type' and 'config' keys (single source)
                   OR Dictionary with 'data_sources' and 'data_source_routing' keys (multiple sources)
            
        Returns:
            I3XDataSource instance (either single source or DataSourceManager)
            
        Raises:
            ValueError: If data source type is not supported
        """
        # Check if this is multi-source configuration
        if "data_sources" in config:
            return DataSourceFactory._create_multi_source_manager(config)

        # Single source configuration (legacy)
        data_source_type = config.get("type", "mock").lower()
        data_source_config = config.get("config", {})
        
        return DataSourceFactory._create_single_source(data_source_type, data_source_config)

    @staticmethod
    def _create_single_source(data_source_type: str, data_source_config: Dict[str, Any]) -> I3XDataSource:
        """Create a single data source instance"""
        if data_source_type == "mock":
            return MockDataSource()
        elif data_source_type == "mqtt":
            return MQTTDataSource(data_source_config)
        elif data_source_type == "cnc-mock" or data_source_type == "cnc_mock":
            from .cnc_mock.cnc_data_source import CNCDataSource
            return CNCDataSource()
        elif data_source_type == "ignition-cnc" or data_source_type == "ignition_cnc":
            return IgnitionCNCDataSource()
        else:
            raise ValueError(f"Unsupported data source type: {data_source_type}")
    
    @staticmethod
    def _create_multi_source_manager(config: Dict[str, Any]) -> DataSourceManager:
        """Create a DataSourceManager with multiple data sources"""
        data_sources_config = config.get("data_sources", {})
        routing_config = config.get("data_source_routing", {})

        # Create individual data sources
        data_sources = {}
        for name, source_config in data_sources_config.items():
            source_type = source_config.get("type", "mock").lower()
            source_config_data = source_config.get("config", {})
            data_sources[name] = DataSourceFactory._create_single_source(source_type, source_config_data)

        return DataSourceManager(data_sources, routing_config)

    @staticmethod
    def get_supported_types() -> list:
        """Get list of supported data source types"""
        return ["mock", "mqtt", "cnc-mock", "ignition-cnc"]