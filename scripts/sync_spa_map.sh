#!/usr/bin/env bash
set -e
SLCS=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_integrations
DLCS=/home/dboeckle/frappe-bench/apps/lcs_integrations
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

echo "=== Remove obsolete desk page in WSL ==="
rm -rf "$DLCS/lcs_integrations/lcs_integrations/page/lcs_projects_map" && echo "  - page/lcs_projects_map/"

echo
echo "=== Updated backend (latitude/longitude) ==="
cp "$SLCS/lcs_integrations/projects/map_api.py" "$DLCS/lcs_integrations/projects/map_api.py" && echo "  ~ projects/map_api.py"

echo
echo "=== Frontend (LCS-owned + upstream-additive) ==="
cp "$SFRO/src/components/lcs/ProjectMap.vue"   "$DFRO/src/components/lcs/ProjectMap.vue"   && echo "  ~ components/lcs/ProjectMap.vue (heightClass prop)"
cp "$SFRO/src/pages/LCSProjectsMap.vue"        "$DFRO/src/pages/LCSProjectsMap.vue"        && echo "  + pages/LCSProjectsMap.vue"
cp "$SFRO/src/router.js"                       "$DFRO/src/router.js"                       && echo "  ~ router.js (route added)"
cp "$SFRO/src/components/Layouts/AppSidebar.vue" "$DFRO/src/components/Layouts/AppSidebar.vue" && echo "  ~ AppSidebar.vue (sidebar entry)"
