#!/usr/bin/env bash
set -e

echo "=== pull latest fixes into apps/lcs_bizcard ==="
cd /home/dboeckle/frappe-bench/apps/lcs_bizcard
# origin was rewritten to GitHub earlier; pull from there
git fetch origin --quiet 2>&1 || git fetch upstream --quiet 2>&1 || true
git log --oneline HEAD..origin/main 2>&1 | head -5 || true
git checkout main 2>&1 | tail -2
git pull origin main --ff-only 2>&1 | tail -3

echo
echo "=== ensure dependencies up to date ==="
/home/dboeckle/frappe-bench/env/bin/pip install --quiet -e . 2>&1 | tail -2
