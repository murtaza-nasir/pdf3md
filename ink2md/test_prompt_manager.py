#!/usr/bin/env python3
"""
Simple test script for the prompt manager functionality
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_prompt_manager():
    """Test the prompt manager functionality without external dependencies."""
    print("=== Testing Prompt Manager ===")
    
    try:
        from prompt_manager import PromptManager
        
        # Create a mock config manager for testing
        class MockConfigManager:
            def __init__(self):
                self.config_path = '/tmp/test_config.json'
        
        config_manager = MockConfigManager()
        prompt_manager = PromptManager(config_manager)
        
        # Test getting default prompts
        print("\n1. Testing default prompt retrieval:")
        htr_prompt = prompt_manager.get_prompt('htr_default')
        print(f"✓ HTR Default Prompt loaded ({len(htr_prompt)} chars)")
        print(f"  Preview: {htr_prompt[:100]}...")
        
        formatting_prompt = prompt_manager.get_prompt('formatting_clean', content="Test content")
        print(f"✓ Formatting Prompt loaded ({len(formatting_prompt)} chars)")
        print(f"  Preview: {formatting_prompt[:100]}...")
        
        # Test listing templates
        print("\n2. Testing template listing:")
        templates = prompt_manager.list_templates()
        print(f"✓ Found {len(templates)} templates")
        
        categories = prompt_manager.get_categories()
        print(f"✓ Categories: {categories}")
        
        for category in categories:
            category_templates = prompt_manager.list_templates(category=category)
            print(f"  - {category}: {len(category_templates)} templates")
        
        # Test adding custom template
        print("\n3. Testing custom template:")
        success = prompt_manager.add_template(
            name="test_custom",
            content="Please process this {document_type} with focus on {focus_area}.",
            description="Test custom template",
            category="test"
        )
        print(f"✓ Added custom template: {success}")
        
        if success:
            custom_prompt = prompt_manager.get_prompt(
                'test_custom',
                document_type='academic paper',
                focus_area='mathematical equations'
            )
            print(f"✓ Custom prompt result: {custom_prompt}")
        
        # Test validation
        print("\n4. Testing template validation:")
        validation = prompt_manager.validate_template("Test template with {variable}")
        print(f"✓ Validation result: {validation}")
        
        # Test variable extraction
        test_content = "Process {document_type} focusing on {area} and {style}"
        variables = prompt_manager._extract_variables(test_content)
        print(f"✓ Extracted variables: {variables}")
        
        # Test fallback prompts
        print("\n5. Testing fallback prompts:")
        fallback = prompt_manager.get_prompt('nonexistent_template')
        print(f"✓ Fallback prompt: {fallback[:50]}...")
        
        print("\n✓ All prompt manager tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_structure():
    """Test the configuration structure."""
    print("\n=== Testing Configuration Structure ===")
    
    try:
        from config_manager import ConfigManager
        
        # Test loading config
        config_manager = ConfigManager()
        
        # Test getting prompt templates
        prompt_templates = config_manager.get_setting('prompt_templates', {})
        print(f"✓ Found {len(prompt_templates)} prompt template references")
        
        # Test getting processing profiles
        profiles = config_manager.get_setting('processing_profiles', {})
        print(f"✓ Found {len(profiles)} processing profiles")
        for profile_name, profile_config in profiles.items():
            print(f"  - {profile_name}: {profile_config.get('description', 'No description')}")
        
        # Test getting active services
        active_services = config_manager.get_setting('active_services', {})
        print(f"✓ Active services: {active_services}")
        
        # Test AI provider configs
        ai_configs = config_manager.get_setting('ai_provider_configs', {})
        print(f"✓ Found {len(ai_configs)} AI provider configurations")
        for provider_id, provider_config in ai_configs.items():
            capabilities = []
            if provider_config.get('is_htr_capable'):
                capabilities.append('HTR')
            if provider_config.get('is_formatting_capable'):
                capabilities.append('Formatting')
            if provider_config.get('is_vlm_capable'):
                capabilities.append('VLM')
            print(f"  - {provider_id}: {capabilities}")
        
        print("\n✓ All configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Starting Enhanced AI Tests for Ink2MD")
    print("=" * 50)
    
    success = True
    
    # Test prompt manager
    if not test_prompt_manager():
        success = False
    
    # Test configuration
    if not test_config_structure():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Install required dependencies: pip install anthropic requests")
        print("2. Set ANTHROPIC_API_KEY environment variable")
        print("3. Test with real AI services")
    else:
        print("✗ Some tests failed!")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)