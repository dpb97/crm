#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps/crm

# What did upstream change in each conflicted file between v1.71.0..v1.71.4?
for f in frontend/src/components/Layouts/AppSidebar.vue \
         frontend/src/pages/Deal.vue \
         frontend/src/pages/Lead.vue \
         frontend/src/router.js; do
  echo "===== $f ====="
  echo "--- upstream v1.71.0..v1.71.4 ---"
  git log --oneline v1.71.0..v1.71.4 -- "$f" 2>&1 | head -8
  git diff v1.71.0..v1.71.4 -- "$f" 2>&1 | head -30
  echo
done
