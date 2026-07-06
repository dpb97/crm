#!/usr/bin/env bash
set -e
DST=/home/dboeckle/frappe-bench/apps/pilanda_pls/pilanda_pls/pilanda_pls
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda_pls/pilanda_pls/pilanda_pls

rm -rf "$DST/pls"
cp -r "$SRC/pls" "$DST/pls"
echo "  ✓ rebuilt $DST/pls"

find "$DST/pls" -type f -not -name "*.pyc" 2>&1
