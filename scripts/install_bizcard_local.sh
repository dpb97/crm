#!/usr/bin/env bash
set -e

SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard

echo "=== copy workspace → bench apps dir ==="
# Use git clone of the local workspace, not raw cp, so the destination
# carries a real .git/ — pip install -e and Frappe both prefer that.
cd /home/dboeckle/frappe-bench/apps
git clone "$SRC" lcs_bizcard 2>&1 | tail -3

echo
echo "=== register origin to GitHub so future bench update can fetch ==="
cd lcs_bizcard
git remote set-url origin https://github.com/Pilanda-ERP/frappe-bizcard-scanner.git
git remote -v

echo
echo "=== pip install -e ==="
cd /home/dboeckle/frappe-bench
env/bin/pip install --quiet -e apps/lcs_bizcard 2>&1 | tail -3

echo
echo "=== ensure app appears in apps.txt and apps.json ==="
if ! grep -q '^lcs_bizcard$' sites/apps.txt 2>/dev/null; then
  echo "lcs_bizcard" >> sites/apps.txt
  echo "  + added to sites/apps.txt"
else
  echo "  ✓ already in sites/apps.txt"
fi

echo
echo "=== assets symlink ==="
mkdir -p sites/assets
if [ ! -L sites/assets/lcs_bizcard ]; then
  ln -sfn /home/dboeckle/frappe-bench/apps/lcs_bizcard/lcs_bizcard/public sites/assets/lcs_bizcard
fi
ls -la sites/assets/lcs_bizcard 2>&1 | head -2
