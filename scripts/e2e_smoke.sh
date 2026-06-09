#!/usr/bin/env bash
set -e
echo "=== container status ==="
docker ps --filter "name=lcs-bizcard-scanner" --format "  {{.Names}}: {{.Status}} ({{.Ports}})"
echo
echo "=== healthz direct ==="
sleep 2
curl -sS http://localhost:8089/healthz
echo
echo
echo "=== set bench config ==="
cd /home/dboeckle/frappe-bench
bench --site lcs.local set-config bizcard_scanner_url "http://localhost:8089" 2>&1 | tail -2

echo
echo "=== login + Frappe-proxy health ==="
ADMIN_PASS=$(python3 -c 'import json; print(json.load(open("sites/lcs.local/site_config.json")).get("admin_password","admin"))')

COOKIE=$(mktemp)
curl -sS -c "$COOKIE" -d "usr=Administrator&pwd=$ADMIN_PASS" \
     -H "Host: lcs.local" \
     "http://127.0.0.1:8000/api/method/login" -o /dev/null -w "  login HTTP %{http_code}\n"
curl -sS -b "$COOKIE" -H "Host: lcs.local" \
     "http://127.0.0.1:8000/api/method/lcs_bizcard.api.health" | head -c 400
echo
rm -f "$COOKIE"
