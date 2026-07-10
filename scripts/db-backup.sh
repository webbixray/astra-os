#!/bin/bash
set -euo pipefail

# ASTRA OS Database Backup Script
# Usage: ./scripts/db-backup.sh [output-dir]

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/astra_${TIMESTAMP}.sql.gz"
RETAIN_DAYS=30

mkdir -p "${BACKUP_DIR}"

echo "=== ASTRA OS Database Backup ==="
echo "Backup directory: ${BACKUP_DIR}"
echo "Timestamp: ${TIMESTAMP}"

# Check required tools
command -v pg_dump >/dev/null 2>&1 || { echo "ERROR: pg_dump not found"; exit 1; }
command -v gzip >/dev/null 2>&1 || { echo "ERROR: gzip not found"; exit 1; }

# Source database URL from environment or .env
DB_URL="${DATABASE_URL:-}"
if [ -z "${DB_URL}" ] && [ -f .env ]; then
    DB_URL=$(grep -oP '^DATABASE_URL=\K.*' .env || echo "")
fi

if [ -z "${DB_URL}" ]; then
    echo "ERROR: DATABASE_URL not set. Set it or create a .env file."
    exit 1
fi

echo "Starting pg_dump..."

# Perform the backup
pg_dump \
    --no-owner \
    --no-acl \
    --compress=0 \
    --format=custom \
    --dbname="${DB_URL}" \
    | gzip > "${BACKUP_FILE}"

echo "Backup completed: ${BACKUP_FILE}"

# Get file size
FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "Backup size: ${FILE_SIZE}"

# Rotate old backups
echo "Cleaning up backups older than ${RETAIN_DAYS} days..."
find "${BACKUP_DIR}" -name "astra_*.sql.gz" -mtime +${RETAIN_DAYS} -delete

# Count remaining backups
COUNT=$(find "${BACKUP_DIR}" -name "astra_*.sql.gz" | wc -l)
echo "Retained backups: ${COUNT}"

# Restore command (for reference):
# gunzip -c "${BACKUP_FILE}" | pg_restore --clean --no-owner --dbname="${DB_URL}"
echo ""
echo "=== Backup Complete ==="
echo "To restore: gunzip -c ${BACKUP_FILE} | pg_restore --clean --no-owner --dbname=\"\$DATABASE_URL\""
