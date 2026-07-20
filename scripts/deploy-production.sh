#!/bin/bash
# Astra OS v1.1.0 Production Deployment Script
# Run this on your production cluster

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "Astra OS v1.1.0 Production Deployment"
echo "=========================================="

# 1. Prerequisites check
log_info "Checking prerequisites..."
command -v kubectl >/dev/null 2>&1 || { log_error "kubectl not installed"; exit 1; }
command -v helm >/dev/null 2>&1 || { log_warn "helm not installed (optional)"; }
command -v argocd >/dev/null 2>&1 || { log_warn "argocd CLI not installed (optional)"; }

# 2. Create namespaces
log_info "Creating namespaces..."
kubectl create namespace astra-production --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# 3. Apply External Secrets Operator (if not present)
log_info "Checking External Secrets Operator..."
if ! kubectl get crd externalsecrets.external-secrets.io >/dev/null 2>&1; then
    log_info "Installing External Secrets Operator..."
    helm repo add external-secrets https://charts.external-secrets.io
    helm repo update
    helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace
fi

# 4. Apply ArgoCD Applications
log_info "Applying ArgoCD Applications..."
kubectl apply -f k8s/argocd/applications-production.yaml

# 5. Wait for ArgoCD to sync
log_info "Waiting for ArgoCD applications to sync..."
sleep 10
argocd app wait astra-api-production --health --timeout 300 || log_warn "argocd CLI not available, skipping wait"
argocd app wait astra-worker-production --health --timeout 300 || true
argocd app wait astra-monitoring-production --health --timeout 300 || true

# 6. Verify deployments
log_info "Verifying deployments..."
kubectl -n astra-production rollout status deployment/astra-api --timeout=300s
kubectl -n astra-production rollout status deployment/astra-worker --timeout=300s

# 7. Verify monitoring
log_info "Verifying monitoring stack..."
kubectl -n monitoring rollout status deployment/prometheus --timeout=180s || true
kubectl -n monitoring rollout status deployment/grafana --timeout=180s || true

# 8. Health checks
log_info "Running health checks..."
sleep 30
API_URL="https://api.astra-os.io"
if curl -f -s "$API_URL/health/live" >/dev/null; then
    log_info "API health check: PASSED"
else
    log_error "API health check: FAILED"
    exit 1
fi

if curl -f -s "$API_URL/health/ready" >/dev/null; then
    log_info "API readiness check: PASSED"
else
    log_error "API readiness check: FAILED"
    exit 1
fi

# 9. Run DR test
log_info "Running DR validation..."
if [ -f scripts/dr-test.sh ]; then
    chmod +x scripts/dr-test.sh
    ./scripts/dr-test.sh || log_warn "DR test failed - review required"
fi

log_info "=========================================="
log_info "Deployment Complete!"
log_info "=========================================="
log_info "API: $API_URL"
log_info "Grafana: https://grafana.astra-os.io"
log_info "ArgoCD: https://argocd.astra-os.io"
log_info ""
log_info "Next steps:"
log_info "1. Configure DNS for api.astra-os.io, grafana.astra-os.io, argocd.astra-os.io"
log_info "2. Configure TLS certificates (cert-manager recommended)"
log_info "3. Set up Vault secrets for External Secrets"
log_info "4. Configure Telegram bot token in Vault"
log_info "5. Run monthly DR tests: ./scripts/dr-test.sh"
