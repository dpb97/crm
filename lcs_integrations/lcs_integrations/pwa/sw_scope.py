"""Service-Worker scope header for the CRM PWA.

The CRM service worker is physically served from
``/assets/crm/frontend/sw.js``, but it must control the ``/crm`` navigation
scope so offline deep links (e.g. ``/crm/deals/CRM-DEAL-0001``) resolve from
cache. Per the Service Worker spec a worker may only widen its scope beyond
its own directory when the sw.js HTTP response carries the
``Service-Worker-Allowed`` header
(https://www.w3.org/TR/service-workers/#service-worker-allowed). Without it
the browser rejects ``register(url, {scope: "/crm"})`` with:

    The path of the provided scope ('/crm') is not under the max scope
    allowed ('/assets/crm/frontend/').

Production nginx sets this header directly on the sw.js location — see
``docker/nginx/nginx.conf`` (``location = /assets/crm/frontend/sw.js``).
KEEP THE TWO IN SYNC. This hook is the application-level equivalent for any
deployment where the sw.js request is proxied through to the Frappe WSGI app
(e.g. gunicorn) instead of being served by a static front end.

KNOWN LIMITATION — Frappe dev server: ``bench serve`` serves everything under
``/assets/*`` via werkzeug ``SharedDataMiddleware`` (see
``frappe/app.py:application_with_statics``), which wraps the WSGI app and
returns the file BEFORE any ``after_request`` hook runs. In that mode this
hook does NOT fire for sw.js (verify with ``curl -I`` -> the ETag has the
``wzsdm-`` prefix). To get the ``/crm`` scope on a dev bench, front it with
nginx (which sets the header) or serve sw.js through the app. In dev without
that, the frontend falls back to the default (narrow) scope and only cold
offline deep-navigation degrades — asset caching still works.
"""

from __future__ import annotations

from typing import Any

# Suffix match (not equality): tolerate an optional deployment path prefix in
# front of the asset mount while still pinning the exact sw.js asset.
_SW_SUFFIX = "/assets/crm/frontend/sw.js"


def set_sw_allowed_scope(response: Any, request: Any) -> None:
    """after_request hook: allow the CRM sw.js to claim the ``/crm`` scope.

    Signature matches ``frappe.app.run_after_request_hooks``, which calls
    ``frappe.call(task, response=response, request=request)``. ``frappe.call``
    filters kwargs to the callable's parameters, so both are always supplied.

    Fail-loud by design: no ``try/except`` swallowing here. A malformed
    response/request object is a real bug we want surfaced;
    ``run_after_request_hooks`` already logs (and cannot re-raise) at the
    outer boundary, so a genuine error is recorded rather than hidden.
    """
    if request.path.endswith(_SW_SUFFIX):
        response.headers["Service-Worker-Allowed"] = "/crm"
