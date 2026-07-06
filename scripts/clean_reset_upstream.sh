#!/usr/bin/env bash
set -e
cd /home/dboeckle/frappe-bench/apps/crm

echo "=== Reset Deal.vue + Lead.vue to v1.71.4 (LCS edits no longer needed) ==="
git checkout HEAD -- frontend/src/pages/Deal.vue frontend/src/pages/Lead.vue
echo "  ✓"
