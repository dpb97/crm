# Coding Style Rules

## File Organization

- Many small files over few large files
- 200-400 lines typical, 800 max per file
- Organize by Frappe module, not by type
- One DocType per directory with controller, schema, client script, tests
- Keep custom API endpoints in dedicated `api/` modules

## Python Conventions

- Use `snake_case` for functions, variables, file names
- Use `PascalCase` for class names (DocType controllers)
- Use `UPPER_SNAKE_CASE` for constants
- Type hints on all function signatures (Python 3.11+ syntax)
- Use `@frappe.whitelist()` for all API endpoints
- Docstrings on all public functions (Google style)
- Use `dataclasses` or `TypedDict` for structured data

## Vue / JS Conventions (Pilanda-Frontend)

- Frontend ist **Vue 3 + Vite** (Pilanda-Stack-Standard) — **kein React**.
  Beachte: die Vertriebs-UI ist primär die eingebettete Frappe-CRM-SPA.
- Single-File-Components mit `<script setup>`; `PascalCase` für Komponenten-Dateien
- `camelCase` für Variablen/Funktionen/Props, `UPPER_SNAKE_CASE` für Konstanten
- Optik **ausschließlich** über `pilanda_theme`-CSS-Tokens (`--pp-*`) — keine
  nackten Hex/Radien, **kein Tailwind**
- Gebaut nach `<app>/public/dist`, gemountet über eine Desk-Page

## Code Quality

- No `print()` in production code — use `frappe.logger()` or `frappe.log_error()`
- No magic numbers or strings — use constants or enums
- No commented-out code — use version control
- No emojis in code, comments, or documentation
- Keep functions under 30 lines — extract helpers
- Maximum 3 parameters per function — use dicts/dataclasses for more
- Use Ruff for linting and formatting (Python)
- Use ESLint + Prettier for the Vue/JS frontend
