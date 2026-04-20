#!/usr/bin/env bash
# Install / reinstall the lcs_integrations Frappe app on a local bench.
#
# Assumes `bootstrap_wsl.sh` has already created the bench + site. Run from
# the bench root (the folder that contains apps/, sites/, env/).
#
# Idempotent: safe to re-run after pulling new commits.

set -euo pipefail

SITE="${SITE:-crm.lcs.local}"
APP="lcs_integrations"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
APP_SOURCE="${REPO_ROOT}/lcs_integrations"

[[ -d "$APP_SOURCE" ]] || { echo "lcs_integrations/ not found at $APP_SOURCE" >&2; exit 1; }
command -v bench >/dev/null 2>&1 || { echo "bench CLI not on PATH — are you in the right venv?" >&2; exit 1; }

# Add the app to the bench — get-app accepts a local path.
if ! bench get-app --help >/dev/null 2>&1; then
  echo "bench get-app unavailable" >&2; exit 1
fi

if [[ ! -d "apps/${APP}" ]]; then
  echo "→ registering local app path with bench"
  bench get-app --skip-assets --overwrite "${APP_SOURCE}"
else
  echo "→ app already registered, updating in place"
  (cd "apps/${APP}" && git pull --ff-only || true)
fi

if ! bench --site "${SITE}" list-apps | grep -q "^${APP}$"; then
  echo "→ installing ${APP} on ${SITE}"
  bench --site "${SITE}" install-app "${APP}"
else
  echo "→ ${APP} already installed on ${SITE} (running migrate)"
fi

echo "→ bench migrate"
bench --site "${SITE}" migrate

echo "→ running post-install hooks"
bench --site "${SITE}" execute lcs_integrations.msal_sso.provider.install_or_update || \
  echo "  (skipped — ENTRA_* env vars not set yet)"

echo "✓ ${APP} ready on ${SITE}"
