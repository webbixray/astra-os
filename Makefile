SHELL := /bin/bash

.PHONY: help bootstrap setup dev dev-api dev-web stop test test-api test-web test-e2e test-cov test-load \
        lint lint-api lint-web format format-api typecheck security-scan \
        db-migrate db-upgrade db-downgrade db-seed db-reset db-check \
        docker-up docker-down docker-build docker-logs docker-ps docker-restart docker-clean \
        docker-build-prod docker-up-prod docker-down-prod docker-logs-prod docker-ps-prod docker-test-prod docker-sbom \
        monitoring monitoring-down deploy k8s-deploy k8s-status k8s-logs k8s-delete clean build version check install-hooks

help: ## Show this help
	@echo "Astra OS Commands"; echo "======================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# Setup
bootstrap setup: ## Install deps, create .env, start services
	@cp -n docker/dev/.env .env 2>/dev/null || true
	@pnpm install; cd apps/api && pip install -e ".[dev]" 2>/dev/null || true
	@echo "Run 'make dev' to start."

# Dev
dev: ## Start all dev services
	@docker compose up -d postgres redis temporal; sleep 5; pnpm dev
dev-api: ## Start API only
	@cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
dev-web: ## Start Web only
	@cd apps/web && npm run dev
stop: ## Stop all services
	@docker compose down

# Tests
test: ## All tests
	@pnpm test
test-api: ## API tests
	@cd apps/api && python -m pytest -v --tb=short
test-web: ## Web tests
	@cd apps/web && npx vitest run
test-e2e: ## E2E tests
	@cd apps/web && npx playwright test
test-cov: ## Coverage report
	@cd apps/api && python -m pytest -v --cov=app --cov-report=term --cov-report=html
test-load: ## k6 load tests
	@k6 run tests/load/k6-load-test.js 2>/dev/null || k6 run tests/load/staging-load-test.js

# Code Quality
lint: lint-api lint-web ## Lint all
lint-api: ## Python lint
	@cd apps/api && ruff check .
lint-web: ## TypeScript lint
	@cd apps/web && next lint
format: ## Format code
	@pnpm format
format-api: ## Format Python
	@cd apps/api && ruff format .
typecheck: ## TypeScript checks
	@pnpm typecheck
security-scan: ## Bandit SAST
	@cd apps/api && bandit -r . -f json -o bandit-report.json --skip B101,B601 2>/dev/null || true

# Database
db-migrate: ## New migration
	@cd apps/api && alembic revision --autogenerate -m "$(msg)"
db-upgrade: ## Apply migrations
	@cd apps/api && alembic upgrade head
db-downgrade: ## Rollback last
	@cd apps/api && alembic downgrade -1
db-seed: ## Seed data
	@cd apps/api && python scripts/seed_db.py
db-reset: ## Reset DB
	@cd apps/api && alembic downgrade base && alembic upgrade head
db-check: ## Migration status
	@cd apps/api && alembic current

# Docker Dev
docker-up: ## Start dev stack
	@docker compose up -d
docker-down: ## Stop dev stack
	@docker compose down
docker-build: ## Build dev images
	@docker compose build
docker-logs: ## View logs
	@docker compose logs -f
docker-ps: ## Show containers
	@docker compose ps
docker-restart: ## Restart services
	@docker compose restart
docker-clean: ## Remove volumes
	@docker compose down -v

# Docker Production
docker-build-prod: ## Build production images
	@echo "Building API..." && docker build -t astra-api:latest -f apps/api/Dockerfile .
	@echo "Building Web..." && docker build -t astra-web:latest -f apps/web/Dockerfile .
	@echo "Building Worker..." && docker build -t astra-worker:latest -f apps/api/Dockerfile.worker .
	@echo "✅ Production images built"
docker-up-prod: ## Start production
	@./deploy.sh up
docker-down-prod: ## Stop production
	@./deploy.sh down
docker-logs-prod: ## Production logs
	@./deploy.sh logs $(filter-out $@,$(MAKECMDGOALS))
docker-ps-prod: ## Production status
	@./deploy.sh status
docker-test-prod: ## Build + smoke test
	@echo "=== Production Smoke Test ==="
	@docker build -t astra-api:test -f apps/api/Dockerfile . || exit 1
	@docker run -d --name astra-smoke --rm -e ENVIRONMENT=production -e SECRET_KEY=test123 -p 8001:8000 astra-api:test
	@for i in $$(seq 1 30); do curl -sf http://localhost:8001/api/v1/health/live >/dev/null 2>&1 && echo "✅ Healthy" && break; [ $$i -eq 30 ] && exit 1; sleep 2; done
	@docker stop astra-smoke 2>/dev/null; echo "✅ Passed"
docker-sbom: ## Generate SBOM
	@docker build -t astra-api:sbom -f apps/api/Dockerfile . 2>/dev/null
	@syft astra-api:sbom -o json > sbom-api.json 2>/dev/null || echo "Install syft: brew install syft"
	@echo "sbom-api.json generated"

# Monitoring
monitoring: ## Start Prometheus + Grafana + Loki + Tempo
	@docker compose -f docker/monitoring/docker-compose.full.yml up -d 2>/dev/null || \
	 docker compose -f docker/monitoring/docker-compose.yml up -d
	@echo "Grafana: http://localhost:3001"
monitoring-down: ## Stop monitoring
	@docker compose -f docker/monitoring/docker-compose.full.yml down 2>/dev/null || \
	 docker compose -f docker/monitoring/docker-compose.yml down

# Deploy
deploy: ## Run deploy.sh
	@./deploy.sh $(filter-out $@,$(MAKECMDGOALS))

# Kubernetes
k8s-deploy: ## Deploy to K8s
	@kubectl apply -k k8s/
k8s-status: ## K8s status
	@kubectl get pods -n astra; kubectl get services -n astra
k8s-logs: ## K8s logs
	@kubectl logs -f deployment/astra-api -n astra
k8s-delete: ## Delete K8s deployment
	@kubectl delete -k k8s/

# Utilities
clean: ## Clean artifacts
	@pnpm clean; cd apps/api && rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache *.db coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
build: ## Build packages
	@pnpm build
version: ## Show version
	@node -e "console.log(require('./package.json').version)"
check: lint typecheck test ## Full pre-commit check
install-hooks: ## Install pre-commit
	@pre-commit install --hook-type commit-msg 2>/dev/null; echo "Hooks installed"

# Catch-all for arg targets
%:
	@:
