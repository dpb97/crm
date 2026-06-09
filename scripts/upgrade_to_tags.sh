#!/usr/bin/env bash
set -e
cd /home/dboeckle/frappe-bench/apps

declare -A TARGETS=(
  ["frappe"]="v16.18.2"
  ["erpnext"]="v16.18.3"
  ["hrms"]="v16.7.0"
  ["lms"]="v2.54.1"
  ["builder"]="v1.24.6"
  ["crm"]="v1.71.4"
)

for app in "${!TARGETS[@]}"; do
  tag="${TARGETS[$app]}"
  echo
  echo "=== $app -> $tag ==="
  before=$(git -C "$app" log -1 --format='%h')

  git -C "$app" fetch upstream --tags --quiet 2>&1 | tail -3
  if ! git -C "$app" rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    echo "  ! tag $tag not found after fetch — skipping"
    continue
  fi

  git -C "$app" checkout "$tag" 2>&1 | tail -3
  after=$(git -C "$app" log -1 --format='%h %s')
  echo "  $before -> $after"
done
