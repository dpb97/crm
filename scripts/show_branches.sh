#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps
for app in frappe erpnext hrms lms builder crm; do
  echo "=== $app ==="
  cur=$(git -C "$app" log -1 --format='%h %s')
  echo "  HEAD: $cur"
  echo "  remote branches matching HEAD:"
  git -C "$app" branch -r --contains HEAD 2>&1 | head -5
  echo "  all local + remote branches:"
  git -C "$app" branch -a 2>&1 | grep -E 'version|develop|master|main|release|stable' | head -8
  echo
done
