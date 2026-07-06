#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

echo "=== final sync of router.js + AppSidebar.vue ==="
cp "$SFRO/src/router.js"                                "$DFRO/src/router.js"
cp "$SFRO/src/components/Layouts/AppSidebar.vue"        "$DFRO/src/components/Layouts/AppSidebar.vue"
echo "  ✓"

echo
echo "=== yarn build ==="
cd "$DFRO"
yarn build 2>&1 | tail -15
