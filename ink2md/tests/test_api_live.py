#!/usr/bin/env python3
"""
Ink2MD Live API Tests
Tests that run against a live Ink2MD server instance.
"""

import os
import sys
import json
import time
import requests
import tempfile
from pathlib import Path

class LiveAPITester:
    """Test runner for live API endpoints."""
    
    def __init__(self, base_url='http://localhost:6201', timeout=10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def test_server_connectivity(self):
        """Test if server is reachable."""
        print("🔗 Testing server connectivity...")
        try:
            response = self.session.get(f'{self.base_url}/', timeout=self.timeout)
            if response.status_code == 200:
                print("✅ Server is reachable")
                return True
            else:
                print(f"⚠️  Server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Server not reachable: {e}")
            return False
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        print("🏥 Testing health endpoint...")
        try:
            response = self.session.get(f'{self.base_url}/api/health', timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Database: {data.get('database', {}).get('status', 'unknown')}")
                print(f"   AI Services: {len(data.get('ai_services', {}).get('providers', []))} providers")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_config_endpoints(self):
        """Test configuration endpoints."""
        print("⚙️  Testing configuration endpoints...")
        
        try:
            # Test GET config
            response = self.session.get(f'{self.base_url}/api/config', timeout=self.timeout)
            
            if response.status_code != 200:
                print(f"❌ GET config failed: {response.status_code}")
                return False
            
            config = response.json()
            print("✅ GET config successful")
            print(f"   App settings: {'✅' if 'app_settings' in config else '❌'}")
            print(f"   AI providers: {'✅' if 'ai_providers' in config else '❌'}")
            
            # Test POST config update (non-destructive)
            original_pattern = config.get('app_settings', {}).get('default_output_pattern', '')
            test_pattern = 'test-[OriginalFileName].md'
            
            update_data = {
                'app_settings': {
                    'default_output_pattern': test_pattern
                }
            }
            
            response = self.session.post(
                f'{self.base_url}/api/config',
                json=update_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                print("✅ POST config update successful")
                
                # Restore original pattern
                restore_data = {
                    'app_settings': {
                        'default_output_pattern': original_pattern
                    }
                }
                self.session.post(f'{self.base_url}/api/config', json=restore_data)
                return True
            else:
                print(f"❌ POST config failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Config endpoints error: {e}")
            return False
    
    def test_history_endpoints(self):
        """Test conversion history endpoints."""
        print("📚 Testing history endpoints...")
        
        try:
            # Test GET history
            response = self.session.get(f'{self.base_url}/api/history', timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ GET history successful")
                print(f"   Total conversions: {data.get('total', 0)}")
                print(f"   Current page: {data.get('page', 1)}")
                print(f"   Conversions returned: {len(data.get('conversions', []))}")
                return True
            else:
                print(f"❌ GET history failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ History endpoints error: {e}")
            return False
    
    def test_providers_endpoints(self):
        """Test AI providers endpoints."""
        print("🤖 Testing AI providers endpoints...")
        
        try:
            # Test GET providers
            response = self.session.get(f'{self.base_url}/api/providers', timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ GET providers successful")
                print(f"   Active provider: {data.get('active_provider', 'none')}")
                print(f"   Available providers: {len(data.get('providers', []))}")
                
                for provider in data.get('providers', []):
                    print(f"     - {provider.get('name', 'unknown')}: {provider.get('status', 'unknown')}")
                
                return True
            else:
                print(f"❌ GET providers failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Providers endpoints error: {e}")
            return False
    
    def test_statistics_endpoint(self):
        """Test statistics endpoint."""
        print("📊 Testing statistics endpoint...")
        
        try:
            response = self.session.get(f'{self.base_url}/api/statistics', timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ GET statistics successful")
                print(f"   Total conversions: {data.get('total_conversions', 0)}")
                print(f"   Successful: {data.get('successful_conversions', 0)}")
                print(f"   Failed: {data.get('failed_conversions', 0)}")
                return True
            else:
                print(f"❌ GET statistics failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Statistics endpoint error: {e}")
            return False
    
    def test_conversion_endpoint(self):
        """Test PDF conversion endpoint with a minimal PDF."""
        print("📄 Testing conversion endpoint...")
        
        try:
            # Create a minimal PDF for testing
            minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            
            # Test conversion
            files = {'file': ('test.pdf', minimal_pdf, 'application/pdf')}
            
            response = self.session.post(
                f'{self.base_url}/convert',
                files=files,
                timeout=30  # Longer timeout for conversion
            )
            
            if response.status_code == 200:
                print("✅ Conversion endpoint successful")
                # Note: This might return a conversion ID for async processing
                return True
            else:
                print(f"⚠️  Conversion endpoint returned: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Conversion endpoint error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting Live API Tests")
        print("=" * 50)
        print(f"Target: {self.base_url}")
        print()
        
        tests = [
            self.test_server_connectivity,
            self.test_health_endpoint,
            self.test_config_endpoints,
            self.test_history_endpoints,
            self.test_providers_endpoints,
            self.test_statistics_endpoint,
            self.test_conversion_endpoint
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                print()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                print()
        
        print("=" * 50)
        print(f"📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All API tests passed!")
            return True
        else:
            print("💥 Some API tests failed!")
            return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ink2MD Live API Tester')
    parser.add_argument('--url', default='http://localhost:6201',
                       help='Base URL of Ink2MD server (default: http://localhost:6201)')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Request timeout in seconds (default: 10)')
    
    args = parser.parse_args()
    
    tester = LiveAPITester(args.url, args.timeout)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()