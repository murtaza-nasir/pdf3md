#!/usr/bin/env python3
"""
Ink2MD AI Services Base Classes
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
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AIServiceCapability(Enum):
    """Enumeration of AI service capabilities."""
    HTR = "htr"  # Handwritten Text Recognition
    FORMATTING = "formatting"  # Text formatting and enhancement
    LAYOUT_ANALYSIS = "layout_analysis"  # Document layout analysis
    VLM_DIRECT = "vlm_direct"  # Direct vision-language model processing
    DOCUMENT_INTELLIGENCE = "document_intelligence"  # Advanced document understanding

class AIServiceInterface(ABC):
    """
    Abstract base class for AI service providers.
    
    This interface defines the contract that all AI service implementations
    must follow to ensure consistent behavior across different providers.
    """
    
    def __init__(self, provider_id: str, config: Dict[str, Any]):
        """
        Initialize the AI service.
        
        Args:
            provider_id: Unique identifier for this provider instance
            config: Configuration dictionary containing provider-specific settings
        """
        self.provider_id = provider_id
        self.config = config
        self.display_name = config.get('display_name', provider_id)
        self.enabled = config.get('enabled', True)
        
        # Capability flags
        self.is_htr_capable = config.get('is_htr_capable', False)
        self.is_formatting_capable = config.get('is_formatting_capable', False)
        
        logger.info(f"Initialized AI service: {self.display_name} (ID: {provider_id})")

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the service is available and properly configured.
        
        Returns:
            bool: True if the service is ready to use, False otherwise
        """
        pass

    @abstractmethod
    def get_htr_text(self, image_file_path: str, **kwargs) -> str:
        """
        Extract text from an image using Handwritten Text Recognition.
        
        Args:
            image_file_path: Path to the image file to process
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            NotImplementedError: If the provider doesn't support HTR
            Exception: If the HTR process fails
        """
        pass

    @abstractmethod
    def format_markdown(self, raw_text: str, **kwargs) -> str:
        """
        Format and enhance raw text into clean markdown.
        
        Args:
            raw_text: Raw text to be formatted
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Formatted markdown text
            
        Raises:
            NotImplementedError: If the provider doesn't support formatting
            Exception: If the formatting process fails
        """
        pass

    def extract_layout(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        Extract document layout and structure from an image.
        
        Args:
            image_path: Path to the image file
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict containing layout information (blocks, regions, etc.)
            
        Raises:
            NotImplementedError: If the provider doesn't support layout analysis
        """
        if not self.supports_capability(AIServiceCapability.LAYOUT_ANALYSIS):
            raise NotImplementedError("This service does not support layout analysis")
        raise NotImplementedError("Layout analysis not implemented for this service")

    def process_with_vlm(self, image_path: str, prompt_template: str, **kwargs) -> str:
        """
        Process image directly with vision-language model.
        
        Args:
            image_path: Path to the image file
            prompt_template: Formatted prompt for the VLM
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Direct output from vision-language model
            
        Raises:
            NotImplementedError: If the provider doesn't support VLM processing
        """
        if not self.supports_capability(AIServiceCapability.VLM_DIRECT):
            raise NotImplementedError("This service does not support VLM processing")
        raise NotImplementedError("VLM processing not implemented for this service")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the AI service (for backward compatibility).
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        # Default implementation for text-only services
        raise NotImplementedError("Text generation not implemented for this service")

    def get_capabilities(self) -> List[AIServiceCapability]:
        """
        Get the list of capabilities supported by this service.
        
        Returns:
            List[AIServiceCapability]: List of supported capabilities
        """
        capabilities = []
        if self.is_htr_capable:
            capabilities.append(AIServiceCapability.HTR)
        if self.is_formatting_capable:
            capabilities.append(AIServiceCapability.FORMATTING)
        
        # Check for additional capabilities from config
        if self.config.get('is_layout_capable', False):
            capabilities.append(AIServiceCapability.LAYOUT_ANALYSIS)
        if self.config.get('is_vlm_capable', False):
            capabilities.append(AIServiceCapability.VLM_DIRECT)
        if self.config.get('is_document_intelligence_capable', False):
            capabilities.append(AIServiceCapability.DOCUMENT_INTELLIGENCE)
            
        return capabilities

    def supports_capability(self, capability: AIServiceCapability) -> bool:
        """
        Check if the service supports a specific capability.
        
        Args:
            capability: The capability to check
            
        Returns:
            bool: True if the capability is supported
        """
        return capability in self.get_capabilities()

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this service.
        
        Returns:
            Dict containing service information
        """
        return {
            'provider_id': self.provider_id,
            'display_name': self.display_name,
            'type': self.config.get('type', 'unknown'),
            'enabled': self.enabled,
            'available': self.is_available(),
            'capabilities': [cap.value for cap in self.get_capabilities()],
            'is_htr_capable': self.is_htr_capable,
            'is_formatting_capable': self.is_formatting_capable,
            'is_layout_capable': self.config.get('is_layout_capable', False),
            'is_vlm_capable': self.config.get('is_vlm_capable', False),
            'is_document_intelligence_capable': self.config.get('is_document_intelligence_capable', False)
        }

    def validate_config(self) -> Dict[str, str]:
        """
        Validate the service configuration.
        
        Returns:
            Dict[str, str]: Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        if not self.provider_id:
            errors['provider_id'] = "Provider ID is required"
        
        if not self.display_name:
            errors['display_name'] = "Display name is required"
        
        if not self.is_htr_capable and not self.is_formatting_capable:
            errors['capabilities'] = "Service must support at least one capability"
        
        return errors

class MockAIService(AIServiceInterface):
    """
    Mock AI service implementation for testing and development.
    
    This service provides dummy implementations that can be used
    when real AI services are not available or for testing purposes.
    """
    
    def __init__(self, provider_id: str, config: Dict[str, Any]):
        super().__init__(provider_id, config)
        self.mock_delay = config.get('mock_delay', 0.5)  # Simulate processing time
    
    def is_available(self) -> bool:
        """Mock service is always available."""
        return self.enabled
    
    def get_htr_text(self, image_file_path: str, **kwargs) -> str:
        """
        Mock HTR implementation that returns placeholder text.
        """
        if not self.is_htr_capable:
            raise NotImplementedError("This service does not support HTR")
        
        import time
        import os
        
        # Simulate processing time
        time.sleep(self.mock_delay)
        
        filename = os.path.basename(image_file_path)
        return f"""# Mock HTR Output

This is mock handwritten text recognition output for image: {filename}

## Sample Content
- Handwritten note 1
- Handwritten note 2
- Mathematical equation: E = mc²
- Date: {time.strftime('%Y-%m-%d')}

*Note: This is generated by the mock AI service for testing purposes.*
"""
    
    def format_markdown(self, raw_text: str, **kwargs) -> str:
        """
        Mock formatting implementation that adds basic structure.
        """
        if not self.is_formatting_capable:
            raise NotImplementedError("This service does not support formatting")
        
        import time
        
        # Simulate processing time
        time.sleep(self.mock_delay)
        
        # Basic formatting: add headers and structure
        lines = raw_text.split('\n')
        formatted_lines = []
        
        formatted_lines.append("# Formatted Document")
        formatted_lines.append("")
        formatted_lines.append(f"*Formatted by {self.display_name} on {time.strftime('%Y-%m-%d %H:%M:%S')}*")
        formatted_lines.append("")
        
        for line in lines:
            line = line.strip()
            if line:
                # Simple formatting rules
                if line.isupper() and len(line) < 50:
                    formatted_lines.append(f"## {line.title()}")
                elif line.startswith('-') or line.startswith('*'):
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append("")
        
        formatted_lines.append("")
        formatted_lines.append("---")
        formatted_lines.append("*End of formatted document*")
        
        return '\n'.join(formatted_lines)

# Utility functions for service management
def validate_service_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate a service configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Dict[str, str]: Dictionary of validation errors
    """
    errors = {}
    
    required_fields = ['display_name', 'type']
    for field in required_fields:
        if not config.get(field):
            errors[field] = f"{field} is required"
    
    # Type-specific validation
    service_type = config.get('type', '').lower()
    
    if service_type == 'anthropic':
        if not config.get('api_key'):
            errors['api_key'] = "API key is required for Anthropic services"
        if not config.get('model'):
            errors['model'] = "Model is required for Anthropic services"
    
    elif service_type == 'ollama':
        if not config.get('api_base_url'):
            errors['api_base_url'] = "API base URL is required for Ollama services"
        if not config.get('model'):
            errors['model'] = "Model is required for Ollama services"
    
    # Capability validation
    is_htr = config.get('is_htr_capable', False)
    is_formatting = config.get('is_formatting_capable', False)
    
    if not is_htr and not is_formatting:
        errors['capabilities'] = "Service must support at least one capability (HTR or formatting)"
    
    return errors

def create_service_from_config(provider_id: str, config: Dict[str, Any]) -> AIServiceInterface:
    """
    Create an AI service instance from configuration.
    
    Args:
        provider_id: Unique identifier for the service
        config: Configuration dictionary
        
    Returns:
        AIServiceInterface: Configured service instance
        
    Raises:
        ValueError: If configuration is invalid
        ImportError: If required service implementation is not available
    """
    # Validate configuration
    errors = validate_service_config(config)
    if errors:
        raise ValueError(f"Invalid service configuration: {errors}")
    
    service_type = config.get('type', '').lower()
    
    # Import and create appropriate service
    if service_type == 'mock':
        return MockAIService(provider_id, config)
    elif service_type == 'anthropic':
        from .anthropic_service import AnthropicService
        return AnthropicService(provider_id, config)
    elif service_type == 'ollama':
        from .ollama_service import OllamaService
        return OllamaService(provider_id, config)
    else:
        raise ValueError(f"Unknown service type: {service_type}")

# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test mock service
    mock_config = {
        'display_name': 'Mock AI Service',
        'type': 'mock',
        'is_htr_capable': True,
        'is_formatting_capable': True,
        'mock_delay': 0.1
    }
    
    service = MockAIService('mock_test', mock_config)
    print(f"Service info: {service.get_service_info()}")
    print(f"Available: {service.is_available()}")
    print(f"Capabilities: {[cap.value for cap in service.get_capabilities()]}")
    
    # Test HTR
    if service.supports_capability(AIServiceCapability.HTR):
        htr_result = service.get_htr_text('/path/to/test/image.png')
        print(f"HTR result: {htr_result[:100]}...")
    
    # Test formatting
    if service.supports_capability(AIServiceCapability.FORMATTING):
        raw_text = "MEETING NOTES\n- Item 1\n- Item 2\nConclusion: All good"
        formatted = service.format_markdown(raw_text)
        print(f"Formatted result: {formatted[:100]}...")