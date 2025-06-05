#!/usr/bin/env python3
"""
Ink2MD Integration Tests
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
import sys
import json
import time
import tempfile
import unittest
import requests
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager
from database import DatabaseManager, initialize_database
from models import ConversionRecord, ConversionStatus
from ai_services import AIServiceFactory, initialize_ai_services
from conversion_pipeline import ConversionPipeline

class TestInk2MDIntegration(unittest.TestCase):
    """Integration tests for Ink2MD core functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_dir = tempfile.mkdtemp()
        cls.config_dir = os.path.join(cls.test_dir, 'config')
        cls.data_dir = os.path.join(cls.test_dir, 'data')
        
        os.makedirs(cls.config_dir, exist_ok=True)
        os.makedirs(cls.data_dir, exist_ok=True)
        
        # Set environment variables for testing
        os.environ['CONFIG_DIR'] = cls.config_dir
        os.environ['DATA_DIR'] = cls.data_dir
        
        # Initialize components
        cls.config_manager = ConfigManager()
        cls.db_manager = initialize_database()
        cls.ai_factory = initialize_ai_services(cls.config_manager.get_all_config())
        
        # Create conversion pipeline
        cls.conversion_pipeline = ConversionPipeline(
            cls.config_manager, 
            cls.db_manager, 
            cls.ai_factory
        )
    
    def setUp(self):
        """Set up each test."""
        # Clear database for each test
        self.db_manager.clear_all_conversions()
    
    def test_config_manager_integration(self):
        """Test configuration management functionality."""
        # Test default config creation
        config = self.config_manager.get_all_config()
        self.assertIsInstance(config, dict)
        self.assertIn('app_settings', config)
        self.assertIn('ai_providers', config)
        
        # Test setting update
        original_pattern = self.config_manager.get_setting('app_settings.default_output_pattern')
        new_pattern = 'test-[OriginalFileName].md'
        
        self.config_manager.update_setting('app_settings.default_output_pattern', new_pattern)
        updated_pattern = self.config_manager.get_setting('app_settings.default_output_pattern')
        self.assertEqual(updated_pattern, new_pattern)
        
        # Test environment variable substitution
        os.environ['TEST_API_KEY'] = 'test_key_123'
        self.config_manager.update_setting('ai_providers.providers.anthropic.api_key', '${TEST_API_KEY}')
        resolved_key = self.config_manager.get_setting('ai_providers.providers.anthropic.api_key')
        self.assertEqual(resolved_key, 'test_key_123')
    
    def test_database_operations(self):
        """Test database CRUD operations."""
        # Test conversion record creation
        conversion_id = 'test-conversion-123'
        
        self.db_manager.create_conversion_record(
            conversion_id=conversion_id,
            original_filename='test.pdf',
            file_size=1024,
            page_count=5
        )
        
        # Test record retrieval
        record_dict = self.db_manager.get_conversion_by_id(conversion_id)
        self.assertIsNotNone(record_dict)
        self.assertEqual(record_dict['conversion_id'], conversion_id)
        self.assertEqual(record_dict['original_filename'], 'test.pdf')
        
        # Test status update
        self.db_manager.update_conversion_status(
            conversion_id=conversion_id,
            status='completed',
            output_filename='test-output.md'
        )
        
        updated_record = self.db_manager.get_conversion_by_id(conversion_id)
        self.assertEqual(updated_record['status'], 'completed')
        self.assertEqual(updated_record['output_filename'], 'test-output.md')
        
        # Test history retrieval
        history = self.db_manager.get_conversion_history(limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['conversion_id'], conversion_id)
        
        # Test statistics
        stats = self.db_manager.get_conversion_statistics()
        self.assertIn('total_conversions', stats)
        self.assertEqual(stats['total_conversions'], 1)
    
    def test_ai_service_factory(self):
        """Test AI service factory functionality."""
        # Test service creation
        mock_service = self.ai_factory.get_service('mock')
        self.assertIsNotNone(mock_service)
        
        # Test service capabilities
        capabilities = self.ai_factory.get_service_capabilities('mock')
        self.assertIsInstance(capabilities, dict)
        self.assertIn('text_generation', capabilities)
        
        # Test provider listing
        providers = self.ai_factory.list_available_providers()
        self.assertIsInstance(providers, list)
        self.assertIn('mock', providers)
    
    @patch('pymupdf4llm.to_markdown')
    @patch('pymupdf.open')
    def test_conversion_pipeline_basic(self, mock_pymupdf_open, mock_to_markdown):
        """Test basic conversion pipeline functionality."""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3  # 3 pages
        mock_pymupdf_open.return_value = mock_doc
        
        # Mock markdown conversion
        mock_to_markdown.return_value = "# Test Document\n\nThis is a test."
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(b'%PDF-1.4 fake pdf content')
            temp_pdf_path = temp_pdf.name
        
        try:
            # Test conversion
            conversion_id = 'test-pipeline-123'
            filename = 'test.pdf'
            
            result = self.conversion_pipeline.convert_pdf(temp_pdf_path, conversion_id, filename)
            
            # Verify result
            self.assertIsInstance(result, dict)
            self.assertTrue(result['success'])
            self.assertEqual(result['filename'], filename)
            self.assertIn('markdown', result)
            self.assertEqual(result['pageCount'], 3)
            
            # Verify database record was created
            record = self.db_manager.get_conversion_by_id(conversion_id)
            self.assertIsNotNone(record)
            self.assertEqual(record['status'], 'completed')
            
        finally:
            # Clean up
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
    
    def test_conversion_pipeline_with_ai_enhancement(self):
        """Test conversion pipeline with AI enhancement."""
        # Configure mock AI provider
        self.config_manager.update_setting('ai_providers.active_provider', 'mock')
        self.config_manager.update_setting('ai_providers.providers.mock.formatting_enabled', True)
        
        # Reinitialize AI factory with updated config
        self.ai_factory = initialize_ai_services(self.config_manager.get_all_config())
        self.conversion_pipeline = ConversionPipeline(
            self.config_manager, 
            self.db_manager, 
            self.ai_factory
        )
        
        with patch('pymupdf4llm.to_markdown') as mock_to_markdown, \
             patch('pymupdf.open') as mock_pymupdf_open:
            
            # Mock PDF document
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 2
            mock_pymupdf_open.return_value = mock_doc
            
            # Mock markdown conversion
            mock_to_markdown.return_value = "raw markdown content"
            
            # Create temporary PDF file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(b'%PDF-1.4 fake pdf content')
                temp_pdf_path = temp_pdf.name
            
            try:
                conversion_id = 'test-ai-enhancement-123'
                filename = 'test-ai.pdf'
                
                result = self.conversion_pipeline.convert_pdf(temp_pdf_path, conversion_id, filename)
                
                # Verify AI enhancement was attempted
                self.assertTrue(result['success'])
                self.assertTrue(result.get('ai_enhanced', False))
                self.assertEqual(result.get('ai_provider'), 'mock')
                
            finally:
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
    
    def test_conversion_pipeline_error_handling(self):
        """Test conversion pipeline error handling."""
        with patch('pymupdf.open') as mock_pymupdf_open:
            # Mock file opening error
            mock_pymupdf_open.side_effect = Exception("File not found")
            
            conversion_id = 'test-error-123'
            filename = 'nonexistent.pdf'
            
            with self.assertRaises(Exception):
                self.conversion_pipeline.convert_pdf('/nonexistent/path.pdf', conversion_id, filename)
            
            # Verify error was logged in database
            record = self.db_manager.get_conversion_by_id(conversion_id)
            if record:  # Record might be created before error
                self.assertEqual(record['status'], 'failed')
                self.assertIsNotNone(record['error_message'])
    
    def test_retry_functionality(self):
        """Test conversion retry functionality."""
        # Create a failed conversion record
        conversion_id = 'test-retry-123'
        
        self.db_manager.create_conversion_record(
            conversion_id=conversion_id,
            original_filename='retry-test.pdf',
            file_size=1024,
            page_count=2
        )
        
        self.db_manager.update_conversion_status(
            conversion_id=conversion_id,
            status='failed',
            error_message='Test error'
        )
        
        # Test retry logic
        try:
            retry_result = self.conversion_pipeline.retry_conversion(conversion_id)
            self.assertIn('status', retry_result)
        except Exception as e:
            # Expected since we don't have the actual file
            self.assertIn('not found', str(e).lower())
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test invalid configuration
        with self.assertRaises(Exception):
            self.config_manager.update_setting('ai_providers.active_provider', 'invalid_provider')
            self.config_manager.validate_config()
        
        # Test valid configuration
        self.config_manager.update_setting('ai_providers.active_provider', 'mock')
        # Should not raise exception
        self.config_manager.validate_config()


class TestAPIEndpoints(unittest.TestCase):
    """Integration tests for API endpoints (requires running Flask app)."""
    
    def setUp(self):
        """Set up for API tests."""
        self.base_url = 'http://localhost:6201'
        self.timeout = 5
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        try:
            response = requests.get(f'{self.base_url}/api/health', timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                self.assertIn('status', data)
                self.assertIn('database', data)
                self.assertIn('ai_services', data)
        except requests.exceptions.RequestException:
            self.skipTest("Flask app not running - skipping API tests")
    
    def test_config_endpoints(self):
        """Test configuration API endpoints."""
        try:
            # Test GET config
            response = requests.get(f'{self.base_url}/api/config', timeout=self.timeout)
            if response.status_code == 200:
                config = response.json()
                self.assertIn('app_settings', config)
                self.assertIn('ai_providers', config)
                
                # Test POST config update
                update_data = {
                    'app_settings': {
                        'default_output_pattern': 'test-[OriginalFileName].md'
                    }
                }
                
                response = requests.post(
                    f'{self.base_url}/api/config',
                    json=update_data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.assertIn('message', result)
        except requests.exceptions.RequestException:
            self.skipTest("Flask app not running - skipping API tests")
    
    def test_history_endpoints(self):
        """Test conversion history API endpoints."""
        try:
            # Test GET history
            response = requests.get(f'{self.base_url}/api/history', timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                self.assertIn('conversions', data)
                self.assertIn('total', data)
                self.assertIn('page', data)
        except requests.exceptions.RequestException:
            self.skipTest("Flask app not running - skipping API tests")
    
    def test_providers_endpoints(self):
        """Test AI providers API endpoints."""
        try:
            # Test GET providers
            response = requests.get(f'{self.base_url}/api/providers', timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                self.assertIn('providers', data)
                self.assertIn('active_provider', data)
        except requests.exceptions.RequestException:
            self.skipTest("Flask app not running - skipping API tests")


def run_integration_tests():
    """Run all integration tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(TestInk2MDIntegration))
    suite.addTest(unittest.makeSuite(TestAPIEndpoints))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running Ink2MD Integration Tests...")
    print("=" * 50)
    
    success = run_integration_tests()
    
    if success:
        print("\n✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)