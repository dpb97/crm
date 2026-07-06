#!/usr/bin/env bash
set -e
S_UMB=/mnt/c/Users/d.boeckle/Dev/pilanda
D_UMB=/home/dboeckle/frappe-bench/apps/pilanda
S_PLS=/mnt/c/Users/d.boeckle/Dev/pilanda_pls
D_PLS=/home/dboeckle/frappe-bench/apps/pilanda_pls

cp "$S_UMB/pilanda/public/icons.svg"               "$D_UMB/pilanda/public/icons.svg"
cp "$S_UMB/pilanda/public/css/pilanda_home.css"    "$D_UMB/pilanda/public/css/pilanda_home.css"
cp "$S_UMB/pilanda/www/pilanda.html"               "$D_UMB/pilanda/www/pilanda.html"
cp "$S_UMB/pilanda/pilanda/page/pilanda_home/pilanda_home.js" "$D_UMB/pilanda/pilanda/page/pilanda_home/pilanda_home.js"
cp "$S_PLS/pilanda_pls/www/pls.html"               "$D_PLS/pilanda_pls/www/pls.html"
echo "  ~ synced icon files"

cd /home/dboeckle/frappe-bench
bench --site lcs.local clear-website-cache 2>&1 | tail -1
bench --site lcs.local clear-cache 2>&1 | tail -1

echo
echo "=== smoke ==="
printf "  /assets/pilanda/icons.svg : "; curl -s -o /dev/null -w "HTTP %{http_code} size=%{size_download}\n" -m 5 http://127.0.0.1:8000/assets/pilanda/icons.svg
printf "  /pilanda                  : "; curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 5 http://127.0.0.1:8000/pilanda
printf "  /pls                      : "; curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 5 http://127.0.0.1:8000/pls
echo
echo "  count icon symbols in sprite:"
curl -s -m 5 http://127.0.0.1:8000/assets/pilanda/icons.svg | grep -oE 'id="icon-[a-z-]+"' | wc -l
echo "  icons referenced in /pilanda HTML:"
curl -s -m 5 http://127.0.0.1:8000/pilanda | grep -oE 'icons.svg#icon-[a-z-]+' | sort -u | head -25
