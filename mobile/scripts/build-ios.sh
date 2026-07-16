#!/usr/bin/env bash
# Build the SPA, sync into the Capacitor wrapper, open Xcode (Mac only).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

( cd "$ROOT/../frontend" && yarn install --frozen-lockfile && yarn build )
( cd "$ROOT" && yarn install --frozen-lockfile && npx cap sync ios )
( cd "$ROOT" && npx cap open ios )
