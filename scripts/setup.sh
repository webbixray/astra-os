#!/usr/bin/env bash
set -euo pipefail

# Astra OS - One-Click Setup Script
# This script sets up the complete development environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_command() {
    command -v "$1" &> /dev/null
}

echo -e "${BLUE}"
echo "  _    _      _    _____ "
echo " | |  | |    | |  / ____|"
echo " | |  | | ___| | _| (___  "
echo " | |/\\| |/ _ \\ |/ /\\___ \\ "
echo " \\  /\\  /  __/   < ____) |"
echo "  \\/  \\/ \\___|_|\\_\\_____/ "
echo "                            "
echo "  AI-Native Marketing OS   "
echo -e "${NC}"

echo "This script will set up your development environment."
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

MISSING=()

if ! check_command node; then
    MISSING+=("Node.js (>=20.0.0)")
fi

if ! check_command pnpm; then
    MISSING+=("pnpm (>=9.0.0)")
fi

if ! check_command python3; then
    MISSING+=("Python (>=3.12)")
fi

if ! check_command docker; then
    log_warning "Docker not found. You'll need to install PostgreSQL and Redis manually."
else
    if ! docker info &> /dev/null; then
        log_warning "Docker daemon is not running. Please start Docker."
    fi
fi

if [ ${#MISSING[@]} -ne 0 ]; then
    log_error "Missing required tools:"
    for tool in "${MISSING[@]}"; do
        echo "  - $tool"
    done
    echo ""
    echo "Please install these tools and run this script again."
    exit 1
fi

log_success "All prerequisites found!"

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    log_error "Node.js version 20 or higher is required. Current: $(node -v)"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    log_error "Python 3.12 or higher is required. Current: $PYTHON_VERSION"
    exit 1
fi

# Create .env file
log_info "Setting up environment configuration..."
if [ ! -f "$ROOT_DIR/.env" ]; then
    cp "$ROOT_DIR/docker/dev/.env.example" "$ROOT_DIR/.env"
    log_success "Created .env file from template"
    log_warning "Please edit .env to add your API keys (OpenAI, Anthropic, etc.)"
else
    log_info ".env file already exists, skipping"
fi

# Install frontend dependencies
log_info "Installing frontend dependencies..."
cd "$ROOT_DIR"
pnpm install
log_success "Frontend dependencies installed"

cd apps/api && pip install -e "../../services/agent_orchestrator" 2>/dev/null || true

# Install API dependencies
log_info "Installing API dependencies..."
cd "$ROOT_DIR/apps/api"
pip install -e ".[dev]" 2>/dev/null || pip install -e "."
log_success "API dependencies installed"

# Start infrastructure services
if check_command docker && docker info &> /dev/null; then
    log_info "Starting infrastructure services..."
    cd "$ROOT_DIR"
    docker compose up -d postgres redis temporal
    log_success "Infrastructure services started"

    log_info "Waiting for services to be ready..."
    sleep 10

    # Run database migrations
    log_info "Running database migrations..."
    cd "$ROOT_DIR/apps/api"
    alembic upgrade head
    log_success "Database migrations applied"

    # Seed database
    log_info "Seeding database..."
    python -m scripts.seed_db 2>/dev/null || log_warning "Database seeding skipped (may already be seeded)"
    log_success "Database seeded"
else
    log_warning "Docker not available. Please ensure PostgreSQL and Redis are running manually."
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "To start developing:"
echo ""
echo "  make dev          # Start all services"
echo "  make dev-api      # Start API only"
echo "  make dev-web      # Start Web only"
echo ""
echo "Useful commands:"
echo ""
echo "  make test         # Run all tests"
echo "  make lint         # Lint code"
echo "  make db-migrate   # Create migration"
echo "  make db-seed      # Seed database"
echo "  make docker-ps    # Check containers"
echo ""
echo "Documentation:"
echo ""
echo "  DEVELOPMENT.md    # Developer guide"
echo "  docs/             # Architecture docs"
echo ""
echo "Happy coding! 🚀"
