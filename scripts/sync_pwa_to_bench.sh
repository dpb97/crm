#!/usr/bin/env bash
set -e
S=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
D=/home/dboeckle/frappe-bench/apps/crm/frontend
ls -la "$D/index.html" 2>&1 | head -2
echo
cp "$S/index.html"                  "$D/index.html"                  && echo "  ~ index.html"
cp "$S/public/lcs-pwa-bootstrap.js" "$D/public/lcs-pwa-bootstrap.js" && echo "  + public/lcs-pwa-bootstrap.js"
cp "$S/public/manifest.webmanifest" "$D/public/manifest.webmanifest" && echo "  + public/manifest.webmanifest"
cp "$S/public/sw.js"                "$D/public/sw.js"                && echo "  + public/sw.js"
