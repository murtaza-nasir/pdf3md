"""
AI Services Package

This package provides a pluggable architecture for integrating different AI providers
for Handwritten Text Recognition (HTR) and text formatting tasks.

Supported providers:
- Anthropic Claude (formatting)
- Ollama (HTR with LLaVA, formatting with Mistral)
- Extensible for future providers (OpenAI, Google, etc.)
"""

from .base import AIServiceInterface, AIServiceCapability
from .factory import AIServiceFactory, get_ai_service, get_ai_service_factory, initialize_ai_services
from .anthropic_service import AnthropicService
from .ollama_service import OllamaService

__all__ = [
    'AIServiceInterface',
    'AIServiceCapability',
    'AIServiceFactory',
    'get_ai_service',
    'get_ai_service_factory',
    'initialize_ai_services',
    'AnthropicService',
    'OllamaService'
]