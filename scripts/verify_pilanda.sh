#!/usr/bin/env bash
echo "=== installed apps (site=lcs.local) ==="
/home/dboeckle/.local/bin/bench --site lcs.local list-apps 2>&1 | grep -E "pilanda|frappe |erpnext " | head
echo
echo "=== workspaces in DB ==="
/home/dboeckle/.local/bin/bench --site lcs.local execute frappe.client.get_list \
  --kwargs '{"doctype":"Workspace","filters":{"module":"Pilanda"},"fields":["name","category","sequence_id"],"order_by":"sequence_id","limit_page_length":30}' 2>&1 | tail -3
echo
echo "=== home page status ==="
/home/dboeckle/.local/bin/bench --site lcs.local execute frappe.client.get_value \
  --kwargs '{"doctype":"Page","filters":{"name":"pilanda-home"},"fieldname":["name","title","module"]}' 2>&1 | tail -3
