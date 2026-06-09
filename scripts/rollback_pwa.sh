#!/usr/bin/env bash
set -e
D=/home/dboeckle/frappe-bench/apps/crm/frontend
# Restore upstream index.html from git
cd "$D" && git checkout -- index.html && echo "  ~ restored upstream index.html"
# Remove our extra public files that would clobber vite-plugin-pwa
for f in lcs-pwa-bootstrap.js manifest.webmanifest sw.js; do
  if [ -f "$D/public/$f" ]; then
    rm "$D/public/$f" && echo "  - removed public/$f"
  fi
done
