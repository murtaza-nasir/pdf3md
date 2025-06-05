# Enhanced AI Features for Ink2MD

## Overview

This document describes the enhanced AI capabilities implemented in Ink2MD, including the prompt management system, vision-language model support, and advanced document processing features.

## ✅ Implemented Features

### 1. Prompt Management System (`prompt_manager.py`)

A comprehensive system for managing AI prompts with the following capabilities:

- **Template-based prompts** with variable substitution
- **Categorized templates** (HTR, formatting, VLM)
- **Custom prompt creation** and management
- **Prompt validation** and error checking
- **Fallback mechanisms** for missing templates

#### Default Prompt Templates

**HTR (Handwritten Text Recognition):**
- `htr_default` - General handwritten text extraction
- `htr_academic` - Academic document focused HTR
- `htr_handwritten` - Specialized for handwritten content
- `htr_forms` - Form and structured document HTR

**Formatting:**
- `formatting_clean` - Clean markdown formatting
- `formatting_academic` - Academic document formatting
- `formatting_notes` - Note-style formatting

**VLM (Vision-Language Model):**
- `vlm_direct` - Direct image-to-markdown conversion
- `vlm_academic` - Academic document processing
- `vlm_handwritten` - Handwritten document processing

### 2. Enhanced AI Service Interface

Extended the base AI service interface with new capabilities:

- **VLM Direct Processing** (`process_with_vlm`)
- **Layout Analysis** (`extract_layout`)
- **Enhanced capability detection** (HTR, Formatting, VLM, Layout Analysis, Document Intelligence)

### 3. Enhanced Anthropic Service

Upgraded the Anthropic service with:

- **Vision capabilities** using Claude 3.5 Sonnet
- **Prompt manager integration**
- **Document type detection**
- **Flexible prompt selection**
- **Image processing with base64 encoding**

### 4. Advanced Configuration System

Enhanced configuration with:

- **Processing profiles** (high_quality, balanced, cost_effective)
- **Multiple AI provider support**
- **Prompt template references**
- **Service capability flags**

### 5. Enhanced Conversion Pipeline

Updated the conversion pipeline to support:

- **VLM-first processing** for end-to-end conversion
- **Fallback to traditional pipeline**
- **Document type detection**
- **Prompt manager integration**
- **Processing method tracking**

## Configuration Structure

```json
{
  "active_services": {
    "htr_provider_id": "anthropic_claude_sonnet",
    "formatting_provider_id": "anthropic_claude_sonnet", 
    "vlm_provider_id": "anthropic_claude_sonnet"
  },
  "prompt_templates": {
    "htr_default": "htr_default",
    "formatting_clean": "formatting_clean",
    "vlm_direct": "vlm_direct"
  },
  "processing_profiles": {
    "high_quality": {
      "htr_service": "anthropic_claude_sonnet",
      "formatting_service": "anthropic_claude_sonnet",
      "vlm_service": "anthropic_claude_sonnet",
      "prompt_set": "academic"
    }
  },
  "ai_provider_configs": {
    "anthropic_claude_sonnet": {
      "display_name": "Anthropic (Claude 3.5 Sonnet)",
      "type": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "is_htr_capable": true,
      "is_formatting_capable": true,
      "is_vlm_capable": true,
      "enabled": true
    }
  }
}
```

## Usage Examples

### Using Custom Prompts

```python
from prompt_manager import PromptManager
from config_manager import ConfigManager

config_manager = ConfigManager()
prompt_manager = PromptManager(config_manager)

# Get a formatted prompt
prompt = prompt_manager.get_prompt(
    'htr_academic',
    document_type='research paper',
    focus_area='mathematical equations'
)

# Add custom template
prompt_manager.add_template(
    name="custom_legal",
    content="Extract legal text from this {document_type} focusing on {legal_area}",
    description="Legal document processing",
    category="legal"
)
```

### Using Enhanced AI Services

```python
from ai_services.anthropic_service import AnthropicService

config = {
    'display_name': 'Claude 3.5 Sonnet',
    'type': 'anthropic',
    'api_key': 'your-api-key',
    'model': 'claude-3-5-sonnet-20241022',
    'is_vlm_capable': True
}

service = AnthropicService('claude_sonnet', config)

# Direct VLM processing
markdown = service.process_with_vlm(
    image_path='document.png',
    prompt_template=prompt_manager.get_prompt('vlm_academic'),
    document_type='academic'
)

# Enhanced formatting with prompts
formatted = service.format_markdown(
    raw_text,
    prompt_manager=prompt_manager,
    prompt_template='formatting_academic',
    style='academic'
)
```

## Testing

Run the test suite to verify functionality:

```bash
cd ink2md
python3 test_prompt_manager.py
```

Expected output:
- ✓ All prompt manager tests passed!
- ✓ All configuration tests passed!

## Next Steps

### Phase 2: Additional AI Services

1. **Azure AI Vision Service** - Commercial HTR service
2. **Google Cloud Vision API** - Alternative commercial HTR
3. **AWS Textract** - Document intelligence service
4. **TrOCR Service** - Open-source transformer OCR
5. **Surya OCR Service** - Multilingual document OCR

### Phase 3: Advanced Features

1. **Layout Analysis Models** (LayoutLMv3, DiT)
2. **Quality Metrics** and validation
3. **Batch Processing** capabilities
4. **Performance Optimization**

## API Key Requirements

To use the enhanced features, you'll need:

1. **Anthropic API Key** - For Claude 3.5 Sonnet vision capabilities
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

2. **Install Dependencies**
   ```bash
   pip install anthropic requests
   ```

## Architecture Benefits

1. **Modular Design** - Easy to add new AI services
2. **Flexible Prompts** - Customizable for different document types
3. **Quality-First** - Multiple high-quality AI options
4. **Fallback Support** - Graceful degradation when services unavailable
5. **Configuration-Driven** - Easy to switch between processing profiles

## Performance Characteristics

- **VLM Processing**: Higher quality but slower, best for complex documents
- **Traditional Pipeline**: Faster processing, good for simple documents
- **Prompt Optimization**: Tailored prompts improve output quality significantly
- **Service Selection**: Automatic fallback ensures reliability

This implementation provides a solid foundation for advanced AI-powered document processing while maintaining flexibility and extensibility for future enhancements.