# Git Workflow Rules

## Commit Message Format

Use Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Description                                    |
|------------|------------------------------------------------|
| `feat`     | New feature                                    |
| `fix`      | Bug fix                                        |
| `refactor` | Code change that neither fixes nor adds        |
| `docs`     | Documentation only                             |
| `test`     | Adding or correcting tests                     |
| `chore`    | Build process, CI, tooling                     |
| `style`    | Formatting, whitespace (no logic change)       |
| `perf`     | Performance improvement                        |
| `ci`       | CI/CD pipeline changes                         |
| `revert`   | Reverting a previous commit                    |

### Examples

```
feat(auth): add JWT refresh token endpoint
fix(orders): correct total calculation with discounts
refactor(users): extract validation into FluentValidation
docs(api): update OpenAPI spec for v2 endpoints
test(payments): add integration tests for Stripe webhook
```

## Branch Strategy (Git Flow)

- `main` — Production-ready code. **Protected, no direct pushes.**
- `develop` — Integration branch. **Protected, no direct pushes.**
- `feature/<ticket-id>-<short-description>` — New features, branch from `develop`
- `bugfix/<ticket-id>-<short-description>` — Bug fixes, branch from `develop`
- `hotfix/<ticket-id>-<short-description>` — Urgent production fixes, branch from `main`
- `release/<version>` — Release preparation, branch from `develop`

## Pull Request Workflow

1. Create feature/bugfix branch from `develop`
2. Make small, focused commits
3. Push branch and open PR to `develop`
4. PR requires at least 1 approval
5. All CI checks must pass (build, test, lint)
6. Squash merge preferred for clean history
7. Delete branch after merge

## Rules

- Never commit directly to `main` or `develop`
- Always test locally before pushing (`bench run-tests` + `npm test`)
- Keep PRs small and focused (< 400 lines changed)
- Write meaningful PR descriptions
- Link PRs to issues/tickets
- Include Frappe patches in `patches.txt` when schema changes
