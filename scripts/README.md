# scripts/ — Automation Scripts

Build, deployment, and development utility scripts for Frappe Bench.

## What Belongs Here

| File                      | Purpose                                        |
|---------------------------|------------------------------------------------|
| `setup-dev.ps1`           | First-time development environment setup       |
| `setup-dev.sh`            | First-time setup (Linux/macOS)                 |
| `test.ps1` / `test.sh`   | Run all tests with coverage                    |
| `migrate.ps1`             | Apply Frappe patches and migrate               |
| `seed.ps1`                | Seed the database with test data               |
| `docker-up.ps1`           | Start Docker development services              |
| `build-frontend.ps1`      | Build React frontend assets                    |
| `deploy.ps1`              | Production deployment script                   |

## Example: setup-dev.ps1

```powershell
#!/usr/bin/env pwsh
# First-time development environment setup for Frappe Bench

Write-Host "Setting up Frappe development environment..." -ForegroundColor Cyan

# Check prerequisites
$prerequisites = @("python", "node", "redis-cli", "mysql")
foreach ($cmd in $prerequisites) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$cmd not found. Please install it first."
        exit 1
    }
}

# Check Python version
$pyVersion = python --version 2>&1
Write-Host "Python: $pyVersion"

# Initialize bench (if not already)
if (-not (Test-Path "Procfile")) {
    Write-Host "Initializing Frappe Bench..."
    bench init . --frappe-branch version-16 --skip-redis-config-generation
}

# Create site (if not exists)
$siteName = "my-site.localhost"
if (-not (Test-Path "sites/$siteName")) {
    Write-Host "Creating site: $siteName"
    bench new-site $siteName --mariadb-root-password frappe --admin-password admin
    bench --site $siteName set-config developer_mode 1
}

# Install app
if (Test-Path "apps/my_app") {
    bench --site $siteName install-app my_app
}

# Copy environment template
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from template. Edit it with your local settings."
}

Write-Host "Setup complete! Run 'bench start' to begin development." -ForegroundColor Green
```

## Example: test.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

SITE=${1:-my-site.localhost}
APP=${2:-my_app}

echo "Running tests for $APP on $SITE..."

# Run Frappe tests
bench --site "$SITE" run-tests --app "$APP" --coverage

# Run pytest (unit tests outside Frappe context)
cd "apps/$APP"
python -m pytest tests/unit/ -v --cov="$APP" --cov-report=html

# Run frontend tests
if [ -d "frontend" ]; then
    cd frontend
    npm test -- --coverage
fi

echo "All tests passed!"
```

## Example: migrate.ps1

```powershell
#!/usr/bin/env pwsh
# Apply Frappe migrations and patches

param(
    [string]$Site = "my-site.localhost"
)

Write-Host "Migrating site: $Site" -ForegroundColor Cyan

bench --site $Site migrate
bench --site $Site clear-cache

Write-Host "Migration complete." -ForegroundColor Green
```

## Rules

- PowerShell (`.ps1`) for Windows-primary teams
- Bash (`.sh`) for cross-platform / CI scripts
- Always include error handling
- Use `bench` CLI commands — never manipulate Frappe internals directly
- Document script parameters and usage in comments
- Document required parameters at the top
- Make scripts idempotent (safe to run multiple times)
