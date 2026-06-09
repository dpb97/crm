#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard
cp "$SRC/docker/app/parser.py" "$DST/docker/app/parser.py"
cd "$DST/docker"
docker compose up -d --build 2>&1 | tail -4
