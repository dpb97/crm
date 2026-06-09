"""Re-run install_custom_fields so the new ToDo / User fields land:
- ToDo: lcs_kind, lcs_reason, lcs_visible_to_manager, lcs_notify_*
- User: sales_manager
Idempotent.
"""

from lcs_integrations.patches.v1_0.install_custom_fields import execute as install


def execute():
    install()
