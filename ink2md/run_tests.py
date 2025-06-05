#!/usr/bin/env python3
"""
Ink2MD Test Runner
Comprehensive test execution script for integration and unit tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_integration_tests():
    """Run integration tests."""
    print("🧪 Running Integration Tests...")
    print("=" * 50)
    
    test_file = Path(__file__).parent / 'tests' / 'test_integration.py'
    
    try:
        result = subprocess.run([
            sys.executable, str(test_file)
        ], capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_pytest_tests():
    """Run tests using pytest if available."""
    print("🧪 Running Tests with pytest...")
    print("=" * 50)
    
    try:
        # Check if pytest is available
        subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                      capture_output=True, check=True)
        
        # Run tests with pytest
        test_dir = Path(__file__).parent / 'tests'
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            str(test_dir), 
            '-v', 
            '--tb=short',
            '--durations=10'
        ], timeout=300)
        
        return result.returncode == 0
    except subprocess.CalledProcessError:
        print("⚠️  pytest not available, falling back to unittest")
        return run_integration_tests()
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking Dependencies...")
    print("=" * 30)
    
    required_modules = [
        'flask',
        'pymupdf4llm', 
        'pymupdf',
        'requests'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - MISSING")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("\n✅ All dependencies available")
    return True

def setup_test_environment():
    """Set up test environment variables."""
    print("🔧 Setting up test environment...")
    
    # Set test-specific environment variables
    test_env = {
        'FLASK_ENV': 'testing',
        'CONFIG_DIR': './test_config',
        'DATA_DIR': './test_data',
        'ANTHROPIC_API_KEY': 'test_key_placeholder',
        'OLLAMA_BASE_URL': 'http://localhost:11434'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    # Create test directories
    os.makedirs('./test_config', exist_ok=True)
    os.makedirs('./test_data', exist_ok=True)
    
    print("✅ Test environment ready")

def cleanup_test_environment():
    """Clean up test environment."""
    print("🧹 Cleaning up test environment...")
    
    import shutil
    
    # Remove test directories
    test_dirs = ['./test_config', './test_data']
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"  Removed {test_dir}")
    
    print("✅ Cleanup complete")

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Ink2MD Test Runner')
    parser.add_argument('--pytest', action='store_true', 
                       help='Use pytest instead of unittest')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup after tests')
    parser.add_argument('--check-deps', action='store_true',
                       help='Only check dependencies')
    
    args = parser.parse_args()
    
    print("🚀 Ink2MD Test Runner")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_deps:
        print("✅ Dependency check complete")
        sys.exit(0)
    
    try:
        # Setup test environment
        setup_test_environment()
        
        # Run tests
        if args.pytest:
            success = run_pytest_tests()
        else:
            success = run_integration_tests()
        
        # Report results
        if success:
            print("\n🎉 All tests passed!")
            exit_code = 0
        else:
            print("\n💥 Some tests failed!")
            exit_code = 1
    
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit_code = 1
    
    finally:
        # Cleanup
        if not args.no_cleanup:
            cleanup_test_environment()
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()