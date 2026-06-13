# Copilot Instructions

## Project Context

This is a Python / Frappe Framework (v16) ERP project with MariaDB, following Frappe's modular app architecture.

## Tech Stack

- **Language:** Python 3.11+ (backend), TypeScript (frontend)
- **Framework:** Frappe Framework v16
- **ORM:** Frappe ORM (DocType-based)
- **Database:** MariaDB 10.6+
- **Cache/Queue:** Redis (cache, queue, socketio)
- **Testing:** pytest + Frappe test runner (Python), Vitest (TypeScript)
- **Frontend:** React + TypeScript for custom pages, Frappe UI for standard views
- **Icons:** Bootstrap Icons (`react-bootstrap-icons`)
- **CSS:** Tailwind CSS for React pages
- **Auth:** Frappe built-in (dev), MSAL / OIDC (release/production)

## Architecture

Frappe modular app structure:

| Layer              | Location                        | Purpose                                   |
|--------------------|---------------------------------|-------------------------------------------|
| DocType Controller | `<module>/doctype/<name>/`      | Business logic, lifecycle hooks           |
| API Endpoints      | `api/`                          | Whitelisted functions, permission-checked |
| Services / Utils   | `utils/`                        | Shared business logic, helpers            |
| Hooks              | `hooks.py`                      | App events, scheduler, overrides          |
| Frontend (React)   | `frontend/src/`                 | Custom React + TypeScript pages           |
| Client Scripts     | `<doctype>/<doctype>.js`        | Frappe form client-side logic             |

## Code Style

- Use `snake_case` for functions, variables, file names
- Use `PascalCase` for class names (DocType controllers)
- Use `UPPER_SNAKE_CASE` for constants
- Type hints on all function signatures (Python 3.11+ syntax)
- Docstrings on all public functions (Google style)
- Max 800 lines per file; prefer 200-400
- No magic numbers or strings — use constants or enums
- No `print()` — use `frappe.logger()` or `frappe.log_error()`
- Use Ruff for Python linting/formatting
- Use ESLint + Prettier for TypeScript/React

## Patterns to Follow

### Whitelisted API (with permissions)

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
from frappe import _
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

### React Frontend Page (TypeScript)

```tsx
import React, { useEffect, useState } from "react";

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

## Testing

- TDD: write tests first
- Name tests: `test_<function>_<scenario>_<expected>`
- Use Arrange/Act/Assert pattern
- Mock external dependencies, not your own code
- 80% minimum coverage; 90%+ for domain logic
- Use `frappe.tests.utils.FrappeTestCase` for DocType tests

```python
def test_get_item_details_with_valid_code_returns_item():
    """Valid item code returns correct item details."""
    # Arrange
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": "TEST-001",
        "item_name": "Test Item",
    }).insert()

    # Act
    result = get_item_details(item.item_code)

    # Assert
    assert result is not None
    assert result["item_name"] == "Test Item"
```

## Database

- Frappe ORM for all data access — avoid raw SQL
- DocType JSON defines the schema — never modify tables manually
- Parameterized queries only: `frappe.db.sql(query, values=params)`
- Migrations via Frappe patches (in `patches.txt`)
- Paginate all list endpoints with `limit_page_length`

## Security

- No hardcoded secrets — use `site_config.json` (dev) or Azure Key Vault (prod)
- Validate all user input with Frappe validators
- Use `frappe.has_permission()` for authorization checks
- Use `@frappe.whitelist()` with permission checks on all APIs
- HTTPS everywhere in production
- MSAL (OIDC) for release builds only

## Git

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Never commit to `main` or `develop` directly
- Feature branches: `feature/<ticket>-<description>`
- Small, focused PRs (< 400 lines changed)
