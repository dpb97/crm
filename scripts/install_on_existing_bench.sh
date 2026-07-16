#!/usr/bin/env bash
# Install LCS CRM (crm fork + lcs_integrations + pilanda_theme +
# pilanda_sales) into an EXISTING bench — e.g. a VM that already runs
# LMS/Helpdesk. Plain bench, no Docker.
#
#   cd ~/frappe-bench
#   SITE=<your-site> bash apps/crm/scripts/install_on_existing_bench.sh
#
# Private repos (pilanda_theme, pilanda_sales) need credentials — either
# a stored git credential helper or:  GITHUB_TOKEN=<read-only PAT> SITE=… bash …
#
# Idempotent: safe to re-run after pulling new commits.

set -euo pipefail

SITE="${SITE:?set SITE=<site name>, e.g. SITE=crm.lcs-group.com}"
BENCH_ROOT="$(pwd)"
[[ -d "$BENCH_ROOT/apps" && -d "$BENCH_ROOT/sites" ]] || {
  echo "run from the bench root (contains apps/ and sites/)" >&2; exit 1; }

CRM_REPO="${CRM_REPO:-https://github.com/dpb97/crm}"
THEME_REPO="${THEME_REPO:-https://github.com/Pilanda-ERP/pilanda_theme}"
SALES_REPO="${SALES_REPO:-https://github.com/Pilanda-ERP/pilanda_sales}"
BRANCH="${BRANCH:-develop}"

auth_url() {
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    echo "${1/https:\/\/github.com/https://x-access-token:${GITHUB_TOKEN}@github.com}"
  else
    echo "$1"
  fi
}

echo "==> [0/6] preflight"
# Frappe major version — the fork targets v16
FRAPPE_MAJOR=$(./env/bin/python -c "import frappe; print(frappe.__version__.split('.')[0])")
[[ "$FRAPPE_MAJOR" == "16" ]] || {
  echo "WARNING: bench runs frappe v${FRAPPE_MAJOR}, the CRM fork targets v16." >&2; }
# erpnext is required (customer sync, custom fields on Quotation/Sales Order,
# pilanda_sales required_apps)
if ! bench --site "$SITE" list-apps | grep -q "^erpnext"; then
  echo "ERROR: erpnext is not installed on ${SITE} — install it first:" >&2
  echo "  bench get-app --branch version-16 erpnext && bench --site ${SITE} install-app erpnext" >&2
  exit 1
fi

echo "==> [1/6] get apps (branch ${BRANCH})"
[[ -d apps/crm ]]           || bench get-app --branch "$BRANCH" crm "$(auth_url "$CRM_REPO")"
[[ -d apps/pilanda_theme ]] || bench get-app --branch "$BRANCH" pilanda_theme "$(auth_url "$THEME_REPO")"
[[ -d apps/pilanda_sales ]] || bench get-app --branch "$BRANCH" pilanda_sales "$(auth_url "$SALES_REPO")"

echo "==> [2/6] register lcs_integrations (lives inside the crm repo)"
[[ -L apps/lcs_integrations || -d apps/lcs_integrations ]] \
  || ln -s "$BENCH_ROOT/apps/crm/lcs_integrations" apps/lcs_integrations
./env/bin/pip install -q -e apps/lcs_integrations
# newline-safe append (a missing trailing newline once glued two app names)
grep -qx lcs_integrations sites/apps.txt || printf '\nlcs_integrations\n' >> sites/apps.txt
# collapse accidental blank lines
sed -i '/^$/d' sites/apps.txt

echo "==> [3/6] install on ${SITE} (order matters)"
for app in pilanda_theme crm lcs_integrations pilanda_sales; do
  if bench --site "$SITE" list-apps | grep -q "^${app}"; then
    echo "    ${app} already installed"
  else
    bench --site "$SITE" install-app "$app"
  fi
done

echo "==> [4/6] migrate + build"
bench --site "$SITE" migrate
bench build --apps crm,pilanda_theme,pilanda_sales

echo "==> [5/6] SSO / mail-sync provider (needs ENTRA_* env — see below)"
bench --site "$SITE" execute lcs_integrations.msal_sso.provider.install_or_update \
  || echo "    (skipped — ENTRA_* not set yet)"

echo "==> [6/6] restart"
bench restart 2>/dev/null || echo "    (bench restart failed — dev bench? restart manually)"

cat <<'EOF'

DONE. Next steps:

1. ENTRA_* env vars (SSO + Outlook mail sync read the SAME three vars):
     ENTRA_TENANT_ID / ENTRA_CLIENT_ID / ENTRA_CLIENT_SECRET
   On a supervisor-managed bench, exporting in .bashrc is NOT enough —
   workers and web run under supervisor. Add them to the [program:*]
   sections via `environment=` in config/supervisor.conf (then
   `bench setup supervisor` regenerates — keep them in a shared include),
   or use /etc/environment. App registration runbook:
     apps/crm/docs/operations/entra-app-registration.md
   (one registration, delegated User.Read etc. for SSO PLUS
    application Mail.Read + admin consent for the sync;
    set an Exchange Application Access Policy to scope mailboxes!)

2. Re-run the provider installer once ENTRA_* is live:
     bench --site $SITE execute lcs_integrations.msal_sso.provider.install_or_update

3. Per synced mailbox create one 'Outlook Mailbox Binding' record in Desk.
   First delta manually:
     bench --site $SITE execute lcs_integrations.outlook_sync.delta_service.sync_all_bindings

EOF
