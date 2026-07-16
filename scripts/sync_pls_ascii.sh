#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda_pls
DST=/home/dboeckle/frappe-bench/apps/pilanda_pls

cp "$SRC/pilanda_pls/pilanda_pls/doctype/lcs_fruehwarnung/lcs_fruehwarnung.json" "$DST/pilanda_pls/pilanda_pls/doctype/lcs_fruehwarnung/lcs_fruehwarnung.json"
cp "$SRC/pilanda_pls/pilanda_pls/doctype/lcs_fruehwarnung/lcs_fruehwarnung.py"   "$DST/pilanda_pls/pilanda_pls/doctype/lcs_fruehwarnung/lcs_fruehwarnung.py"
cp "$SRC/pilanda_pls/pilanda_pls/workspace/projektleitstelle/projektleitstelle.json" "$DST/pilanda_pls/pilanda_pls/workspace/projektleitstelle/projektleitstelle.json"
cp "$SRC/pilanda_pls/www/pls.py"   "$DST/pilanda_pls/www/pls.py"
cp "$SRC/pilanda_pls/www/pls.html" "$DST/pilanda_pls/www/pls.html"
echo "  ~ synced"

cd /home/dboeckle/frappe-bench
echo
echo "=== migrate ==="
bench --site lcs.local migrate 2>&1 | grep -iE "pilanda_pls|Fruehwarnung|Transportauftrag|Workspace|Removing orphan|Error|Updating DocTypes for pilanda_pls" | tail -15
echo
echo "=== verify ==="
bench --site lcs.local execute frappe.client.get_list --kwargs '{"doctype":"DocType","filters":{"module":"PLS"},"fields":["name"]}'
echo
bench --site lcs.local execute frappe.client.get_value --kwargs '{"doctype":"Workspace","filters":{"name":"Projektleitstelle"},"fieldname":["name","module","icon","sequence_id"]}'
