#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

for f in useUserPreferences.js useOfflineDoc.js useOfflineList.js; do
  if [ -f "$SFRO/src/composables/$f" ]; then
    cp "$SFRO/src/composables/$f" "$DFRO/src/composables/$f" && echo "  + composables/$f"
  fi
done

echo
cd "$DFRO" && yarn build 2>&1 | tail -10
