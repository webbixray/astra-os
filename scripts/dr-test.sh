#!/bin/bash
# DR Test Script - Validate RPO/RTO for Astra OS
# Run this monthly in production

set -euo pipefail

NAMESPACE="astra-production"
DR_NAMESPACE="astra-dr"
BACKUP_STORAGE="velero-backups"

echo "=========================================="
echo "Astra OS - Disaster Recovery Test"
echo "Date: $(date)"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Track results
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local name=$1
    local cmd=$2
    echo -n "Testing: $name ... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Verify Velero is installed and healthy
run_test "Velero installed" "kubectl get deployment velero -n velero"
run_test "Velero healthy" "velero version --client-only"
run_test "Backup storage accessible" "velero backup-location get"

# 2. Verify backup schedule
run_test "Daily backup schedule exists" "velero schedule get daily-backup -o jsonpath='{.status.phase}' | grep -q Completed"
run_test "Hourly backup schedule exists" "velero schedule get hourly-backup -o jsonpath='{.status.phase}' | grep -q Completed"

# 3. Trigger manual backup
log_info "Triggering manual backup..."
BACKUP_NAME="dr-test-$(date +%Y%m%d-%H%M%S)"
velero backup create "$BACKUP_NAME" --include-namespaces "$NAMESPACE" --wait

run_test "Backup completed successfully" "velero backup get $BACKUP_NAME -o jsonpath='{.status.phase}' | grep -q Completed"

# 4. Verify backup contents
log_info "Verifying backup contents..."
BACKUP_ITEMS=$(velero backup describe "$BACKUP_NAME" --details | grep -c "PersistentVolumeClaim\|Deployment\|Service\|ConfigMap\|Secret")
run_test "Backup contains expected resources" "[ $BACKUP_ITEMS -gt 50 ]"

# 4. Create DR namespace
log_info "Creating DR namespace..."
kubectl create namespace "$DR_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# 5. Restore to DR namespace
log_info "Restoring to DR namespace..."
velero restore create --from-backup "$BACKUP_NAME" --namespace-mappings "$NAMESPACE:$DR_NAMESPACE" --wait

run_test "Restore completed" "velero restore get --from-backup $BACKUP_NAME -o jsonpath='{.items[0].status.phase}' | grep -q Completed"

# 6. Verify restored resources
log_info "Verifying restored resources..."
RESTORED_DEPLOYMENTS=$(kubectl get deployments -n "$DR_NAMESPACE" --no-headers | wc -l)
run_test "Deployments restored" "[ $RESTORED_DEPLOYMENTS -gt 5 ]"

RESTORED_PVCS=$(kubectl get pvc -n "$DR_NAMESPACE" --no-headers | wc -l)
run_test "PVCs restored" "[ $RESTORED_PVCS -gt 3 ]"

RESTORED_SECRETS=$(kubectl get secrets -n "$DR_NAMESPACE" --no-headers | grep -v "default-token" | wc -l)
run_test "Secrets restored" "[ $RESTORED_SECRETS -gt 10 ]"

# 6. Verify database restore (check data integrity)
log_info "Verifying database data..."
DB_POD=$(kubectl get pods -n "$DR_NAMESPACE" -l app=postgres --no-headers | head -1 | awk '{print $1}')
if [ -n "$DB_POD" ]; then
    TABLE_COUNT=$(kubectl exec -n "$DR_NAMESPACE" "$DB_POD" -- psql -U postgres -d astra_prod -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    run_test "Database tables restored" "[ $TABLE_COUNT -gt 20 ]"

    USER_COUNT=$(kubectl exec -n "$DR_NAMESPACE" "$DB_POD" -- psql -U postgres -d astra_prod -t -c "SELECT count(*) FROM users;" | xargs)
    run_test "User data restored" "[ $USER_COUNT -gt 0 ]"
fi

# 7. Verify application health in DR
log_info "Checking DR application health..."
sleep 30  # Wait for pods to be ready

DR_API_POD=$(kubectl get pods -n "$DR_NAMESPACE" -l app=api --no-headers | head -1 | awk '{print $1}')
if [ -n "$DR_API_POD" ]; then
    HEALTH_CHECK=$(kubectl exec -n "$DR_NAMESPACE" "$DR_API_POD" -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/live)
    run_test "DR API health endpoint" "[ $HEALTH_CHECK -eq 200 ]"
fi

# 8. Measure RTO (time to restore)
RESTORE_TIME=$(velero restore get --from-backup "$BACKUP_NAME" -o jsonpath='{.items[0].status.completionTimestamp}')
BACKUP_TIME=$(velero backup get "$BACKUP_NAME" -o jsonpath='{.status.completionTimestamp}')
RTO_SECONDS=$(( $(date -d "$RESTORE_TIME" +%s) - $(date -d "$BACKUP_TIME" +%s) ))

run_test "RTO within 4 hours" "[ $RTO_SECONDS -le 14400 ]"
log_info "RTO: ${RTO_SECONDS}s ($((RTO_SECONDS/60)) minutes)"

# 9. Verify RPO (data loss window)
LAST_BACKUP=$(velero backup get --output json | jq -r '.items[0].status.completionTimestamp' | xargs -I {} date -d {} +%s)
NOW=$(date +%s)
RPO_SECONDS=$((NOW - LAST_BACKUP))
run_test "RPO within 1 hour" "[ $RPO_SECONDS -le 3600 ]"
log_info "RPO: ${RPO_SECONDS}s ($((RPO_SECONDS/60)) minutes)"

# 10. Cleanup DR namespace
log_info "Cleaning up DR test resources..."
velero restore delete --from-backup "$BACKUP_NAME" --confirm
kubectl delete namespace "$DR_NAMESPACE" --wait=false
velero backup delete "$BACKUP_NAME" --confirm

# Summary
echo ""
echo "=========================================="
echo "DR TEST SUMMARY"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""
echo "RTO: ${RTO_SECONDS}s ($((RTO_SECONDS/60)) minutes) - Target: < 4 hours"
echo "RPO: ${RPO_SECONDS}s ($((RPO_SECONDS/60)) minutes) - Target: < 1 hour"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}ALL TESTS PASSED - DR READY${NC}"
    exit 0
else
    echo -e "${RED}SOME TESTS FAILED - REVIEW REQUIRED${NC}"
    exit 1
fi
