#!/usr/bin/env bash
#
# Copy + pip install -e + register the three new Pilanda apps
# (pilanda_vertrieb, pilanda_engineering, pilanda_field_service)
# in the bench at /home/dboeckle/frappe-bench/.
#
# Idempotent — re-running refreshes the in-bench source from the
# workspace and only appends to apps.txt if the entry is missing.

set -e

WORKSPACE=/mnt/c/Users/d.boeckle/Dev
BENCH=/home/dboeckle/frappe-bench
PY=/home/dboeckle/.local/share/uv/tools/frappe-bench/bin/python

install_one () {
  local app="$1"
  local src="$WORKSPACE/$app"
  local dst="$BENCH/apps/$app"

  echo "=== installing $app ==="
  if [ -d "$dst" ]; then
    echo "  already in bench, refreshing"
    rm -rf "$dst"
  fi
  cp -r "$src" "$dst"

  # pip install -e so frappe picks up live source edits
  "$PY" -m pip install --quiet -e "$dst" 2>&1 | tail -2 || true

  # apps.txt: ensure trailing newline first, then append if missing
  if ! grep -qxF "$app" "$BENCH/sites/apps.txt"; then
    tail -c1 "$BENCH/sites/apps.txt" | xxd -p | grep -q "0a" || echo "" >> "$BENCH/sites/apps.txt"
    echo "$app" >> "$BENCH/sites/apps.txt"
    echo "  added to sites/apps.txt"
  fi
  echo
}

install_one pilanda_vertrieb
install_one pilanda_engineering
install_one pilanda_field_service

echo "=== sites/apps.txt now ==="
cat "$BENCH/sites/apps.txt"
echo
echo "=== bench install-app per site ==="
cd "$BENCH"
for app in pilanda_vertrieb pilanda_engineering pilanda_field_service; do
  bench --site lcs.local install-app "$app" 2>&1 | tail -3
done
