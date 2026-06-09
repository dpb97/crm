#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps
for app in frappe erpnext crm hrms lms builder lcs_bizcard lcs_integrations; do
  if [ -d "$app/.git" ]; then
    dirty=$(git -C "$app" status --porcelain | grep -v -E '^\?\? .*\.pyc$|^.. .*__pycache__|^.. .*\.cpython-' | wc -l)
    head=$(git -C "$app" log -1 --format='%h')
    branch=$(git -C "$app" rev-parse --abbrev-ref HEAD)
    printf "  %-18s branch=%-7s HEAD=%s dirty=%s\n" "$app" "$branch" "$head" "$dirty"
  fi
done
