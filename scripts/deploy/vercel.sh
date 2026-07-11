#!/usr/bin/env bash
set -euo pipefail

# Deploy to Vercel (Frontend only)
# Prerequisites: npm install -g vercel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Deploying Astra OS Frontend to Vercel..."

cd "$ROOT_DIR/apps/web"

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

# Deploy
if [ "${1:-}" = "--prod" ]; then
    echo "Deploying to production..."
    vercel --prod
else
    echo "Deploying preview..."
    vercel
fi

echo "Deployment complete!"
echo "Don't forget to set environment variables in Vercel dashboard:"
echo "  - NEXT_PUBLIC_API_URL"
