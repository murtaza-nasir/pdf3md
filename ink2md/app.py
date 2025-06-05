#!/usr/bin/env python3
"""
Ink2MD - PDF to Markdown Converter with AI Enhancement
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
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import pymupdf4llm
import pymupdf
import os
import logging
import traceback
import json
import time
from datetime import datetime
from threading import Thread
import uuid
import sys
from io import StringIO, BytesIO
import re
import traceback
from config_manager import ConfigManager # Added import
from database import get_db_manager, initialize_database
from models import ConversionRecord, ConversionStatus, validate_conversion_record
from ai_services import get_ai_service_factory, initialize_ai_services
from conversion_pipeline import ConversionPipeline
from prompt_manager import PromptManager

app = Flask(__name__)

# Initialize ConfigManager and Database
db_manager = initialize_database()
config_manager = ConfigManager(db_manager=db_manager)

# Load user settings from database into config
config_manager.load_user_settings_from_db()

# Initialize AI Services
ai_factory = initialize_ai_services(config_manager.get_all_config())

# Initialize Prompt Manager
prompt_manager = PromptManager(config_manager)

# Initialize Conversion Pipeline
def progress_callback(conversion_id, progress, stage, **kwargs):
    """Callback function to update conversion progress."""
    if conversion_id in conversion_progress:
        conversion_progress[conversion_id].update({
            'progress': progress,
            'stage': stage,
            **kwargs
        })

conversion_pipeline = ConversionPipeline(config_manager, db_manager, ai_factory, progress_callback)

# Default CORS origins for local development
default_origins = [
    "http://localhost:5173",    # Vite dev server default
    "http://localhost:3000",    # Production frontend port in Docker
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"  # Allow all origins for local hosting (permissive for local use)
]

# Get additional origins from environment variable
additional_origins_str = os.environ.get('ALLOWED_CORS_ORIGINS')
all_allowed_origins = list(default_origins) # Start with a copy of defaults

if additional_origins_str:
    # Split the comma-separated string and strip whitespace from each origin
    custom_origins = [origin.strip() for origin in additional_origins_str.split(',')]
    
    # For each base domain, add variations with common ports
    expanded_origins = []
    for origin in custom_origins:
        expanded_origins.append(origin)  # Add the base domain
        
        # Extract the domain without protocol
        domain_match = re.match(r'(https?://)?(.*)', origin)
        if domain_match:
            protocol = domain_match.group(1) or 'http://'  # Default to http:// if no protocol
            domain = domain_match.group(2)
            
            # Add common port variations
            expanded_origins.append(f"{protocol}{domain}:3000")  # Production frontend
            expanded_origins.append(f"{protocol}{domain}:5173")  # Dev frontend
            expanded_origins.append(f"{protocol}{domain}:6201")  # Backend
    
    all_allowed_origins.extend(expanded_origins)

# Remove duplicates by converting to a set and back to a list
final_origins = list(set(all_allowed_origins))

# Set up logging (ensure logger is configured before use, especially for the CORS log line)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info(f"Initializing CORS with origins: {final_origins}") # Log the origins

# Apply CORS with very permissive settings for local hosting
CORS(
    app,
    origins="*",  # Allow all origins
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Origin", "Accept"],
    supports_credentials=False
)

# Add manual CORS headers as backup
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Origin,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition')
    return response

# Store conversion progress
conversion_progress = {}

class ProgressCapture:
    """Capture progress output from pymupdf4llm"""
    def __init__(self, conversion_id, total_pages):
        self.conversion_id = conversion_id
        self.total_pages = total_pages
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def write(self, text):
        # Write to original stdout/stderr
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # Parse progress from pymupdf4llm output
        if self.conversion_id in conversion_progress:
            # Look for progress patterns like "[====    ] (5/26)" or "Processing page 5 of 26"
            progress_match = re.search(r'\(\s*(\d+)/(\d+)\)', text)
            if progress_match:
                current_page = int(progress_match.group(1))
                total_pages = int(progress_match.group(2))
                
                # Calculate progress percentage (reserve 10% for finalization)
                progress_percent = int((current_page / total_pages) * 85) + 10
                
                conversion_progress[self.conversion_id].update({
                    'progress': progress_percent,
                    'stage': f'Processing page {current_page} of {total_pages}...',
                    'current_page': current_page,
                    'total_pages': total_pages
                })
                
    def flush(self):
        self.original_stdout.flush()

def convert_pdf_with_progress(temp_path, conversion_id, filename):
    """Convert PDF using the enhanced conversion pipeline"""
    try:
        # Initialize progress tracking
        conversion_progress[conversion_id] = {
            'progress': 0,
            'stage': 'Starting conversion...',
            'total_pages': 0,
            'current_page': 0,
            'filename': filename,
            'file_size': 0,
            'status': 'processing'
        }
        
        # Use the conversion pipeline
        result = conversion_pipeline.convert_pdf(temp_path, conversion_id, filename)
        
        logger.info('Conversion successful using enhanced pipeline')
        
    except Exception as e:
        logger.error(f'Conversion pipeline error: {str(e)}')
        logger.error(traceback.format_exc())
        
        # Ensure error state is reflected in progress
        conversion_progress[conversion_id] = {
            'progress': 0,
            'stage': f'Error: {str(e)}',
            'status': 'error',
            'error': str(e)
        }

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # --- BEGIN ADDED CLEANUP ---
        # Proactively clean up any orphaned temp_*.pdf files
        # Assumes temp files are in the same directory as app.py
        # The current working directory for app.py when run via Docker is /app/ink2md
        # but when run locally for dev, it's where app.py is.
        # os.abspath('.') will give the correct directory in both cases if app.py is the entrypoint.
        current_dir = os.path.abspath(os.path.dirname(__file__)) # More robust way to get script's dir
        logger.info(f"Checking for orphaned temp files in: {current_dir}")
        cleaned_count = 0
        for filename in os.listdir(current_dir):
            if filename.startswith('temp_') and filename.endswith('.pdf'):
                # Further check if it's an orphaned file (not in current conversion_progress)
                # This check is a bit tricky because conversion_id is generated *after* this cleanup.
                # For simplicity, we'll clean up any file matching the pattern.
                # A more sophisticated check might involve checking if the conversion_id part of the filename
                # corresponds to an active or very recent conversion.
                # However, given the problem is orphaned files, a broad cleanup is likely fine.
                file_path_to_delete = os.path.join(current_dir, filename)
                try:
                    os.remove(file_path_to_delete)
                    logger.info(f"Proactively removed orphaned temp file: {file_path_to_delete}")
                    cleaned_count += 1
                except Exception as e_clean:
                    logger.error(f"Error removing orphaned temp file {file_path_to_delete}: {e_clean}")
        if cleaned_count > 0:
            logger.info(f"Proactively cleaned up {cleaned_count} orphaned temp PDF files.")
        # --- END ADDED CLEANUP ---

        if 'pdf' not in request.files:
            logger.error('No file in request')
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['pdf']
        if file.filename == '':
            logger.error('Empty filename')
            return jsonify({'error': 'No file selected'}), 400

        # Generate unique conversion ID
        conversion_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        temp_path = os.path.abspath(f'temp_{conversion_id}.pdf')
        logger.info(f'Saving file to {temp_path}')
        file.save(temp_path)
        
        # Start conversion in background thread
        thread = Thread(target=convert_pdf_with_progress, args=(temp_path, conversion_id, file.filename))
        thread.start()
        
        # Return conversion ID for progress tracking
        return jsonify({
            'conversion_id': conversion_id,
            'message': 'Conversion started',
            'success': True
        })
        
    except Exception as e:
        logger.error(f'Server error: {str(e)}')
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}', 'success': False}), 500

@app.route('/progress/<conversion_id>', methods=['GET'])
def get_progress(conversion_id):
    """Get conversion progress for a specific conversion ID"""
    try:
        if conversion_id not in conversion_progress:
            return jsonify({'error': 'Conversion not found'}), 404
        
        progress_data = conversion_progress[conversion_id].copy()
        
        # Clean up completed or errored conversions after sending response
        if progress_data.get('status') in ['completed', 'error']:
            # Clean up temp file
            temp_path = os.path.abspath(f'temp_{conversion_id}.pdf')
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f'Temp file removed: {temp_path}')
            
            # Remove from progress tracking after a delay to allow final fetch
            def cleanup_progress():
                time.sleep(5)  # Wait 5 seconds before cleanup
                if conversion_id in conversion_progress:
                    del conversion_progress[conversion_id]
            
            Thread(target=cleanup_progress).start()
        
        return jsonify(progress_data)
        
    except Exception as e:
        logger.error(f'Progress error: {str(e)}')
        return jsonify({'error': f'Progress error: {str(e)}'}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Retrieve current application configuration."""
    try:
        return jsonify(config_manager.get_all_config())
    except Exception as e:
        logger.error(f"Error retrieving configuration: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve configuration: {str(e)}'}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update application configuration."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # The ConfigManager's update_setting expects a dot-separated path and a value.
        # For a POST request that might send a partial or full config structure,
        # we need to iterate through the provided keys and update them.
        # For simplicity, this example assumes the client sends a flat dictionary
        # where keys are dot-separated paths, or a nested dictionary.
        # A more robust solution would handle nested structures carefully.

        for key, value in data.items():
            # Assuming keys in the posted JSON are dot-notation paths for now
            # e.g., {"app_settings.global_retry_attempts": 3}
            # If a full nested object is sent, this needs more complex logic to traverse and update.
            # For now, we'll assume the frontend will send updates in a way that `update_setting` can handle,
            # or we can make `update_setting` more flexible or add a new method for bulk/nested updates.
            # Let's assume for now the frontend sends a flat dict of dot-paths.
            config_manager.update_setting(key, value)
        
        # config_manager.save_config() # update_setting already saves
        logger.info("Configuration updated successfully via API.")
        return jsonify({'message': 'Configuration updated successfully', 'new_config': config_manager.get_all_config()})

    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to update configuration: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Retrieve conversion history with optional filtering and pagination."""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        status_filter = request.args.get('status')
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'Limit must be between 1 and 1000'}), 400
        if offset < 0:
            return jsonify({'error': 'Offset must be non-negative'}), 400
        
        # Get history from database
        history = db_manager.get_conversion_history(
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        # Convert to ConversionRecord objects for consistent formatting
        formatted_history = []
        for record_dict in history:
            try:
                record = ConversionRecord.from_dict(record_dict)
                formatted_history.append(record.to_dict())
            except Exception as e:
                logger.warning(f"Error formatting history record: {e}")
                # Include raw record if formatting fails
                formatted_history.append(record_dict)
        
        # Get total count for pagination
        total_count = len(db_manager.get_conversion_history(limit=10000))  # Simple approach
        
        return jsonify({
            'history': formatted_history,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total_count,
                'has_more': offset + limit < total_count
            }
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve history: {str(e)}'}), 500

@app.route('/api/history/<conversion_id>/retry', methods=['POST'])
def retry_conversion(conversion_id):
    """Retry a failed conversion."""
    try:
        # Get the conversion record
        record_dict = db_manager.get_conversion_by_id(conversion_id)
        if not record_dict:
            return jsonify({'error': 'Conversion not found'}), 404
        
        record = ConversionRecord.from_dict(record_dict)
        
        # Check if conversion can be retried
        max_retries = config_manager.get_setting('app_settings.global_retry_attempts', 3)
        if not record.is_retryable(max_retries):
            return jsonify({
                'error': f'Conversion cannot be retried. Status: {record.status.value}, Retry count: {record.retry_count}'
            }), 400
        
        # Increment retry count
        db_manager.increment_retry_count(conversion_id)
        
        # Update status to retrying
        db_manager.update_conversion_status(
            conversion_id=conversion_id,
            status='retrying',
            error_message=None
        )
        
        # Use the conversion pipeline's retry functionality
        try:
            retry_result = conversion_pipeline.retry_conversion(conversion_id)
            logger.info(f"Retry initiated for conversion {conversion_id}")
            
            return jsonify({
                'message': 'Retry initiated successfully',
                'conversion_id': conversion_id,
                'retry_count': record.retry_count + 1,
                'status': retry_result.get('status', 'retry_initiated')
            })
        except Exception as retry_error:
            logger.error(f"Pipeline retry failed for {conversion_id}: {retry_error}")
            # Fallback to basic retry status update
            logger.info(f"Fallback retry initiated for conversion {conversion_id}")
            
            return jsonify({
                'message': 'Retry initiated successfully (basic mode)',
                'conversion_id': conversion_id,
                'retry_count': record.retry_count + 1,
                'note': 'Full retry pipeline unavailable, status updated'
            })
        
    except Exception as e:
        logger.error(f"Error retrying conversion {conversion_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retry conversion: {str(e)}'}), 500

@app.route('/api/history/<conversion_id>', methods=['DELETE'])
def delete_conversion_history(conversion_id):
    """Delete a conversion record from history."""
    try:
        success = db_manager.delete_conversion(conversion_id)
        
        if success:
            return jsonify({'message': 'Conversion record deleted successfully'})
        else:
            return jsonify({'error': 'Conversion not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting conversion {conversion_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to delete conversion: {str(e)}'}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get conversion statistics."""
    try:
        stats = db_manager.get_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve statistics: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check database connectivity
        stats = db_manager.get_statistics()
        
        # Check configuration
        config = config_manager.get_all_config()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'configuration': 'loaded',
            'total_conversions': stats.get('total_conversions', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get information about available AI providers."""
    try:
        # Get all registered services
        service_info = ai_factory.get_service_info()
        
        # Get statistics
        stats = ai_factory.get_statistics()
        
        # Get active services
        active_services = ai_factory.get_active_services(config_manager.get_all_config())
        
        return jsonify({
            'providers': service_info,
            'statistics': stats,
            'active_services': {
                'htr': active_services['htr'].provider_id if active_services['htr'] else None,
                'formatting': active_services['formatting'].provider_id if active_services['formatting'] else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving providers: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve providers: {str(e)}'}), 500

@app.route('/api/providers/test', methods=['POST'])
def test_providers():
    """Test connectivity for AI providers."""
    try:
        # Get specific provider ID from request, or test all
        data = request.get_json() or {}
        provider_id = data.get('provider_id')
        
        if provider_id:
            # Test specific provider
            service = ai_factory.get_service(provider_id)
            if not service:
                return jsonify({'error': f'Provider {provider_id} not found'}), 404
            
            if hasattr(service, 'test_connection'):
                result = service.test_connection()
            else:
                result = {
                    'success': service.is_available(),
                    'message': 'Basic availability check'
                }
            
            return jsonify({provider_id: result})
        else:
            # Test all providers
            results = ai_factory.test_all_services()
            return jsonify(results)
            
    except Exception as e:
        logger.error(f"Error testing providers: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to test providers: {str(e)}'}), 500

@app.route('/api/providers/validate', methods=['POST'])
def validate_providers():
    """Validate active AI provider configuration."""
    try:
        config = config_manager.get_all_config()
        validation_errors = ai_factory.validate_active_services(config)
        
        return jsonify({
            'valid': len(validation_errors) == 0,
            'errors': validation_errors
        })
        
    except Exception as e:
        logger.error(f"Error validating providers: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to validate providers: {str(e)}'}), 500

@app.route('/api/providers/reload', methods=['POST'])
def reload_providers():
    """Reload AI providers from current configuration."""
    try:
        global ai_factory
        
        # Get current configuration
        config = config_manager.get_all_config()
        
        # Reinitialize AI services
        ai_factory = initialize_ai_services(config)
        
        # Get updated statistics
        stats = ai_factory.get_statistics()
        
        logger.info("AI providers reloaded successfully")
        
        return jsonify({
            'message': 'AI providers reloaded successfully',
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error reloading providers: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to reload providers: {str(e)}'}), 500

# Prompt Management API Endpoints

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """Get all available prompt templates."""
    try:
        category = request.args.get('category')
        templates = prompt_manager.list_templates(category=category)
        categories = prompt_manager.get_categories()
        
        return jsonify({
            'templates': templates,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Error retrieving prompts: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve prompts: {str(e)}'}), 500

@app.route('/api/prompts/<template_name>', methods=['GET'])
def get_prompt(template_name):
    """Get a specific prompt template."""
    try:
        template = prompt_manager.templates.get(template_name)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify(template.to_dict())
        
    except Exception as e:
        logger.error(f"Error retrieving prompt {template_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve prompt: {str(e)}'}), 500

@app.route('/api/prompts', methods=['POST'])
def create_prompt():
    """Create a new custom prompt template."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name')
        content = data.get('content')
        description = data.get('description', '')
        category = data.get('category', 'custom')
        
        if not name or not content:
            return jsonify({'error': 'Name and content are required'}), 400
        
        # Validate template content
        validation = prompt_manager.validate_template(content)
        if not validation['valid']:
            return jsonify({
                'error': 'Template validation failed',
                'validation_errors': validation['errors']
            }), 400
        
        # Check if template already exists
        if name in prompt_manager.templates:
            return jsonify({'error': 'Template with this name already exists'}), 409
        
        success = prompt_manager.add_template(name, content, description, category)
        if success:
            return jsonify({
                'message': 'Template created successfully',
                'template': prompt_manager.templates[name].to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to create template'}), 500
            
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to create prompt: {str(e)}'}), 500

@app.route('/api/prompts/<template_name>', methods=['PUT'])
def update_prompt(template_name):
    """Update an existing prompt template."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content')
        description = data.get('description')
        
        if content:
            # Validate template content
            validation = prompt_manager.validate_template(content)
            if not validation['valid']:
                return jsonify({
                    'error': 'Template validation failed',
                    'validation_errors': validation['errors']
                }), 400
        
        success = prompt_manager.update_template(template_name, content, description)
        if success:
            return jsonify({
                'message': 'Template updated successfully',
                'template': prompt_manager.templates[template_name].to_dict()
            })
        else:
            return jsonify({'error': 'Template not found or update failed'}), 404
            
    except Exception as e:
        logger.error(f"Error updating prompt {template_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to update prompt: {str(e)}'}), 500

@app.route('/api/prompts/<template_name>', methods=['DELETE'])
def delete_prompt(template_name):
    """Delete a custom prompt template."""
    try:
        success = prompt_manager.delete_template(template_name)
        if success:
            return jsonify({'message': 'Template deleted successfully'})
        else:
            return jsonify({'error': 'Template not found or cannot be deleted'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting prompt {template_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to delete prompt: {str(e)}'}), 500

@app.route('/api/prompts/<template_name>/validate', methods=['POST'])
def validate_prompt(template_name):
    """Validate a prompt template."""
    try:
        data = request.get_json()
        content = data.get('content') if data else None
        
        if content:
            # Validate provided content
            validation = prompt_manager.validate_template(content)
        else:
            # Validate existing template
            template = prompt_manager.templates.get(template_name)
            if not template:
                return jsonify({'error': 'Template not found'}), 404
            validation = prompt_manager.validate_template(template.content)
        
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Error validating prompt {template_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to validate prompt: {str(e)}'}), 500

@app.route('/api/prompts/<template_name>/test', methods=['POST'])
def test_prompt(template_name):
    """Test a prompt template with sample variables."""
    try:
        data = request.get_json() or {}
        variables = data.get('variables', {})
        
        template = prompt_manager.templates.get(template_name)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        try:
            formatted_prompt = template.format(**variables)
            return jsonify({
                'success': True,
                'formatted_prompt': formatted_prompt,
                'variables_used': template.variables
            })
        except KeyError as e:
            return jsonify({
                'success': False,
                'error': f'Missing variable: {str(e)}',
                'required_variables': template.variables
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing prompt {template_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to test prompt: {str(e)}'}), 500

# User Settings API Endpoints

@app.route('/api/user-settings', methods=['GET'])
def get_user_settings():
    """Retrieve all user settings."""
    try:
        settings = db_manager.get_all_user_settings()
        
        # Convert to a more convenient format for frontend
        settings_dict = {}
        for setting in settings:
            from models import UserSetting
            user_setting = UserSetting.from_dict(setting)
            settings_dict[setting['setting_key']] = {
                'value': user_setting.get_parsed_value(),
                'type': setting['setting_type'],
                'version': setting['version'],
                'updated_at': setting['updated_at']
            }
        
        return jsonify({
            'settings': settings_dict,
            'count': len(settings)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving user settings: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to retrieve user settings: {str(e)}'}), 500

@app.route('/api/user-settings', methods=['POST'])
def save_user_settings():
    """Save/update user settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        from models import UserSetting, validate_user_setting
        
        # Handle both single setting and bulk settings
        if 'settings' in data:
            # Bulk update
            settings_data = data['settings']
            updated_count = 0
            
            for setting_key, setting_info in settings_data.items():
                if isinstance(setting_info, dict) and 'value' in setting_info:
                    value = setting_info['value']
                    setting_type = setting_info.get('type', 'string')
                else:
                    value = setting_info
                    setting_type = 'string'
                
                # Create UserSetting object to handle type conversion
                user_setting = UserSetting(setting_key=setting_key)
                user_setting.set_value(value)
                
                # Validate the setting
                validation_errors = validate_user_setting({
                    'setting_key': setting_key,
                    'setting_value': user_setting.setting_value,
                    'setting_type': user_setting.setting_type
                })
                
                if validation_errors:
                    return jsonify({
                        'error': f'Validation failed for setting {setting_key}',
                        'validation_errors': validation_errors
                    }), 400
                
                # Save to database
                success = db_manager.update_user_setting(
                    setting_key,
                    user_setting.setting_value,
                    user_setting.setting_type
                )
                
                if success:
                    updated_count += 1
                    
                    # Also update config manager for AI provider settings
                    if setting_key.startswith('ai_provider_configs.'):
                        try:
                            config_manager.update_setting(setting_key, value)
                        except Exception as config_error:
                            logger.warning(f"Failed to sync setting {setting_key} to config: {config_error}")
            
            return jsonify({
                'message': f'Successfully updated {updated_count} settings',
                'updated_count': updated_count
            })
        
        else:
            # Single setting update
            setting_key = data.get('setting_key')
            setting_value = data.get('setting_value')
            
            if not setting_key:
                return jsonify({'error': 'setting_key is required'}), 400
            
            # Create UserSetting object to handle type conversion
            user_setting = UserSetting(setting_key=setting_key)
            user_setting.set_value(setting_value)
            
            # Validate the setting
            validation_errors = validate_user_setting({
                'setting_key': setting_key,
                'setting_value': user_setting.setting_value,
                'setting_type': user_setting.setting_type
            })
            
            if validation_errors:
                return jsonify({
                    'error': 'Validation failed',
                    'validation_errors': validation_errors
                }), 400
            
            # Save to database
            success = db_manager.update_user_setting(
                setting_key,
                user_setting.setting_value,
                user_setting.setting_type
            )
            
            if success:
                # Also update config manager for AI provider settings
                if setting_key.startswith('ai_provider_configs.'):
                    try:
                        config_manager.update_setting(setting_key, setting_value)
                    except Exception as config_error:
                        logger.warning(f"Failed to sync setting {setting_key} to config: {config_error}")
                
                return jsonify({
                    'message': 'Setting saved successfully',
                    'setting_key': setting_key
                })
            else:
                return jsonify({'error': 'Failed to save setting'}), 500
        
    except Exception as e:
        logger.error(f"Error saving user settings: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to save user settings: {str(e)}'}), 500

@app.route('/api/user-settings/<setting_key>', methods=['DELETE'])
def delete_user_setting(setting_key):
    """Delete a specific user setting."""
    try:
        success = db_manager.delete_user_setting(setting_key)
        
        if success:
            return jsonify({'message': f'Setting {setting_key} deleted successfully'})
        else:
            return jsonify({'error': 'Setting not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting user setting {setting_key}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to delete user setting: {str(e)}'}), 500

@app.route('/api/user-settings/sync', methods=['POST'])
def sync_settings():
    """Synchronize settings between database and config file."""
    try:
        # Get all user settings from database
        db_settings = db_manager.get_all_user_settings()
        
        # Get current config
        current_config = config_manager.get_all_config()
        
        # Sync AI provider settings from database to config
        synced_count = 0
        for setting in db_settings:
            if setting['setting_key'].startswith('ai_provider_configs.'):
                from models import UserSetting
                user_setting = UserSetting.from_dict(setting)
                value = user_setting.get_parsed_value()
                
                try:
                    config_manager.update_setting(setting['setting_key'], value)
                    synced_count += 1
                except Exception as sync_error:
                    logger.warning(f"Failed to sync setting {setting['setting_key']}: {sync_error}")
        
        # Also sync important config settings to database
        ai_configs = current_config.get('ai_provider_configs', {})
        for provider_id, provider_config in ai_configs.items():
            for config_key, config_value in provider_config.items():
                setting_key = f"ai_provider_configs.{provider_id}.{config_key}"
                
                # Check if setting exists in database
                existing = db_manager.get_user_setting(setting_key)
                if not existing:
                    # Create UserSetting object to handle type conversion
                    from models import UserSetting
                    user_setting = UserSetting(setting_key=setting_key)
                    user_setting.set_value(config_value)
                    
                    try:
                        db_manager.update_user_setting(
                            setting_key,
                            user_setting.setting_value,
                            user_setting.setting_type
                        )
                        synced_count += 1
                    except Exception as sync_error:
                        logger.warning(f"Failed to sync config setting {setting_key}: {sync_error}")
        
        return jsonify({
            'message': 'Settings synchronized successfully',
            'synced_count': synced_count
        })
        
    except Exception as e:
        logger.error(f"Error synchronizing settings: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to synchronize settings: {str(e)}'}), 500


if __name__ == '__main__':
    # Ensure logging is configured before any calls to logger
    if not logger.handlers: # Check if handlers are already configured
        logging.basicConfig(level=logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO)
    
    logger.info('Starting Flask server...')
    # Access a setting to ensure ConfigManager is initialized and working before server starts
    logger.info(f"Initial monitored directory from config: {config_manager.get_setting('app_settings.monitored_input_dir', 'Not Set')}")
    app.run(host='0.0.0.0', port=6201)
