SHELL := /bin/bash
.PHONY: test coverage install clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run tests"
	@echo "  coverage   - Run tests with coverage (requires 100%)"
	@echo "  clean      - Clean up generated files"
	@echo "  help       - Show this help message"

# Install dependencies
install:
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

# Run tests without coverage
test:
	. venv/bin/activate && PYTHONPATH=. pytest tests/ -v

# Run tests with coverage (100% required)
coverage:
	. venv/bin/activate && PYTHONPATH=. pytest tests/ --cov=src --cov-report=xml --cov-report=html --cov-report=term --cov-fail-under=100

# Clean up generated files
clean:
	rm -rf venv/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
