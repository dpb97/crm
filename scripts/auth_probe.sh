#!/usr/bin/env bash
# Get the admin password from site_config (no quoting drama via subshell python)
ADMIN_PW=$(python3 -c 'import json; print(json.load(open("/home/dboeckle/frappe-bench/sites/lcs.local/site_config.json")).get("admin_password",""))')
echo "  admin_password in site_config: ${ADMIN_PW:+set (len=${#ADMIN_PW})}${ADMIN_PW:-empty}"

# Try several common dev passwords
COOKIE=$(mktemp)
for pw in "$ADMIN_PW" admin Admin1234 frappe; do
  [ -z "$pw" ] && continue
  rm -f "$COOKIE"
  status=$(curl -sS -c "$COOKIE" -d "usr=Administrator&pwd=$pw" \
       -H "Host: lcs.local" \
       "http://127.0.0.1:8000/api/method/login" -o /dev/null -w "%{http_code}")
  if [ "$status" = "200" ]; then
    echo "  ✓ login ok with pw='$pw'"
    break
  else
    echo "  · pw='${pw:0:3}…' -> HTTP $status"
  fi
done

if [ "$status" = "200" ]; then
  echo
  echo "=== scan page as Administrator ==="
  curl -sS -b "$COOKIE" -H "Host: lcs.local" "http://127.0.0.1:8000/bizcard/scan" \
    | grep -E "window\.csrf_token|window\.frappe\.session" | head -3
fi
rm -f "$COOKIE"
