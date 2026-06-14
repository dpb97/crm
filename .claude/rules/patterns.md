# Architecture & Patterns Rules

## Frappe App Architecture

```
DocType (core)      ->  Schema + Controller (business logic)
API (endpoints)     ->  Whitelisted functions, permission-checked
Hooks (lifecycle)   ->  App events, scheduler, overrides
Frontend (UI)       ->  Vue 3 pages (Vite) + Frappe client scripts
```

## Key Patterns

### DocType Controller Pattern
- Business logic lives in DocType controller classes
- Use lifecycle hooks: `validate`, `before_save`, `on_submit`, `on_cancel`
- Keep controllers focused — extract complex logic to `utils/` or `services/`
- One DocType per directory

### Service Layer (for complex logic)
- Extract shared business logic into `utils/` or dedicated service modules
- Services are plain Python modules with functions
- Use type hints and docstrings on all public functions
- Keep services stateless — pass data in, get data out

### Whitelisted API Pattern
- All external-facing APIs use `@frappe.whitelist()`
- Always check permissions: `frappe.has_permission()` or `frappe.only_for()`
- Return dicts or lists — Frappe serializes automatically
- Group related endpoints in `api/` submodules

### API Response Convention
- Frappe wraps responses in `{"message": ...}` automatically
- For custom response structure, return a dict with `success`, `data`, `error` keys
- Use proper HTTP exceptions: `frappe.throw()` with appropriate `exc` type

### Error Handling
- Use Frappe exception types (`DoesNotExistError`, `ValidationError`, `PermissionError`)
- `frappe.throw()` for user-facing errors with translatable messages
- `frappe.log_error()` for server-side logging (writes to Error Log DocType)
- Never expose stack traces in production
- Use `frappe._("message")` for translatable error messages

### Event-Driven Patterns
- Use Frappe hooks (`doc_events`) to react to DocType lifecycle
- Use `frappe.enqueue()` for background jobs (Redis Queue)
- Use Frappe Scheduler for recurring tasks (defined in `hooks.py`)

## Frontend Patterns (Pilanda)

- Frontend ist **Vue 3 + Vite** (Pilanda-Stack-Standard) — **kein React**.
  Beachte: die Vertriebs-UI ist primär die eingebettete Frappe-CRM-SPA.
- Single-File-Components (`<script setup>`), gebaut nach `<app>/public/dist`,
  gemountet über eine Desk-Page.
- Optik **ausschließlich** über `pilanda_theme`-CSS-Tokens (`--pp-*`) — keine
  nackten Hex/Radien, kein Tailwind.

## Database Patterns

- Frappe ORM for all standard data access
- DocType JSON defines the schema — never modify tables manually
- Migrations via Frappe patches (listed in `patches.txt`)
- Use `frappe.get_list()` with `limit_page_length` for paginated queries
- Use `frappe.db.sql()` with parameterized queries when ORM is insufficient
- Index frequently queried fields in DocType definitions
