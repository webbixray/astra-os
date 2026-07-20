#!/bin/bash

# ASTRA OS - Production Deployment Script
# Usage: ./deploy.sh [dev|build|up|down|logs|status|migrate|backup|restore|init-ssl|monitoring]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROD_COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"
MONITORING_COMPOSE_FILE="$SCRIPT_DIR/docker/monitoring/docker-compose.yml"
FULL_MONITORING_COMPOSE="$SCRIPT_DIR/docker/monitoring/docker-compose.full.yml"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

check_env() {
  if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE="$SCRIPT_DIR/.env.prod"
    [ ! -f "$ENV_FILE" ] && { log_error "No .env found. Copy docker/prod/.env.example .env"; exit 1; }
  fi
}
check_docker() {
  command -v docker &>/dev/null || { log_error "Docker not installed"; exit 1; }
  docker compose version &>/dev/null || { log_error "Docker Compose not installed"; exit 1; }
}

build_images() {
  log_step "Building Production Images"
  docker build -t astra-api:latest -f "$SCRIPT_DIR/apps/api/Dockerfile" "$SCRIPT_DIR"
  docker build -t astra-web:latest -f "$SCRIPT_DIR/apps/web/Dockerfile" "$SCRIPT_DIR"
  docker build -t astra-worker:latest -f "$SCRIPT_DIR/apps/api/Dockerfile.worker" "$SCRIPT_DIR"
  log_info "✅ astra-api:latest, astra-web:latest, astra-worker:latest"
}

deploy_up() {
  check_env
  log_step "Starting Production Services"
  local CMD="docker compose -f $PROD_COMPOSE_FILE --env-file $ENV_FILE"
  $CMD up -d --remove-orphans
  for i in $(seq 1 30); do
    curl -sf http://localhost:8000/api/v1/health/live &>/dev/null && { log_info "✅ API healthy"; break; }
    [ "$i" -eq 30 ] && log_warn "⚠️ API health check timed out" || { echo -n .; sleep 2; }
  done
  echo
  DOMAIN=$(grep '^DOMAIN=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "localhost")
  log_step "Deployed → API: https://$DOMAIN/api/v1/docs | Web: https://$DOMAIN | Grafana: http://localhost:3001"
}

deploy_dev() {
  log_step "Starting Development Environment"
  docker compose -f "$COMPOSE_FILE" up -d postgres redis temporal
  sleep 3
  docker compose -f "$COMPOSE_FILE" up api web
}

deploy_down() {
  log_step "Stopping Services"
  [ -f "$PROD_COMPOSE_FILE" ] && docker compose -f "$PROD_COMPOSE_FILE" --env-file "$ENV_FILE" down -v 2>/dev/null || true
  docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
  log_info "✅ Stopped"
}

start_monitoring() {
  log_step "Starting Monitoring"
  if [ -f "$FULL_MONITORING_COMPOSE" ]; then
    docker compose -f "$FULL_MONITORING_COMPOSE" up -d
    log_info "Full stack: Prometheus, Grafana, Loki, Tempo, Alertmanager"
  elif [ -f "$MONITORING_COMPOSE" ]; then
    docker compose -f "$MONITORING_COMPOSE" up -d
    log_info "Core: Prometheus, Grafana"
  else
    log_error "Monitoring compose not found"; exit 1
  fi
  log_info "Grafana: http://localhost:3001"
}

show_logs() {
  local CMD="docker compose -f $PROD_COMPOSE_FILE --env-file $ENV_FILE"
  ${CMD} logs -f --tail=50 "${1:-}"
}
show_status() {
  docker compose -f "$PROD_COMPOSE_FILE" --env-file "$ENV_FILE" ps 2>/dev/null
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || true
}
run_migrations() {
  check_env
  log_step "Running Migrations"
  docker compose -f "$PROD_COMPOSE_FILE" --env-file "$ENV_FILE" exec -T api python -m alembic upgrade head 2>/dev/null ||
    (cd "$SCRIPT_DIR/apps/api" && alembic upgrade head)
  log_info "✅ Migrations complete"
}
backup_database() {
  check_env
  log_step "Backing Up Database"
  local TS=$(date +%Y%m%d-%H%M%S) BACKUP_DIR="$SCRIPT_DIR/backups"
  mkdir -p "$BACKUP_DIR"
  local FILE="$BACKUP_DIR/astra-$TS.sql"
  docker compose -f "$PROD_COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_dump -U astra --clean --if-exists astra > "$FILE" 2>/dev/null ||
    docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U astra --clean --if-exists astra > "$FILE"
  gzip "$FILE"
  log_info "✅ Backup: ${FILE}.gz ($(du -h "${FILE}.gz" | cut -f1))"
}
restore_database() {
  local FILE="${1:-}"
  [ -z "$FILE" ] && { log_error "Usage: $0 restore <file>"; exit 1; }
  [ ! -f "$FILE" ] && { log_error "File not found: $FILE"; exit 1; }
  log_warn "⚠️ Restoring $FILE — data will be DESTROYED"
  read -p "Continue? (y/N) " -n 1 -r; echo
  [[ ! $REPLY =~ ^[Yy]$ ]] && { log_info "Cancelled"; exit 0; }
  gunzip -c "$FILE" | docker compose -f "$PROD_COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres psql -U astra astra 2>/dev/null ||
    gunzip -c "$FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U astra astra
  log_info "✅ Restored"
}
init_ssl() {
  local SSL_DIR="$SCRIPT_DIR/docker/prod/ssl"
  mkdir -p "$SSL_DIR"
  echo "1) Let's Encrypt  2) Self-signed  3) Skip"
  read -p "Choice (1-3): " c
  case $c in
    1) read -p "Domain: " d
       docker run --rm -p 80:80 -v "$SSL_DIR:/etc/letsencrypt" certbot/certbot certonly --standalone -d "$d" --agree-tos -m "admin@$d"
       ln -sf "/etc/letsencrypt/live/$d/fullchain.pem" "$SSL_DIR/" && ln -sf "/etc/letsencrypt/live/$d/privkey.pem" "$SSL_DIR/" ;;
    2) openssl req -x509 -newkey rsa:4096 -nodes -out "$SSL_DIR/fullchain.pem" -keyout "$SSL_DIR/privkey.pem" -days 365 -subj "/CN=localhost"
       log_info "Self-signed cert created" ;;
    3) log_info "Skipped" ;;
  esac
}

usage() { cat <<'EOF'
Commands: dev | build | up | down | status | logs [svc] | migrate | backup | restore <file> | init-ssl | monitoring
EOF
}

main() {
  check_docker
  case "${1:-help}" in
    dev) deploy_dev ;;
    build) build_images ;;
    up) deploy_up ;;
    down) deploy_down ;;
    status) show_status ;;
    logs) show_logs "$2" ;;
    migrate) run_migrations ;;
    backup) backup_database ;;
    restore) restore_database "$2" ;;
    init-ssl) init_ssl ;;
    monitoring) start_monitoring ;;
    help) usage ;;
    *) log_error "Unknown: $1"; usage; exit 1 ;;
  esac
}

main "$@"
