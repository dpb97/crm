#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard
cp "$SRC/docker/app/parser.py"           "$DST/docker/app/parser.py"
cp "$SRC/lcs_bizcard/public/js/scan.js"  "$DST/lcs_bizcard/public/js/scan.js"
echo "  ✓ files synced"

cd "$DST/docker"
docker compose up -d --build 2>&1 | tail -5

cd /home/dboeckle/frappe-bench
/home/dboeckle/.local/bin/bench --site lcs.local clear-website-cache 2>&1 | tail -2
