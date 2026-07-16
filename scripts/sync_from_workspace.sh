#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard

echo "=== source repo HEAD ==="
git -C "$SRC" log --oneline -1

echo
echo "=== fetch from workspace repo (works without GitHub auth) ==="
cd "$DST"
git remote set-url origin "$SRC" 2>&1
git fetch origin --quiet 2>&1
git checkout main 2>&1 | tail -2
git reset --hard origin/main 2>&1 | tail -2

echo
echo "=== restore GitHub origin so future pushes go right ==="
git remote set-url origin https://github.com/Pilanda-ERP/frappe-bizcard-scanner.git
git log --oneline -1
