#!/usr/bin/env bash
set -e
S_UMB=/mnt/c/Users/d.boeckle/Dev/pilanda
D_UMB=/home/dboeckle/frappe-bench/apps/pilanda
S_PLS=/mnt/c/Users/d.boeckle/Dev/pilanda_pls
D_PLS=/home/dboeckle/frappe-bench/apps/pilanda_pls

cp "$S_UMB/pilanda/www/pilanda.html"          "$D_UMB/pilanda/www/pilanda.html"
cp "$S_UMB/pilanda/public/css/pilanda.css"    "$D_UMB/pilanda/public/css/pilanda.css"
cp "$S_PLS/pilanda_pls/www/pls.html"          "$D_PLS/pilanda_pls/www/pls.html"
cp "$S_PLS/pilanda_pls/www/pls.py"            "$D_PLS/pilanda_pls/www/pls.py"
echo "  ~ synced"

cd /home/dboeckle/frappe-bench
bench --site lcs.local clear-website-cache 2>&1 | tail -1
bench --site lcs.local clear-cache 2>&1 | tail -1

echo
echo "=== smoke ==="
printf "  /pilanda  : "; curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 5 http://127.0.0.1:8000/pilanda
printf "  /pls      : "; curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 5 http://127.0.0.1:8000/pls
echo
echo "=== sidebar link sample (top 5 hrefs) ==="
curl -s -m 5 http://127.0.0.1:8000/pilanda | grep -oE 'pilanda-side-link[^>]*href="[^"]+"' | head -5
echo
echo "=== Übersicht entry present? ==="
curl -s -m 5 http://127.0.0.1:8000/pilanda | grep -oE 'Übersicht' | head -2
echo
echo "=== /pls sidebar — Projektleitstelle marked active? ==="
curl -s -m 5 http://127.0.0.1:8000/pls | grep -oE 'is-active[^>]*href="[^"]*"' | head -3
