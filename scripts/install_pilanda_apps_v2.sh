#!/usr/bin/env bash
set -e
BENCH=/home/dboeckle/frappe-bench
PIP="$BENCH/env/bin/pip"

for app in pilanda_vertrieb pilanda_engineering pilanda_field_service; do
  echo "=== pip install -e $app into bench env ==="
  "$PIP" install --quiet -e "$BENCH/apps/$app" 2>&1 | tail -3
done

echo
"$BENCH/env/bin/pip" list 2>/dev/null | grep -i pilanda

echo
echo "=== install-app per site ==="
cd "$BENCH"
for app in pilanda_vertrieb pilanda_engineering pilanda_field_service; do
  echo "--- $app ---"
  bench --site lcs.local install-app "$app" 2>&1 | tail -3
done

echo
echo "=== modules now registered ==="
bench --site lcs.local execute frappe.client.get_list \
  --kwargs '{"doctype":"Module Def","filters":[["app_name","in",["pilanda_vertrieb","pilanda_engineering","pilanda_field_service"]]],"fields":["name","app_name"]}' 2>&1 | tail -3
