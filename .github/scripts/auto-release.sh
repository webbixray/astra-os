#!/bin/bash
# Auto-release script for Astra OS
# Usage: ./scripts/auto-release.sh [major|minor|patch] [prerelease]

set -euo pipefail

BUMP_TYPE="${1:-patch}"
PRERELEASE="${2:-}"
DRY_RUN="${3:-false}"

echo "🚀 Astra OS Auto-Release"
echo "========================"
echo "Bump type: $BUMP_TYPE"
echo "Prerelease: ${PRERELEASE:-none}"
echo "Dry run: $DRY_RUN"
echo ""

cd "$(git rev-parse --show-toplevel)"

# Verify we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "❌ Error: Must be on main branch (currently on $CURRENT_BRANCH)"
    exit 1
fi

# Verify working tree is clean
if [[ -n "$(git status --porcelain)" ]]; then
    echo "❌ Error: Working tree is not clean"
    git status --short
    exit 1
fi

# Run tests first
echo "🧪 Running tests..."
if ! python -m pytest apps/api/tests/ -x -q --tb=line 2>/dev/null; then
    echo "❌ Tests failed. Aborting release."
    exit 1
fi

echo "✅ Tests passed"

# Run linting
echo "🔍 Running linters..."
if ! ruff check . --quiet 2>/dev/null; then
    echo "❌ Linting failed. Run 'ruff check . --fix' and commit."
    exit 1
fi

echo "✅ Linting passed"

# Run version bump
DRY_RUN_FLAG=""
if [[ "$DRY_RUN" == "true" ]]; then
    DRY_RUN_FLAG="--dry-run"
fi

PRERELEASE_FLAG=""
if [[ -n "$PRERELEASE" ]]; then
    PRERELEASE_FLAG="--prerelease $PRERELEASE"
fi

echo "📦 Bumping version ($BUMP_TYPE)..."
python .github/scripts/version.py release "$BUMP_TYPE" $PRERELEASE_FLAG $DRY_RUN_FLAG

if [[ "$DRY_RUN" != "true" ]]; then
    echo ""
    echo "✅ Release committed and tagged!"
    echo ""
    echo "Next steps:"
    echo "  git push origin main --tags"
    echo "  gh release create v\$(python .github/scripts/version.py current) --generate-notes"
fi