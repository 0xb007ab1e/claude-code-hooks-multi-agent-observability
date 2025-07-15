# Multi-Agent Observability Test Harness

A comprehensive, language-agnostic test suite for the multi-agent observability system that ensures all server implementations meet the required standards.

## Overview

This test harness provides:
- **REST API Testing**: Complete coverage of all API endpoints
- **WebSocket Testing**: Real-time event streaming validation
- **Database Side-effects Testing**: Verification of data persistence
- **Edge Case Testing**: Robust error handling and boundary conditions
- **Performance Testing**: Response time and concurrent request handling
- **Cross-branch Testing**: Ensuring parity between feature branches

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
cd test-harness
python3 -m venv test-env
source test-env/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
python run_e2e_tests.py

# Run specific test suite
python run_e2e_tests.py --test-pattern tests/test_rest_api.py

# Run with custom server
python run_e2e_tests.py --server-image my-server:latest --branch feature/xyz
```

## Test Categories

### 1. REST API Tests (`test_rest_api.py`)
- ✅ Root endpoint verification
- ✅ Event creation and retrieval
- ✅ Recent events with pagination
- ✅ Filter options endpoint
- ✅ Response format validation

### 2. WebSocket Tests (`test_websockets.py`)
- ✅ Connection establishment
- ✅ Initial event streaming
- ✅ Real-time event broadcasting
- ✅ Connection cleanup

### 3. Database Tests (`test_database.py`)
- ✅ SQLite event storage verification
- ✅ PostgreSQL integration (when available)
- ✅ MongoDB integration (when available)
- ✅ Data integrity checks

### 4. Edge Case Tests (`test_edge_cases.py`)
- ✅ Invalid request handling
- ✅ Missing field validation
- ✅ Large payload handling
- ✅ Special character support
- ✅ Concurrent request handling
- ✅ Performance benchmarks
- ✅ CORS header validation

### 5. Themes API Tests (`test_themes_api.py`)
- ✅ Theme creation and validation
- ✅ Theme retrieval and search
- ✅ Theme updates and deletion
- ✅ Import/export functionality
- ✅ Statistics endpoint

## Features

### Comprehensive Coverage
- **25+ test cases** covering all major functionality
- **Edge case testing** for robustness
- **Performance validation** with timing assertions
- **Concurrent request handling** verification

### Language Agnostic
- Tests work with any HTTP/WebSocket server implementation
- Docker containerization support
- Environment variable configuration
- Multiple database backend support

### Reporting
- **HTML reports** with detailed test results
- **JSON reports** for programmatic analysis
- **Branch comparison** reports
- **Performance metrics** tracking

### CI/CD Integration
- **Exit codes** for automated testing
- **Configurable timeouts** and retries
- **Parallel test execution** support
- **Docker orchestration** capabilities

## Architecture

```
test-harness/
├── config/
│   ├── test_config.py          # Test configuration
│   └── __init__.py
├── tests/
│   ├── test_rest_api.py        # REST API tests
│   ├── test_websockets.py      # WebSocket tests
│   ├── test_database.py        # Database tests
│   ├── test_edge_cases.py      # Edge case tests
│   ├── test_themes_api.py      # Themes API tests
│   └── __init__.py
├── utils/
│   ├── docker_utils.py         # Docker management
│   └── __init__.py
├── reports/                    # Test reports
├── run_e2e_tests.py           # Main test runner
├── branch_comparison.py        # Branch comparison tool
├── Dockerfile                  # Test environment container
├── requirements.txt            # Python dependencies
└── pytest.ini                 # Pytest configuration
```

## Configuration

### Environment Variables

```bash
# Server configuration
export SERVER_HOST=localhost
export SERVER_PORT=4000
export SERVER_PROTOCOL=http
export WS_PROTOCOL=ws

# Database configuration
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=testdb
export POSTGRES_USER=user
export POSTGRES_PASSWORD=password

# Test configuration
export REQUEST_TIMEOUT=30
export WEBSOCKET_TIMEOUT=30
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: your_server_image
    ports:
      - "4000:4000"
    depends_on:
      - db
  
  db:
    image: postgres:latest
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
```

## Advanced Usage

### Branch Comparison

```bash
# Compare current branch with main
python branch_comparison.py --branches main feature/new-api --baseline main

# Auto-discover and test all branches
python branch_comparison.py --auto-discover --baseline main
```

### Performance Testing

```bash
# Run performance-focused tests
python run_e2e_tests.py --test-pattern "test_performance or test_concurrent"

# Custom performance thresholds
export REQUEST_TIMEOUT=1  # 1 second max response time
python run_e2e_tests.py
```

### Custom Test Runners

```python
from run_e2e_tests import E2ETestRunner

# Custom test execution
runner = E2ETestRunner(server_image="my-server:v1.0", branch="feature/abc")
runner.run_all_tests()
summary = runner.print_summary()
```

## Test Results

### Sample Output

```
🎯 E2E Test Summary
============================================================
⏱️  Duration: 2.30s
📊 Total Suites: 5
✅ Passed: 4
❌ Failed: 1
📈 Success Rate: 80.0%

📋 Suite Results:
  ✅ PASS REST API Tests (0.35s)
  ✅ PASS WebSocket Tests (0.43s)
  ❌ FAIL Database Tests (0.42s)
  ✅ PASS Edge Case Tests (0.42s)
  ✅ PASS Integration Tests (0.68s)
============================================================
```

### Generated Reports

- **HTML Report**: `reports/report.html` - Interactive test results
- **JSON Report**: `reports/report.json` - Machine-readable results
- **E2E Summary**: `reports/e2e_results_TIMESTAMP.json` - Comprehensive summary
- **Branch Comparison**: `reports/branch_comparison_TIMESTAMP.json` - Cross-branch analysis

## Ensuring Server Compliance

### Mandatory Requirements
All server implementations must:
1. ✅ Return `200 OK` for root endpoint with "Multi-Agent Observability Server" text
2. ✅ Accept POST requests to `/events` with required fields
3. ✅ Return saved event data in JSON format
4. ✅ Provide `/events/recent` endpoint with optional limit parameter
5. ✅ Provide `/events/filter-options` endpoint with filter data
6. ✅ Support WebSocket connections at `/stream` endpoint
7. ✅ Send initial events on WebSocket connection
8. ✅ Broadcast new events to all connected WebSocket clients
9. ✅ Handle CORS preflight requests correctly
10. ✅ Validate required event fields and return appropriate errors

### Optional Features
- Theme management API (full CRUD operations)
- Database persistence (SQLite, PostgreSQL, MongoDB)
- Performance optimizations
- Extended validation rules

## Contributing

### Adding New Tests

1. Create test files in the `tests/` directory
2. Use appropriate pytest marks (`@pytest.mark.rest`, `@pytest.mark.websocket`, etc.)
3. Follow existing naming conventions
4. Include docstrings for all test functions
5. Add configuration options to `test_config.py` if needed

### Test Structure

```python
import pytest
import requests
from config.test_config import config

@pytest.mark.rest
def test_new_endpoint():
    """Test description."""
    response = requests.get(f"{config.server.base_url}/new-endpoint")
    assert response.status_code == 200
    assert response.json() == expected_data
```

## Troubleshooting

### Common Issues

1. **Server not responding**: Check if server is running on configured port
2. **Database connection errors**: Verify database configuration and connectivity
3. **WebSocket connection failures**: Ensure WebSocket endpoint is correctly implemented
4. **Docker permission errors**: Add user to docker group or run with sudo

### Debug Mode

```bash
# Run with verbose output
python run_e2e_tests.py --test-pattern tests/test_rest_api.py -v

# Check server logs
docker logs <container_id>

# Manual endpoint testing
curl -X POST http://localhost:4000/events \
  -H "Content-Type: application/json" \
  -d '{"source_app":"test","session_id":"123","hook_event_type":"PreToolUse","payload":{"tool":"test"}}'
```

## License

This test harness is part of the multi-agent observability system and follows the same licensing terms.
