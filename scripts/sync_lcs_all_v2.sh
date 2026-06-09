#!/usr/bin/env bash
set -e
S=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo
D=/home/dboeckle/frappe-bench/apps/crm

echo "=== Resync LCS-touched upstream files (kein Konflikt mit v1.72.0) ==="
cp "$S/crm/fcrm/doctype/crm_lead/crm_lead.json"            "$D/crm/fcrm/doctype/crm_lead/crm_lead.json"
cp "$S/crm/fcrm/doctype/crm_deal/crm_deal.json"            "$D/crm/fcrm/doctype/crm_deal/crm_deal.json"
cp "$S/frontend/vite.config.js"                            "$D/frontend/vite.config.js"
cp "$S/frontend/src/router.js"                             "$D/frontend/src/router.js"
echo "  ~ crm_lead/deal.json · vite.config.js · router.js"

echo
echo "=== Resync LCS-only frontend tree ==="
# LCS pages
for p in LCSProjects.vue LCSProject.vue LCSForecasting.vue LCSQuickNote.vue LCSOfferDetail.vue LCSProjectsMap.vue; do
  cp "$S/frontend/src/pages/$p" "$D/frontend/src/pages/$p" 2>/dev/null && echo "  + pages/$p" || true
done
# LCS components directory
mkdir -p "$D/frontend/src/components/lcs"
cp -r "$S/frontend/src/components/lcs/." "$D/frontend/src/components/lcs/"
echo "  + components/lcs/ ($(ls "$D/frontend/src/components/lcs/" | wc -l) files)"
# LCS composables + utils
for c in useUserPreferences.js useOfflineDoc.js useOfflineList.js; do
  [ -f "$S/frontend/src/composables/$c" ] && cp "$S/frontend/src/composables/$c" "$D/frontend/src/composables/$c" && echo "  + composables/$c"
done
mkdir -p "$D/frontend/src/utils"
for u in offlineDB.js syncEngine.js; do
  [ -f "$S/frontend/src/utils/$u" ] && cp "$S/frontend/src/utils/$u" "$D/frontend/src/utils/$u" && echo "  + utils/$u"
done
# Custom service worker
[ -f "$S/frontend/src/sw.js" ] && cp "$S/frontend/src/sw.js" "$D/frontend/src/sw.js" && echo "  + src/sw.js"
