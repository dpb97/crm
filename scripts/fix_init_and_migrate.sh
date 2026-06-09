#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda
DST=/home/dboeckle/frappe-bench/apps/pilanda
# Mirror the new __init__ files from workspace -> bench
cp "$SRC/pilanda/pilanda/__init__.py"      "$DST/pilanda/pilanda/__init__.py"
cp "$SRC/pilanda/pilanda/page/__init__.py" "$DST/pilanda/pilanda/page/__init__.py"
cp "$SRC/pilanda/www/__init__.py"          "$DST/pilanda/www/__init__.py"
echo "  ✓ synced __init__.py files"

cd /home/dboeckle/frappe-bench
/home/dboeckle/.local/bin/bench --site lcs.local migrate 2>&1 | grep -iE "Error|Executing|pilanda|Workspace|Removing orphan|Traceback|completed|Syncing" | tail -25
