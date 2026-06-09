"""Frankfurter.dev — ECB-backed FX rates.

Public, key-free API at https://api.frankfurter.dev/v1/.
We use two endpoints:

  GET /v1/latest?base=USD&symbols=EUR
  GET /v1/<yyyy-mm-dd>?base=USD&symbols=EUR

Why Frankfurter:
  - free, no API key, no usage cap relevant for an internal CRM
  - ECB reference rates (matches LCS' bookkeeping basis)
  - same endpoint works for historical rates on offer revisions

Caching: Redis, 6h TTL, keyed by (base, target, date|"latest"). The
ECB publishes one set of rates per business day around 16:00 CET, so a
6-hour live cache keeps every sales user from hitting the upstream API
hundreds of times per page render.
"""

from __future__ import annotations

from datetime import date as _date
from typing import Optional

import frappe
import requests


_BASE_URL = "https://api.frankfurter.dev/v1"
_TIMEOUT_SEC = 5
_CACHE_TTL_SEC = 6 * 60 * 60  # 6 hours
_BASE_CURRENCY = "EUR"  # LCS books in EUR; this is the reporting currency


def _cache_key(from_ccy: str, to_ccy: str, on_date: Optional[_date]) -> str:
    bucket = on_date.isoformat() if on_date else "latest"
    return f"lcs_fx:{from_ccy}:{to_ccy}:{bucket}"


def get_rate(
    from_ccy: str,
    to_ccy: str = _BASE_CURRENCY,
    *,
    on_date: Optional[_date] = None,
) -> Optional[float]:
    """Return the FX rate `from_ccy -> to_ccy`, i.e. `amount_in_from *
    rate = amount_in_to`. `None` if Frankfurter doesn't know the pair
    (e.g. unsupported currency, weekend before any historical data).

    `on_date=None` means "latest". When set, returns the published
    rate for that business day (Frankfurter falls back to the most
    recent previous business day automatically).

    Always returns 1.0 for the identity pair.
    """
    if not from_ccy or not to_ccy:
        return None
    from_ccy = from_ccy.upper().strip()
    to_ccy = to_ccy.upper().strip()
    if from_ccy == to_ccy:
        return 1.0

    cache = frappe.cache()
    key = _cache_key(from_ccy, to_ccy, on_date)
    cached = cache.get_value(key)
    if cached is not None:
        try:
            return float(cached)
        except (TypeError, ValueError):
            pass

    path = on_date.isoformat() if on_date else "latest"
    url = f"{_BASE_URL}/{path}"
    params = {"base": from_ccy, "symbols": to_ccy}

    try:
        r = requests.get(url, params=params, timeout=_TIMEOUT_SEC)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        frappe.log_error(
            title="Frankfurter FX request failed",
            message=f"{url}?{params}\n\n{e}",
        )
        return None

    rate = (payload.get("rates") or {}).get(to_ccy)
    if rate is None:
        return None
    try:
        rate_f = float(rate)
    except (TypeError, ValueError):
        return None

    cache.set_value(key, rate_f, expires_in_sec=_CACHE_TTL_SEC)
    return rate_f


def convert(
    amount: float,
    from_ccy: str,
    to_ccy: str = _BASE_CURRENCY,
    *,
    on_date: Optional[_date] = None,
    rate: Optional[float] = None,
) -> Optional[float]:
    """Convert `amount` from `from_ccy` to `to_ccy`.

    Pass a pre-frozen `rate` to use a snapshotted value (offer
    historical rate). Otherwise Frankfurter is consulted.
    """
    if amount is None:
        return None
    if rate is None:
        rate = get_rate(from_ccy, to_ccy, on_date=on_date)
    if rate is None:
        return None
    return round(float(amount) * rate, 2)
