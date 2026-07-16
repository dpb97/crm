#!/usr/bin/env bash
set -e
ROOT=/home/dboeckle/frappe-bench/apps/next_pms/next_pms
for f in $(find $ROOT -path "*/doctype/*.json" -not -path "*__pycache__*" -not -path "*test*" -not -name "Untitled*"); do
  echo "===== $(echo $f | sed "s|$ROOT/||") ====="
  /home/dboeckle/frappe-bench/env/bin/python -c "
import json, sys
d = json.load(open('$f'))
print('  name :', d.get('name'))
print('  module:', d.get('module'))
print('  is_child:', d.get('istable',0))
print('  is_single:', d.get('issingle',0))
print('  fields:')
for fld in d.get('fields', []):
    ft = fld.get('fieldtype','')
    if ft in ('Section Break','Column Break','Tab Break','HTML'): continue
    extra = []
    if fld.get('reqd'): extra.append('reqd')
    if fld.get('options') and ft in ('Link','Table','Table MultiSelect','Dynamic Link','Select'):
        extra.append(repr(fld.get('options')[:60]))
    print('    {:30s} {:20s} {}'.format(fld.get('fieldname',''), ft, ' '.join(extra)))
"
  echo
done
