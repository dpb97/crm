#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/frappe-bizcard-scanner
DST=/home/dboeckle/frappe-bench/apps/lcs_bizcard

echo "=== sync docker/ tree ==="
mkdir -p "$DST/docker/app/engines"
cp "$SRC/docker/Dockerfile"             "$DST/docker/Dockerfile"
cp "$SRC/docker/docker-compose.yml"     "$DST/docker/docker-compose.yml"
cp "$SRC/docker/requirements.txt"       "$DST/docker/requirements.txt"
cp "$SRC/docker/app/main.py"            "$DST/docker/app/main.py"
cp "$SRC/docker/app/ocr.py"             "$DST/docker/app/ocr.py"
cp "$SRC/docker/app/parser.py"          "$DST/docker/app/parser.py"
cp "$SRC/docker/app/preprocess.py"      "$DST/docker/app/preprocess.py"
cp "$SRC/docker/app/engines/__init__.py" "$DST/docker/app/engines/__init__.py"
cp "$SRC/docker/app/engines/tesseract.py" "$DST/docker/app/engines/tesseract.py"
cp "$SRC/docker/app/engines/paddle.py"  "$DST/docker/app/engines/paddle.py"
echo "  ✓ files synced"

echo
echo "=== rebuild + restart container ==="
cd "$DST/docker"
docker compose up -d --build 2>&1 | tail -8
