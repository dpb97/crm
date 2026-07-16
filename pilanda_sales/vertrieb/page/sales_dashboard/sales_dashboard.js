// Vertrieb — Modul-Dashboard (N10, Master ENTWICKLUNGSPLAN §6.2). Laedt die Vue-UI
// aus pilanda_sales/frontend (Bundle: /assets/pilanda_sales/dist/sales_dashboard.{js,css}).
// Einstieg des Vertrieb-Moduls: KPI-Zeile + Karten aus pilanda_sales.api.get_sales_dashboard.
// CRM-SPA (/crm, Owner Dominik) und Pilot-Workbench (/app/pilot-workbench) werden
// NICHT ersetzt — das Dashboard springt dorthin ab. Muster identisch zu pls_dashboard.

frappe.pages["sales-dashboard"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper, title: __("Vertrieb"), single_column: true,
    });
    if (wrapper && wrapper.setAttribute) wrapper.setAttribute("data-pp-module", "vertrieb");

    const base = "/assets/pilanda_sales/dist/sales_dashboard";
    const v = "?v=" + Date.now();

    const host = document.createElement("div");
    host.className = "sales-dashboard-host";
    $(page.body).empty().append(host);

    if (!document.getElementById("sales-dashboard-css")) {
        const link = document.createElement("link");
        link.id = "sales-dashboard-css"; link.rel = "stylesheet"; link.href = base + ".css" + v;
        document.head.appendChild(link);
    }

    function mount() {
        if (window.PilandaSalesDashboard && window.PilandaSalesDashboard.mount) {
            window.PilandaSalesDashboard.mount(host, { page });
        }
    }

    if (window.PilandaSalesDashboard && window.PilandaSalesDashboard.mount) {
        mount();
    } else {
        const s = document.createElement("script");
        s.id = "sales-dashboard-lib"; s.src = base + ".js" + v; s.async = true;
        s.onload = mount;
        s.onerror = () => {
            const err = document.createElement("div");
            err.style.cssText = "padding:24px;color:#dc2626";
            err.textContent = __("sales_dashboard.js nicht gefunden — bitte 'yarn build' (frontend) + 'bench build' ausführen.");
            host.replaceChildren(err);
        };
        document.head.appendChild(s);
    }
};
