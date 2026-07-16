#!/usr/bin/env bash
# Idempotent branch-protection setup for the LCS CRM fork.
#
# Applies the LCS GitFlow standard to `main` and `develop`:
#   - PRs required, at least 1 approving review, stale reviews dismissed
#   - Required status checks: lcs-ci, lcs-codeql, lcs-trivy
#   - Linear history, force-pushes disabled, branch deletions blocked
#
# Run once after cloning the fork, re-run after adding new required checks.

set -euo pipefail

REPO="${REPO:-dpb97/crm}"
BRANCHES=("main" "develop")
REQUIRED_CHECKS=(
  "LCS · CI / Ruff + mypy (lcs_integrations)"
  "LCS · CI / Pytest (lcs_integrations)"
  "LCS · CI / Build Vue frontend"
  "LCS · CodeQL / Analyze (python)"
  "LCS · CodeQL / Analyze (javascript-typescript)"
  "LCS · Trivy Container Scan / Build & scan image"
)

command -v gh >/dev/null 2>&1 || { echo "gh (GitHub CLI) is required" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated — run 'gh auth login' first" >&2; exit 1; }

# Build the required-check JSON array once.
checks_json=$(printf '%s\n' "${REQUIRED_CHECKS[@]}" |
  python -c 'import sys, json; print(json.dumps([{"context":c.strip()} for c in sys.stdin if c.strip()]))')

for branch in "${BRANCHES[@]}"; do
  echo "→ protecting $REPO@$branch"
  # The payload mirrors https://docs.github.com/rest/branches/branch-protection
  payload=$(cat <<JSON
{
  "required_status_checks": {
    "strict": true,
    "checks": ${checks_json}
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "block_creations": false
}
JSON
)
  echo "$payload" | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/${REPO}/branches/${branch}/protection" \
    --input -
done

echo "✓ branch protection applied to: ${BRANCHES[*]}"
