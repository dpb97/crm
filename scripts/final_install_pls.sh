#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda_pls/pilanda_pls
DST=/home/dboeckle/frappe-bench/apps/pilanda_pls/pilanda_pls

echo "=== nuke inner pilanda_pls dir in bench (legacy) ==="
rm -rf "$DST/pilanda_pls"
rm -rf "$DST/pls"

echo "=== copy fresh tree from workspace ==="
cp -r "$SRC/pls" "$DST/pls"
echo "  bench tree (top 3 levels):"
find "$DST" -maxdepth 3 -type d | sort

cd /home/dboeckle/frappe-bench
echo
echo "=== migrate ==="
bench --site lcs.local migrate 2>&1 | grep -iE "Updating DocTypes for pilanda_pls|Fruehwarnung|Transportauftrag|Projektleitstelle|Error|Traceback" | tail -10

echo
echo "=== DocTypes in PLS ==="
bench --site lcs.local execute frappe.client.get_list --kwargs '{"doctype":"DocType","filters":{"module":"PLS"},"fields":["name"]}'
echo
echo "=== Workspace ==="
bench --site lcs.local execute frappe.client.get_value --kwargs '{"doctype":"Workspace","filters":{"name":"Projektleitstelle"},"fieldname":["name","module","icon","sequence_id"]}'
