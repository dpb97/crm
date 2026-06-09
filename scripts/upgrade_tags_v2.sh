#!/usr/bin/env bash
set -e
cd /home/dboeckle/frappe-bench/apps

declare -A TARGETS=(
  ["frappe"]="v16.18.3"
  ["erpnext"]="v16.19.1"
  ["hrms"]="v16.7.1"
  ["lms"]="v2.54.2"
  ["builder"]="v1.24.7"
  ["crm"]="v1.72.0"
)

for app in frappe erpnext hrms lms builder crm; do
  tag="${TARGETS[$app]}"
  echo
  echo "=== $app → $tag ==="
  before=$(git -C "$app" log -1 --format='%h')
  git -C "$app" fetch upstream --tags --quiet 2>&1 | tail -3
  if ! git -C "$app" rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    echo "  ! tag $tag not found, skipping"
    continue
  fi
  git -C "$app" checkout "$tag" 2>&1 | tail -2
  echo "  $before → $(git -C "$app" log -1 --format='%h %s')"
done
