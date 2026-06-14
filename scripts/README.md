# scripts/ — Automation Scripts

App-spezifische Helfer (Build/Migrate/Seed). Die **geteilte** Dev-/Docker-/Deploy-
Automatik liegt zentral in `pilanda_pm/_devenv` + `pilanda_pm/install.sh` — hier nur,
was wirklich app-eigen ist.

## What Belongs Here

| File                      | Purpose                                        |
|---------------------------|------------------------------------------------|
| `migrate.ps1`             | Apply Frappe patches and migrate               |
| `seed.ps1`                | Seed the database with test/demo data          |
| `build-frontend.ps1`      | Build Vue/Vite frontend assets (falls vorhanden) |

## Example: migrate.ps1

```powershell
#!/usr/bin/env pwsh
# Apply Frappe migrations and patches
param([string]$Site = "lcs.local")

Write-Host "Migrating site: $Site" -ForegroundColor Cyan
bench --site $Site migrate
bench --site $Site clear-cache
Write-Host "Migration complete." -ForegroundColor Green
```

## Example: test.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
SITE=${1:-lcs.local}
APP=${2:-<app>}

echo "Running tests for $APP on $SITE..."
bench --site "$SITE" run-tests --app "$APP" --coverage

# Frontend-Tests (falls vorhanden)
if [ -d "apps/$APP/frontend" ]; then
  cd "apps/$APP/frontend" && npm test -- --coverage
fi
```

## Rules

- PowerShell (`.ps1`) für Windows-primäre Teams; Bash (`.sh`) für CI/cross-platform
- Immer Fehlerbehandlung; Skripte idempotent halten
- Nur `bench`-CLI nutzen — keine Frappe-Internals direkt manipulieren
- Parameter oben dokumentieren
