"""Lese-Endpunkte von pilanda_sales fuer die Vertrieb-Modul-UI.

get_sales_dashboard() speist das Vertrieb-Modul-Dashboard (Desk-Page
sales-dashboard, N10 / Master §6.2). Grundsatz: **NUR echte Quellen** —
keine Schatten-/Demo-Daten. Fehlt eine optionale App (Pilot/salesbot-Senke),
wird das ehrlich als "nicht verfuegbar" gemeldet statt erfunden.

Quellen:
  - Pilot Tender (App `pilot`, optional) — Ausschreibungs-Scout: Zaehler,
    Relevanz-Verteilung, neueste Treffer.
  - ERPNext Quotation / Customer — reale Zaehler (0 = ehrlich).
  - ERPNext Project + Custom Field `custom_sales_phase` (Eigentum dieser App)
    — Phasen-Verteilung der Vertriebsprojekte.
  - "Auftraege" = gefilterte Projektliste `status=Auftrag` (Master-Entscheid
    E3: gewonnenes Projekt = Auftrag, kein eigenes Objekt). Das Feld, das die
    Filterliste kuenftig speist (`Project.status` vs. `custom_sales_phase`),
    ist im Fachplan noch OFFEN (SO-Automatik-Spez) — hier bewusst 1:1 der
    Nav-Filter, ehrlich (aktuell i. d. R. 0).
"""

import frappe

# Bekannte Auspraegungen (SSOT: Pilot Tender / custom_sales_phase). Explizite
# Zaehlung statt SQL-Aggregat — vermeidet get_all-Feldvalidierung und ist robust.
_RELEVANZ = ["Hoch", "Mittel", "Niedrig", "Irrelevant"]
_PHASEN = ["Lead", "Projektierung", "Kalkulation", "Angebot", "Verhandlung", "Entscheidung Kunde"]

# Nav-SSOT (pilanda/modules_data.py): Vertrieb ▸ Aufträge → q "status=Auftrag".
_AUFTRAG_STATUS = "Auftrag"


def _has_doctype(dt: str) -> bool:
    return bool(frappe.db.table_exists(dt))


@frappe.whitelist()
def get_sales_dashboard() -> dict:
    """Aggregat fuer das Vertrieb-Modul-Dashboard. Read-only."""
    out = {
        "pilot_available": False,
        "pilot_total": 0,
        "pilot_by_relevanz": [],
        "pilot_newest": [],
        "quotation_total": frappe.db.count("Quotation"),
        "customer_total": frappe.db.count("Customer"),
        "project_total": frappe.db.count("Project"),
        "project_by_phase": [],
        "auftraege_total": frappe.db.count("Project", {"status": _AUFTRAG_STATUS}),
        "auftraege_filter": {"status": _AUFTRAG_STATUS},
        "stand": frappe.utils.format_datetime(frappe.utils.now_datetime(), "dd.MM.yyyy HH:mm"),
    }

    # --- Pilot (salesbot-Senke, optionale App) --------------------------
    if _has_doctype("Pilot Tender"):
        out["pilot_available"] = True
        out["pilot_total"] = frappe.db.count("Pilot Tender")
        rel = []
        for r in _RELEVANZ:
            n = frappe.db.count("Pilot Tender", {"relevanz": r})
            if n:
                rel.append({"relevanz": r, "n": n})
        out["pilot_by_relevanz"] = rel
        out["pilot_newest"] = frappe.get_all(
            "Pilot Tender",
            fields=["name", "titel", "land", "score", "status", "deadline", "url"],
            order_by="published_am desc",
            limit=6,
        )

    # --- Vertriebsprojekte nach Phase (custom_sales_phase) --------------
    dist = []
    assigned = 0
    for p in _PHASEN:
        n = frappe.db.count("Project", {"custom_sales_phase": p})
        assigned += n
        dist.append({"phase": p, "n": n})
    ohne = out["project_total"] - assigned
    if ohne > 0:
        dist.append({"phase": "(ohne Phase)", "n": ohne, "unset": True})
    out["project_by_phase"] = dist

    return out
