#!/usr/bin/env bash
set -e
SLCS=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_integrations
DLCS=/home/dboeckle/frappe-bench/apps/lcs_integrations
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

echo "=== LCS app ==="
mkdir -p "$DLCS/lcs_integrations/currency"
cp "$SLCS/lcs_integrations/currency/__init__.py"   "$DLCS/lcs_integrations/currency/__init__.py"   && echo "  + currency/__init__.py"
cp "$SLCS/lcs_integrations/currency/frankfurter.py" "$DLCS/lcs_integrations/currency/frankfurter.py" && echo "  + currency/frankfurter.py"
cp "$SLCS/lcs_integrations/currency/api.py"        "$DLCS/lcs_integrations/currency/api.py"        && echo "  + currency/api.py"

cp "$SLCS/lcs_integrations/lcs_integrations/doctype/lcs_offer/lcs_offer.json" "$DLCS/lcs_integrations/lcs_integrations/doctype/lcs_offer/lcs_offer.json" && echo "  ~ lcs_offer.json"
cp "$SLCS/lcs_integrations/lcs_integrations/doctype/lcs_offer/lcs_offer.py"   "$DLCS/lcs_integrations/lcs_integrations/doctype/lcs_offer/lcs_offer.py"   && echo "  ~ lcs_offer.py"

echo
echo "=== Frontend ==="
cp "$SFRO/src/pages/LCSOfferDetail.vue" "$DFRO/src/pages/LCSOfferDetail.vue" && echo "  ~ pages/LCSOfferDetail.vue"
