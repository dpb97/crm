#!/usr/bin/env bash
set -e

# 1) Mirror the workspace lcs_bizcard tree into the bench apps/ dir.
SAPP=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_bizcard
DAPP=/home/dboeckle/frappe-bench/apps/lcs_bizcard

if [ -d "$DAPP" ]; then
  echo "  ! $DAPP already exists; refreshing files instead of re-cloning"
  rsync -a --exclude='__pycache__' --exclude='*.pyc' "$SAPP/" "$DAPP/"
else
  echo "  + cloning workspace lcs_bizcard into apps/"
  cp -r "$SAPP" "$DAPP"
fi

# 2) Make sure it's a git repo (Frappe expects one). Initialise quietly.
cd "$DAPP"
if [ ! -d .git ]; then
  git init -q
  git add -A
  git -c user.email=lcs@local -c user.name=LCS commit -q -m "init lcs_bizcard from workspace" || true
fi

# 3) pip-install editable into the bench env if not done yet.
cd /home/dboeckle/frappe-bench
if ! env/bin/pip show lcs_bizcard >/dev/null 2>&1; then
  echo "  + pip install -e apps/lcs_bizcard"
  env/bin/pip install --quiet -e apps/lcs_bizcard
fi

# 4) Register in apps.txt (needed for bench --site install-app).
if ! grep -qx lcs_bizcard sites/apps.txt 2>/dev/null; then
  echo lcs_bizcard >> sites/apps.txt
  echo "  + added to sites/apps.txt"
fi

# 5) Install on the site (idempotent — Frappe noops if already installed).
if ! bench --site lcs.local list-apps 2>/dev/null | grep -qx lcs_bizcard; then
  echo "  + installing app on site lcs.local"
  bench --site lcs.local install-app lcs_bizcard
else
  echo "  - lcs_bizcard already installed on lcs.local"
fi

# 6) Migrate + build so the new www page and public assets land.
bench --site lcs.local migrate 2>&1 | tail -5
bench build --app lcs_bizcard 2>&1 | tail -5

# 7) Smoke-tests
echo
echo "=== Smoke: health (will report scanner offline — expected, container not running yet) ==="
bench --site lcs.local execute lcs_bizcard.api.health 2>&1 | tail -3
echo
echo "=== Smoke: page reachable ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "Host: lcs.local" "http://127.0.0.1:8000/bizcard/scan"
