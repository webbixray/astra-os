.PHONY: help bootstrap setup setup-docker dev dev-api dev-web stop test test-api test-web test-e2e test-cov lint lint-api lint-web format format-api typecheck db-migrate db-upgrade db-downgrade db-seed db-reset docker-up docker-down docker-build docker-logs docker-ps k8s-deploy k8s-status k8s-logs k8s-delete clean build version check

# Default target
help: ## Show this help message
	@echo "Astra OS - Development Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Setup & Installation
# ============================================

bootstrap: ## Full setup from clean clone (installs deps, starts infra, migrates, seeds)
	@make setup

setup: ## Initial project setup (install deps, create .env, start services)
	@echo "Setting up Astra OS..."
	@cp -n docker/dev/.env .env 2>/dev/null || true
	@pnpm install
	@cd apps/api && pip install -e ".[dev]" 2>/dev/null || true
	@echo "Setup complete! Run 'make dev' to start."

setup-docker: ## Setup with Docker (no local Python/Node needed)
	@echo "Setting up Astra OS with Docker..."
	@cp -n docker/dev/.env .env 2>/dev/null || true
	@docker compose up -d postgres redis temporal
	@echo "Infrastructure started. Run 'make dev' to start app services."

# ============================================
# Development
# ============================================

dev: ## Start all development services
	@echo "Starting Astra OS development environment..."
	@docker compose up -d postgres redis temporal
	@echo "Waiting for infrastructure to be ready..."
	@sleep 5
	@pnpm dev

dev-api: ## Start only API server
	@cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Start only Web frontend
	@cd apps/web && npm run dev

stop: ## Stop all running services
	@docker compose down

# ============================================
# Testing
# ============================================

test: ## Run all tests
	@pnpm test

test-api: ## Run API tests
	@cd apps/api && python -m pytest -v --tb=short

test-web: ## Run Web tests
	@cd apps/web && npx vitest run

test-e2e: ## Run E2E tests
	@cd apps/web && npx playwright test

test-cov: ## Run tests with coverage
	@cd apps/api && python -m pytest -v --cov=app --cov-report=term --cov-report=html

# ============================================
# Code Quality
# ============================================

lint: ## Lint all code
	@pnpm lint

lint-api: ## Lint Python code
	@cd apps/api && ruff check .

lint-web: ## Lint TypeScript code
	@cd apps/web && next lint

format: ## Format all code
	@pnpm format

format-api: ## Format Python code
	@cd apps/api && ruff format .

typecheck: ## Type check all code
	@pnpm typecheck

# ============================================
# Database
# ============================================

db-migrate: ## Create a new database migration
	@cd apps/api && alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Apply database migrations
	@cd apps/api && alembic upgrade head

db-downgrade: ## Rollback last migration
	@cd apps/api && alembic downgrade -1

db-seed: ## Seed database with sample data
	@echo "No seed script found. Create apps/api/scripts/seed_db.py to use this target."

db-reset: ## Reset database (drop and recreate)
	@cd apps/api && alembic downgrade base && alembic upgrade head

# ============================================
# Docker
# ============================================

docker-up: ## Start all Docker services
	@docker compose up -d

docker-down: ## Stop all Docker services
	@docker compose down

docker-build: ## Build Docker images
	@docker compose build

docker-logs: ## View Docker logs
	@docker compose logs -f

docker-ps: ## Show running containers
	@docker compose ps

# ============================================
# Kubernetes
# ============================================

k8s-deploy: ## Deploy to Kubernetes
	@kubectl apply -k k8s/

k8s-status: ## Check Kubernetes deployment status
	@kubectl get pods -n astra
	@kubectl get services -n astra

k8s-logs: ## View Kubernetes logs
	@kubectl logs -f deployment/astra-api -n astra

k8s-delete: ## Delete Kubernetes deployment
	@kubectl delete -k k8s/

# ============================================
# Utilities
# ============================================

clean: ## Clean build artifacts
	@pnpm clean
	@cd apps/api && rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache

build: ## Build all packages
	@pnpm build

version: ## Show current version
	@node -e "console.log(require('./package.json').version)"

check: ## Run all checks (lint, typecheck, test)
	@make lint
	@make typecheck
	@make test
