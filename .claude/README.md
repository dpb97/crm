# .claude/ -- Claude Code Configuration

Project-level Claude Code settings following the [everything-claude-code](https://github.com/affaan-m/everything-claude-code) pattern.

## Structure

```
.claude/
|-- commands/              # Slash commands for common workflows
|   |-- plan.md            # /plan -- Implementation planning
|   |-- tdd.md             # /tdd -- Test-driven development
|   |-- code-review.md     # /code-review -- Quality review
|
|-- rules/                 # Always-active guidelines
|   |-- coding-style.md    # Python/TS naming, file org, code quality
|   |-- git-workflow.md    # Commits, branches, PRs
|   |-- testing.md         # TDD, pytest, Vitest, coverage
|   |-- security.md        # Secrets, SQL injection, Frappe auth
|   |-- patterns.md        # Frappe architecture, DocType patterns
```

## How It Works

- **Rules** are loaded automatically and guide every interaction
- **Commands** are invoked with `/command-name` in Claude Code
- **CLAUDE.md** (project root) provides project overview and context

## Customization

- Add new rules: create `.md` files in `rules/`
- Add new commands: create `.md` files in `commands/`
- For advanced usage (agents, hooks, skills), see [everything-claude-code](https://github.com/affaan-m/everything-claude-code)
