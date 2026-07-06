#!/usr/bin/env bash
#
# Scaffold the pilanda_theme Frappe app. Different from the
# sibling-app scaffold script because pilanda_theme ships:
#   - a Single DocType "Pilanda Theme Settings" with brand tokens
#     (primary / accent / surface colors, logo, font, radii)
#   - a boot hook so SPAs read the tokens at load time
#   - a /api/method/pilanda_theme.api.get_tokens whitelist endpoint
#   - an after_request hook that splices an inline <style> with
#     :root { --pilanda-primary: …; … } into every HTML response
#     so the live preview of token changes applies stack-wide

set -e

WORKSPACE=/mnt/c/Users/d.boeckle/Dev
APP=pilanda_theme
TITLE="Pilanda Theme"
MODULE="Theme"
SLUG=theme
DESC="Single-source-of-truth brand tokens (colors, logo, fonts) injected into every Pilanda SPA via boot data + an after_request CSS variables block."

ROOT="$WORKSPACE/$APP"
if [ -d "$ROOT" ]; then
  echo "skip $APP - already scaffolded"
  exit 0
fi

echo "scaffolding $APP ..."
mkdir -p "$ROOT/$APP/$SLUG/doctype/pilanda_theme_settings"

cat > "$ROOT/README.md" <<EOF
# $TITLE

$DESC

Part of the Pilanda umbrella stack. Reads brand tokens from a
Single DocType ("Pilanda Theme Settings") and exposes them three
ways:

1. Boot session: \`frappe.boot.pilanda_theme\` — consumed by the
   Pilanda Vue bundle so the in-Sidebar styling reacts immediately.
2. Whitelisted endpoint:
   \`/api/method/pilanda_theme.api.get_tokens\`
3. \`after_request\` hook injects an inline \`<style>:root { ... }</style>\`
   block into every HTML response so even SPAs we don't fork
   (LMS, Helpdesk, Builder) pick up the brand colors.

## Tokens

- \`primary_color\`, \`accent_color\`, \`success_color\`, \`warning_color\`, \`danger_color\`
- \`surface_color\`, \`ink_color\`, \`ink_soft_color\`, \`muted_color\`, \`border_color\`
- \`brand_logo_url\`, \`favicon_url\`, \`font_family\`
- \`radius\`, \`radius_sm\`

## Install

\`\`\`bash
bench get-app file:///mnt/c/Users/d.boeckle/Dev/$APP
bench --site lcs.local install-app $APP
\`\`\`
EOF

echo "Proprietary - LCS Group internal use only." > "$ROOT/license.txt"

cat > "$ROOT/.gitignore" <<'EOF'
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

cat > "$ROOT/pyproject.toml" <<EOF
[project]
name = "$APP"
version = "0.1.0"
description = "$DESC"
requires-python = ">=3.10"
readme = "README.md"
authors = [{ name = "LCS Group IT" }]
dependencies = []

[build-system]
requires = ["flit_core>=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "$APP"
EOF

echo '__version__ = "0.1.0"' > "$ROOT/$APP/__init__.py"
: > "$ROOT/$APP/patches.txt"
echo "$MODULE" > "$ROOT/$APP/modules.txt"
: > "$ROOT/$APP/$SLUG/__init__.py"
: > "$ROOT/$APP/$SLUG/doctype/__init__.py"
: > "$ROOT/$APP/$SLUG/doctype/pilanda_theme_settings/__init__.py"

cat > "$ROOT/$APP/hooks.py" <<EOF
"""$TITLE - brand tokens consumed by every Pilanda SPA."""

app_name = "$APP"
app_title = "$TITLE"
app_publisher = "LCS Group"
app_description = "$DESC"
app_email = "it@lcs-group.com"
app_license = "proprietary"

# Boot session - exposes the resolved token dict at
# frappe.boot.pilanda_theme so the Pilanda Vue Sidebar reacts
# to brand changes without a hard refresh.
boot_session = "pilanda_theme.api.boot_session"

# Inject :root CSS variables into every HTML response so even
# SPAs we don't fork (LMS, Helpdesk, Builder) pick them up.
after_request = ["pilanda_theme.api.inject_tokens"]
EOF

# Single DocType definition
cat > "$ROOT/$APP/$SLUG/doctype/pilanda_theme_settings/pilanda_theme_settings.json" <<'EOF'
{
  "actions": [],
  "creation": "2026-06-01 22:00:00",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "brand_section",
    "brand_logo_url",
    "favicon_url",
    "font_family",
    "color_section",
    "primary_color",
    "primary_color_dark",
    "accent_color",
    "column_break_1",
    "success_color",
    "warning_color",
    "danger_color",
    "surface_section",
    "surface_color",
    "surface_alt_color",
    "ink_color",
    "column_break_2",
    "ink_soft_color",
    "muted_color",
    "border_color",
    "shape_section",
    "radius",
    "radius_sm"
  ],
  "fields": [
    {"fieldname":"brand_section","fieldtype":"Section Break","label":"Brand"},
    {"fieldname":"brand_logo_url","fieldtype":"Data","label":"Brand Logo URL","default":"/assets/pilanda/brand-mark.svg"},
    {"fieldname":"favicon_url","fieldtype":"Data","label":"Favicon URL","default":"/assets/pilanda/images/favicon.ico"},
    {"fieldname":"font_family","fieldtype":"Data","label":"Font Family","default":"Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"},

    {"fieldname":"color_section","fieldtype":"Section Break","label":"Colors"},
    {"fieldname":"primary_color","fieldtype":"Color","label":"Primary","default":"#0B3A6F"},
    {"fieldname":"primary_color_dark","fieldtype":"Color","label":"Primary Dark","default":"#082C56"},
    {"fieldname":"accent_color","fieldtype":"Color","label":"Accent","default":"#F5A524"},
    {"fieldname":"column_break_1","fieldtype":"Column Break"},
    {"fieldname":"success_color","fieldtype":"Color","label":"Success","default":"#16A34A"},
    {"fieldname":"warning_color","fieldtype":"Color","label":"Warning","default":"#D97706"},
    {"fieldname":"danger_color","fieldtype":"Color","label":"Danger","default":"#DC2626"},

    {"fieldname":"surface_section","fieldtype":"Section Break","label":"Surfaces"},
    {"fieldname":"surface_color","fieldtype":"Color","label":"Surface","default":"#F8FAFC"},
    {"fieldname":"surface_alt_color","fieldtype":"Color","label":"Surface Alt","default":"#F1F5F9"},
    {"fieldname":"ink_color","fieldtype":"Color","label":"Ink","default":"#0F172A"},
    {"fieldname":"column_break_2","fieldtype":"Column Break"},
    {"fieldname":"ink_soft_color","fieldtype":"Color","label":"Ink Soft","default":"#334155"},
    {"fieldname":"muted_color","fieldtype":"Color","label":"Muted","default":"#64748B"},
    {"fieldname":"border_color","fieldtype":"Color","label":"Border","default":"#E5E7EB"},

    {"fieldname":"shape_section","fieldtype":"Section Break","label":"Shape"},
    {"fieldname":"radius","fieldtype":"Data","label":"Radius","default":"12px"},
    {"fieldname":"radius_sm","fieldtype":"Data","label":"Radius Small","default":"8px"}
  ],
  "issingle": 1,
  "links": [],
  "modified": "2026-06-01 22:00:00",
  "modified_by": "Administrator",
  "module": "Theme",
  "name": "Pilanda Theme Settings",
  "naming_rule": "Expression (old style)",
  "owner": "Administrator",
  "permissions": [
    {"role":"System Manager","read":1,"write":1,"create":1}
  ],
  "sort_field": "modified",
  "sort_order": "DESC"
}
EOF

cat > "$ROOT/$APP/$SLUG/doctype/pilanda_theme_settings/pilanda_theme_settings.py" <<'EOF'
import frappe
from frappe.model.document import Document


class PilandaThemeSettings(Document):
    """Single DocType — brand tokens for the whole Pilanda stack."""

    def on_update(self):
        """Bust the cached token snapshot so the next request picks
        up the change."""
        frappe.cache().delete_value("pilanda_theme_tokens")
EOF

# API module — whitelisted endpoint + boot + after_request hook
cat > "$ROOT/$APP/api.py" <<'EOF'
"""Public API for the Pilanda theme tokens."""
from __future__ import annotations

from typing import Any

import frappe

FIELDS = [
    "brand_logo_url", "favicon_url", "font_family",
    "primary_color", "primary_color_dark", "accent_color",
    "success_color", "warning_color", "danger_color",
    "surface_color", "surface_alt_color", "ink_color",
    "ink_soft_color", "muted_color", "border_color",
    "radius", "radius_sm",
]

CSS_VAR_MAP = {
    "primary_color":      "--pilanda-primary",
    "primary_color_dark": "--pilanda-primary-d",
    "accent_color":       "--pilanda-accent",
    "success_color":      "--pilanda-success",
    "warning_color":      "--pilanda-warning",
    "danger_color":       "--pilanda-danger",
    "surface_color":      "--pilanda-surface",
    "surface_alt_color":  "--pilanda-surface-2",
    "ink_color":          "--pilanda-ink",
    "ink_soft_color":     "--pilanda-ink-soft",
    "muted_color":        "--pilanda-muted",
    "border_color":       "--pilanda-border",
    "radius":             "--pilanda-radius",
    "radius_sm":          "--pilanda-radius-sm",
}


def _resolve_tokens() -> dict:
    cached = frappe.cache().get_value("pilanda_theme_tokens")
    if cached:
        return cached
    try:
        doc = frappe.get_cached_doc("Pilanda Theme Settings")
    except Exception:
        return {}
    tokens = {f: doc.get(f) for f in FIELDS if doc.get(f)}
    frappe.cache().set_value("pilanda_theme_tokens", tokens)
    return tokens


@frappe.whitelist(allow_guest=True)
def get_tokens() -> dict:
    """Whitelisted — consumed by the Pilanda Vue bundle and any
    external SPA that wants the brand tokens as JSON."""
    return _resolve_tokens()


def boot_session(bootinfo) -> None:
    """Frappe boot hook — expose tokens on frappe.boot.pilanda_theme."""
    bootinfo["pilanda_theme"] = _resolve_tokens()


def _css_block(tokens: dict) -> str:
    if not tokens:
        return ""
    decls = []
    for k, v in tokens.items():
        var = CSS_VAR_MAP.get(k)
        if not var or not v:
            continue
        decls.append("%s:%s" % (var, v))
    if not decls:
        return ""
    return "<style id=\"pilanda-theme-vars\">:root{%s}</style>" % ";".join(decls)


def inject_tokens(response: Any, request: Any) -> None:
    """after_request hook — splices :root { --pilanda-* } into
    every HTML response so SPAs we don't fork still pick up the
    brand colors. Skips JSON / file responses."""
    try:
        ct = (response.headers.get("Content-Type") or "").lower()
        if "text/html" not in ct:
            return
        body = response.get_data(as_text=True)
        if not body or "</head>" not in body:
            return
        if "pilanda-theme-vars" in body:
            return
        block = _css_block(_resolve_tokens())
        if not block:
            return
        response.set_data(body.replace("</head>", block + "</head>", 1))
    except Exception:
        frappe.logger().exception("Pilanda theme injection failed")
EOF

cd "$ROOT" && git init -q -b main && git add . && \
    git -c user.email=it@lcs-group.com -c user.name="LCS IT" \
        commit -q -m "feat: initial $APP scaffold with Theme Settings + token injection"

echo "  ✓ $APP scaffolded at $ROOT"
ls "$ROOT/"
