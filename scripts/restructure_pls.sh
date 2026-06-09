#!/usr/bin/env bash
set -e
DST=/home/dboeckle/frappe-bench/apps/pilanda_pls/pilanda_pls/pilanda_pls
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda_pls/pilanda_pls/pilanda_pls

echo "=== nuke + restore tree ==="
rm -rf "$DST/doctype" "$DST/workspace" "$DST/page" "$DST/pls"
mkdir -p "$DST/pls"
cp -r "$SRC/pls/." "$DST/pls/"
echo "  current under $DST:"
find "$DST" -maxdepth 3 -type d | sort

echo
cd /home/dboeckle/frappe-bench
echo "=== migrate ==="
bench --site lcs.local migrate 2>&1 | grep -iE "Updating DocTypes for pilanda_pls|Fruehwarnung|Transportauftrag|Workspace|Error|Traceback" | tail -20

echo
echo "=== DocTypes in PLS ==="
bench --site lcs.local execute frappe.client.get_list --kwargs '{"doctype":"DocType","filters":{"module":"PLS"},"fields":["name"]}'
echo
echo "=== Workspace ==="
bench --site lcs.local execute frappe.client.get_value --kwargs '{"doctype":"Workspace","filters":{"name":"Projektleitstelle"},"fieldname":["name","module","icon"]}'
