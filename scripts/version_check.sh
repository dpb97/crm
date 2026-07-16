#!/usr/bin/env bash
for app in frappe erpnext hrms lms builder crm; do
  cd /home/dboeckle/frappe-bench/apps/$app
  printf "  %-8s: " "$app"
  git describe --tags --exact-match HEAD 2>/dev/null || git log -1 --format='%h %s' 2>/dev/null
done
