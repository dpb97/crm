"""Re-run install_custom_fields so the new P-04 lead-qualification
fields (country, budget_range, decision_level, expected_timeline)
land on CRM Lead + CRM Deal. Idempotent."""

from lcs_integrations.patches.v1_0.install_custom_fields import execute as install


def execute():
    install()
