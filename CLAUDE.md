# CLAUDE.md — pilanda_sales

> Frappe-App im LCS-Pilanda-Stack für **Vertrieb / Sales** — LCS-spezifische
> Vertriebslogik rund um die Frappe-CRM-SPA (`/crm`). Teil der geteilten
> Pilanda-Bench (Site `lcs.local`, mehrere Apps) — nicht standalone. **Frühes
> Stadium:** aus dem Org-Template initialisiert; App-Code via `bench new-app pilanda_sales`.

## Pilanda-Stack-Kontext (verbindlich)

- **Pilanda-Modul:** Vertrieb (`modules_data.py`-Slug `vertrieb`, Navigationsziel `/crm`).
- **Custom-Field-Namespace:** `custom_sales_` — Eigentum: Vertriebs-/Sales-Felder am Project.
- **Project-Objekt-SSOT:** EIN geteiltes Project (ERPNext-Standard, eine `tabProject`).
  Erweitern nur per Custom Field (als Code, `after_migrate`), ein Eigentümer je Feld.
  Kanonische Regel: `pilanda/docs/conventions/project-object-ssot.md` (Repo `pilanda`).
- **Theme/CSS-SSOT:** App `pilanda_theme` (`--pp-*`-Tokens, `--pp-radius-ui`). Keine nackten Hex/Radien.
- Hinweis: Die Vertriebs-Oberfläche IST die Frappe-CRM-SPA (3rd-party, via `chrome_injection` eingebettet); `pilanda_sales` ergänzt LCS-Logik/Felder/Reports — kein CRM-Nachbau.
- **Bench:** `docker exec pilanda-frappe bash -lc "cd /workspace/frappe-bench && bench --site lcs.local <cmd>"`.

> Die folgenden Abschnitte sind das Org-Standard-Template — gelten zusätzlich.

## Project Overview

**Stack:** Python 3.11+ / Frappe Framework (v16) for ERP projects
**Frontend:** React + TypeScript for custom pages, Frappe UI for standard views
**Database:** MariaDB 10.6+ (Frappe default — deviation from org PostgreSQL standard, justified by framework requirement)
**Architecture:** Frappe MVC with modular app structure
**Primary Language:** Python (backend), TypeScript (frontend)
**Auth:** MSAL (Microsoft Identity) for release/production builds; Frappe built-in auth for development

## Critical Rules

### 1. Code Organization

- Many small files over few large files
- 200-400 lines typical, 800 max per file
- Organize by Frappe module, not by type
- One DocType per directory with its controller, tests, and fixtures
- Keep custom API endpoints in dedicated `api/` modules
- Separate React frontend code in `frontend/` directory

### 2. Code Style

- No emojis in code, comments, or documentation
- Use `snake_case` for functions, variables, file names
- Use `PascalCase` for class names
- Use `UPPER_SNAKE_CASE` for constants
- No `print()` in production code — use `frappe.logger()` or `frappe.log_error()`
- Type hints on all function signatures (Python 3.11+ syntax)
- Use `frappe.whitelist()` for all API endpoints
- Docstrings on all public functions (Google style)

### 3. Testing

- TDD: Write tests first
- 80% minimum coverage
- Unit tests for services, business logic, utils
- Integration tests for API endpoints, DocType workflows
- Use pytest + frappe test runner
- Factory Boy or frappe test fixtures for test data

### 4. Security

- No hardcoded secrets — use environment variables or Frappe site config
- Never use `frappe.db.sql()` with string concatenation — use parameterized queries
- Validate all user inputs with Frappe validators or custom validation
- Use `frappe.has_permission()` for authorization checks
- All whitelisted APIs must have proper permission decorators
- HTTPS everywhere in production

### 5. Database

- Frappe ORM for all data access — avoid raw SQL where possible
- DocType definitions are the schema — never modify tables manually
- Use `frappe.db.sql()` with parameterized queries only when ORM is insufficient
- Migrations via Frappe patches (in `patches.txt`)
- Index frequently queried fields in DocType definitions

### 6. Frontend

- New custom pages: React + TypeScript
- Icon set: Bootstrap Icons (`react-bootstrap-icons` / `bootstrap-icons`)
- Standard Frappe views: use Frappe UI patterns
- Tailwind CSS for React page styling
- No plain CSS files — Tailwind utility classes only in React pages

## File Structure

```
/
|-- apps/                             # Frappe apps (created by bench)
|   |-- my_app/                       # Custom Frappe app
|       |-- my_app/
|       |   |-- __init__.py
|       |   |-- hooks.py              # App hooks (scheduler, fixtures, etc.)
|       |   |-- patches.txt           # Migration patches list
|       |   |-- modules.json          # Module definitions
|       |   |-- api/                   # Custom whitelisted API endpoints
|       |   |-- utils/                 # Shared utility functions
|       |   |-- overrides/             # DocType controller overrides
|       |   |-- templates/             # Jinja2 templates, web views
|       |   |-- www/                   # Web pages (Frappe www)
|       |   |-- public/                # Static assets (JS, CSS, images)
|       |   |-- <module_name>/         # Frappe modules
|       |       |-- doctype/
|       |       |   |-- <doctype_name>/
|       |       |       |-- <doctype_name>.py        # Controller
|       |       |       |-- <doctype_name>.json       # Schema
|       |       |       |-- <doctype_name>.js         # Client script
|       |       |       |-- test_<doctype_name>.py    # Tests
|       |       |-- report/
|       |       |-- page/
|       |       |-- workspace/
|       |-- frontend/                  # React + TypeScript frontend
|       |   |-- src/
|       |   |-- package.json
|       |   |-- tsconfig.json
|       |   |-- tailwind.config.js
|       |-- setup.py
|       |-- pyproject.toml
|
|-- frontend/                          # Standalone React app (if not embedded)
|   |-- src/
|   |-- package.json
|   |-- tsconfig.json
|   |-- vite.config.ts
|   |-- tailwind.config.js
|
|-- tests/                             # Additional test suites
|   |-- unit/                          # Unit tests
|   |-- integration/                   # Integration tests
|   |-- e2e/                           # End-to-end tests (Playwright/Cypress)
|
|-- docs/                              # Documentation
|   |-- api/                           # API documentation
|   |-- architecture/                  # ADRs, diagrams
|   |-- guides/                        # Developer guides
|
|-- infrastructure/                    # Docker, bench setup, deployment
|-- scripts/                           # Automation scripts
```

## Key Patterns

### Frappe Whitelisted API

```python
import frappe
from frappe import _


@frappe.whitelist()
def get_item_details(item_code: str) -> dict:
    """Get item details by item code.

    Args:
        item_code: The item code to look up.

    Returns:
        Dict with item details.

    Raises:
        frappe.DoesNotExistError: If item not found.
    """
    frappe.has_permission("Item", "read", throw=True)

    item = frappe.get_doc("Item", item_code)
    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "stock_uom": item.stock_uom,
    }
```

### DocType Controller

```python
import frappe
from frappe.model.document import Document


class SalesOrder(Document):
    def validate(self):
        self._validate_items()
        self._calculate_totals()

    def on_submit(self):
        self._create_delivery_note()

    def _validate_items(self):
        if not self.items:
            frappe.throw(_("At least one item is required"))

    def _calculate_totals(self):
        self.total = sum(item.amount for item in self.items)

    def _create_delivery_note(self):
        # Business logic for creating linked documents
        pass
```

### React Frontend Page (TypeScript)

```tsx
import React, { useEffect, useState } from "react";
import { BootstrapIcon } from "react-bootstrap-icons";

interface ItemDetails {
  item_code: string;
  item_name: string;
  stock_uom: string;
}

export const ItemView: React.FC<{ itemCode: string }> = ({ itemCode }) => {
  const [item, setItem] = useState<ItemDetails | null>(null);

  useEffect(() => {
    frappe.call({
      method: "my_app.api.get_item_details",
      args: { item_code: itemCode },
      callback: (r: { message: ItemDetails }) => setItem(r.message),
    });
  }, [itemCode]);

  if (!item) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">{item.item_name}</h1>
      <p className="text-gray-600">{item.item_code}</p>
    </div>
  );
};
```

### Error Handling

```python
import frappe
from frappe import _


def process_order(order_id: str) -> dict:
    try:
        order = frappe.get_doc("Sales Order", order_id)
        order.submit()
        return {"success": True, "data": order.as_dict()}
    except frappe.DoesNotExistError:
        frappe.throw(
            _("Order {0} not found").format(order_id),
            exc=frappe.DoesNotExistError,
        )
    except frappe.ValidationError as e:
        frappe.log_error(title="Order Processing Error")
        frappe.throw(_("Validation failed: {0}").format(str(e)))
```

## Environment Variables

```bash
# Required (set in site_config.json or environment)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=my_site
DB_PASSWORD=...
REDIS_CACHE=redis://localhost:13000
REDIS_QUEUE=redis://localhost:11000
REDIS_SOCKETIO=redis://localhost:12000

# Optional
FRAPPE_SITE=my_site.localhost
DEVELOPER_MODE=1

# MSAL (release builds only)
MSAL_CLIENT_ID=
MSAL_TENANT_ID=
MSAL_CLIENT_SECRET=
```

## Git Workflow

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Never commit to `main` or `develop` directly — branches are protected
- Feature branches from `develop`, PRs required with review
- All tests must pass before merge
- Squash merge preferred for clean history

## Available Commands

- `/plan` - Create implementation plan
- `/tdd` - Test-driven development workflow
- `/code-review` - Review code quality
- `/bench-fix` - Fix bench/build errors
