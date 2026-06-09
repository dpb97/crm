#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda
DST=/home/dboeckle/frappe-bench/apps/pilanda
cp "$SRC/pilanda/www/pilanda.html"             "$DST/pilanda/www/pilanda.html"
cp "$SRC/pilanda/public/css/pilanda_home.css"  "$DST/pilanda/public/css/pilanda_home.css"
echo "  ~ synced template + css"

cd /home/dboeckle/frappe-bench
/home/dboeckle/.local/bin/bench --site lcs.local clear-website-cache 2>&1 | tail -1
/home/dboeckle/.local/bin/bench --site lcs.local clear-cache 2>&1 | tail -1

echo
echo "=== verify ==="
printf "  HTTP /pilanda                : "
curl -s -o /dev/null -w "HTTP %{http_code}  size=%{size_download}\n" -m 5 http://127.0.0.1:8000/pilanda
printf "  HTTP css                     : "
curl -s -o /dev/null -w "HTTP %{http_code}  size=%{size_download}\n" -m 5 http://127.0.0.1:8000/assets/pilanda/css/pilanda_home.css
echo
echo "=== rendered HTML markers ==="
curl -s -m 5 http://127.0.0.1:8000/pilanda | grep -oE "pilanda-shell|pilanda-side|pilanda-top|pilanda-main|pilanda-side-zone--[a-z]" | sort -u
