import frappe

from lcs_integrations.contacts.domain_binding import backfill_all


def execute():
    """Bind every existing Contact to its customer (CRM Organization) by mail
    domain and fill the visible company_name. Idempotent — the domain_binding
    hooks keep new/edited contacts bound going forward."""
    backfill_all()
