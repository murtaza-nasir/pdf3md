# Ink2MD Testing Framework

This directory contains comprehensive integration and API tests for the Ink2MD application.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_integration.py         # Integration tests for core functionality
├── test_api_live.py           # Live API endpoint tests
└── README.md                  # This file
```

## Test Categories

### Integration Tests (`test_integration.py`)

Tests core application functionality with mocked dependencies:

- **Configuration Management**: Config loading, validation, environment variables
- **Database Operations**: CRUD operations, conversion history, statistics
- **AI Service Factory**: Provider management, service creation, capabilities
- **Conversion Pipeline**: End-to-end PDF conversion with AI enhancement
- **Error Handling**: Exception handling, retry logic, fallback mechanisms

### Live API Tests (`test_api_live.py`)

Tests against a running Ink2MD server instance:

- **Health Endpoint**: Server status and component health
- **Configuration API**: GET/POST config operations
- **History API**: Conversion history retrieval
- **Providers API**: AI provider status and capabilities
- **Statistics API**: Conversion statistics
- **Conversion API**: PDF upload and processing

## Running Tests

### Option 1: Using the Test Runner (Recommended)

```bash
# Run all integration tests
python ink2md/run_tests.py

# Run with pytest (if available)
python ink2md/run_tests.py --pytest

# Check dependencies only
python ink2md/run_tests.py --check-deps

# Skip cleanup after tests
python ink2md/run_tests.py --no-cleanup
```

### Option 2: Direct Test Execution

```bash
# Run integration tests directly
python ink2md/tests/test_integration.py

# Run live API tests (requires running server)
python ink2md/tests/test_api_live.py

# Run with pytest
cd ink2md && python -m pytest tests/ -v
```

### Option 3: Using pytest directly

```bash
cd ink2md
pip install pytest
python -m pytest tests/ -v --tb=short
```

## Test Environment

The test runner automatically sets up a clean test environment:

- **Test Directories**: `./test_config`, `./test_data`
- **Environment Variables**: Test-specific configuration
- **Database**: Isolated test database
- **Cleanup**: Automatic cleanup after tests

## Prerequisites

### Required Dependencies

```bash
pip install flask pymupdf4llm pymupdf requests pytest
```

### For Live API Tests

1. Start the Ink2MD server:
   ```bash
   # Using Docker
   ./docker-start.sh dev
   
   # Or directly
   cd ink2md && python app.py
   ```

2. Run the live API tests:
   ```bash
   python ink2md/tests/test_api_live.py
   ```

## Test Configuration

### pytest.ini

The `pytest.ini` file configures pytest behavior:

- Test discovery patterns
- Output formatting
- Test markers for categorization
- Warning suppression

### Test Markers

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.unit` - Unit tests

## Mocking Strategy

Integration tests use mocking for external dependencies:

- **PDF Processing**: Mock `pymupdf` and `pymupdf4llm`
- **AI Services**: Use built-in mock AI service
- **File System**: Temporary files and directories
- **Network**: No external API calls in integration tests

## Test Data

Tests use minimal, programmatically generated test data:

- **PDF Files**: Minimal valid PDF content
- **Configuration**: Test-specific config values
- **Database Records**: Synthetic conversion records

## Continuous Integration

The test framework is designed for CI/CD integration:

- **Exit Codes**: Proper exit codes for success/failure
- **Output Format**: Clear, parseable output
- **Environment**: Self-contained test environment
- **Dependencies**: Explicit dependency checking

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the correct directory
2. **Database Errors**: Check write permissions for test directories
3. **API Test Failures**: Ensure server is running on correct port
4. **Timeout Errors**: Increase timeout values for slow systems

### Debug Mode

For detailed debugging, run tests with verbose output:

```bash
python ink2md/run_tests.py --pytest
python -m pytest tests/ -v -s --tb=long
```

### Manual Testing

For manual verification:

1. Start the server: `./docker-start.sh dev`
2. Check health: `curl http://localhost:6201/api/health`
3. Run API tests: `python ink2md/tests/test_api_live.py`

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate test markers
3. Mock external dependencies
4. Include both positive and negative test cases
5. Update this README if adding new test categories

## Test Coverage

Current test coverage includes:

- ✅ Configuration management
- ✅ Database operations
- ✅ AI service integration
- ✅ Conversion pipeline
- ✅ API endpoints
- ✅ Error handling
- ✅ Retry mechanisms

Future test additions:

- [ ] Frontend integration tests
- [ ] Performance tests
- [ ] Security tests
- [ ] Load tests