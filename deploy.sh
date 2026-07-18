#!/bin/bash

# ASTRA OS - Production Deployment Script
# Usage: ./deploy.sh [build|up|down|logs|status|migrate|backup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROD_DIR="$SCRIPT_DIR/docker/prod"
ENV_FILE="$SCRIPT_DIR/.env.prod"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

check_env() {
  if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    log_info "Copy from template: cp docker/prod/.env.example .env.prod"
    exit 1
  fi
}

check_docker() {
  if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
  fi

  if ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not installed"
    exit 1
  fi
}

build_images() {
  log_info "Building production images..."

  log_info "Building API image..."
  docker build -t astra-api:latest -f "$SCRIPT_DIR/apps/api/Dockerfile" "$SCRIPT_DIR"

  log_info "Building Web image..."
  docker build -t astra-web:latest -f "$SCRIPT_DIR/apps/web/Dockerfile" "$SCRIPT_DIR"

  log_info "Images built successfully"
}

deploy_up() {
  check_env
  log_info "Starting ASTRA OS services..."

  cd "$PROD_DIR"
  docker compose --env-file "$ENV_FILE" up -d

  log_info "Waiting for services to be healthy..."
  sleep 5

  log_info "Checking service health..."
  docker compose --env-file "$ENV_FILE" ps

  log_info "Deployment complete!"
  log_info "Access your application at: https://$(grep '^DOMAIN=' "$ENV_FILE" | cut -d= -f2)"
}

deploy_down() {
  log_warn "Stopping ASTRA OS services..."
  cd "$PROD_DIR"
  docker compose --env-file "$ENV_FILE" down
  log_info "Services stopped"
}

show_logs() {
  check_env
  cd "$PROD_DIR"

  SERVICE="${1:-}"
  if [ -z "$SERVICE" ]; then
    log_info "Showing logs from all services (Ctrl+C to exit)..."
    docker compose --env-file "$ENV_FILE" logs -f --tail=50
  else
    log_info "Showing logs from $SERVICE..."
    docker compose --env-file "$ENV_FILE" logs -f --tail=100 "$SERVICE"
  fi
}

show_status() {
  check_env
  cd "$PROD_DIR"

  log_info "Service Status:"
  docker compose --env-file "$ENV_FILE" ps

  log_info ""
  log_info "Resource Usage:"
  docker compose --env-file "$ENV_FILE" stats --no-stream

  log_info ""
  log_info "Health Checks:"
  for service in postgres redis temporal api web nginx; do
    STATUS=$(docker compose --env-file "$ENV_FILE" ps --filter "service=$service" --format "{{.Status}}")
    if [ ! -z "$STATUS" ]; then
      echo "  $service: $STATUS"
    fi
  done
}

run_migrations() {
  check_env
  log_info "Running database migrations..."

  cd "$PROD_DIR"
  docker compose --env-file "$ENV_FILE" exec -T api python -m alembic upgrade head

  log_info "Migrations completed"
}

backup_database() {
  check_env
  log_info "Backing up PostgreSQL database..."

  cd "$PROD_DIR"
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  BACKUP_FILE="$SCRIPT_DIR/backup-$TIMESTAMP.sql"

  docker compose --env-file "$ENV_FILE" exec -T postgres \
    pg_dump -U astra astra > "$BACKUP_FILE"

  log_info "Database backup saved to: $BACKUP_FILE"
  log_info "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
}

restore_database() {
  check_env

  BACKUP_FILE="${1:-}"
  if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    log_info "Usage: $0 restore <backup-file>"
    exit 1
  fi

  log_warn "Restoring database from: $BACKUP_FILE"
  read -p "Are you sure? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Restore cancelled"
    exit 0
  fi

  cd "$PROD_DIR"
  docker compose --env-file "$ENV_FILE" exec -T postgres \
    psql -U astra astra < "$BACKUP_FILE"

  log_info "Database restored successfully"
}

init_ssl() {
  log_warn "SSL Certificate Setup"
  log_info "This script can help initialize SSL certificates"
  log_info ""
  log_info "Option 1: Using Let's Encrypt (Recommended)"
  log_info "  1. Install certbot: sudo apt-get install certbot"
  log_info "  2. Generate cert: sudo certbot certonly --standalone -d your-domain.com"
  log_info "  3. Copy files:"
  log_info "     sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem $PROD_DIR/ssl/"
  log_info "     sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem $PROD_DIR/ssl/"
  log_info ""
  log_info "Option 2: Self-signed certificate (testing only)"
  read -p "Generate self-signed certificate? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$PROD_DIR/ssl"
    openssl req -x509 -newkey rsa:4096 -nodes \
      -out "$PROD_DIR/ssl/fullchain.pem" \
      -keyout "$PROD_DIR/ssl/privkey.pem" \
      -days 365 \
      -subj "/CN=localhost"
    log_info "Self-signed certificate created"
  fi
}

usage() {
  cat << EOF
ASTRA OS - Production Deployment Script

Usage: $0 <command> [options]

Commands:
  build              Build production Docker images
  up                 Start all services
  down               Stop all services
  logs [service]     View logs (optionally for specific service)
  status             Show service status and resource usage
  migrate            Run database migrations
  backup             Backup PostgreSQL database
  restore <file>     Restore PostgreSQL from backup
  init-ssl           Initialize SSL certificates
  help               Show this help message

Examples:
  $0 build
  $0 up
  $0 logs api
  $0 backup
  $0 restore backup-20240101-120000.sql

EOF
}

main() {
  check_docker

  COMMAND="${1:-help}"

  case "$COMMAND" in
    build)
      build_images
      ;;
    up)
      deploy_up
      ;;
    down)
      deploy_down
      ;;
    logs)
      show_logs "$2"
      ;;
    status)
      show_status
      ;;
    migrate)
      run_migrations
      ;;
    backup)
      backup_database
      ;;
    restore)
      restore_database "$2"
      ;;
    init-ssl)
      init_ssl
      ;;
    help)
      usage
      ;;
    *)
      log_error "Unknown command: $COMMAND"
      usage
      exit 1
      ;;
  esac
}

main "$@"
