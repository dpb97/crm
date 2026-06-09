import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from pypika import functions as fn

from lcs_integrations.currency.frankfurter import convert, get_rate


class LCSOffer(Document):
    def on_trash(self):
        """Clear back-links on ERPNext Quotation + Sales Order when this
        offer is deleted — leaves the commercial artefacts intact but
        removes the stale pointer back to a non-existent offer."""
        if self.erpnext_quotation and frappe.db.exists("Quotation", self.erpnext_quotation):
            frappe.db.set_value("Quotation", self.erpnext_quotation, "lcs_offer", None)
        if self.erpnext_sales_order and frappe.db.exists("Sales Order", self.erpnext_sales_order):
            frappe.db.set_value("Sales Order", self.erpnext_sales_order, "lcs_project", None)

    def validate(self):
        self.validate_version()
        self.freeze_fx_rate()
        self.sync_project_phase()

    def freeze_fx_rate(self):
        """Snapshot the EUR conversion rate at save time.

        Re-freezes only when value/currency changed since the last save,
        otherwise the historical rate stays — that's the whole point of
        "frozen" pricing for offer revisions.
        """
        if not self.value or not self.currency:
            self.exchange_rate_to_eur = None
            self.value_eur = None
            self.rate_frozen_at = None
            return

        prev_value, prev_currency, prev_rate = None, None, None
        if not self.is_new():
            prev_value, prev_currency, prev_rate = frappe.db.get_value(
                "LCS Offer",
                self.name,
                ("value", "currency", "exchange_rate_to_eur"),
            ) or (None, None, None)

        # prev_rate may be 0.0 (Float column default) before the very
        # first freeze — treat that as "no rate yet".
        had_rate_before = bool(prev_rate) and float(prev_rate) > 0
        unchanged = (
            self.value == prev_value
            and self.currency == prev_currency
            and had_rate_before
        )
        if unchanged:
            return

        rate = get_rate(self.currency, "EUR")
        if rate is None:
            # Upstream Frankfurter unreachable: keep the stale rate
            # rather than zeroing it out. The UI shows a banner so
            # the user knows the frozen value might be from a prior
            # save.
            return

        self.exchange_rate_to_eur = rate
        self.value_eur = round(float(self.value) * rate, 2)
        self.rate_frozen_at = now_datetime()

    def validate_version(self):
        """Ensure version increments per project.

        Uses frappe.qb instead of raw SQL so schema renames on tabLCS Offer
        don't silently break this path.
        """
        if self.version:
            return
        Offer = frappe.qb.DocType("LCS Offer")
        query = (
            frappe.qb.from_(Offer)
            .select(fn.Max(Offer.version).as_("max_version"))
            .where(Offer.project == self.project)
        )
        if self.name:
            query = query.where(Offer.name != self.name)
        result = query.run(as_dict=True)
        max_version = (result[0].get("max_version") if result else None) or 0
        self.version = max_version + 1

    def sync_project_phase(self):
        """Keep project phase in sync with offer status for clarity.

        Phase vocabulary matches LCS Project.phase as of 2026-05
        (Qualified / Budget / Richtpreis / Offer / Negotiation / Won /
        Execution / Completed / Lost).
        """
        if not self.project:
            return
        status_to_phase = {
            "Sent": "Offer",
            "In Review": "Negotiation",
            "Accepted": "Won",
            "Rejected": "Lost",
        }
        new_phase = status_to_phase.get(self.status)
        if new_phase:
            current_phase = frappe.db.get_value("LCS Project", self.project, "phase")
            phase_order = [
                "Qualified",
                "Budget",
                "Richtpreis",
                "Offer",
                "Negotiation",
                "Won",
                "Execution",
                "Completed",
                "Lost",
            ]
            # Defensive against legacy/unknown values: only forward-advance
            # if both phases are known. Otherwise leave the project alone.
            try:
                if phase_order.index(new_phase) > phase_order.index(
                    current_phase or "Qualified"
                ):
                    frappe.db.set_value("LCS Project", self.project, "phase", new_phase)
            except ValueError:
                pass

        # When offer accepted, copy its EUR-converted value into the
        # project's angebot_total so reporting stays in the base currency.
        if self.status == "Accepted" and self.value:
            angebot_total = (
                self.value_eur
                if self.value_eur is not None
                else convert(self.value, self.currency or "EUR", "EUR")
            ) or self.value
            frappe.db.set_value("LCS Project", self.project, "angebot_total", angebot_total)
