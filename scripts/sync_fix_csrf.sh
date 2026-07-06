#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner/lcs_bizcard
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard/lcs_bizcard

cp "$SRC/www/bizcard/scan.html" "$DST/www/bizcard/scan.html" && echo "  ~ scan.html"
cp "$SRC/www/bizcard/scan.py"   "$DST/www/bizcard/scan.py"   && echo "  + scan.py"
cp "$SRC/public/js/scan.js"     "$DST/public/js/scan.js"     && echo "  ~ scan.js"

echo
echo "=== clear caches (page templates, website cache, asset paths) ==="
cd /home/dboeckle/frappe-bench
bench --site lcs.local clear-cache 2>&1 | tail -3
bench --site lcs.local clear-website-cache 2>&1 | tail -3

echo
echo "=== fetch fresh page (anonymous — should show empty csrf_token but valid HTML) ==="
curl -s -H "Host: lcs.local" "http://127.0.0.1:8000/bizcard/scan" | head -25
