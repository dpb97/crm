#!/usr/bin/env bash
set -e
cd /home/dboeckle/frappe-bench/apps

STAMP=$(date +%Y%m%d-%H%M%S)

for app in crm builder; do
  cd "$app"
  if [ -n "$(git status --porcelain | grep -v -E '^\?\? .*\.pyc$|^.. .*__pycache__|^.. .*\.cpython-')" ]; then
    msg="lcs-pre-update-${STAMP}"
    git stash push -u -m "$msg"
    echo "  ✓ $app: stashed as '$msg'"
  else
    echo "  - $app: nothing to stash"
  fi
  cd ..
done

echo
echo "=== Stash list (crm) ==="
git -C crm stash list

echo "=== Stash list (builder) ==="
git -C builder stash list
