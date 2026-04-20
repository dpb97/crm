"""Business logic for the abas integration.

Takes Frappe documents in, hands DTOs to the client, writes audit logs and
updates entity maps. Everything here is covered by unit tests that mock the
`AbasClient`.
"""

from __future__ import annotations

import time
from typing import Any

import frappe

from .client import AbasClient, AbasClientError
from .schemas import AbasCustomer, DeliveryStatusEvent


# ---- Mapping helpers ----
def _customer_to_dto(doc: Any) -> AbasCustomer:
    # ERPNext Customer fields: customer_name, email_id (via primary Contact
    # link, absent on Customer directly — fall back to the doc's fields),
    # mobile_no, country (billing address lookup deferred to a follow-up).
    return AbasCustomer(
        abas_id=doc.get("abas_id") or "",
        name=doc.get("customer_name") or doc.get("company_name") or doc.get("full_name") or "",
        email=doc.get("email_id"),
        phone=doc.get("mobile_no") or doc.get("phone"),
        country=doc.get("country"),
    )


# ---- Audit ----
def _log(direction: str, entity: str, *, status: str, payload: dict, response: dict | None = None,
         error: str | None = None, duration_ms: int = 0, ref: tuple[str, str] | None = None) -> None:
    frappe.flags.in_abas_sync = True
    try:
        log = frappe.new_doc("ABAS Sync Log")
        log.direction = direction
        log.entity = entity
        log.status = status
        log.duration_ms = duration_ms
        if ref:
            log.reference_doctype, log.reference_name = ref
        log.request_payload = frappe.as_json(payload)
        if response is not None:
            log.response_payload = frappe.as_json(response)
        if error:
            log.error_message = error
        log.insert(ignore_permissions=True)
    finally:
        frappe.flags.in_abas_sync = False


# ---- Operations ----
def push_customer(crm_doctype: str, crm_name: str) -> str:
    """Push a CRM Deal's linked customer to abas. Returns the abas ID."""
    doc = frappe.get_doc(crm_doctype, crm_name)
    dto = _customer_to_dto(doc.as_dict())
    started = time.monotonic()
    try:
        with AbasClient() as client:
            response = client.push_customer(dto.model_dump(exclude_none=True))
        duration = int((time.monotonic() - started) * 1000)
        abas_id = response.get("abas_id", dto.abas_id)
        _upsert_entity_map(crm_doctype, crm_name, "Customer", abas_id, direction="push")
        _log("push", "Customer", status="succeeded", payload=dto.model_dump(), response=response,
             duration_ms=duration, ref=(crm_doctype, crm_name))
        return abas_id
    except AbasClientError as exc:
        duration = int((time.monotonic() - started) * 1000)
        _log("push", "Customer", status="failed", payload=dto.model_dump(),
             error=str(exc), duration_ms=duration, ref=(crm_doctype, crm_name))
        raise


def handle_delivery_webhook(raw: dict[str, Any]) -> None:
    """Apply an incoming delivery-status event to the ERPNext Sales Order."""
    event = DeliveryStatusEvent.model_validate(raw)
    orders = frappe.get_all("Sales Order", filters={"abas_order_no": event.order_no}, pluck="name")
    if not orders:
        _log("pull", "Delivery", status="failed", payload=raw,
             error=f"No sales order for abas order {event.order_no}")
        return
    for name in orders:
        # Use LCS-namespaced fields — ERPNext's own `delivery_status` tracks
        # ERPNext's delivery lifecycle, not abas's.
        frappe.db.set_value("Sales Order", name, {
            "lcs_delivery_status": event.status,
            "lcs_planned_ship_date": event.planned_ship_date,
        }, update_modified=True)
        _log("pull", "Delivery", status="succeeded", payload=raw, ref=("Sales Order", name))


def _upsert_entity_map(crm_doctype: str, crm_name: str, abas_type: str, abas_id: str, *,
                       direction: str) -> None:
    filters = {"crm_doctype": crm_doctype, "crm_name": crm_name, "abas_type": abas_type}
    existing = frappe.db.exists("ABAS Entity Map", filters)
    if existing:
        frappe.db.set_value("ABAS Entity Map", existing, {
            "abas_id": abas_id,
            "last_sync": frappe.utils.now_datetime(),
            "last_sync_direction": direction,
        })
        return
    frappe.get_doc({
        "doctype": "ABAS Entity Map",
        **filters,
        "abas_id": abas_id,
        "last_sync": frappe.utils.now_datetime(),
        "last_sync_direction": direction,
    }).insert(ignore_permissions=True)


def reconcile_delta() -> None:
    """Daily reconciliation job — pulls any out-of-sync customers from abas."""
    # Intentionally a stub: implementation deferred until the scoping workshop
    # clarifies the abas change-feed format.
    frappe.logger().info("[abas] reconcile_delta not yet implemented")
