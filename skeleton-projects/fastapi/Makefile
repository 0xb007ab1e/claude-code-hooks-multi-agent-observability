.PHONY: install dev test build clean docker-build docker-run

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=src --cov-report=html

build:
	python setup.py sdist bdist_wheel

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

docker-build:
	docker build -t fastapi-skeleton .

docker-run:
	docker run -p 8000:8000 fastapi-skeleton

lint:
	flake8 src/ tests/
	black --check src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/
