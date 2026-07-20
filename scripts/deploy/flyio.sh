#!/usr/bin/env bash
set -euo pipefail

# Deploy to Fly.io
# Prerequisites: curl -L https://fly.io/install.sh | sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Deploying Astra OS to Fly.io..."

cd "$ROOT_DIR"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "Installing Fly.io CLI..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "Please login to Fly.io first:"
    flyctl auth login
fi

# Check if app exists
if [ ! -f "fly.toml" ]; then
    echo "Launching new app..."
    flyctl launch --no-deploy

    echo "Setting up secrets..."
    echo "Please set your secrets:"
    echo "  flyctl secrets set SECRET_KEY=your-secret-key"
    echo "  flyctl secrets set DATABASE_URL=your-database-url"
    echo "  flyctl secrets set OPENAI_API_KEY=your-openai-key"
fi

# Deploy
if [ "${1:-}" = "--prod" ]; then
    echo "Deploying to production..."
    flyctl deploy
else
    echo "Deploying preview..."
    flyctl deploy --strategy=immediate
fi

echo "Deployment complete!"
echo "Check status with: flyctl status"
echo "View logs with: flyctl logs"
