.PHONY: help dev dev-full install db-init db-test lint clean

help:  ## Show all commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python dependencies
	cd backend && pip install -r requirements.txt

dev:  ## Start backend (SQLite, no Docker) + frontend dev server
	@echo "Starting backend (SQLite mode)..."
	cd backend && DB_TYPE=sqlite REDIS_ENABLED=false uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev

dev-full:  ## Start with Docker (MySQL + Redis + backend)
	docker compose up --build

db-init:  ## Initialize MySQL tables
	@mysql -u root -p < db/init.sql

db-test:  ## Test database connection
	python scripts/test_db.py

lint:  ## Run code checks
	ruff check backend/ scripts/

clean:  ## Clean temp files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."
