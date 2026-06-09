#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps

for app in crm builder; do
  echo "=== $app: stash pop ==="
  if git -C "$app" stash list | grep -q lcs-pre-update; then
    if git -C "$app" stash pop 2>&1; then
      echo "  ✓ pop clean"
    else
      echo "  ! conflicts in $app — leaving stash in place"
      git -C "$app" status --short | head -15
    fi
  else
    echo "  - no stash labelled lcs-pre-update"
  fi
  echo
done

echo "=== Final dirty status (excl. pycache) ==="
for app in crm builder; do
  echo "--- $app ---"
  git -C "$app" status --porcelain | grep -v -E '\.pyc$|__pycache__|\.cpython-' | head -15
done
