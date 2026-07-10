#!/bin/bash
set -euo pipefail

echo "=== Migration Check ==="

cd "$(dirname "$0")/../apps/api"

# Check for pending migrations
echo "--- Checking for pending migrations ---"
.venv/bin/alembic check 2>&1 || {
    echo "WARNING: Database is not up-to-date with migrations."
    echo "Run: cd apps/api && .venv/bin/alembic upgrade head"
}

# Check migration tree is linear (no branches)
echo "--- Checking migration history ---"
HISTORY=$(.venv/bin/alembic history 2>/dev/null)
if echo "$HISTORY" | grep -q "(branch)"; then
    echo "ERROR: Migration branches detected. All migrations must be linear."
    exit 1
fi

# Check for merge conflicts in migration files
echo "--- Checking for duplicate migration IDs ---"
DUPS=$(.venv/bin/alembic heads 2>/dev/null | wc -l)
if [ "$DUPS" -gt 1 ]; then
    echo "ERROR: Multiple migration heads detected. Merge them with: alembic merge heads"
    exit 1
fi

echo "--- Migration check passed ---"
