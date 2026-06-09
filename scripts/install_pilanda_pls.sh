#!/usr/bin/env bash
set -e
SRC_PLS=/mnt/c/Users/d.boeckle/Dev/pilanda_pls
SRC_UMB=/mnt/c/Users/d.boeckle/Dev/pilanda
DST_UMB=/home/dboeckle/frappe-bench/apps/pilanda

echo "=== sync umbrella delete (drop stub PLS workspace in bench) ==="
rm -rf "$DST_UMB/pilanda/pilanda/workspace/projektleitstelle" 2>/dev/null && echo "  - removed stub" || echo "  ~ already gone"

echo
echo "=== clone pilanda_pls into apps ==="
cd /home/dboeckle/frappe-bench/apps
if [ -d pilanda_pls ]; then
  echo "  ! apps/pilanda_pls exists already — bailing"
  exit 1
fi
git clone "$SRC_PLS" pilanda_pls 2>&1 | tail -3

echo
echo "=== pip install -e ==="
cd /home/dboeckle/frappe-bench
env/bin/pip install --quiet -e apps/pilanda_pls 2>&1 | tail -3

echo
echo "=== append to apps.txt (with trailing newline) ==="
if ! grep -q '^pilanda_pls$' sites/apps.txt; then
  tail -c1 sites/apps.txt | xxd -p | grep -q '^0a$' || echo "" >> sites/apps.txt
  echo "pilanda_pls" >> sites/apps.txt
  echo "  + added"
else
  echo "  ✓ already present"
fi
tail -3 sites/apps.txt | cat -A

echo
echo "=== assets symlink ==="
ln -sfn /home/dboeckle/frappe-bench/apps/pilanda_pls/pilanda_pls/public sites/assets/pilanda_pls
ls -la sites/assets/pilanda_pls | head -2

echo
echo "=== install-app + migrate ==="
/home/dboeckle/.local/bin/bench --site lcs.local install-app pilanda_pls 2>&1 | tail -10
echo
/home/dboeckle/.local/bin/bench --site lcs.local migrate 2>&1 | grep -iE "Error|pilanda_pls|projektleitstelle|Workspace|Removing orphan|Traceback" | tail -10

echo
echo "=== restart web so new pilanda_pls module loads ==="
pkill -f "frappe serve --port 8000" 2>/dev/null || true
