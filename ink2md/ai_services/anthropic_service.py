#!/usr/bin/env python3
"""
Ink2MD Anthropic Claude AI Service
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
import os
import logging
from typing import Dict, Any, Optional
import base64
import mimetypes

from .base import AIServiceInterface, AIServiceCapability

logger = logging.getLogger(__name__)

class AnthropicService(AIServiceInterface):
    """
    Anthropic Claude AI service implementation.
    
    This service provides text formatting capabilities using Claude models.
    Note: Anthropic's vision models can also handle HTR, but this implementation
    focuses on text formatting as the primary use case.
    """
    
    def __init__(self, provider_id: str, config: Dict[str, Any]):
        super().__init__(provider_id, config)
        
        # Anthropic-specific configuration
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'claude-3-haiku-20240307')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.1)
        
        # Initialize Anthropic client
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Anthropic client."""
        try:
            import anthropic
            
            if not self.api_key:
                logger.error(f"No API key provided for Anthropic service {self.provider_id}")
                return
            
            self._client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic client initialized for {self.provider_id}")
            
        except ImportError:
            logger.error("Anthropic library not installed. Install with: pip install anthropic")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            self._client = None
    
    def is_available(self) -> bool:
        """Check if the Anthropic service is available."""
        if not self.enabled:
            return False
        
        if not self._client:
            return False
        
        if not self.api_key:
            logger.warning(f"Anthropic service {self.provider_id} has no API key")
            return False
        
        # Optional: Test API connectivity
        try:
            # Simple test to verify API key works
            # We'll skip this for now to avoid unnecessary API calls
            return True
        except Exception as e:
            logger.error(f"Anthropic service {self.provider_id} connectivity test failed: {e}")
            return False
    
    def get_htr_text(self, image_file_path: str, **kwargs) -> str:
        """
        Extract text from an image using Claude's vision capabilities.
        
        Args:
            image_file_path: Path to the image file
            **kwargs: Additional parameters (prompt_template, prompt_manager, etc.)
        """
        if not self.is_htr_capable:
            raise NotImplementedError("This Anthropic service is not configured for HTR")
        
        if not self.is_available():
            raise RuntimeError("Anthropic service is not available")
        
        try:
            # Get prompt from prompt manager or use custom/default
            prompt = self._get_prompt_for_htr(**kwargs)
            
            # Process image with vision model
            return self._process_image_with_prompt(image_file_path, prompt)
            
        except Exception as e:
            logger.error(f"HTR failed for {image_file_path}: {e}")
            raise RuntimeError(f"Anthropic HTR failed: {str(e)}")
    
    def format_markdown(self, raw_text: str, **kwargs) -> str:
        """
        Format raw text into clean markdown using Claude.
        
        Args:
            raw_text: Raw text to format
            **kwargs: Additional parameters (prompt_template, prompt_manager, style, etc.)
        """
        if not self.is_formatting_capable:
            raise NotImplementedError("This Anthropic service is not configured for formatting")
        
        if not self.is_available():
            raise RuntimeError("Anthropic service is not available")
        
        try:
            # Get prompt from prompt manager or use custom/default
            prompt = self._get_prompt_for_formatting(raw_text, **kwargs)
            
            # Create message
            message = {
                "role": "user",
                "content": prompt
            }
            
            # Call Claude API
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[message]
            )
            
            # Extract formatted text
            formatted_text = response.content[0].text
            
            logger.info(f"Successfully formatted text using Anthropic ({len(raw_text)} -> {len(formatted_text)} chars)")
            return formatted_text
            
        except Exception as e:
            logger.error(f"Formatting failed: {e}")
            raise RuntimeError(f"Anthropic formatting failed: {str(e)}")
    
    def process_with_vlm(self, image_path: str, prompt_template: str, **kwargs) -> str:
        """
        Process image directly with Claude's vision capabilities.
        
        Args:
            image_path: Path to the image file
            prompt_template: Formatted prompt for the VLM
            **kwargs: Additional parameters
        """
        if not self.supports_capability(AIServiceCapability.VLM_DIRECT):
            raise NotImplementedError("This Anthropic service is not configured for VLM processing")
        
        if not self.is_available():
            raise RuntimeError("Anthropic service is not available")
        
        try:
            return self._process_image_with_prompt(image_path, prompt_template)
            
        except Exception as e:
            logger.error(f"VLM processing failed for {image_path}: {e}")
            raise RuntimeError(f"Anthropic VLM processing failed: {str(e)}")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Claude (for backward compatibility).
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional parameters
        """
        if not self.is_available():
            raise RuntimeError("Anthropic service is not available")
        
        try:
            # Create message
            message = {
                "role": "user",
                "content": prompt
            }
            
            # Call Claude API
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[message]
            )
            
            # Extract text from response
            generated_text = response.content[0].text
            
            logger.info(f"Successfully generated text using Anthropic ({len(generated_text)} chars)")
            return generated_text
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise RuntimeError(f"Anthropic text generation failed: {str(e)}")
    
    def _process_image_with_prompt(self, image_path: str, prompt: str) -> str:
        """
        Process an image with a given prompt using Claude's vision capabilities.
        
        Args:
            image_path: Path to the image file
            prompt: Text prompt for processing
            
        Returns:
            str: Response from Claude
        """
        try:
            # Read and encode the image
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Determine media type
            media_type, _ = mimetypes.guess_type(image_path)
            if not media_type or not media_type.startswith('image/'):
                media_type = 'image/jpeg'  # Default fallback
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create message with image
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
            
            # Call Claude API
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[message]
            )
            
            # Extract text from response
            result = response.content[0].text
            
            logger.info(f"Successfully processed image {image_path} using Anthropic vision")
            return result
            
        except Exception as e:
            logger.error(f"Image processing failed for {image_path}: {e}")
            raise
    
    def _get_prompt_for_htr(self, **kwargs) -> str:
        """
        Get appropriate prompt for HTR processing.
        
        Args:
            **kwargs: Parameters including prompt_manager, prompt_template, custom_prompt, etc.
            
        Returns:
            str: Formatted prompt for HTR
        """
        # Check for custom prompt first
        custom_prompt = kwargs.get('custom_prompt')
        if custom_prompt:
            return custom_prompt
        
        # Check for prompt manager and template
        prompt_manager = kwargs.get('prompt_manager')
        prompt_template = kwargs.get('prompt_template', 'htr_default')
        
        if prompt_manager:
            try:
                return prompt_manager.get_prompt(prompt_template, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to get prompt from manager: {e}")
        
        # Fallback to default based on document type or style
        document_type = kwargs.get('document_type', 'general')
        
        if document_type == 'academic':
            return """Please extract all text from this academic document image with high precision.

Focus on:
- Academic content including citations, references, and footnotes
- Mathematical equations, formulas, and scientific notation
- Tables, figures, and captions
- Handwritten annotations and margin notes
- Preserve academic formatting and structure

Maintain the original academic structure and formatting in your text extraction."""
        
        elif document_type == 'handwritten':
            return """Please focus specifically on extracting handwritten text from this image.

Pay special attention to:
- Handwritten notes, whether in cursive or print
- Personal annotations and comments
- Sketches or diagrams with text labels
- Margin notes and corrections
- Any handwritten mathematical expressions

Please be patient with unclear handwriting and provide your best interpretation while noting any uncertain text with [unclear] markers."""
        
        elif document_type == 'forms':
            return """Please extract text from this form or structured document.

Focus on:
- Form field labels and their corresponding values
- Checkboxes and their status (checked/unchecked)
- Tables with headers and data
- Signatures and handwritten entries
- Document structure and layout

Organize the extracted information to preserve the form's logical structure."""
        
        else:  # Default
            return """Please analyze this image and extract all visible text, including handwritten text.

Focus on:
- Handwritten notes and annotations
- Printed text
- Mathematical equations or formulas
- Dates, numbers, and measurements
- Any other textual content

Please provide the extracted text in a clear, organized format. If the text appears to be structured (like notes, lists, or sections), please maintain that structure in your output."""
    
    def _get_prompt_for_formatting(self, raw_text: str, **kwargs) -> str:
        """
        Get appropriate prompt for markdown formatting.
        
        Args:
            raw_text: Text to be formatted
            **kwargs: Parameters including prompt_manager, prompt_template, style, etc.
            
        Returns:
            str: Formatted prompt for markdown generation
        """
        # Check for custom prompt first
        custom_prompt = kwargs.get('custom_prompt')
        if custom_prompt:
            return custom_prompt.format(content=raw_text)
        
        # Check for prompt manager and template
        prompt_manager = kwargs.get('prompt_manager')
        prompt_template = kwargs.get('prompt_template', 'formatting_clean')
        
        if prompt_manager:
            try:
                return prompt_manager.get_prompt(prompt_template, content=raw_text, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to get prompt from manager: {e}")
        
        # Fallback to default based on style
        style = kwargs.get('style', 'clean')
        
        if style == 'academic':
            prompt = """Please format the following text into clean, well-structured markdown suitable for academic or professional documents.

Focus on:
- Creating clear headings and subheadings with proper hierarchy
- Organizing content into logical sections
- Formatting lists, equations, and citations properly
- Maintaining academic tone and structure
- Adding appropriate emphasis and formatting
- Preserving references and footnotes
- Using proper markdown syntax for academic content

Text to format:
"""
        elif style == 'notes':
            prompt = """Please format the following text into clean, organized markdown notes.

Focus on:
- Creating clear section headers
- Organizing bullet points and lists
- Highlighting key information with appropriate emphasis
- Maintaining the original meaning and structure
- Making the content easy to read and reference
- Using consistent formatting for similar elements

Text to format:
"""
        else:  # clean/default
            prompt = """Please format the following text into clean, well-structured markdown.

Focus on:
- Creating appropriate headings and structure
- Organizing content logically
- Formatting lists, emphasis, and other elements properly
- Improving readability while maintaining the original meaning
- Using proper markdown syntax
- Ensuring consistent formatting throughout

Text to format:
"""
        
        return prompt + "\n\n" + raw_text
    
    def validate_config(self) -> Dict[str, str]:
        """Validate Anthropic-specific configuration."""
        errors = super().validate_config()
        
        if not self.api_key:
            errors['api_key'] = "API key is required for Anthropic service"
        
        if not self.model:
            errors['model'] = "Model is required for Anthropic service"
        
        # Validate model name format
        if self.model and not any(self.model.startswith(prefix) for prefix in ['claude-3', 'claude-2']):
            errors['model'] = f"Invalid Anthropic model: {self.model}"
        
        # Validate token limits
        if self.max_tokens and (self.max_tokens < 1 or self.max_tokens > 8192):
            errors['max_tokens'] = "max_tokens must be between 1 and 8192"
        
        # Validate temperature
        if self.temperature and (self.temperature < 0 or self.temperature > 1):
            errors['temperature'] = "temperature must be between 0 and 1"
        
        return errors
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get Anthropic service information."""
        info = super().get_service_info()
        info.update({
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'api_key_configured': bool(self.api_key),
            'client_initialized': bool(self._client)
        })
        return info
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Anthropic API.
        
        Returns:
            Dict with test results
        """
        if not self._client:
            return {
                'success': False,
                'error': 'Client not initialized',
                'details': 'Anthropic client could not be initialized'
            }
        
        try:
            # Simple test message
            response = self._client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Hello"
                }]
            )
            
            return {
                'success': True,
                'model': self.model,
                'response_length': len(response.content[0].text),
                'message': 'Connection successful'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': f'Failed to connect to Anthropic API with model {self.model}'
            }

# Example usage and testing
if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration
    config = {
        'display_name': 'Claude Haiku',
        'type': 'anthropic',
        'api_key': os.environ.get('ANTHROPIC_API_KEY', 'test_key'),
        'model': 'claude-3-haiku-20240307',
        'is_htr_capable': True,
        'is_formatting_capable': True,
        'max_tokens': 1000,
        'temperature': 0.1
    }
    
    service = AnthropicService('test_anthropic', config)
    
    print(f"Service info: {service.get_service_info()}")
    print(f"Available: {service.is_available()}")
    print(f"Validation errors: {service.validate_config()}")
    
    # Test formatting (if API key is available)
    if service.is_available():
        try:
            test_text = """MEETING NOTES
            - Discussed project timeline
            - Budget approved: $50,000
            - Next meeting: Friday 2pm
            ACTION ITEMS
            - John: prepare presentation
            - Sarah: review contracts"""
            
            formatted = service.format_markdown(test_text)
            print(f"Formatted text:\n{formatted}")
            
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("Service not available for testing")