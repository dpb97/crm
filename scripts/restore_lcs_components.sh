#!/usr/bin/env bash
set -e
SFRO=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/frontend
DFRO=/home/dboeckle/frappe-bench/apps/crm/frontend

echo "=== rsync LCS components and pages from workspace ==="
mkdir -p "$DFRO/src/components/lcs"
# Use cp -r so we recreate the whole lcs/ subtree
cp -ru "$SFRO/src/components/lcs/." "$DFRO/src/components/lcs/"
echo "  components: $(ls "$DFRO/src/components/lcs/" | wc -l) files"

# Also resync the LCS-prefixed pages in case anything else got wiped
for f in LCSProjects.vue LCSProject.vue LCSForecasting.vue LCSQuickNote.vue \
         LCSOfferDetail.vue LCSProjectsMap.vue; do
  if [ -f "$SFRO/src/pages/$f" ]; then
    cp "$SFRO/src/pages/$f" "$DFRO/src/pages/$f"
    echo "  page: $f"
  fi
done

echo
echo "=== Status (excl. pycache/components.d.ts) ==="
cd /home/dboeckle/frappe-bench/apps/crm
git status --porcelain | grep -v -E '\.pyc$|__pycache__|\.cpython-' | wc -l
echo "  → expected: 9 modified + several untracked"
