# Copilot Instructions

## Project Context

Python / Frappe Framework (v16) ERP app in the shared **Pilanda bench** (site
`lcs.local`), Frappe modular app architecture. **Repo-Layout = Root-Layout** (the
repo root IS the installable app). **Frontend = Vue 3 + Vite** (note: the sales UI is
primarily the embedded Frappe CRM SPA).

## Tech Stack

- **Language:** Python 3.11+ (backend), JavaScript/Vue (frontend)
- **Framework:** Frappe Framework v16
- **ORM:** Frappe ORM (DocType-based)
- **Database:** MariaDB 10.6+
- **Cache/Queue:** Redis (cache, queue, socketio)
- **Testing:** pytest + Frappe test runner (Python), Vitest + @vue/test-utils (Vue)
- **Frontend:** Vue 3 + Vite for custom pages, Frappe UI for standard views
- **Styling:** `pilanda_theme` CSS tokens (`--pp-*`) — no Tailwind, no raw hex/radii
- **Auth:** Frappe built-in (dev), MSAL / OIDC (release/production)

## Architecture

| Layer              | Location                        | Purpose                                   |
|--------------------|---------------------------------|-------------------------------------------|
| DocType Controller | `<module>/doctype/<name>/`      | Business logic, lifecycle hooks           |
| API Endpoints      | `api/`                          | Whitelisted functions, permission-checked |
| Services / Utils   | `utils/`                        | Shared business logic, helpers            |
| Hooks              | `hooks.py`                      | App events, scheduler, overrides          |
| Frontend (Vue)     | `frontend/src/`                 | Custom Vue 3 + Vite pages                 |
| Client Scripts     | `<doctype>/<doctype>.js`        | Frappe form client-side logic             |

## Code Style

- Use `snake_case` for functions, variables, file names
- Use `PascalCase` for class names (DocType controllers) and Vue components
- Use `UPPER_SNAKE_CASE` for constants
- Type hints on all function signatures (Python 3.11+ syntax)
- Docstrings on all public functions (Google style)
- Max 800 lines per file; prefer 200-400
- No magic numbers or strings — use constants or enums
- No `print()` — use `frappe.logger()` or `frappe.log_error()`
- Use Ruff for Python linting/formatting; ESLint + Prettier for the Vue/JS frontend

## Patterns to Follow

### Whitelisted API (with permissions)

```python
import frappe
from frappe import _


@frappe.whitelist()
def get_item_details(item_code: str) -> dict:
    """Get item details by item code."""
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


class ExampleDoc(Document):
    def validate(self):
        self._validate_items()

    def _validate_items(self):
        if not self.items:
            frappe.throw(_("At least one item is required"))
```

### Error Handling

```python
import frappe
from frappe import _


def process(order_id: str) -> dict:
    try:
        doc = frappe.get_doc("Sales Order", order_id)
        doc.submit()
        return {"success": True, "data": doc.as_dict()}
    except frappe.DoesNotExistError:
        frappe.throw(_("Order {0} not found").format(order_id), exc=frappe.DoesNotExistError)
    except frappe.ValidationError as e:
        frappe.log_error(title="Order Processing Error")
        frappe.throw(_("Validation failed: {0}").format(str(e)))
```

### Vue Frontend Page (Vue 3 SFC)

```vue
<script setup>
import { ref, onMounted } from "vue";

const props = defineProps({ itemCode: String });
const item = ref(null);

onMounted(() => {
  frappe.call({
    method: "<app>.api.get_item_details",
    args: { item_code: props.itemCode },
    callback: (r) => (item.value = r.message),
  });
});
</script>

<template>
  <div v-if="!item">Loading…</div>
  <div v-else>
    <h1>{{ item.item_name }}</h1>
    <p>{{ item.item_code }}</p>
  </div>
</template>
```

## Testing

- TDD: write tests first; name `test_<function>_<scenario>_<expected>`
- Arrange/Act/Assert; mock external dependencies, not your own code
- 80% minimum coverage; 90%+ for domain logic
- Use `frappe.tests.utils.FrappeTestCase` for DocType tests; Vitest for Vue

## Database

- Frappe ORM for all data access — avoid raw SQL
- DocType JSON defines the schema — never modify tables manually
- Parameterized queries only: `frappe.db.sql(query, values=params)`
- Migrations via Frappe patches (in `patches.txt`)
- Paginate all list endpoints with `limit_page_length`

## Security

- No hardcoded secrets — use `site_config.json` (dev) / secret manager (prod)
- Validate all user input with Frappe validators
- Use `frappe.has_permission()` for authorization checks
- `@frappe.whitelist()` with permission checks on all APIs
- HTTPS everywhere in production; MSAL (OIDC) for release builds only

## Git

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Never commit to `main` or `develop` directly
- Feature branches: `feature/<ticket>-<description>`
- Small, focused PRs (< 400 lines changed)
