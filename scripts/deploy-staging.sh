#!/bin/bash
# Astra OS v1.1.0 Staging Deployment Script

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "Astra OS v1.1.0 Staging Deployment"
echo "=========================================="

# 1. Create namespaces
log_info "Creating namespaces..."
kubectl create namespace astra-staging --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# 2. Apply ArgoCD Applications
log_info "Applying ArgoCD Staging Applications..."
kubectl apply -f k8s/argocd/applications-staging.yaml

# 3. Wait and verify
log_info "Waiting for deployments..."
sleep 10
kubectl -n astra-staging rollout status deployment/astra-api --timeout=300s
kubectl -n astra-staging rollout status deployment/astra-worker --timeout=300s

# 4. Health checks
log_info "Running health checks..."
sleep 30
API_URL="https://staging-api.astra-os.io"
if curl -f -s "$API_URL/health/live" >/dev/null; then
    log_info "Staging API health check: PASSED"
else
    log_error "Staging API health check: FAILED"
    exit 1
fi

# 5. Run load test
log_info "Running load test..."
if command -v k6 &> /dev/null && [ -f tests/load/staging-load-test.js ]; then
    k6 run tests/load/staging-load-test.js || log_warn "Load test completed with issues"
else
    log_warn "k6 not installed, skipping load test"
fi

log_info "=========================================="
log_info "Staging Deployment Complete!"
log_info "=========================================="
log_info "Staging API: $API_URL"
log_info "Grafana: https://staging-grafana.astra-os.io"
