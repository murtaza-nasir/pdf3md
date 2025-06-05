#!/usr/bin/env python3
"""
Test script for enhanced AI capabilities in Ink2MD
"""

import os
import sys
import logging
from config_manager import ConfigManager
from prompt_manager import PromptManager
from ai_services.factory import AIServiceFactory
from ai_services.anthropic_service import AnthropicService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_prompt_manager():
    """Test the prompt manager functionality."""
    print("=== Testing Prompt Manager ===")
    
    # Create a mock config manager for testing
    class MockConfigManager:
        def __init__(self):
            self.config_path = '/tmp/test_config.json'
    
    config_manager = MockConfigManager()
    prompt_manager = PromptManager(config_manager)
    
    # Test getting default prompts
    print("\n1. Testing default prompt retrieval:")
    htr_prompt = prompt_manager.get_prompt('htr_default')
    print(f"HTR Default Prompt (first 100 chars): {htr_prompt[:100]}...")
    
    formatting_prompt = prompt_manager.get_prompt('formatting_clean', content="Test content")
    print(f"Formatting Prompt (first 100 chars): {formatting_prompt[:100]}...")
    
    # Test listing templates
    print("\n2. Testing template listing:")
    templates = prompt_manager.list_templates()
    print(f"Available templates: {len(templates)}")
    for template in templates[:5]:  # Show first 5
        print(f"  - {template['name']} ({template['category']}): {template['description']}")
    
    # Test adding custom template
    print("\n3. Testing custom template:")
    success = prompt_manager.add_template(
        name="test_custom",
        content="Please process this {document_type} with focus on {focus_area}.",
        description="Test custom template",
        category="test"
    )
    print(f"Added custom template: {success}")
    
    if success:
        custom_prompt = prompt_manager.get_prompt(
            'test_custom',
            document_type='academic paper',
            focus_area='mathematical equations'
        )
        print(f"Custom prompt result: {custom_prompt}")
    
    # Test validation
    print("\n4. Testing template validation:")
    validation = prompt_manager.validate_template("Test template with {variable}")
    print(f"Validation result: {validation}")
    
    return True

def test_anthropic_service():
    """Test the enhanced Anthropic service."""
    print("\n=== Testing Enhanced Anthropic Service ===")
    
    # Check if API key is available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment. Skipping live API tests.")
        print("Testing configuration and capabilities only...")
        
        # Test configuration without API calls
        config = {
            'display_name': 'Claude 3.5 Sonnet',
            'type': 'anthropic',
            'api_key': 'test_key',
            'model': 'claude-3-5-sonnet-20241022',
            'is_htr_capable': True,
            'is_formatting_capable': True,
            'is_vlm_capable': True,
            'enabled': True
        }
        
        service = AnthropicService('test_anthropic', config)
        
        print(f"Service info: {service.get_service_info()}")
        print(f"Capabilities: {[cap.value for cap in service.get_capabilities()]}")
        print(f"Supports HTR: {service.supports_capability('htr')}")
        print(f"Supports VLM: {service.supports_capability('vlm_direct')}")
        
        return True
    
    # Test with real API key
    config = {
        'display_name': 'Claude 3.5 Sonnet',
        'type': 'anthropic',
        'api_key': api_key,
        'model': 'claude-3-5-sonnet-20241022',
        'is_htr_capable': True,
        'is_formatting_capable': True,
        'is_vlm_capable': True,
        'enabled': True
    }
    
    service = AnthropicService('test_anthropic', config)
    
    print(f"Service available: {service.is_available()}")
    print(f"Service info: {service.get_service_info()}")
    
    # Test connection
    connection_result = service.test_connection()
    print(f"Connection test: {connection_result}")
    
    if connection_result.get('success'):
        # Test text generation
        print("\n1. Testing text generation:")
        try:
            result = service.generate_text("Hello, please respond with 'AI service working correctly'")
            print(f"Text generation result: {result}")
        except Exception as e:
            print(f"Text generation failed: {e}")
        
        # Test markdown formatting
        print("\n2. Testing markdown formatting:")
        try:
            test_text = """MEETING NOTES
            - Discussed project timeline
            - Budget approved: $50,000
            - Next meeting: Friday 2pm
            ACTION ITEMS
            - John: prepare presentation
            - Sarah: review contracts"""
            
            formatted = service.format_markdown(test_text, style='clean')
            print(f"Formatted markdown:\n{formatted}")
        except Exception as e:
            print(f"Markdown formatting failed: {e}")
    
    return True

def test_ai_factory():
    """Test the AI service factory with new capabilities."""
    print("\n=== Testing AI Service Factory ===")
    
    factory = AIServiceFactory()
    
    # Test registering services
    anthropic_config = {
        'display_name': 'Claude 3.5 Sonnet',
        'type': 'anthropic',
        'api_key': os.environ.get('ANTHROPIC_API_KEY', 'test_key'),
        'model': 'claude-3-5-sonnet-20241022',
        'is_htr_capable': True,
        'is_formatting_capable': True,
        'is_vlm_capable': True,
        'enabled': True
    }
    
    success = factory.register_service('anthropic_sonnet', anthropic_config)
    print(f"Registered Anthropic service: {success}")
    
    # Test getting services by capability
    htr_services = factory.get_services_by_capability('htr')
    formatting_services = factory.get_services_by_capability('formatting')
    vlm_services = factory.get_services_by_capability('vlm_direct')
    
    print(f"HTR services: {len(htr_services)}")
    print(f"Formatting services: {len(formatting_services)}")
    print(f"VLM services: {len(vlm_services)}")
    
    # Test statistics
    stats = factory.get_statistics()
    print(f"Factory statistics: {stats}")
    
    return True

def main():
    """Run all tests."""
    print("Starting Enhanced AI Tests for Ink2MD")
    print("=" * 50)
    
    try:
        # Test prompt manager
        test_prompt_manager()
        
        # Test enhanced Anthropic service
        test_anthropic_service()
        
        # Test AI factory
        test_ai_factory()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)