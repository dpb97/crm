#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend
cp "$SFRO/src/pages/Deal.vue" "$DFRO/src/pages/Deal.vue"
cp "$SFRO/src/pages/Lead.vue" "$DFRO/src/pages/Lead.vue"
cd "$DFRO" && yarn build 2>&1 | tail -15
