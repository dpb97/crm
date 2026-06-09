#!/usr/bin/env bash
echo "=== Versions ==="
for app in frappe erpnext crm hrms lms builder; do
  cd /home/dboeckle/frappe-bench/apps/$app
  printf "  %-8s: %s\n" "$app" "$(git describe --tags --exact-match HEAD 2>/dev/null || git log -1 --format='%h')"
done

echo
echo "=== Endpoints ==="
printf "  ping            : "
curl -s -m 3 -H "Host: lcs.local" http://127.0.0.1:8000/api/method/ping
echo
printf "  /bizcard/scan   : "
curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 3 -H "Host: lcs.local" http://127.0.0.1:8000/bizcard/scan
printf "  /crm            : "
curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 3 -H "Host: lcs.local" http://127.0.0.1:8000/crm
printf "  OCR healthz     : "
curl -s -m 3 http://localhost:8089/healthz
echo

echo
echo "=== Asset freshness (CRM SPA build) ==="
ls -lt /home/dboeckle/frappe-bench/apps/crm/crm/public/frontend/assets/ 2>&1 | head -3
