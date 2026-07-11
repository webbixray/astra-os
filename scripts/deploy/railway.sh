#!/usr/bin/env bash
set -euo pipefail

# Deploy to Railway
# Prerequisites: npm install -g @railway/cli

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Deploying Astra OS to Railway..."

cd "$ROOT_DIR"

# Check if railway is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway first:"
    railway login
fi

# Check if project exists
if [ ! -f "railway.toml" ]; then
    echo "Linking to Railway project..."
    railway link
fi

# Deploy
if [ "${1:-}" = "--prod" ]; then
    echo "Deploying to production..."
    railway up --service api
    railway up --service web
else
    echo "Deploying preview..."
    railway up
fi

echo "Deployment complete!"
echo "Check status with: railway status"
