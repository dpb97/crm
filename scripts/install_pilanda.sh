#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda
DST=/home/dboeckle/frappe-bench/apps/pilanda

echo "=== clone workspace repo into bench apps ==="
cd /home/dboeckle/frappe-bench/apps
if [ -d pilanda ]; then
  echo "  ! apps/pilanda already exists — bailing (run manual uninstall first)"
  exit 1
fi
git clone "$SRC" pilanda 2>&1 | tail -3

echo
echo "=== pip install -e ==="
cd /home/dboeckle/frappe-bench
env/bin/pip install --quiet -e apps/pilanda 2>&1 | tail -3

echo
echo "=== add to sites/apps.txt (with proper newline) ==="
if ! grep -q '^pilanda$' sites/apps.txt 2>/dev/null; then
  # ensure trailing newline first
  tail -c1 sites/apps.txt | xxd -p | grep -q '^0a$' || echo "" >> sites/apps.txt
  echo "pilanda" >> sites/apps.txt
  echo "  + added to sites/apps.txt"
else
  echo "  ✓ already in sites/apps.txt"
fi
tail -3 sites/apps.txt | cat -A

echo
echo "=== assets symlink ==="
ln -sfn /home/dboeckle/frappe-bench/apps/pilanda/pilanda/public sites/assets/pilanda
ls -la sites/assets/pilanda | head -2

echo
echo "=== install-app + migrate ==="
/home/dboeckle/.local/bin/bench --site lcs.local install-app pilanda 2>&1 | tail -10
/home/dboeckle/.local/bin/bench --site lcs.local migrate 2>&1 | grep -iE "Error|Executing|pilanda|Removing orphan" | tail -10

echo
echo "=== clear caches so the new home + workspaces show up ==="
/home/dboeckle/.local/bin/bench --site lcs.local clear-cache 2>&1 | tail -2
/home/dboeckle/.local/bin/bench --site lcs.local clear-website-cache 2>&1 | tail -2
