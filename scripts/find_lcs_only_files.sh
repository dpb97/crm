#!/usr/bin/env bash
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend/src
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend/src

echo "=== Files in workspace but missing in WSL ==="
( cd "$SFRO" && find . -type f \( -name "*.vue" -o -name "*.js" -o -name "*.ts" \) ) | while read f; do
  if [ ! -f "$DFRO/$f" ]; then
    echo "  MISS: $f"
  fi
done
