#!/usr/bin/env bash
cd /home/dboeckle/frappe-bench/apps/crm
for f in \
  crm/fcrm/doctype/crm_lead/crm_lead.json \
  crm/fcrm/doctype/crm_deal/crm_deal.json \
  frontend/vite.config.js \
  frontend/src/router.js \
  frontend/src/components/Layouts/AppSidebar.vue \
  frontend/src/pages/Deal.vue \
  frontend/src/pages/Lead.vue
do
  n=$(git log --oneline v1.71.4..v1.72.0 -- "$f" 2>&1 | wc -l)
  echo "  $f: $n commits"
done
