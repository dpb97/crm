#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend
cp "$SFRO/vite.config.js" "$DFRO/vite.config.js" && echo "  ~ vite.config.js"
mkdir -p "$DFRO/src"
cp "$SFRO/src/sw.js"      "$DFRO/src/sw.js"      && echo "  + src/sw.js"
