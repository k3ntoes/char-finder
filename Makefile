.PHONY: help install run dev test clean

help:
	@echo "Available commands:"
	@echo "  make install - Install dependencies using uv sync"
	@echo "  make run     - Run the FastAPI application server"
	@echo "  make dev     - Alias for make run"
	@echo "  make test    - Run pytest test suite"
	@echo "  make clean   - Clean Python cache and build artifacts"

install:
	uv sync

run dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=. uv run pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
