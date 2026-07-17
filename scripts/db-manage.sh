#!/usr/bin/env bash
set -euo pipefail

# Astra OS - Database Management Script
# Commands: backup (default), restore, list

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/../backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-astra}"
DB_USER="${DB_USER:-astra}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/astra_${TIMESTAMP}.sql.gz"

# Run backup
log_info "Starting database backup..."
log_info "Database: $DB_NAME @ $DB_HOST:$DB_PORT"

if command -v pg_dump &> /dev/null; then
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --no-owner --no-privileges | gzip > "$BACKUP_FILE"
elif command -v docker &> /dev/null; then
    docker exec astra-postgres pg_dump -U "$DB_USER" -d "$DB_NAME" \
        --no-owner --no-privileges | gzip > "$BACKUP_FILE"
else
    log_error "Neither pg_dump nor docker found. Cannot backup database."
    exit 1
fi

# Verify backup
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup completed: $BACKUP_FILE ($SIZE)"
else
    log_error "Backup failed or file is empty"
    exit 1
fi

# Rotate old backups
log_info "Rotating backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "astra_*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# List remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "astra_*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_info "Total backups: $BACKUP_COUNT ($TOTAL_SIZE)"

# Restore function
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_warning "This will OVERWRITE the current database!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled."
        exit 0
    fi
    
    log_info "Restoring from: $backup_file"
    
    if command -v psql &> /dev/null; then
        gunzip -c "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
    elif command -v docker &> /dev/null; then
        gunzip -c "$backup_file" | docker exec -i astra-postgres psql -U "$DB_USER" -d "$DB_NAME"
    else
        log_error "Neither psql nor docker found. Cannot restore database."
        exit 1
    fi
    
    log_info "Restore completed!"
}

# List backups
list_backups() {
    log_info "Available backups:"
    ls -lh "$BACKUP_DIR"/astra_*.sql.gz 2>/dev/null || log_warning "No backups found"
}

# Show usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  backup    Create a new backup (default)"
    echo "  restore   Restore from a backup file"
    echo "  list      List available backups"
    echo "  help      Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  DB_HOST       Database host (default: localhost)"
    echo "  DB_PORT       Database port (default: 5432)"
    echo "  DB_NAME       Database name (default: astra)"
    echo "  DB_USER       Database user (default: astra)"
    echo "  BACKUP_DIR    Backup directory (default: ../backups)"
    echo "  RETENTION_DAYS Days to keep backups (default: 30)"
}

# Parse command
case "${1:-backup}" in
    backup)
        # Default action already performed above
        ;;
    restore)
        if [ -z "${2:-}" ]; then
            list_backups
            echo ""
            read -p "Enter backup filename: " BACKUP_FILE
            restore_backup "$BACKUP_DIR/$BACKUP_FILE"
        else
            restore_backup "$2"
        fi
        ;;
    list)
        list_backups
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
