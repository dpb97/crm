#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner/lcs_bizcard
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard/lcs_bizcard
cp "$SRC/www/bizcard/scan.html" "$DST/www/bizcard/scan.html"
cp "$SRC/www/bizcard/scan.py"   "$DST/www/bizcard/scan.py"
echo "  ✓ synced scan.html + scan.py"

cd /home/dboeckle/frappe-bench
echo
echo "=== clear caches ==="
env/bin/bench --site lcs.local clear-cache 2>&1 | tail -2
env/bin/bench --site lcs.local clear-website-cache 2>&1 | tail -2

echo
echo "=== fetch fresh (anonymous) ==="
curl -s -H "Host: lcs.local" "http://127.0.0.1:8000/bizcard/scan" | sed -n '24,32p'
