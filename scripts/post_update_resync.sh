#!/usr/bin/env bash
set -e
SCRM=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/crm
DCRM=/home/dboeckle/frappe-bench/apps/crm
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

echo "=== Resync all LCS edits in apps/crm ==="
cp "$SCRM/fcrm/doctype/crm_lead/crm_lead.json"           "$DCRM/crm/fcrm/doctype/crm_lead/crm_lead.json"           && echo "  ~ crm_lead.json"
cp "$SCRM/fcrm/doctype/crm_deal/crm_deal.json"           "$DCRM/crm/fcrm/doctype/crm_deal/crm_deal.json"           && echo "  ~ crm_deal.json"
cp "$SFRO/vite.config.js"                                "$DFRO/vite.config.js"                                    && echo "  ~ vite.config.js"
cp "$SFRO/src/router.js"                                 "$DFRO/src/router.js"                                     && echo "  ~ router.js"
cp "$SFRO/src/components/Layouts/AppSidebar.vue"         "$DFRO/src/components/Layouts/AppSidebar.vue"             && echo "  ~ AppSidebar.vue"
cp "$SFRO/src/components/lcs/ProjectMap.vue"             "$DFRO/src/components/lcs/ProjectMap.vue"                 && echo "  + ProjectMap.vue"
cp "$SFRO/src/pages/Deal.vue"                            "$DFRO/src/pages/Deal.vue"                                && echo "  ~ Deal.vue"
cp "$SFRO/src/pages/Lead.vue"                            "$DFRO/src/pages/Lead.vue"                                && echo "  ~ Lead.vue"
cp "$SFRO/src/pages/LCSOfferDetail.vue"                  "$DFRO/src/pages/LCSOfferDetail.vue"                      && echo "  + LCSOfferDetail.vue"
# LCSProjectsMap.vue + sw.js are already in WSL (they were stashed as untracked, then survived)

echo
echo "=== Drop builder stash (build artefacts, not LCS edits) ==="
cd /home/dboeckle/frappe-bench/apps/builder
git checkout HEAD -- frontend/components.d.ts yarn.lock 2>&1 || true
git stash drop "stash@{0}" 2>&1 | head -2

echo
echo "=== Final status check ==="
cd /home/dboeckle/frappe-bench/apps/crm
git status --porcelain | grep -v -E '\.pyc$|__pycache__|\.cpython-' | head -15
