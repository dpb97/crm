#!/usr/bin/env bash
set -e
SLCS=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_integrations
DLCS=/home/dboeckle/frappe-bench/apps/lcs_integrations
SCRM=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/crm
DCRM=/home/dboeckle/frappe-bench/apps/crm

echo "=== LCS app ==="
cp "$SLCS/lcs_integrations/patches.txt"                                              "$DLCS/lcs_integrations/patches.txt"                                              && echo "  ~ lcs_integrations/patches.txt"
cp "$SLCS/lcs_integrations/patches/v1_0/install_custom_fields.py"                    "$DLCS/lcs_integrations/patches/v1_0/install_custom_fields.py"                    && echo "  ~ patches/v1_0/install_custom_fields.py"
cp "$SLCS/lcs_integrations/patches/drop_lead_deal_qualification_custom_fields.py"    "$DLCS/lcs_integrations/patches/drop_lead_deal_qualification_custom_fields.py"    && echo "  + patches/drop_lead_deal_qualification_custom_fields.py"

# Remove the obsolete patch file (the new flow no longer references it)
if [ -f "$DLCS/lcs_integrations/patches/install_pipeline_qualification_fields.py" ]; then
  rm "$DLCS/lcs_integrations/patches/install_pipeline_qualification_fields.py" && echo "  - removed obsolete patches/install_pipeline_qualification_fields.py"
fi

echo
echo "=== CRM app (UPSTREAM TOUCH) ==="
cp "$SCRM/fcrm/doctype/crm_lead/crm_lead.json"  "$DCRM/crm/fcrm/doctype/crm_lead/crm_lead.json"  && echo "  ~ crm/fcrm/doctype/crm_lead/crm_lead.json"
cp "$SCRM/fcrm/doctype/crm_deal/crm_deal.json"  "$DCRM/crm/fcrm/doctype/crm_deal/crm_deal.json"  && echo "  ~ crm/fcrm/doctype/crm_deal/crm_deal.json"
