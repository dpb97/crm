#!/usr/bin/env bash
ADMIN_PASS=$(python3 -c 'import json; print(json.load(open("/home/dboeckle/frappe-bench/sites/lcs.local/site_config.json")).get("admin_password","admin"))')
echo "  admin pw resolved (length=${#ADMIN_PASS})"

COOKIE=$(mktemp)
echo
echo "=== login ==="
curl -sS -c "$COOKIE" -d "usr=Administrator&pwd=$ADMIN_PASS" \
     -H "Host: lcs.local" \
     "http://127.0.0.1:8000/api/method/login" -o /dev/null -w "  HTTP %{http_code}\n"

echo
echo "=== fetch /bizcard/scan as logged-in user, look for csrf_token in HTML ==="
curl -sS -b "$COOKIE" -H "Host: lcs.local" "http://127.0.0.1:8000/bizcard/scan" | grep -oE "csrf_token[^,\"]{0,80}" | head -3
echo
echo "=== first 30 lines of rendered page ==="
curl -sS -b "$COOKIE" -H "Host: lcs.local" "http://127.0.0.1:8000/bizcard/scan" | head -30

rm -f "$COOKIE"
