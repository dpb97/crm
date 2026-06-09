#!/usr/bin/env bash
set -e
SLCS=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_integrations
DLCS=/home/dboeckle/frappe-bench/apps/lcs_integrations

echo "=== Copy map backend ==="
cp "$SLCS/lcs_integrations/projects/map_api.py" "$DLCS/lcs_integrations/projects/map_api.py" && echo "  + projects/map_api.py"

echo
echo "=== Copy desk page ==="
mkdir -p "$DLCS/lcs_integrations/lcs_integrations/page/lcs_projects_map"
for f in __init__.py lcs_projects_map.json lcs_projects_map.py lcs_projects_map.js; do
  cp "$SLCS/lcs_integrations/lcs_integrations/page/lcs_projects_map/$f" \
     "$DLCS/lcs_integrations/lcs_integrations/page/lcs_projects_map/$f" && echo "  + page/lcs_projects_map/$f"
done
