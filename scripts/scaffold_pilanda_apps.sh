#!/usr/bin/env bash
#
# Scaffold three sibling Pilanda Frappe apps following the
# pilanda_pls layout: pilanda_vertrieb, pilanda_engineering,
# pilanda_field_service. Each becomes its own local repo
# (init only, no remote) and ships with a minimal hooks.py
# + module folder so `bench get-app` + `bench install-app`
# succeed straight away.
#
# Idempotent: running the script twice is a no-op (skip if
# the workspace already contains the app dir).

set -e

WORKSPACE=/mnt/c/Users/d.boeckle/Dev

scaffold_app () {
  local app="$1"      # pilanda_vertrieb
  local title="$2"    # "Pilanda Vertrieb"
  local desc="$3"     # one-line description
  local module="$4"   # "Vertrieb" (display)
  local slug="$5"     # vertrieb (snake_case dir)

  local root="$WORKSPACE/$app"
  if [ -d "$root" ]; then
    echo "skip $app — already scaffolded"
    return 0
  fi

  echo "scaffolding $app …"
  mkdir -p "$root/$app/$slug/doctype"

  # ---- README ----------------------------------------------------
  cat > "$root/README.md" <<EOF
# $title

$desc

Part of the Pilanda umbrella stack — see the \`pilanda\` repo for
the navigation, brand and intranet landing. This app owns the
domain logic for the **$module** module.

## Local install

\`\`\`bash
bench get-app file:///mnt/c/Users/d.boeckle/Dev/$app
bench --site lcs.local install-app $app
\`\`\`

## Layout

\`\`\`
$app/
├── pyproject.toml
├── README.md
├── license.txt
└── $app/
    ├── hooks.py
    ├── modules.txt
    ├── patches.txt
    └── $slug/        # the "$module" Frappe module
        └── doctype/
\`\`\`
EOF

  # ---- license ---------------------------------------------------
  echo "Proprietary — LCS Group internal use only." > "$root/license.txt"

  # ---- .gitignore -----------------------------------------------
  cat > "$root/.gitignore" <<'EOF'
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
node_modules/
public/dist/
.env
.env.*
*.local
.DS_Store
Thumbs.db
EOF

  # ---- pyproject.toml -------------------------------------------
  cat > "$root/pyproject.toml" <<EOF
[project]
name = "$app"
version = "0.1.0"
description = "$desc"
requires-python = ">=3.10"
readme = "README.md"
authors = [{ name = "LCS Group IT" }]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "ruff>=0.7,<0.13",
    "mypy>=1.11,<2",
]

[build-system]
requires = ["flit_core>=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "$app"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "SIM", "UP", "C4", "PIE", "RET", "RUF"]
ignore = ["E501", "B008", "RET504", "SIM108"]

[tool.ruff.lint.per-file-ignores]
"**/hooks.py" = ["F401"]

[tool.ruff.lint.isort]
known-first-party = ["$app"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"

[tool.mypy]
python_version = "3.10"
files = ["$app"]
warn_return_any = true
warn_unused_ignores = true
check_untyped_defs = true
show_error_codes = true

[[tool.mypy.overrides]]
module = ["frappe", "frappe.*", "erpnext", "erpnext.*"]
ignore_missing_imports = true
EOF

  # ---- __init__.py -----------------------------------------------
  echo '__version__ = "0.1.0"' > "$root/$app/__init__.py"

  # ---- hooks.py --------------------------------------------------
  cat > "$root/$app/hooks.py" <<EOF
"""$title — Pilanda domain app for the "$module" module.

$desc

Inherits the Pilanda umbrella's brand, sidebar and intranet
look from the \`pilanda\` app — no own CSS or sidebar JS in
this app. Domain DocTypes, controllers and APIs live here.
"""

app_name = "$app"
app_title = "$title"
app_publisher = "LCS Group"
app_description = "$desc"
app_email = "it@lcs-group.com"
app_license = "proprietary"

# No own CSS / JS — the umbrella owns the chrome.

# Module-level fixtures are kept tiny — workspaces ship in the
# umbrella for now; promote them here when the app gains its
# own DocTypes / Pages.
fixtures: list[dict] = []
EOF

  # ---- modules.txt -----------------------------------------------
  echo "$module" > "$root/$app/modules.txt"

  # ---- patches.txt -----------------------------------------------
  : > "$root/$app/patches.txt"

  # ---- module dir markers ----------------------------------------
  : > "$root/$app/$slug/__init__.py"
  : > "$root/$app/$slug/doctype/__init__.py"

  # ---- git init --------------------------------------------------
  ( cd "$root" && git init -q -b main && git add . && \
    git -c user.email=it@lcs-group.com -c user.name="LCS IT" \
        commit -q -m "feat: initial $app scaffold" )

  echo "  ✓ $app scaffolded at $root"
}

scaffold_app \
  "pilanda_vertrieb" \
  "Pilanda Vertrieb" \
  "LCS-specific extensions on top of Frappe CRM (Vertrieb) — sales hierarchy, territory mapping, lead scoring overrides, ERP linkage." \
  "Vertrieb" \
  "vertrieb"

scaffold_app \
  "pilanda_engineering" \
  "Pilanda Engineering" \
  "Engineering bridge connecting EPLAN, Autodesk Fusion Manage (PLM) and ERPNext routings/BOMs into the Pilanda stack." \
  "Engineering" \
  "engineering"

scaffold_app \
  "pilanda_field_service" \
  "Pilanda Field Service" \
  "Mobile-first Field Service module — Montage PWA, offline-fähig, mit Job Card + Maintenance Visit + Foto-Upload." \
  "Field Service" \
  "field_service"

echo
echo "=== summary ==="
for a in pilanda_vertrieb pilanda_engineering pilanda_field_service; do
  ls "$WORKSPACE/$a/" 2>/dev/null && echo
done
