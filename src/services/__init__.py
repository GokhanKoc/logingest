# logingest/src/services/__init__.py
from typing import Dict, Any, Type
from .base_service import BaseService
from .api_services.json_placeholder_service import JsonPlaceholderService
# Import other services as needed

SERVICE_REGISTRY = {
    'json_placeholder': JsonPlaceholderService,
    # Add other services here
}

class ServiceFactory:
    @staticmethod
    def create_service(service_type: str, config: Dict[str, Any]) -> BaseService:
        """Create and return a service instance based on type."""
        service_class = SERVICE_REGISTRY.get(service_type)
        if not service_class:
            raise ValueError(f"Unknown service type: {service_type}")
        return service_class(config)
    
    @classmethod
    def from_config(cls, service_config: Dict[str, Any]) -> BaseService:
        """Create a service instance from configuration."""
        service_type = service_config.get('type')
        if not service_type:
            raise ValueError("Service type not specified in config")
        return cls.create_service(service_type, service_config)