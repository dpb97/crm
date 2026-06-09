#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps
for app in frappe erpnext hrms lms builder crm; do
  echo "=== $app ==="
  git -C "$app" remote -v 2>&1 | head -4
  echo
done
