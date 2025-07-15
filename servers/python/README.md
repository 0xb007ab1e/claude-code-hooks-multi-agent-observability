# Python Server Implementation

![Coverage](https://img.shields.io/badge/coverage-76.59%25-orange)

This directory contains the Python implementation of the observability server using FastAPI.

## Features

- FastAPI framework with async/await support
- WebSocket support for real-time events
- SQLite database integration with SQLAlchemy
- OpenAPI/Swagger documentation
- Pydantic models for data validation
- Comprehensive test coverage
- Error handling and logging

## Getting Started

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Run in development mode
uvicorn main:app --reload

# Run in production
uvicorn main:app --host 0.0.0.0 --port 4000
```

## Testing

This project uses pytest for testing with comprehensive coverage reporting.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests with XML coverage report
pytest --cov=src --cov-report=xml
```

### Test Structure

```
tests/
├── conftest.py                    # Shared test configuration
├── test_app.py                    # Application-level tests
├── test_config/
│   └── test_settings.py          # Configuration tests
├── test_database/
│   └── test_events_db.py         # Database tests
├── test_error_handling/
│   └── test_exceptions.py        # Error handling tests
├── test_models/
│   └── test_hook_event.py        # Model tests
├── test_routes/
│   ├── test_events.py            # Event API tests
│   ├── test_health.py            # Health check tests
│   ├── test_themes.py            # Theme API tests
│   └── test_websockets.py        # WebSocket tests
└── unit/
    ├── conftest.py               # Unit test configuration
    ├── test_config.py            # Unit config tests
    ├── test_database.py          # Unit database tests
    ├── test_main.py              # Unit main module tests
    ├── test_models.py            # Unit model tests
    └── test_services.py          # Unit service tests
```

### Coverage Reports

After running tests with coverage, you can view the reports:

```bash
# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
# Windows: start htmlcov\index.html

# View coverage summary in terminal
coverage report

# Generate coverage badge
coverage-badge -o coverage.svg
```

### Current Coverage: 76.59%

- `src/config.py`: 100.00%
- `src/database.py`: 96.90%
- `src/models.py`: 100.00%
- `src/services.py`: 100.00%
- `src/main.py`: 43.54% (main improvement area)
- `src/utils.py`: 0.00% (needs test coverage)

## Development

### Code Quality

```bash
# Run linting (if configured)
flake8 src/

# Run type checking (if configured)
mypy src/

# Format code (if configured)
black src/ tests/
```

### API Documentation

Once the server is running, you can access:

- **Interactive API docs (Swagger)**: http://localhost:4000/docs
- **Alternative API docs (ReDoc)**: http://localhost:4000/redoc
- **OpenAPI schema**: http://localhost:4000/openapi.json
