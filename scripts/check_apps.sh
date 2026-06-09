#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps
for app in frappe erpnext crm hrms lms builder; do
  if [ -d "$app/.git" ]; then
    echo "=== $app ==="
    git -C "$app" log -1 --format='  current: %h %s (%cr)'
    branch=$(git -C "$app" rev-parse --abbrev-ref HEAD)
    upstream=$(git -C "$app" rev-parse --abbrev-ref @{u} 2>/dev/null || echo "(no upstream)")
    echo "  branch: $branch  upstream: $upstream"
    dirty_count=$(git -C "$app" status --porcelain | grep -v -E "^\?\? .*\.pyc$|^.. .*__pycache__|^.. .*\.cpython-" | wc -l)
    echo "  dirty (excl. pycache): $dirty_count"
    if [ "$dirty_count" -gt 0 ] && [ "$dirty_count" -lt 20 ]; then
      git -C "$app" status --porcelain | grep -v -E "^\?\? .*\.pyc$|^.. .*__pycache__|^.. .*\.cpython-" | head -25 | sed 's/^/    /'
    elif [ "$dirty_count" -ge 20 ]; then
      echo "    (showing first 5 of $dirty_count)"
      git -C "$app" status --porcelain | grep -v -E "^\?\? .*\.pyc$|^.. .*__pycache__|^.. .*\.cpython-" | head -5 | sed 's/^/    /'
    fi
    echo
  fi
done
