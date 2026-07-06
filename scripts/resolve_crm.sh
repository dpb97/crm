#!/usr/bin/env bash
set -e
cd /home/dboeckle/frappe-bench/apps/crm

echo "=== Reset conflicted files to v1.71.4 ==="
git restore --staged --worktree -- \
  frontend/src/components/Layouts/AppSidebar.vue \
  frontend/src/pages/Deal.vue \
  frontend/src/pages/Lead.vue \
  frontend/src/router.js \
  crm/fcrm/doctype/crm_deal/crm_deal.json \
  crm/fcrm/doctype/crm_lead/crm_lead.json \
  frontend/vite.config.js \
  frontend/auto-imports.d.ts 2>&1 || true
git checkout HEAD -- \
  frontend/src/components/Layouts/AppSidebar.vue \
  frontend/src/pages/Deal.vue \
  frontend/src/pages/Lead.vue \
  frontend/src/router.js \
  crm/fcrm/doctype/crm_deal/crm_deal.json \
  crm/fcrm/doctype/crm_lead/crm_lead.json \
  frontend/vite.config.js 2>&1 || true

echo
echo "=== Remove the deleted-by-us LCS files that the merge left behind ==="
# stash pop left them as "DU" (deleted upstream, modified by us). Since they
# are LCS-additive, we'll restore them from the workspace below.
rm -f frontend/src/components/lcs/ProjectMap.vue \
      frontend/src/pages/LCSOfferDetail.vue 2>&1 || true
git rm -f --cached frontend/src/components/lcs/ProjectMap.vue \
                    frontend/src/pages/LCSOfferDetail.vue 2>/dev/null || true

echo
echo "=== Drop the stash (we apply from workspace instead) ==="
git stash drop "stash@{0}" 2>&1 | head -2

echo
echo "=== Status after reset ==="
git status --porcelain | grep -v -E '\.pyc$|__pycache__|\.cpython-' | head -20
