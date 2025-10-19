.PHONY: help install dev-install test lint format clean run-etl run-analytics run-api all

help:
	@echo "Quantitative Finance SQL Warehouse - Available Commands:"
	@echo ""
	@echo "  make install       Install production dependencies"
	@echo "  make dev-install   Install development dependencies"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run code linters"
	@echo "  make format        Format code with black and isort"
	@echo "  make clean         Clean generated files"
	@echo "  make run-etl       Generate and load sample data"
	@echo "  make run-analytics Run analytics queries"
	@echo "  make run-api       Start REST API server"
	@echo "  make all           Run complete pipeline (ETL + Analytics)"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio httpx black flake8 mypy isort

test:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-fast:
	pytest tests/ -v

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	mypy . --ignore-missing-imports

format:
	black .
	isort .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/
	rm -f warehouse.duckdb warehouse.duckdb.wal
	rm -rf logs/*.log

run-etl:
	python etl/generate_data.py
	python etl/load_data.py

run-analytics:
	python analytics/run_analysis.py

run-api:
	python -m api.main

all: run-etl run-analytics
	@echo ""
	@echo "✅ Complete pipeline executed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  - Run 'make run-api' to start the REST API"
	@echo "  - Run 'make test' to execute the test suite"
	@echo "  - Check 'logs/warehouse.log' for detailed logs"

setup: install run-etl
	@echo ""
	@echo "✅ Initial setup complete!"
	@echo ""
	@echo "The database has been created and loaded with sample data."
	@echo "Run 'make run-analytics' or 'make run-api' to get started."


