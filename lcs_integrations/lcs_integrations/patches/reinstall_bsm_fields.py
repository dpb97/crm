"""Re-run install_custom_fields to pick up the newly added BSM Project fields."""

from lcs_integrations.patches.v1_0.install_custom_fields import execute as install


def execute():
    install()
