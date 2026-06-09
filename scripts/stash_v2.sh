#!/usr/bin/env bash
set -e
STAMP=$(date +%Y%m%d-%H%M%S)
cd /home/dboeckle/frappe-bench/apps
for app in crm; do
  cd "$app"
  if [ -n "$(git status --porcelain | grep -v -E '^\?\? .*\.pyc$|^.. .*__pycache__|^.. .*\.cpython-')" ]; then
    git stash push -u -m "lcs-pre-update-${STAMP}" | tail -1
    echo "  ✓ $app stashed"
  fi
  cd ..
done
