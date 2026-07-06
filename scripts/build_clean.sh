#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend
cp "$SFRO/src/components/Layouts/AppSidebar.vue" "$DFRO/src/components/Layouts/AppSidebar.vue"
cd "$DFRO" && yarn build 2>&1 | tail -15
