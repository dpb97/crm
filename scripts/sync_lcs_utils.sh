#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend/src
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend/src

mkdir -p "$DFRO/utils"
for f in offlineDB.js syncEngine.js; do
  if [ -f "$SFRO/utils/$f" ]; then
    cp "$SFRO/utils/$f" "$DFRO/utils/$f" && echo "  + utils/$f"
  fi
done

echo
cd /home/dboeckle/frappe-bench/apps/crm/frontend
yarn build 2>&1 | tail -10
