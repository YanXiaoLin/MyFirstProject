# Makefile for iwhereGIS Grid Engine

.PHONY: help install dev-install test lint format clean build run docker-build docker-run docker-stop

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PROJECT_NAME := iwheregis-grid-engine
DOCKER_IMAGE := iwheregis/grid-engine
DOCKER_TAG := latest

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run code linters"
	@echo "  make format        - Format code with black"
	@echo "  make clean         - Clean up temporary files"
	@echo "  make run           - Run the application"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with Docker Compose"
	@echo "  make docker-stop   - Stop Docker containers"

# Installation
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev-install: install
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true
	$(PIP) install pytest pytest-cov pytest-flask black flake8 mypy pylint

# Testing
test:
	@echo "Running unit tests..."
	pytest tests/ -v --cov=airspace_grid --cov=utils --cov-report=term-missing

test-coverage:
	@echo "Running tests with coverage report..."
	pytest tests/ -v --cov=airspace_grid --cov=utils --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

test-integration:
	@echo "Running integration tests..."
	pytest tests/test_api.py -v

# Code quality
lint:
	@echo "Running linters..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	pylint --exit-zero airspace_grid utils
	mypy --ignore-missing-imports airspace_grid utils

format:
	@echo "Formatting code with black..."
	black .

check-format:
	@echo "Checking code format..."
	black --check .

# Cleaning
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf logs/*.log

# Running
run:
	@echo "Starting application..."
	$(PYTHON) app.py

run-dev:
	@echo "Starting in development mode..."
	export APP_ENV=development && \
	export DEBUG=True && \
	$(PYTHON) app.py

run-prod:
	@echo "Starting in production mode..."
	export APP_ENV=production && \
	gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 30 app:app

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

docker-shell:
	@echo "Opening shell in app container..."
	docker-compose exec app /bin/bash

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

# Database
db-migrate:
	@echo "Running database migrations..."
	# Add migration commands when database is implemented

db-seed:
	@echo "Seeding database..."
	# Add seed commands when database is implemented

# Deployment
deploy-dev:
	@echo "Deploying to development..."
	# Add development deployment commands

deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands

deploy-prod:
	@echo "Deploying to production..."
	@echo "WARNING: This will deploy to production. Continue? [y/N]"
	@read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		echo "Deploying to production..."; \
		# Add production deployment commands
	else \
		echo "Deployment cancelled."; \
	fi

# Monitoring
logs:
	@echo "Showing application logs..."
	tail -f logs/app.log

metrics:
	@echo "Showing application metrics..."
	# Add metrics commands

# Documentation
docs:
	@echo "Building documentation..."
	sphinx-build -b html docs/ docs/_build/

docs-serve:
	@echo "Serving documentation..."
	cd docs/_build && python -m http.server 8080

# Utilities
version:
	@echo "iwhereGIS Grid Engine v2.0.0"

check-env:
	@echo "Checking environment..."
	@command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed."; exit 1; }
	@echo "Environment check passed!"

init: check-env dev-install
	@echo "Project initialized successfully!"
	@echo "Run 'make run' to start the application"