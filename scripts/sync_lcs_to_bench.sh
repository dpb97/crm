#!/usr/bin/env bash
# Sync Phase A-F LCS additions from the Windows workspace into the
# WSL frappe-bench app directory. Idempotent — re-running just
# overwrites with current workspace state.

set -euo pipefail

S=/mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_integrations
D=/home/dboeckle/frappe-bench/apps/lcs_integrations

if [[ ! -d "$S" || ! -d "$D" ]]; then
  echo "ERROR: source or destination missing" >&2
  echo "  S=$S"
  echo "  D=$D"
  exit 1
fi

echo ">>> Copy NEW doctype dirs"
for d in lcs_segment lcs_sales_territory lcs_sales_territory_country lcs_sales_territory_segment lcs_segment_responsibility lcs_trip_report lcs_business_card_ocr_settings; do
  cp -r "$S/lcs_integrations/lcs_integrations/doctype/$d" "$D/lcs_integrations/lcs_integrations/doctype/"
  echo "  + doctype/$d"
done

echo ">>> Copy NEW module dirs"
for d in territory followups contacts reporting; do
  cp -r "$S/lcs_integrations/$d" "$D/lcs_integrations/"
  echo "  + $d"
done

echo ">>> Copy NEW patches"
for p in seed_market_split.py install_pipeline_qualification_fields.py migrate_project_phase.py install_followup_fields.py; do
  cp "$S/lcs_integrations/patches/$p" "$D/lcs_integrations/patches/"
  echo "  + patches/$p"
done

echo ">>> Overwrite CHANGED files"
cp "$S/lcs_integrations/hooks.py"                                                 "$D/lcs_integrations/hooks.py"                                                 && echo "  ~ hooks.py"
cp "$S/lcs_integrations/patches.txt"                                              "$D/lcs_integrations/patches.txt"                                              && echo "  ~ patches.txt"
cp "$S/lcs_integrations/patches/v1_0/install_custom_fields.py"                    "$D/lcs_integrations/patches/v1_0/install_custom_fields.py"                    && echo "  ~ install_custom_fields.py"
cp "$S/lcs_integrations/lcs_integrations/doctype/lcs_project/lcs_project.json"    "$D/lcs_integrations/lcs_integrations/doctype/lcs_project/lcs_project.json"    && echo "  ~ lcs_project.json"

echo
echo ">>> Done."
