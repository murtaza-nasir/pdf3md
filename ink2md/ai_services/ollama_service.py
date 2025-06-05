#!/usr/bin/env python3
"""
Ink2MD Ollama AI Service
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
import requests
import json
import base64
from typing import Dict, Any, Optional, List
import mimetypes
import traceback # Added for detailed exception logging

from .base import AIServiceInterface, AIServiceCapability

logger = logging.getLogger(__name__)

class OllamaService(AIServiceInterface):
    """
    Ollama AI service implementation.
    
    This service provides both HTR (using vision models like LLaVA) and 
    text formatting capabilities (using text models like Mistral) through
    the Ollama local inference server.
    """
    
    def __init__(self, provider_id: str, config: Dict[str, Any]):
        super().__init__(provider_id, config)
        
        # Ollama-specific configuration
        self.api_base_url = config.get('api_base_url', 'http://localhost:11434')
        self.model = config.get('model', 'llava')
        self.timeout = config.get('timeout', 120)  # Longer timeout for local inference
        self.temperature = config.get('temperature', 0.1)
        self.num_predict = config.get('num_predict', 2048)
        
        # Ensure API base URL doesn't end with slash
        self.api_base_url = self.api_base_url.rstrip('/')
        
        logger.info(f"Ollama service '{self.display_name}' initialized with API base URL: {self.api_base_url}, Model: {self.model}")
    
    def is_available(self) -> bool:
        """Check if the Ollama service is available."""
        if not self.enabled:
            return False
        
        try:
            # Test connection to Ollama server
            response = requests.get(
                f"{self.api_base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                # Check if our model is available
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                # Check for exact match or partial match (for model variants)
                model_available = any(
                    self.model in model_name or model_name.startswith(self.model)
                    for model_name in available_models
                )
                
                if not model_available:
                    logger.warning(f"Model {self.model} not found in Ollama. Available: {available_models}")
                    return False
                
                return True
            else:
                logger.warning(f"Ollama server responded with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Cannot connect to Ollama server at {self.api_base_url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False
    
    def _make_ollama_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Ollama API.
        
        Args:
            endpoint: API endpoint (e.g., 'generate', 'chat')
            data: Request payload
            
        Returns:
            Dict: Response data
        """
        url = f"{self.api_base_url}/api/{endpoint}"
        
        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                stream=False
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Ollama request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {str(e)}")
    
    def get_htr_text(self, image_file_path: str, **kwargs) -> str:
        """
        Extract text from an image using Ollama vision model (e.g., LLaVA).
        
        Args:
            image_file_path: Path to the image file
            **kwargs: Additional parameters (custom_prompt, etc.)
        """
        if not self.is_htr_capable:
            raise NotImplementedError("This Ollama service is not configured for HTR")
        
        if not self.is_available():
            raise RuntimeError("Ollama service is not available")
        
        try:
            # Read and encode the image
            with open(image_file_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Custom prompt or default
            custom_prompt = kwargs.get('custom_prompt')
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = """Please analyze this image and extract all visible text, including handwritten text. 

Focus on:
- Handwritten notes and annotations
- Printed text  
- Mathematical equations or formulas
- Dates, numbers, and measurements
- Any other textual content

Please provide the extracted text in a clear, organized format. If the text appears to be structured (like notes, lists, or sections), please maintain that structure in your output."""
            
            # Prepare request data for vision model
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.num_predict
                }
            }
            
            # Make request to Ollama
            response_data = self._make_ollama_request("generate", request_data)
            
            # Extract text from response
            extracted_text = response_data.get('response', '')
            
            if not extracted_text:
                raise RuntimeError("Empty response from Ollama vision model")
            
            logger.info(f"Successfully extracted text from {image_file_path} using Ollama {self.model}")
            return extracted_text
            
        except Exception as e:
            logger.error(f"HTR failed for {image_file_path}: {e}")
            raise RuntimeError(f"Ollama HTR failed: {str(e)}")
    
    def format_markdown(self, raw_text: str, **kwargs) -> str:
        """
        Format raw text into clean markdown using Ollama text model.
        
        Args:
            raw_text: Raw text to format
            **kwargs: Additional parameters (style, custom_prompt, etc.)
        """
        if not self.is_formatting_capable:
            raise NotImplementedError("This Ollama service is not configured for formatting")
        
        if not self.is_available():
            raise RuntimeError("Ollama service is not available")
        
        try:
            # Custom prompt or default
            custom_prompt = kwargs.get('custom_prompt')
            style = kwargs.get('style', 'clean')
            
            if custom_prompt:
                prompt = custom_prompt
            else:
                if style == 'academic':
                    prompt = """Please format the following text into clean, well-structured markdown suitable for academic or professional documents. 

Focus on:
- Creating clear headings and subheadings
- Organizing content into logical sections
- Formatting lists, equations, and citations properly
- Maintaining academic tone and structure
- Adding appropriate emphasis and formatting

Only return the formatted markdown, no additional commentary.

Text to format:
"""
                elif style == 'notes':
                    prompt = """Please format the following text into clean, organized markdown notes.

Focus on:
- Creating clear section headers
- Organizing bullet points and lists
- Highlighting key information
- Maintaining the original meaning and structure
- Making the content easy to read and reference

Only return the formatted markdown, no additional commentary.

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

Only return the formatted markdown, no additional commentary.

Text to format:
"""
            
            # Combine prompt with text
            full_prompt = prompt + "\n\n" + raw_text
            
            # Prepare request data
            request_data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.num_predict
                }
            }
            
            # Make request to Ollama
            response_data = self._make_ollama_request("generate", request_data)
            
            # Extract formatted text
            formatted_text = response_data.get('response', '')
            
            if not formatted_text:
                raise RuntimeError("Empty response from Ollama text model")
            
            logger.info(f"Successfully formatted text using Ollama {self.model} ({len(raw_text)} -> {len(formatted_text)} chars)")
            return formatted_text
            
        except Exception as e:
            logger.error(f"Formatting failed: {e}")
            raise RuntimeError(f"Ollama formatting failed: {str(e)}")
    
    def validate_config(self) -> Dict[str, str]:
        """Validate Ollama-specific configuration."""
        errors = super().validate_config()
        
        if not self.api_base_url:
            errors['api_base_url'] = "API base URL is required for Ollama service"
        
        if not self.model:
            errors['model'] = "Model is required for Ollama service"
        
        # Validate URL format
        if self.api_base_url and not (self.api_base_url.startswith('http://') or self.api_base_url.startswith('https://')):
            errors['api_base_url'] = "API base URL must start with http:// or https://"
        
        # Validate timeout
        if self.timeout and (self.timeout < 1 or self.timeout > 600):
            errors['timeout'] = "timeout must be between 1 and 600 seconds"
        
        # Validate temperature
        if self.temperature and (self.temperature < 0 or self.temperature > 2):
            errors['temperature'] = "temperature must be between 0 and 2"
        
        # Validate num_predict
        if self.num_predict and (self.num_predict < 1 or self.num_predict > 8192):
            errors['num_predict'] = "num_predict must be between 1 and 8192"
        
        return errors
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get Ollama service information."""
        info = super().get_service_info()
        info.update({
            'api_base_url': self.api_base_url,
            'model': self.model,
            'timeout': self.timeout,
            'temperature': self.temperature,
            'num_predict': self.num_predict
        })
        return info
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Ollama server.
        
        Returns:
            Dict with test results
        """
        try:
            logger.info(f"Testing Ollama connection for '{self.display_name}' at {self.api_base_url} with model {self.model}")
            
            # Test server connectivity
            tags_url = f"{self.api_base_url}/api/tags"
            logger.info(f"Attempting to GET {tags_url}")
            response = requests.get(tags_url, timeout=5)
            logger.info(f"GET {tags_url} status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"Ollama server at {self.api_base_url} responded with status {response.status_code} to /api/tags. Response: {response.text}")
                return {
                    'success': False,
                    'error': f'Server responded with status {response.status_code} to /api/tags check.',
                    'details': response.text,
                    'server_url': self.api_base_url,
                    'model_tested': self.model
                }
            
            # Check available models
            models_data = response.json()
            available_models = [model_info['name'] for model_info in models_data.get('models', [])]
            logger.info(f"Available models from {self.api_base_url}: {available_models}")
            
            # Check if our model is available
            model_available = any(
                self.model in model_name or model_name.startswith(self.model.split(':')[0])
                for model_name in available_models
            )
            
            if not model_available:
                logger.warning(f"Model '{self.model}' not found in available models: {available_models}")
                return {
                    'success': False,
                    'error': f"Model '{self.model}' not available on server",
                    'details': f"Available models: {', '.join(available_models)}",
                    'server_url': self.api_base_url,
                    'model': self.model,
                    'available_models': available_models
                }

            logger.info(f"Ollama connection test for '{self.display_name}' successful. Model '{self.model}' is available.")
            return {
                'success': True,
                'server_url': self.api_base_url,
                'model': self.model,
                'available_models': available_models,
                'message': f'Connection successful. Model "{self.model}" is available.'
            }
            
        except requests.exceptions.RequestException as re:
            logger.error(f"Ollama connection test for '{self.display_name}' failed due to RequestException: {str(re)}")
            return {
                'success': False,
                'error': f'RequestException: {str(re)}',
                'details': f'Failed to connect to Ollama server at {self.api_base_url}. Check server URL and network connectivity.',
                'server_url': self.api_base_url,
                'model_tested': self.model
            }
        except Exception as e:
            logger.error(f"Ollama connection test for '{self.display_name}' failed: {str(e)}\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'details': f'An unexpected error occurred while testing connection to Ollama server at {self.api_base_url}. Check logs for details.',
                'server_url': self.api_base_url,
                'model_tested': self.model
            }
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models from Ollama server.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.api_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []

# Example usage and testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration for LLaVA (vision model)
    llava_config = {
        'display_name': 'Ollama LLaVA',
        'type': 'ollama',
        'api_base_url': 'http://localhost:11434',
        'model': 'llava',
        'is_htr_capable': True,
        'is_formatting_capable': False,
        'timeout': 60,
        'temperature': 0.1
    }
    
    # Test configuration for Mistral (text model)
    mistral_config = {
        'display_name': 'Ollama Mistral',
        'type': 'ollama',
        'api_base_url': 'http://localhost:11434',
        'model': 'mistral',
        'is_htr_capable': False,
        'is_formatting_capable': True,
        'timeout': 60,
        'temperature': 0.1
    }
    
    # Test LLaVA service
    llava_service = OllamaService('test_llava', llava_config)
    print(f"LLaVA Service info: {llava_service.get_service_info()}")
    print(f"LLaVA Available: {llava_service.is_available()}")
    
    # Test Mistral service
    mistral_service = OllamaService('test_mistral', mistral_config)
    print(f"Mistral Service info: {mistral_service.get_service_info()}")
    print(f"Mistral Available: {mistral_service.is_available()}")
    
    # Test formatting (if Mistral is available)
    if mistral_service.is_available():
        try:
            test_text = """MEETING NOTES
            - Discussed project timeline
            - Budget approved: $50,000
            - Next meeting: Friday 2pm
            ACTION ITEMS
            - John: prepare presentation
            - Sarah: review contracts"""
            
            formatted = mistral_service.format_markdown(test_text)
            print(f"Formatted text:\n{formatted}")
            
        except Exception as e:
            print(f"Formatting test failed: {e}")
    else:
        print("Mistral service not available for testing")