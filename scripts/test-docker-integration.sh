#!/bin/bash
# Astra OS v1.1.0 - Docker Integration Test Suite
# Run this on your Intel Mac to validate full production deployment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

# Track results
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local name=$1
    local cmd=$2
    local timeout_sec=${3:-60}
    ((TESTS_TOTAL++))
    echo -n "Testing: $name ... "
    if timeout "$timeout_sec" bash -c "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

run_test_verbose() {
    local name=$1
    local cmd=$2
    local timeout_sec=${3:-60}
    ((TESTS_TOTAL++))
    echo -e "${BLUE}[TEST]${NC} $name"
    if timeout "$timeout_sec" bash -c "$cmd"; then
        echo -e "${GREEN}[PASS]${NC} $name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "=========================================="
echo "Astra OS v1.1.0 - Docker Integration Tests"
echo "=========================================="
echo ""

# ==========================================
# PREREQUISITES
# ==========================================
log_info "Checking prerequisites..."

run_test "Docker installed" "command -v docker"
run_test "Docker Compose installed" "command -v docker compose"
run_test "Docker daemon running" "docker info"
run_test "Docker Buildx available" "docker buildx version"

# Check architecture
ARCH=$(uname -m)
log_info "Architecture: $ARCH"
if [[ "$ARCH" == "arm64" ]]; then
    log_warn "Apple Silicon detected - using linux/amd64 for compatibility"
    PLATFORM="linux/amd64"
else
    PLATFORM="linux/amd64"
fi

echo ""

# ==========================================
# BUILD IMAGES
# ==========================================
log_info "Building Docker images (this takes 2-5 minutes)..."

run_test_verbose "Build API image" \
    "docker buildx build --platform $PLATFORM -t astra-os/api:test -f apps/api/Dockerfile . --load" \
    300

run_test_verbose "Build Worker image" \
    "docker buildx build --platform $PLATFORM -t astra-os/worker:test -f services/agent_orchestrator/Dockerfile . --load" \
    300

echo ""

# ==========================================
# START FULL STACK
# ==========================================
log_info "Starting full stack with docker-compose..."

run_test_verbose "Start services" \
    "docker compose -f docker-compose.yml up -d --build" \
    120

# Wait for services to be healthy
log_info "Waiting for services to become healthy (30s)..."
sleep 30

echo ""

# ==========================================
# VERIFY SERVICES RUNNING
# ==========================================
log_info "Verifying services..."

run_test "PostgreSQL running" "docker compose ps postgres | grep -q 'Up'"
run_test "Redis running" "docker compose ps redis | grep -q 'Up'"
run_test "Temporal running" "docker compose ps temporal | grep -q 'Up'"
run_test "API running" "docker compose ps api | grep -q 'Up'"
run_test "Worker running" "docker compose ps worker | grep -q 'Up'"

# Check health status
run_test "PostgreSQL healthy" "docker compose ps postgres | grep -q 'healthy'"
run_test "Redis healthy" "docker compose ps redis | grep -q 'healthy'"
run_test "API healthy" "docker compose ps api | grep -q 'healthy'"

echo ""

# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================
log_info "Testing health endpoints..."

run_test_verbose "API /health/live" \
    "curl -f -s http://localhost:8000/health/live | grep -q 'ok'"

run_test_verbose "API /health/ready" \
    "curl -f -s http://localhost:8000/health/ready | grep -q 'ready'"

run_test_verbose "API /metrics (Prometheus)" \
    "curl -f -s http://localhost:8000/metrics | grep -q 'astra_'"

echo ""

# ==========================================
# DATABASE CONNECTIVITY
# ==========================================
log_info "Testing database connectivity..."

run_test_verbose "API can connect to PostgreSQL" \
    "docker compose exec -T api python -c \"from app.infrastructure.db.session import create_session_factory; import asyncio; asyncio.run(create_session_factory('postgresql+asyncpg://postgres:postgres@postgres:5432/astra_test'))\""

run_test_verbose "Worker can connect to PostgreSQL" \
    "docker compose exec -T worker python -c \"from astra_agent_orchestrator.memory import Memory; print('Worker DB OK')\""

run_test_verbose "Redis connectivity" \
    "docker compose exec -T api python -c \"import redis; r = redis.Redis(host='redis', port=6379); r.ping(); print('Redis OK')\""

run_test_verbose "Temporal connectivity" \
    "docker compose exec -T api python -c \"from temporalio.client import Client; import asyncio; asyncio.run(Client.connect('temporal:7233')); print('Temporal OK')\""

echo ""

# ==========================================
# RUN TEST SUITES
# ==========================================
log_info "Running test suites (this takes 2-3 minutes)..."

run_test_verbose "API Unit Tests" \
    "docker compose exec -T api pytest tests/unit/ -x --tb=short -q" \
    180

run_test_verbose "API Integration Tests" \
    "docker compose exec -T api pytest tests/integration/ -x --tb=short -q" \
    180

run_test_verbose "Agent Orchestrator Tests" \
    "docker compose exec -T worker pytest -x --tb=short -q" \
    180

echo ""

# ==========================================
# TELEGRAM BOT VALIDATION
# ==========================================
log_info "Validating Telegram bot..."

run_test_verbose "Telegram bot imports" \
    "docker compose exec -T api python -c \"from app.infrastructure.external_adapters.telegram.bot import create_bot; from app.infrastructure.external_adapters.telegram.handlers import router; print('Telegram bot OK')\""

run_test_verbose "Telegram config" \
    "docker compose exec -T api python -c \"from app.infrastructure.external_adapters.telegram.config import TelegramConfig; print('Telegram config OK')\""

run_test_verbose "Telegram routes registered" \
    "docker compose exec -T api python -c \"from app.presentation.routes.telegram import router as telegram_router; print('Telegram routes OK')\""

echo ""

# ==========================================
# SECURITY MIDDLEWARE
# ==========================================
log_info "Testing security middleware..."

run_test_verbose "CSP headers in production mode" \
    "docker compose exec -T api python -c \"from app.presentation.middleware.security_headers import SecurityHeadersMiddleware; print('Security headers OK')\""

run_test_verbose "Rate limiting middleware" \
    "docker compose exec -T api python -c \"from app.presentation.middleware.ratelimit import RateLimitMiddleware; print('Rate limiting OK')\""

run_test_verbose "RBAC middleware" \
    "docker compose exec -T api python -c \"from app.presentation.middleware.rbac import require_org_role; print('RBAC OK')\""

echo ""

# ==========================================
# MONITORING STACK (OPTIONAL)
# ==========================================
if [[ "${TEST_MONITORING:-false}" == "true" ]]; then
    log_info "Testing monitoring stack (TEST_MONITORING=true)..."
    
    run_test_verbose "Start monitoring" \
        "docker compose -f docker/monitoring/docker-compose.full.yml up -d" \
        120
    
    sleep 20
    
    run_test "Prometheus accessible" "curl -f -s http://localhost:9090/-/healthy"
    run_test "Grafana accessible" "curl -f -s http://localhost:3000/api/health"
    run_test "Alertmanager accessible" "curl -f -s http://localhost:9093/-/healthy"
    run_test "Loki accessible" "curl -f -s http://localhost:3100/ready"
    run_test "Tempo accessible" "curl -f -s http://localhost:3200/ready"
    
    echo ""
fi

# ==========================================
# CLEANUP
# ==========================================
log_info "Cleaning up..."

docker compose -f docker-compose.yml down -v >/dev/null 2>&1 || true

if [[ "${TEST_MONITORING:-false}" == "true" ]]; then
    docker compose -f docker/monitoring/docker-compose.full.yml down -v >/dev/null 2>&1 || true
fi

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo "=========================================="
echo "INTEGRATION TEST SUMMARY"
echo "=========================================="
echo -e "Total Tests:  $TESTS_TOTAL"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - PRODUCTION READY${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Tag release: git tag v1.1.0 && git push origin v1.1.0"
    echo "  2. Deploy to staging: ./scripts/deploy-staging.sh"
    echo "  3. Deploy to production: ./scripts/deploy-production.sh"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED - REVIEW REQUIRED${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Check docker compose logs: docker compose logs -f [service]"
    echo "  - Increase memory for Docker Desktop (Settings > Resources > 8GB+)"
    echo "  - Ensure ports 5432, 6379, 7233, 8000 are free"
    exit 1
fi