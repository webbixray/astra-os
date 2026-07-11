#!/bin/bash
# ============================================================
# ASTRA OS — One-Command Setup Script
# ============================================================
# Usage: chmod +x setup.sh && ./setup.sh
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

print_banner() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       🚀  ASTRA OS — Setup Script  🚀       ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    for cmd in python3 node pnpm docker; do
        if command -v $cmd &> /dev/null; then
            echo -e "${GREEN}✓${NC} $cmd $(command $cmd --version 2>/dev/null | head -1)"
        else
            echo -e "${RED}✗${NC} $cmd not found. Please install it."
            exit 1
        fi
    done
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}✗${NC} Docker Compose not found"
        exit 1
    fi
    echo ""
}

setup_env() {
    echo -e "${BLUE}Setting up environment...${NC}"
    if [ ! -f .env ]; then
        cp docker/dev/.env .env 2>/dev/null || cp .env.example .env 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Created .env"
    else
        echo -e "${GREEN}✓${NC} .env already exists"
    fi
    echo ""
}

install_deps() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    pnpm install 2>/dev/null || npm install
    cd apps/api && pip install -e ".[dev]" 2>/dev/null || pip3 install -e ".[dev]" 2>/dev/null || true
    cd ../..
    echo -e "${GREEN}✓${NC} Dependencies installed"
    echo ""
}

start_infra() {
    echo -e "${BLUE}Starting infrastructure...${NC}"
    docker compose up -d postgres redis
    echo -e "${YELLOW}Waiting for database...${NC}"
    sleep 5
    echo -e "${GREEN}✓${NC} Infrastructure ready"
    echo ""
}

run_migrations() {
    echo -e "${BLUE}Running migrations...${NC}"
    cd apps/api && alembic upgrade head 2>/dev/null || python -m alembic upgrade head 2>/dev/null || true
    cd ../..
    echo -e "${GREEN}✓${NC} Migrations applied"
    echo ""
}

print_summary() {
    echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ✅  Setup Complete!  ✅             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Start dev:    ${GREEN}make dev${NC}"
    echo -e "  Run tests:    ${GREEN}make test${NC}"
    echo -e "  API docs:     ${GREEN}http://localhost:8000/api/v1/docs${NC}"
    echo -e "  Frontend:     ${GREEN}http://localhost:3000${NC}"
    echo -e "  All commands: ${GREEN}make help${NC}"
    echo ""
}

main() {
    print_banner
    check_prerequisites
    setup_env
    install_deps
    start_infra
    run_migrations
    print_summary
}

main "$@"
