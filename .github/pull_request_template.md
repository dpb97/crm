<!--
LCS PR template — please fill every section. PRs that skip sections may be rejected.
-->

## Summary

<!-- 1–3 sentences: what does this change and why? -->

## Type of change

- [ ] feat — user-visible feature
- [ ] fix — bug fix
- [ ] refactor — no behavior change
- [ ] chore / ci / docs
- [ ] breaking change (see "Migration notes" below)

## Related tickets / issues

<!-- Linear / GitHub issue IDs. Use "Closes #N" to auto-close. -->

## Test plan

- [ ] `pytest` in `lcs_integrations/` passes, coverage ≥ 80 %
- [ ] `yarn test` in `frontend/` passes
- [ ] Manually verified the happy path
- [ ] Manually verified at least one edge case
- [ ] Does NOT rely on mocks for DB integration tests

## Security checklist

- [ ] No secrets committed; new config flows through env / Azure Key Vault
- [ ] New endpoints are `@frappe.whitelist(allow_guest=False)` unless justified
- [ ] External calls use HMAC / OAuth2 — no unauthenticated webhooks
- [ ] SBOM / Trivy scan is green (CRITICAL/HIGH = 0)

## Screenshots / recordings

<!-- For UI changes: before → after. Required for frontend PRs. -->

## Migration / rollout notes

<!-- DB migrations, feature flags, env vars, deprecations, rollback plan. -->

## Reviewer focus

<!-- Where should reviewers look first? Any risky spots? -->
