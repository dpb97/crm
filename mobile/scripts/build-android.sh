#!/usr/bin/env bash
# Build the SPA, sync into the Capacitor wrapper, open Android Studio.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 1) Build production SPA
( cd "$ROOT/../frontend" && yarn install --frozen-lockfile && yarn build )

# 2) Sync wrapper
( cd "$ROOT" && yarn install --frozen-lockfile && npx cap sync android )

# 3) Open IDE
( cd "$ROOT" && npx cap open android )
