"""Re-run install_custom_fields so the new ERPNext Project.lcs_project
back-link field gets installed on existing sites. Idempotent."""

from lcs_integrations.patches.v1_0.install_custom_fields import execute as install


def execute():
    install()
