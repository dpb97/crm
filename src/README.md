# src/ — Source Code

This folder is intentionally empty. Create your Frappe app structure here when starting a new project.

---

## Frappe App Structure

When you initialize your app with `bench new-app`, the following structure is created automatically:

```
src/
|-- my_app/                           # Custom Frappe app
    |-- my_app/
    |   |-- __init__.py               # Package init
    |   |-- hooks.py                  # App hooks (doc_events, scheduler, fixtures)
    |   |-- patches.txt               # Migration patches list
    |   |-- modules.json              # Module definitions
    |   |
    |   |-- api/                      # Custom whitelisted API endpoints
    |   |   |-- __init__.py
    |   |   |-- items.py              # Item-related API functions
    |   |   |-- orders.py             # Order-related API functions
    |   |
    |   |-- utils/                    # Shared utility functions
    |   |   |-- __init__.py
    |   |   |-- validators.py         # Custom validators
    |   |   |-- formatters.py         # Data formatting helpers
    |   |
    |   |-- overrides/                # DocType controller overrides
    |   |   |-- __init__.py
    |   |   |-- sales_invoice.py      # Override standard DocType behavior
    |   |
    |   |-- templates/                # Jinja2 templates
    |   |   |-- pages/                # Web page templates
    |   |   |-- emails/               # Email templates
    |   |
    |   |-- www/                      # Web pages (Frappe www pattern)
    |   |
    |   |-- public/                   # Static assets
    |   |   |-- js/                   # Client-side JavaScript
    |   |   |-- css/                  # Stylesheets (Frappe standard views only)
    |   |   |-- images/               # Image assets
    |   |
    |   |-- <module_name>/            # Frappe modules (one per business domain)
    |       |-- doctype/
    |       |   |-- <doctype_name>/
    |       |       |-- <doctype_name>.py        # Controller (business logic)
    |       |       |-- <doctype_name>.json       # Schema (field definitions)
    |       |       |-- <doctype_name>.js         # Client script (form UI logic)
    |       |       |-- test_<doctype_name>.py    # DocType tests
    |       |-- report/               # Custom reports
    |       |-- page/                 # Custom desk pages
    |       |-- workspace/            # Workspace definitions
    |
    |-- frontend/                     # React + TypeScript frontend
    |   |-- src/
    |   |   |-- components/           # Reusable React components
    |   |   |-- pages/                # Page-level components
    |   |   |-- hooks/                # Custom React hooks
    |   |   |-- types/                # TypeScript type definitions
    |   |   |-- utils/                # Frontend utility functions
    |   |   |-- App.tsx               # Main App component
    |   |   |-- main.tsx              # Entry point
    |   |-- package.json
    |   |-- tsconfig.json
    |   |-- vite.config.ts
    |   |-- tailwind.config.js
    |
    |-- setup.py                      # Python package setup
    |-- pyproject.toml                # Python project config (Ruff, deps)
    |-- MANIFEST.in                   # Package manifest
    |-- requirements.txt              # Python dependencies
    |-- license.txt
```

---

## Frappe App Lifecycle

```
hooks.py          -- Defines app behavior (scheduler, doc_events, fixtures)
patches.txt       -- Lists migration patches in order
modules.json      -- Declares app modules
```

### hooks.py (Key Sections)

```python
app_name = "my_app"
app_title = "My App"
app_publisher = "Your Company"
app_description = "ERP extension for ..."

# DocType events (react to document lifecycle)
doc_events = {
    "Sales Invoice": {
        "on_submit": "my_app.overrides.sales_invoice.on_submit",
        "on_cancel": "my_app.overrides.sales_invoice.on_cancel",
    },
}

# Scheduled tasks
scheduler_events = {
    "daily": [
        "my_app.utils.cleanup.daily_cleanup",
    ],
    "cron": {
        "0 9 * * *": [
            "my_app.utils.notifications.send_daily_report",
        ],
    },
}

# Fixtures (exported DocType data)
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "My Module"]]},
]
```

---

## Quick Setup Commands

```bash
# Create a new Frappe app (from bench directory)
bench new-app my_app

# Install app on site
bench --site my-site.localhost install-app my_app

# Create a new DocType (via Frappe UI)
# Navigate to: /app/doctype/new-doctype-1

# Create a new module
# Add to modules.json, then create the directory structure

# Run migrations after schema changes
bench --site my-site.localhost migrate

# Create a patch
# 1. Add to patches.txt: my_app.patches.v1_0.patch_name
# 2. Create the file: my_app/patches/v1_0/patch_name.py

# Build frontend assets
bench build --app my_app

# Watch for frontend changes (development)
bench watch

# Run tests
bench --site my-site.localhost run-tests --app my_app

# Run specific test
bench --site my-site.localhost run-tests --module my_app.my_module.doctype.my_doctype.test_my_doctype
```

---

## React Frontend Setup

For custom pages using React + TypeScript:

```bash
cd src/my_app/frontend

# Initialize (if not already)
npm init -y
npm install react react-dom
npm install -D typescript @types/react @types/react-dom
npm install -D vite @vitejs/plugin-react
npm install -D tailwindcss postcss autoprefixer
npm install react-bootstrap-icons

# Initialize Tailwind
npx tailwindcss init -p

# Initialize TypeScript
npx tsc --init

# Start development server
npm run dev
```

### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../my_app/public/frontend",
    emptyOutDir: true,
  },
});
```

---

## Layer Dependencies (Frappe Architecture)

```
DocType Controller  -->  Frappe ORM  -->  MariaDB
       |
       +--> utils/ (shared logic)
       +--> api/ (whitelisted endpoints)
       |
hooks.py (wires everything together)
       |
frontend/ (React) --> frappe.call() --> API endpoints
```

| Layer                | Depends On              | Never Depends On                    |
|----------------------|-------------------------|-------------------------------------|
| **DocType Controller** | Frappe ORM, utils/    | frontend/, api/ directly            |
| **API (api/)**       | DocType, utils/         | frontend/                           |
| **Utils**            | Frappe ORM              | DocType controllers, API            |
| **Frontend (React)** | API via `frappe.call()` | Python code directly                |
| **hooks.py**         | All app modules         | (orchestration layer)               |
dotnet sln src/MyApp.sln add src/MyApp.Application/MyApp.Application.csproj
dotnet sln src/MyApp.sln add src/MyApp.Domain/MyApp.Domain.csproj
dotnet sln src/MyApp.sln add src/MyApp.Infrastructure/MyApp.Infrastructure.csproj
dotnet sln src/MyApp.sln add src/MyApp.Shared/MyApp.Shared.csproj

# Add project references (enforce Clean Architecture)
dotnet add src/MyApp.Api/MyApp.Api.csproj reference src/MyApp.Application/MyApp.Application.csproj
dotnet add src/MyApp.Api/MyApp.Api.csproj reference src/MyApp.Infrastructure/MyApp.Infrastructure.csproj
dotnet add src/MyApp.Application/MyApp.Application.csproj reference src/MyApp.Domain/MyApp.Domain.csproj
dotnet add src/MyApp.Infrastructure/MyApp.Infrastructure.csproj reference src/MyApp.Application/MyApp.Application.csproj
dotnet add src/MyApp.Infrastructure/MyApp.Infrastructure.csproj reference src/MyApp.Domain/MyApp.Domain.csproj

# Add common NuGet packages
dotnet add src/MyApp.Api package Swashbuckle.AspNetCore
dotnet add src/MyApp.Api package Serilog.AspNetCore
dotnet add src/MyApp.Application package FluentValidation
dotnet add src/MyApp.Application package AutoMapper
dotnet add src/MyApp.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer
dotnet add src/MyApp.Infrastructure package Microsoft.EntityFrameworkCore.Tools
```

---

## What Belongs Where — Quick Reference

| You want to add...                  | Put it in...             |
|-------------------------------------|--------------------------|
| API controller                      | `Api/Controllers/`       |
| Middleware (auth, logging, errors)  | `Api/Middleware/`        |
| DI registration                    | `Api/Extensions/`        |
| Service interface                  | `Application/Interfaces/`|
| Service implementation (use case)  | `Application/Services/`  |
| Request/Response DTO               | `Application/DTOs/`      |
| Validation rules                   | `Application/Validators/`|
| Entity with business logic         | `Domain/Entities/`       |
| Value Object (Email, Money)        | `Domain/ValueObjects/`   |
| Enum                               | `Domain/Enums/`          |
| EF Core DbContext                  | `Infrastructure/Data/`   |
| Entity configuration (Fluent API)  | `Infrastructure/Data/Configurations/` |
| Repository implementation          | `Infrastructure/Repositories/` |
| External API client                | `Infrastructure/Services/`|
| Extension methods, constants       | `Shared/`                |

---

## Minimal Setup

A minimal project needs only 3 projects:

```
src/
|-- MyApp.Api/
|-- MyApp.Domain/
|-- MyApp.Infrastructure/
```

Skip `Application/` for simple CRUD apps (put interfaces in Domain).
Skip `Shared/` if you have no cross-cutting utilities.
