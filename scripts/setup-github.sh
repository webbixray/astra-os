#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Astra OS - GitHub Branch Protection Setup
# Run this after: gh auth login
# ============================================================

echo "=== Astra OS - Branch Protection Setup ==="

# Check gh is available
if ! command -v gh &> /dev/null; then
    echo "ERROR: gh CLI not found. Install it:"
    echo "  macOS: brew install gh"
    echo "  Linux: sudo apt install gh"
    echo "  Or visit: https://cli.github.com/"
    exit 1
fi

# Check auth
if ! gh auth status &> /dev/null; then
    echo "ERROR: Not authenticated. Run: gh auth login"
    exit 1
fi

REPO="webbixray/astra-os"

echo ""
echo "Setting branch protection rules for: $REPO"
echo ""

# Protect main branch
echo "1. Configuring 'main' branch protection..."
gh api "repos/$REPO/branches/main/protection" \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint","security","test","k8s-policy"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"require_last_push_approval":false}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field block_creations=false \
  --field required_conversation_resolution=true \
  2>/dev/null && echo "   ✓ main branch protection enabled" || echo "   ⚠ Failed (may need admin permissions)"

# Protect develop branch
echo "2. Configuring 'develop' branch protection..."
gh api "repos/$REPO/branches/develop/protection" \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint","test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_conversation_resolution=true \
  2>/dev/null && echo "   ✓ develop branch protection enabled" || echo "   ⚠ Failed (branch may not exist yet)"

# Configure repo settings
echo "3. Configuring repository settings..."
gh api "repos/$REPO" \
  --method PATCH \
  --field has_issues=true \
  --field has_projects=true \
  --field has_wiki=false \
  --field allow_squash_merge=true \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=true \
  --field delete_branch_on_merge=true \
  --field enable_automated_security_fixes=true \
  --field enable_vulnerability_alerts=true \
  2>/dev/null && echo "   ✓ Repository settings updated" || echo "   ⚠ Failed"

# Enable vulnerability alerts
echo "4. Enabling Dependabot alerts..."
gh api "repos/$REPO/vulnerability-alerts" \
  --method PUT \
  2>/dev/null && echo "   ✓ Vulnerability alerts enabled" || echo "   ⚠ Failed"

# Enable auto-merge for dependabot PRs
echo "5. Enabling auto-merge for Dependabot..."
gh api "repos/$REPO" \
  --method PATCH \
  --field allow_auto_merge=true \
  2>/dev/null && echo "   ✓ Auto-merge enabled" || echo "   ⚠ Failed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Summary of protections on 'main':"
echo "  - Required status checks: lint, security, test, k8s-policy"
echo "  - Require pull request reviews (1 approval)"
echo "  - Dismiss stale reviews"
echo "  - Require code owner reviews"
echo "  - Require conversation resolution"
echo "  - No force pushes"
echo "  - No branch deletion"
echo "  - Admins must follow rules"
echo ""
echo "Summary of protections on 'develop':"
echo "  - Required status checks: lint, test"
echo "  - Require pull request reviews (1 approval)"
echo "  - Dismiss stale reviews"
echo "  - No force pushes"
echo ""
echo "Repository settings:"
echo "  - Squash merge: enabled"
echo "  - Rebase merge: enabled"
echo "  - Merge commits: disabled"
echo "  - Delete branch on merge: enabled"
echo "  - Dependabot alerts: enabled"
