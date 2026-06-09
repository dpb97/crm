"""Owner-facing sales report (R-05).

Aggregates LCS Project + LCS Offer + CRM Deal data along three axes:
Sales Manager x Territory x Segment, plus pipeline-stage totals and
forecast (sum of estimated_value * win-probability).

Two output formats:
  - Excel via openpyxl: one sheet per axis + raw deal list.
  - PDF via Frappe's print rendering of the template
    `print_format/lcs_sales_report.html` (template kept inline below
    because it is short and we want it auditable in one place).

Time range is parameterised; the API entrypoint is whitelisted so the
Owner can pull it on demand from a button or scheduled job.
"""

from __future__ import annotations

import io
from datetime import date, datetime, timedelta
from typing import Optional

import frappe
from frappe import _
from frappe.utils import getdate, today


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def collect(start: date, end: date) -> dict:
    """Pull the data once; both Excel and PDF render from the same dict."""
    deals = frappe.db.sql(
        """
        SELECT  d.name,
                d.organization,
                d.deal_owner,
                d.sales_manager,
                d.country,
                d.status,
                d.annual_revenue,
                d.modified,
                d.creation
        FROM    `tabCRM Deal` d
        WHERE   d.modified BETWEEN %s AND %s
        """,
        (start, end),
        as_dict=True,
    )

    projects = frappe.db.sql(
        """
        SELECT  p.name,
                p.project_name,
                p.country,
                p.phase,
                p.sales_manager,
                p.salesperson,
                p.estimated_value,
                p.probability,
                p.modified
        FROM    `tabLCS Project` p
        WHERE   p.modified BETWEEN %s AND %s
        """,
        (start, end),
        as_dict=True,
    )

    offers = frappe.db.sql(
        """
        SELECT  o.name,
                o.project,
                o.status,
                o.value,
                o.currency,
                o.probability,
                o.lost_reason,
                o.modified
        FROM    `tabLCS Offer` o
        WHERE   o.modified BETWEEN %s AND %s
        """,
        (start, end),
        as_dict=True,
    )

    by_manager = _group_sum(projects, "sales_manager")
    by_territory = _group_sum(projects, "country")
    forecast = sum(
        (p.get("estimated_value") or 0) * (p.get("probability") or 0) / 100
        for p in projects
    )
    lost_reasons = _count(offers, "lost_reason", where=lambda r: r["status"] == "Lost")

    return {
        "start": start,
        "end": end,
        "deals": deals,
        "projects": projects,
        "offers": offers,
        "by_manager": by_manager,
        "by_territory": by_territory,
        "forecast": forecast,
        "lost_reasons": lost_reasons,
    }


def _group_sum(rows: list[dict], key: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for r in rows:
        k = r.get(key) or "(unassigned)"
        out[k] = out.get(k, 0) + (r.get("estimated_value") or 0)
    return out


def _count(rows: list[dict], key: str, where=lambda r: True) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        if not where(r):
            continue
        k = r.get(key) or "(none)"
        out[k] = out.get(k, 0) + 1
    return out


# ---------------------------------------------------------------------------
# Excel export
# ---------------------------------------------------------------------------

def to_xlsx(data: dict) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError:
        frappe.throw(_("openpyxl is not installed on this bench."))

    wb = Workbook()

    ws = wb.active
    ws.title = "Summary"
    ws.append(["LCS Sales Report"])
    ws.append([f"Range: {data['start']} – {data['end']}"])
    ws.append([])
    ws.append(["Forecast (sum of estimated_value * probability)", data["forecast"]])
    ws.append([])

    ws2 = wb.create_sheet("By Sales Manager")
    ws2.append(["Sales Manager", "Pipeline Value"])
    for k, v in sorted(data["by_manager"].items(), key=lambda kv: -kv[1]):
        ws2.append([k, v])

    ws3 = wb.create_sheet("By Country")
    ws3.append(["Country", "Pipeline Value"])
    for k, v in sorted(data["by_territory"].items(), key=lambda kv: -kv[1]):
        ws3.append([k, v])

    ws4 = wb.create_sheet("Lost Reasons")
    ws4.append(["Lost Reason", "Count"])
    for k, v in sorted(data["lost_reasons"].items(), key=lambda kv: -kv[1]):
        ws4.append([k, v])

    ws5 = wb.create_sheet("Projects (raw)")
    headers = ["name", "project_name", "country", "phase", "sales_manager",
               "salesperson", "estimated_value", "probability", "modified"]
    ws5.append(headers)
    for p in data["projects"]:
        ws5.append([p.get(h) for h in headers])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF export — Frappe's get_pdf renders an inline HTML template.
# ---------------------------------------------------------------------------

PDF_TEMPLATE = """
<h1>LCS Sales Report</h1>
<p><strong>Range:</strong> {{ start }} – {{ end }}</p>
<h2>Forecast</h2>
<p>{{ "{:,.0f}".format(forecast) }} (sum of estimated value &times; win probability)</p>

<h2>By Sales Manager</h2>
<table border="1" cellpadding="4">
  <thead><tr><th>Sales Manager</th><th>Pipeline Value</th></tr></thead>
  <tbody>
    {% for k, v in by_manager_sorted %}
      <tr><td>{{ k }}</td><td>{{ "{:,.0f}".format(v) }}</td></tr>
    {% endfor %}
  </tbody>
</table>

<h2>By Country</h2>
<table border="1" cellpadding="4">
  <thead><tr><th>Country</th><th>Pipeline Value</th></tr></thead>
  <tbody>
    {% for k, v in by_territory_sorted %}
      <tr><td>{{ k }}</td><td>{{ "{:,.0f}".format(v) }}</td></tr>
    {% endfor %}
  </tbody>
</table>

<h2>Lost Reasons</h2>
<table border="1" cellpadding="4">
  <thead><tr><th>Reason</th><th>Count</th></tr></thead>
  <tbody>
    {% for k, v in lost_reasons_sorted %}
      <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
    {% endfor %}
  </tbody>
</table>
"""


def to_pdf(data: dict) -> bytes:
    from frappe.utils.pdf import get_pdf
    html = frappe.render_template(PDF_TEMPLATE, {
        **data,
        "by_manager_sorted": sorted(data["by_manager"].items(), key=lambda kv: -kv[1]),
        "by_territory_sorted": sorted(data["by_territory"].items(), key=lambda kv: -kv[1]),
        "lost_reasons_sorted": sorted(data["lost_reasons"].items(), key=lambda kv: -kv[1]),
    })
    return get_pdf(html)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def export(format: str = "xlsx", start: Optional[str] = None, end: Optional[str] = None) -> dict:
    """Whitelisted entrypoint. Returns a file-attached URL.

    `format` is "xlsx" or "pdf". `start`/`end` are ISO dates; if
    omitted, defaults to the trailing 90 days.
    """
    if format not in ("xlsx", "pdf"):
        frappe.throw(_("format must be xlsx or pdf"))

    end_d = getdate(end) if end else getdate(today())
    start_d = getdate(start) if start else end_d - timedelta(days=90)

    data = collect(start_d, end_d)

    if format == "xlsx":
        payload = to_xlsx(data)
        filename = f"lcs-sales-report-{start_d}_{end_d}.xlsx"
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        payload = to_pdf(data)
        filename = f"lcs-sales-report-{start_d}_{end_d}.pdf"
        content_type = "application/pdf"

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "is_private": 1,
        "content": payload,
    }).insert(ignore_permissions=True)

    return {
        "file_url": file_doc.file_url,
        "file_name": filename,
        "content_type": content_type,
    }
