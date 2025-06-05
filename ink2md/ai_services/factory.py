#!/usr/bin/env python3
"""
Ink2MD AI Service Factory
Based on PDF3MD by Murtaza Nsair
Original: https://github.com/murtaza-nasir/pdf3md

Copyright (C) 2025 Ink2MD Contributors
Copyright (C) 2024 Murtaza Nsair (original PDF3MD)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import logging
from typing import Dict, Any, Optional, List
from .base import AIServiceInterface, AIServiceCapability, create_service_from_config
from .anthropic_service import AnthropicService
from .ollama_service import OllamaService

logger = logging.getLogger(__name__)

class AIServiceFactory:
    """
    Factory class for creating and managing AI service instances.
    
    This factory provides a centralized way to create, configure, and manage
    different AI service providers based on configuration.
    """
    
    # Registry of available service types
    SERVICE_TYPES = {
        'anthropic': AnthropicService,
        'ollama': OllamaService,
        'mock': None  # Handled in base.py
    }
    
    def __init__(self):
        self._services: Dict[str, AIServiceInterface] = {}
        self._config: Dict[str, Dict[str, Any]] = {}
    
    def register_service(self, provider_id: str, config: Dict[str, Any]) -> bool:
        """
        Register a new AI service with the factory.
        
        Args:
            provider_id: Unique identifier for the service
            config: Service configuration dictionary
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            # Validate configuration
            service_type = config.get('type', '').lower()
            if service_type not in self.SERVICE_TYPES:
                logger.error(f"Unknown service type: {service_type}")
                return False
            
            # Create service instance
            service = create_service_from_config(provider_id, config)
            
            # Validate the service
            validation_errors = service.validate_config()
            if validation_errors:
                logger.error(f"Service validation failed for {provider_id}: {validation_errors}")
                return False
            
            # Store service and config
            self._services[provider_id] = service
            self._config[provider_id] = config.copy()
            
            logger.info(f"Registered AI service: {provider_id} ({service.display_name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {provider_id}: {e}")
            return False
    
    def unregister_service(self, provider_id: str) -> bool:
        """
        Unregister an AI service from the factory.
        
        Args:
            provider_id: ID of the service to unregister
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        if provider_id in self._services:
            del self._services[provider_id]
            del self._config[provider_id]
            logger.info(f"Unregistered AI service: {provider_id}")
            return True
        else:
            logger.warning(f"Service {provider_id} not found for unregistration")
            return False
    
    def get_service(self, provider_id: str) -> Optional[AIServiceInterface]:
        """
        Get an AI service instance by ID.
        
        Args:
            provider_id: ID of the service to retrieve
            
        Returns:
            AIServiceInterface or None if not found
        """
        return self._services.get(provider_id)
    
    def get_services_by_capability(self, capability: AIServiceCapability) -> List[AIServiceInterface]:
        """
        Get all services that support a specific capability.
        
        Args:
            capability: The capability to filter by
            
        Returns:
            List of services supporting the capability
        """
        return [
            service for service in self._services.values()
            if service.supports_capability(capability) and service.enabled
        ]
    
    def get_available_services(self) -> List[AIServiceInterface]:
        """
        Get all services that are currently available.
        
        Returns:
            List of available services
        """
        return [
            service for service in self._services.values()
            if service.is_available()
        ]
    
    def get_htr_services(self) -> List[AIServiceInterface]:
        """Get all services capable of HTR."""
        return self.get_services_by_capability(AIServiceCapability.HTR)
    
    def get_formatting_services(self) -> List[AIServiceInterface]:
        """Get all services capable of text formatting."""
        return self.get_services_by_capability(AIServiceCapability.FORMATTING)
    
    def get_service_info(self, provider_id: str = None) -> Dict[str, Any]:
        """
        Get information about services.
        
        Args:
            provider_id: Specific service ID, or None for all services
            
        Returns:
            Dict containing service information
        """
        if provider_id:
            service = self.get_service(provider_id)
            return service.get_service_info() if service else {}
        else:
            return {
                service_id: service.get_service_info()
                for service_id, service in self._services.items()
            }
    
    def test_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Test connectivity for all registered services.
        
        Returns:
            Dict mapping service IDs to test results
        """
        results = {}
        for service_id, service in self._services.items():
            try:
                if hasattr(service, 'test_connection'):
                    results[service_id] = service.test_connection()
                else:
                    results[service_id] = {
                        'success': service.is_available(),
                        'message': 'Basic availability check'
                    }
            except Exception as e:
                results[service_id] = {
                    'success': False,
                    'error': str(e)
                }
        return results
    
    def load_from_config(self, config: Dict[str, Any]) -> int:
        """
        Load multiple services from configuration.
        
        Args:
            config: Configuration dictionary with ai_provider_configs section
            
        Returns:
            int: Number of services successfully loaded
        """
        ai_configs = config.get('ai_provider_configs', {})
        loaded_count = 0
        
        for provider_id, provider_config in ai_configs.items():
            if self.register_service(provider_id, provider_config):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} AI services from configuration")
        return loaded_count
    
    def get_active_services(self, config: Dict[str, Any]) -> Dict[str, Optional[AIServiceInterface]]:
        """
        Get the currently active services based on configuration.
        
        Args:
            config: Application configuration
            
        Returns:
            Dict with 'htr' and 'formatting' keys mapping to active services
        """
        active_services = config.get('active_services', {})
        
        htr_provider_id = active_services.get('htr_provider_id')
        formatting_provider_id = active_services.get('formatting_provider_id')
        
        return {
            'htr': self.get_service(htr_provider_id) if htr_provider_id else None,
            'formatting': self.get_service(formatting_provider_id) if formatting_provider_id else None
        }
    
    def validate_active_services(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate that active services are properly configured.
        
        Args:
            config: Application configuration
            
        Returns:
            Dict of validation errors
        """
        errors = {}
        active_services = self.get_active_services(config)
        
        # Check HTR service
        htr_service = active_services.get('htr')
        if not htr_service:
            errors['htr_service'] = "No HTR service configured or service not found"
        elif not htr_service.is_available():
            errors['htr_service'] = f"HTR service {htr_service.provider_id} is not available"
        elif not htr_service.supports_capability(AIServiceCapability.HTR):
            errors['htr_service'] = f"Service {htr_service.provider_id} does not support HTR"
        
        # Check formatting service
        formatting_service = active_services.get('formatting')
        if not formatting_service:
            errors['formatting_service'] = "No formatting service configured or service not found"
        elif not formatting_service.is_available():
            errors['formatting_service'] = f"Formatting service {formatting_service.provider_id} is not available"
        elif not formatting_service.supports_capability(AIServiceCapability.FORMATTING):
            errors['formatting_service'] = f"Service {formatting_service.provider_id} does not support formatting"
        
        return errors
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered services.
        
        Returns:
            Dict containing service statistics
        """
        total_services = len(self._services)
        available_services = len(self.get_available_services())
        htr_services = len(self.get_htr_services())
        formatting_services = len(self.get_formatting_services())
        
        service_types = {}
        for service in self._services.values():
            service_type = service.config.get('type', 'unknown')
            service_types[service_type] = service_types.get(service_type, 0) + 1
        
        return {
            'total_services': total_services,
            'available_services': available_services,
            'htr_services': htr_services,
            'formatting_services': formatting_services,
            'service_types': service_types,
            'service_list': list(self._services.keys())
        }

# Global factory instance
_global_factory: Optional[AIServiceFactory] = None

def get_ai_service_factory() -> AIServiceFactory:
    """Get the global AI service factory instance."""
    global _global_factory
    if _global_factory is None:
        _global_factory = AIServiceFactory()
    return _global_factory

def get_ai_service(provider_id: str) -> Optional[AIServiceInterface]:
    """
    Convenience function to get an AI service by ID.
    
    Args:
        provider_id: ID of the service to retrieve
        
    Returns:
        AIServiceInterface or None if not found
    """
    factory = get_ai_service_factory()
    return factory.get_service(provider_id)

def initialize_ai_services(config: Dict[str, Any]) -> AIServiceFactory:
    """
    Initialize AI services from configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        AIServiceFactory: Initialized factory
    """
    factory = get_ai_service_factory()
    factory.load_from_config(config)
    return factory

# Example usage and testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration
    test_config = {
        'ai_provider_configs': {
            'ollama_llava': {
                'display_name': 'Ollama LLaVA',
                'type': 'ollama',
                'api_base_url': 'http://localhost:11434',
                'model': 'llava',
                'is_htr_capable': True,
                'is_formatting_capable': False
            },
            'ollama_mistral': {
                'display_name': 'Ollama Mistral',
                'type': 'ollama',
                'api_base_url': 'http://localhost:11434',
                'model': 'mistral',
                'is_htr_capable': False,
                'is_formatting_capable': True
            },
            'anthropic_claude': {
                'display_name': 'Claude Haiku',
                'type': 'anthropic',
                'api_key': 'test_key',
                'model': 'claude-3-haiku-20240307',
                'is_htr_capable': True,
                'is_formatting_capable': True
            }
        },
        'active_services': {
            'htr_provider_id': 'ollama_llava',
            'formatting_provider_id': 'anthropic_claude'
        }
    }
    
    # Initialize factory
    factory = AIServiceFactory()
    loaded_count = factory.load_from_config(test_config)
    print(f"Loaded {loaded_count} services")
    
    # Get statistics
    stats = factory.get_statistics()
    print(f"Statistics: {stats}")
    
    # Get active services
    active = factory.get_active_services(test_config)
    print(f"Active HTR service: {active['htr'].display_name if active['htr'] else 'None'}")
    print(f"Active formatting service: {active['formatting'].display_name if active['formatting'] else 'None'}")
    
    # Validate active services
    validation_errors = factory.validate_active_services(test_config)
    print(f"Validation errors: {validation_errors}")
    
    # Test all services
    test_results = factory.test_all_services()
    print(f"Test results: {test_results}")