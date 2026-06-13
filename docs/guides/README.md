# docs/guides -- Developer Guides

Onboarding documentation, how-to guides, and development workflows.

## What Belongs Here

| File                        | Purpose                                    |
|-----------------------------|--------------------------------------------|
| `getting-started.md`        | First-time setup for new developers        |
| `development-workflow.md`   | Daily development process and tools        |
| `frappe-patches.md`         | How to create and apply Frappe patches     |
| `doctype-guide.md`          | How to create and customize DocTypes       |
| `testing-guide.md`          | Testing strategy, running tests, coverage  |
| `deployment-guide.md`       | How to deploy to each environment          |
| `react-frontend-guide.md`   | Setting up and developing React pages      |
| `troubleshooting.md`        | Common issues and solutions                |

## Getting Started (Quick Reference)

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend build tools)
- MariaDB 10.6+
- Redis 7+
- IDE: VS Code with Python + Pylance extensions
- Docker (optional, for containerized development)

### First-Time Setup

```bash
# 1. Install bench CLI
pip install frappe-bench

# 2. Initialize bench
bench init my-bench --frappe-branch version-16
cd my-bench

# 3. Create a new site
bench new-site my-site.localhost --mariadb-root-password <password>

# 4. Clone/create the app
bench get-app <repo-url>
# OR: bench new-app my_app

# 5. Install app on site
bench --site my-site.localhost install-app my_app

# 6. Enable developer mode
bench --site my-site.localhost set-config developer_mode 1

# 7. Start development server
bench start

# 8. Run tests
bench --site my-site.localhost run-tests --app my_app
```

### Daily Workflow

```bash
# Start bench (web server + workers + redis + socketio)
bench start

# After pulling changes
bench --site my-site.localhost migrate
bench build --app my_app

# Create a new DocType
# Use the Frappe UI at /app/doctype/new

# Run tests
bench --site my-site.localhost run-tests --app my_app

# Build frontend
cd apps/my_app/frontend
npm run build
```

1. Pull latest `develop`
2. Create feature branch: `feature/<ticket>-<description>`
3. Write tests first (TDD)
4. Implement feature
5. Run all tests: `dotnet test`
6. Push and create PR to `develop`
