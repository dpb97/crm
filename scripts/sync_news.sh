#!/usr/bin/env bash
set -e
SRC=/mnt/c/Users/d.boeckle/Dev/pilanda
DST=/home/dboeckle/frappe-bench/apps/pilanda

echo "=== flatten leftover extra-level doctype dir (one-time cleanup) ==="
if [ -d "$DST/pilanda/pilanda/pilanda" ]; then
  rm -rf "$DST/pilanda/pilanda/pilanda"
fi
mkdir -p "$DST/pilanda/pilanda/doctype/pilanda_news"
mkdir -p "$DST/pilanda/templates/includes"
mkdir -p "$DST/pilanda/www/news"

echo "=== copy app files ==="
cp "$SRC/pilanda/hooks.py"                                                "$DST/pilanda/hooks.py"
cp "$SRC/pilanda/api.py"                                                  "$DST/pilanda/api.py"
cp "$SRC/pilanda/public/css/pilanda.css"                                  "$DST/pilanda/public/css/pilanda.css"
cp "$SRC/pilanda/www/pilanda.py"                                          "$DST/pilanda/www/pilanda.py"
cp "$SRC/pilanda/www/pilanda.html"                                        "$DST/pilanda/www/pilanda.html"
cp "$SRC/pilanda/www/news_detail.py"                                      "$DST/pilanda/www/news_detail.py"
cp "$SRC/pilanda/www/news_detail.html"                                    "$DST/pilanda/www/news_detail.html"
cp "$SRC/pilanda/www/news/__init__.py"                                    "$DST/pilanda/www/news/__init__.py"
cp "$SRC/pilanda/www/news/index.py"                                       "$DST/pilanda/www/news/index.py"
cp "$SRC/pilanda/www/news/index.html"                                     "$DST/pilanda/www/news/index.html"
cp "$SRC/pilanda/templates/includes/pilanda_sidebar.html"                 "$DST/pilanda/templates/includes/pilanda_sidebar.html"

# DocType (correct layout: app / module-slug / doctype / doctype-slug)
cp "$SRC/pilanda/pilanda/__init__.py"                                     "$DST/pilanda/pilanda/__init__.py" 2>/dev/null || true
cp "$SRC/pilanda/pilanda/doctype/__init__.py"                             "$DST/pilanda/pilanda/doctype/__init__.py"
cp "$SRC/pilanda/pilanda/doctype/pilanda_news/__init__.py"                "$DST/pilanda/pilanda/doctype/pilanda_news/__init__.py"
cp "$SRC/pilanda/pilanda/doctype/pilanda_news/pilanda_news.json"          "$DST/pilanda/pilanda/doctype/pilanda_news/pilanda_news.json"
cp "$SRC/pilanda/pilanda/doctype/pilanda_news/pilanda_news.py"            "$DST/pilanda/pilanda/doctype/pilanda_news/pilanda_news.py"

echo "  ~ files copied"
find "$DST/pilanda/pilanda/doctype/pilanda_news" -type f

cd /home/dboeckle/frappe-bench
echo
echo "=== migrate ==="
bench --site lcs.local migrate 2>&1 | grep -iE "Updating DocTypes for pilanda|Pilanda News|Error|Traceback" | tail -10
echo
echo "=== clear cache ==="
bench --site lcs.local clear-website-cache 2>&1 | tail -1
bench --site lcs.local clear-cache 2>&1 | tail -1
