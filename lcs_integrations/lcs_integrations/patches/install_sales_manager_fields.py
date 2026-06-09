"""Re-run install_custom_fields so the new sales_manager fields land
on CRM Lead + CRM Deal. Idempotent — safe to re-run."""

from lcs_integrations.patches.v1_0.install_custom_fields import execute as install


def execute():
    install()
