#!/usr/bin/env python3
"""
Ink2MD Prompt Management System
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

import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Default prompt templates
DEFAULT_PROMPT_TEMPLATES = {
    "htr_default": """Please analyze this image and extract all visible text, including handwritten text.

Focus on:
- Handwritten notes and annotations
- Printed text
- Mathematical equations or formulas
- Dates, numbers, and measurements
- Any other textual content

Please provide the extracted text in a clear, organized format. If the text appears to be structured (like notes, lists, or sections), please maintain that structure in your output.""",

    "htr_academic": """Please extract all text from this academic document image with high precision.

Focus on:
- Academic content including citations, references, and footnotes
- Mathematical equations, formulas, and scientific notation
- Tables, figures, and captions
- Handwritten annotations and margin notes
- Preserve academic formatting and structure

Maintain the original academic structure and formatting in your text extraction.""",

    "htr_handwritten": """Please focus specifically on extracting handwritten text from this image.

Pay special attention to:
- Handwritten notes, whether in cursive or print
- Personal annotations and comments
- Sketches or diagrams with text labels
- Margin notes and corrections
- Any handwritten mathematical expressions

Please be patient with unclear handwriting and provide your best interpretation while noting any uncertain text with [unclear] markers.""",

    "htr_forms": """Please extract text from this form or structured document.

Focus on:
- Form field labels and their corresponding values
- Checkboxes and their status (checked/unchecked)
- Tables with headers and data
- Signatures and handwritten entries
- Document structure and layout

Organize the extracted information to preserve the form's logical structure.""",

    "formatting_clean": """Please format the following text into clean, well-structured markdown.

Focus on:
- Creating appropriate headings and structure
- Organizing content logically
- Formatting lists, emphasis, and other elements properly
- Improving readability while maintaining the original meaning
- Using proper markdown syntax
- Ensuring consistent formatting throughout

Text to format:
{content}""",

    "formatting_academic": """Please format the following text into clean, well-structured markdown suitable for academic or professional documents.

Focus on:
- Creating clear headings and subheadings with proper hierarchy
- Organizing content into logical sections
- Formatting lists, equations, and citations properly
- Maintaining academic tone and structure
- Adding appropriate emphasis and formatting
- Preserving references and footnotes
- Using proper markdown syntax for academic content

Text to format:
{content}""",

    "formatting_notes": """Please format the following text into clean, organized markdown notes.

Focus on:
- Creating clear section headers
- Organizing bullet points and lists
- Highlighting key information with appropriate emphasis
- Maintaining the original meaning and structure
- Making the content easy to read and reference
- Using consistent formatting for similar elements

Text to format:
{content}""",

    "vlm_direct": """Please convert this document page directly into clean, well-structured markdown.

Analyze the entire page and:
- Extract all visible text accurately
- Preserve the document's structure and hierarchy
- Format headings, lists, and emphasis appropriately
- Handle tables, figures, and captions properly
- Maintain the logical flow of information
- Use proper markdown syntax throughout

Provide only the markdown content without additional commentary.""",

    "vlm_academic": """Please convert this academic document page into properly formatted markdown.

Analyze the page and:
- Extract all text including citations, references, and footnotes
- Preserve academic structure and hierarchy
- Format mathematical equations and scientific notation
- Handle tables, figures, and captions appropriately
- Maintain proper academic formatting conventions
- Use appropriate markdown syntax for academic content

Provide clean, academic-quality markdown output.""",

    "vlm_handwritten": """Please convert this handwritten document into clean markdown format.

Carefully analyze the handwriting and:
- Extract all handwritten text with high accuracy
- Interpret unclear handwriting to the best of your ability
- Preserve the structure and organization of the notes
- Format lists, headings, and emphasis appropriately
- Note any uncertain text with [unclear] markers
- Maintain the logical flow of the handwritten content

Provide well-structured markdown that accurately represents the handwritten content."""
}

class PromptTemplate:
    """Represents a single prompt template with metadata."""
    
    def __init__(self, name: str, content: str, description: str = "", 
                 category: str = "general", variables: List[str] = None):
        self.name = name
        self.content = content
        self.description = description
        self.category = category
        self.variables = variables or []
        self.created_at = datetime.now().isoformat()
        self.modified_at = self.created_at
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        try:
            return self.content.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable {e} for template {self.name}")
            return self.content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization."""
        return {
            'name': self.name,
            'content': self.content,
            'description': self.description,
            'category': self.category,
            'variables': self.variables,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create template from dictionary."""
        template = cls(
            name=data['name'],
            content=data['content'],
            description=data.get('description', ''),
            category=data.get('category', 'general'),
            variables=data.get('variables', [])
        )
        template.created_at = data.get('created_at', template.created_at)
        template.modified_at = data.get('modified_at', template.modified_at)
        return template

class PromptManager:
    """
    Manages prompt templates for AI services.
    
    Provides functionality to:
    - Load and save prompt templates
    - Format templates with variables
    - Customize prompts for different use cases
    - Organize prompts by category
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.templates: Dict[str, PromptTemplate] = {}
        self.custom_templates_path = self._get_custom_templates_path()
        self._load_templates()
    
    def _get_custom_templates_path(self) -> str:
        """Get path for custom templates file."""
        config_dir = os.path.dirname(self.config_manager.config_path)
        return os.path.join(config_dir, 'prompt_templates.json')
    
    def _load_templates(self):
        """Load templates from default and custom sources."""
        # Load default templates
        for name, content in DEFAULT_PROMPT_TEMPLATES.items():
            category = self._get_category_from_name(name)
            description = self._get_description_from_name(name)
            variables = self._extract_variables(content)
            
            self.templates[name] = PromptTemplate(
                name=name,
                content=content,
                description=description,
                category=category,
                variables=variables
            )
        
        # Load custom templates if they exist
        if os.path.exists(self.custom_templates_path):
            try:
                with open(self.custom_templates_path, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                
                for template_data in custom_data.get('templates', []):
                    template = PromptTemplate.from_dict(template_data)
                    self.templates[template.name] = template
                
                logger.info(f"Loaded {len(custom_data.get('templates', []))} custom templates")
                
            except Exception as e:
                logger.error(f"Failed to load custom templates: {e}")
    
    def _get_category_from_name(self, name: str) -> str:
        """Determine category from template name."""
        if name.startswith('htr_'):
            return 'htr'
        elif name.startswith('formatting_'):
            return 'formatting'
        elif name.startswith('vlm_'):
            return 'vlm'
        else:
            return 'general'
    
    def _get_description_from_name(self, name: str) -> str:
        """Generate description from template name."""
        descriptions = {
            'htr_default': 'Default handwritten text recognition prompt',
            'htr_academic': 'HTR prompt optimized for academic documents',
            'htr_handwritten': 'HTR prompt focused on handwritten content',
            'htr_forms': 'HTR prompt for forms and structured documents',
            'formatting_clean': 'Clean markdown formatting prompt',
            'formatting_academic': 'Academic document formatting prompt',
            'formatting_notes': 'Note-style formatting prompt',
            'vlm_direct': 'Direct vision-to-markdown conversion prompt',
            'vlm_academic': 'Academic document vision processing prompt',
            'vlm_handwritten': 'Handwritten document vision processing prompt'
        }
        return descriptions.get(name, f'Custom prompt: {name}')
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        import re
        variables = re.findall(r'\{(\w+)\}', content)
        return list(set(variables))
    
    def get_prompt(self, template_name: str, **variables) -> str:
        """
        Get formatted prompt with variable substitution.
        
        Args:
            template_name: Name of the template to use
            **variables: Variables to substitute in the template
            
        Returns:
            Formatted prompt string
        """
        template = self.templates.get(template_name)
        if not template:
            logger.warning(f"Template '{template_name}' not found, using default")
            return self._get_fallback_prompt(template_name, **variables)
        
        return template.format(**variables)
    
    def _get_fallback_prompt(self, template_name: str, **variables) -> str:
        """Get fallback prompt when template is not found."""
        if template_name.startswith('htr_'):
            return DEFAULT_PROMPT_TEMPLATES['htr_default']
        elif template_name.startswith('formatting_'):
            content = variables.get('content', '[No content provided]')
            return DEFAULT_PROMPT_TEMPLATES['formatting_clean'].format(content=content)
        elif template_name.startswith('vlm_'):
            return DEFAULT_PROMPT_TEMPLATES['vlm_direct']
        else:
            return "Please process this content appropriately."
    
    def add_template(self, name: str, content: str, description: str = "", 
                    category: str = "custom") -> bool:
        """
        Add a new custom template.
        
        Args:
            name: Template name
            content: Template content
            description: Template description
            category: Template category
            
        Returns:
            True if template was added successfully
        """
        try:
            variables = self._extract_variables(content)
            template = PromptTemplate(
                name=name,
                content=content,
                description=description,
                category=category,
                variables=variables
            )
            
            self.templates[name] = template
            self._save_custom_templates()
            
            logger.info(f"Added custom template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add template {name}: {e}")
            return False
    
    def update_template(self, name: str, content: str = None, 
                       description: str = None) -> bool:
        """
        Update an existing template.
        
        Args:
            name: Template name
            content: New content (optional)
            description: New description (optional)
            
        Returns:
            True if template was updated successfully
        """
        template = self.templates.get(name)
        if not template:
            logger.warning(f"Template '{name}' not found for update")
            return False
        
        try:
            if content is not None:
                template.content = content
                template.variables = self._extract_variables(content)
            
            if description is not None:
                template.description = description
            
            template.modified_at = datetime.now().isoformat()
            
            # Only save if it's a custom template
            if template.category == 'custom' or name not in DEFAULT_PROMPT_TEMPLATES:
                self._save_custom_templates()
            
            logger.info(f"Updated template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template {name}: {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a custom template.
        
        Args:
            name: Template name
            
        Returns:
            True if template was deleted successfully
        """
        if name in DEFAULT_PROMPT_TEMPLATES:
            logger.warning(f"Cannot delete default template: {name}")
            return False
        
        if name not in self.templates:
            logger.warning(f"Template '{name}' not found for deletion")
            return False
        
        try:
            del self.templates[name]
            self._save_custom_templates()
            
            logger.info(f"Deleted template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template {name}: {e}")
            return False
    
    def _save_custom_templates(self):
        """Save custom templates to file."""
        try:
            # Get only custom templates (not defaults)
            custom_templates = [
                template.to_dict() 
                for template in self.templates.values()
                if template.name not in DEFAULT_PROMPT_TEMPLATES
            ]
            
            data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'templates': custom_templates
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.custom_templates_path), exist_ok=True)
            
            with open(self.custom_templates_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(custom_templates)} custom templates")
            
        except Exception as e:
            logger.error(f"Failed to save custom templates: {e}")
    
    def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """
        List available templates.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of template information dictionaries
        """
        templates = []
        for template in self.templates.values():
            if category is None or template.category == category:
                templates.append({
                    'name': template.name,
                    'description': template.description,
                    'category': template.category,
                    'variables': template.variables,
                    'is_custom': template.name not in DEFAULT_PROMPT_TEMPLATES
                })
        
        return sorted(templates, key=lambda x: (x['category'], x['name']))
    
    def get_categories(self) -> List[str]:
        """Get list of available template categories."""
        categories = set(template.category for template in self.templates.values())
        return sorted(list(categories))
    
    def validate_template(self, content: str) -> Dict[str, Any]:
        """
        Validate template content.
        
        Args:
            content: Template content to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'variables': []
        }
        
        try:
            # Extract variables
            variables = self._extract_variables(content)
            result['variables'] = variables
            
            # Check for common issues
            if len(content.strip()) < 10:
                result['warnings'].append('Template content is very short')
            
            if not content.strip():
                result['errors'].append('Template content cannot be empty')
                result['valid'] = False
            
            # Test formatting with dummy variables
            test_vars = {var: f'[{var}]' for var in variables}
            try:
                content.format(**test_vars)
            except Exception as e:
                result['errors'].append(f'Template formatting error: {e}')
                result['valid'] = False
            
        except Exception as e:
            result['errors'].append(f'Template validation error: {e}')
            result['valid'] = False
        
        return result

# Example usage and testing
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with a mock config manager
    class MockConfigManager:
        def __init__(self):
            self.config_path = '/tmp/test_config.json'
    
    config_manager = MockConfigManager()
    prompt_manager = PromptManager(config_manager)
    
    # Test getting prompts
    print("=== Testing Prompt Retrieval ===")
    htr_prompt = prompt_manager.get_prompt('htr_default')
    print(f"HTR Default Prompt: {htr_prompt[:100]}...")
    
    formatting_prompt = prompt_manager.get_prompt('formatting_clean', content="Test content")
    print(f"Formatting Prompt: {formatting_prompt[:100]}...")
    
    # Test listing templates
    print("\n=== Available Templates ===")
    templates = prompt_manager.list_templates()
    for template in templates:
        print(f"- {template['name']} ({template['category']}): {template['description']}")
    
    # Test adding custom template
    print("\n=== Testing Custom Template ===")
    custom_content = "Please extract text from this {document_type} with focus on {focus_area}."
    success = prompt_manager.add_template(
        name="custom_test",
        content=custom_content,
        description="Test custom template",
        category="custom"
    )
    print(f"Added custom template: {success}")
    
    # Test validation
    print("\n=== Testing Template Validation ===")
    validation = prompt_manager.validate_template(custom_content)
    print(f"Validation result: {validation}")
    
    # Test formatted custom template
    custom_prompt = prompt_manager.get_prompt(
        'custom_test', 
        document_type='academic paper',
        focus_area='mathematical equations'
    )
    print(f"Custom prompt: {custom_prompt}")