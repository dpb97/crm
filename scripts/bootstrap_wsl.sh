#!/usr/bin/env bash
# bootstrap_wsl.sh — one-shot developer bootstrap for the LCS CRM on WSL2.
#
# Safe to re-run. Must be executed inside a WSL Ubuntu 22.04+ shell, NOT from
# Windows (the Frappe toolchain does not support Windows natively and the
# /mnt/c filesystem is ~10x slower for Frappe's asset build).

set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
NODE_VERSION="${NODE_VERSION:-20}"
BENCH_NAME="${BENCH_NAME:-lcs-bench}"
SITE_NAME="${SITE_NAME:-lcs.local}"
DB_TYPE="${DB_TYPE:-postgres}"

log() { printf '\033[1;34m[bootstrap]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[bootstrap]\033[0m %s\n' "$*" >&2; exit 1; }

# --- Preconditions ---
if ! grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
    die "This script expects to run inside WSL2."
fi

if [[ "$PWD" == /mnt/* ]]; then
    die "Refusing to run from $PWD. Move the repo under \$HOME (e.g. ~/dev/lcs-crm) for acceptable Frappe I/O performance."
fi

# --- System packages ---
log "Installing system packages"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    software-properties-common curl ca-certificates \
    git build-essential pkg-config \
    "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-venv" "python${PYTHON_VERSION}-dev" \
    libpq-dev postgresql-client \
    redis-tools \
    libffi-dev libssl-dev libjpeg-dev zlib1g-dev libwebp-dev \
    wkhtmltopdf

# --- Node via nvm ---
if [[ ! -d "$HOME/.nvm" ]]; then
    log "Installing nvm"
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
fi
# shellcheck source=/dev/null
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install "$NODE_VERSION"
nvm use "$NODE_VERSION"
corepack enable
corepack prepare yarn@stable --activate

# --- bench CLI ---
if ! command -v bench >/dev/null 2>&1; then
    log "Installing frappe-bench"
    pip3 install --user frappe-bench
    export PATH="$HOME/.local/bin:$PATH"
fi

# --- Init bench ---
if [[ ! -d "$HOME/$BENCH_NAME" ]]; then
    log "Initialising $BENCH_NAME"
    cd "$HOME"
    bench init --python "python${PYTHON_VERSION}" --frappe-branch version-15 "$BENCH_NAME"
fi

cd "$HOME/$BENCH_NAME"

# --- Get apps ---
[[ -d apps/crm ]] || bench get-app "$(realpath -s "${BASH_SOURCE%/*}/..")"
[[ -d apps/lcs_integrations ]] || bench get-app "$(realpath -s "${BASH_SOURCE%/*}/..")/lcs_integrations"

# --- Create site ---
if ! bench --site "$SITE_NAME" list-apps >/dev/null 2>&1; then
    log "Creating site $SITE_NAME ($DB_TYPE)"
    bench new-site "$SITE_NAME" \
        --db-type "$DB_TYPE" \
        --db-host "${DB_HOST:-127.0.0.1}" \
        --db-port "${DB_PORT:-5432}" \
        --admin-password "${ADMIN_PASSWORD:-admin}"
    bench --site "$SITE_NAME" install-app crm lcs_integrations
fi

log "Done. Start with: cd ~/$BENCH_NAME && bench start"
log "Frontend dev server (separate terminal): cd ~/$BENCH_NAME/apps/crm/frontend && yarn dev"
