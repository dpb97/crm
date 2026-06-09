#!/usr/bin/env bash
set -e
SLCS=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_integrations
DLCS=/home/dboeckle/frappe-bench/apps/lcs_integrations
SCRM=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/crm
DCRM=/home/dboeckle/frappe-bench/apps/crm
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

echo "=== Sync icons ==="
mkdir -p "$DLCS/lcs_integrations/public/manifest"
cp "$SLCS/lcs_integrations/public/manifest/lcs-icon-192.maskable.png" "$DLCS/lcs_integrations/public/manifest/lcs-icon-192.maskable.png" && echo "  + 192 icon"
cp "$SLCS/lcs_integrations/public/manifest/lcs-icon-512.maskable.png" "$DLCS/lcs_integrations/public/manifest/lcs-icon-512.maskable.png" && echo "  + 512 icon"

echo
echo "=== Sync vite.config.js (UPSTREAM TOUCH) ==="
cp "$SFRO/vite.config.js" "$DFRO/vite.config.js" && echo "  ~ vite.config.js"
