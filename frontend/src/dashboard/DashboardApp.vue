<!--
  DashboardApp — Vertrieb-Modul-Dashboard auf /app/sales-dashboard.

  KOPIE des Theme-Bausteins PpDashboard@2 (Copy-Modell, N10 / Master §6.2). Der
  Baustein liefert die Buehne (Kopf + KPI-Zeile + Karten-Raster); hier werden KPIs
  und Karten ueber benannte Slots mit ECHTEN Quellen gefuellt. EINZIGE Datenquelle:
  pilanda_sales.api.get_sales_dashboard (keine Schatten-Daten, kein zweiter Endpoint):
    · KPI-Zeile   → Pilot-Treffer · Vertriebsprojekte · Aufträge · Angebote · Kunden
    · Pilot-Feed  → neueste Ausschreibungen (App pilot, optional; fehlt sie → ehrlich)
    · Phasen      → Vertriebsprojekte nach custom_sales_phase (Eigentum dieser App)
    · Aufträge    → gefilterte Projektliste status=Auftrag (E3; SO-Automatik OFFEN)
    · Absprünge   → CRM-SPA /crm (Dominik), Pilot-Workbench, Angebote, Kunden,
                    Lastenheft, Varianten — reale Nav-Ziele der Vertriebs-SSOT.

  Dashboard = Einstieg des Vertrieb-Moduls; ersetzt NICHT die CRM-SPA (/crm) oder
  die Pilot-Workbench, sondern verortet sich davor und springt dorthin ab.
  Bausteine: PpDashboard@2, PpDataGrid@3.
-->
<script setup>
import { ref, computed, onMounted } from "vue";
import PpDashboard from "./PpDashboard.vue";
import PpDataGrid from "./PpDataGrid.vue";

defineProps({ ctx: { type: Object, default: () => ({}) } });

// Diese Dashboard-App läuft im Frappe-Desk (/app/sales-dashboard), nicht in der
// CRM-SPA — daher Frappes natives window.__ (mit allen App-Übersetzungen) statt
// des frappe-ui-Plugins. Fallback = Identität, falls (noch) nicht geladen.
const __ = (typeof window !== "undefined" && window.__) ? window.__ : (s) => s;

const data = ref(null);
const loading = ref(true);
const errorMsg = ref("");

// ---- Ableitungen ---------------------------------------------------
const pilotAvailable = computed(() => !!data.value?.pilot_available);
const pilotTotal = computed(() => data.value?.pilot_total || 0);
const pilotRelevanz = computed(() => data.value?.pilot_by_relevanz || []);
const pilotNewest = computed(() => data.value?.pilot_newest || []);
const quotationTotal = computed(() => data.value?.quotation_total || 0);
const customerTotal = computed(() => data.value?.customer_total || 0);
const projectTotal = computed(() => data.value?.project_total || 0);
const phasen = computed(() => data.value?.project_by_phase || []);
const auftraegeTotal = computed(() => data.value?.auftraege_total || 0);

const pilotHoch = computed(() =>
  (pilotRelevanz.value.find((r) => r.relevanz === "Hoch") || {}).n || 0);
const phasenMax = computed(() =>
  Math.max(1, ...phasen.value.map((p) => p.n || 0)));

// ---- KPI-Zeile (echte Zahlen) --------------------------------------
const kpis = computed(() => [
  { key: "pilot", label: __("Pilot hits"),
    value: pilotAvailable.value ? String(pilotTotal.value) : "—",
    hint: pilotAvailable.value
      ? (pilotHoch.value ? `${pilotHoch.value}× ${__("highly relevant")}` : __("Tender scout"))
      : __("Scout not installed"),
    tone: "info", clickable: pilotAvailable.value },
  { key: "projekte", label: __("Sales Projects"), value: String(projectTotal.value),
    hint: __("all projects"), tone: "neutral", clickable: true },
  { key: "auftraege", label: __("Orders"), value: String(auftraegeTotal.value),
    hint: __("Order status"), tone: auftraegeTotal.value > 0 ? "success" : "neutral",
    clickable: true },
  { key: "angebote", label: __("Quotations"), value: String(quotationTotal.value),
    hint: __("Quotation"), tone: "neutral", clickable: true },
  { key: "kunden", label: __("Customers"), value: String(customerTotal.value),
    hint: __("Customer"), tone: "neutral", clickable: true },
]);

// ---- Karten-Konfiguration ------------------------------------------
const cards = computed(() => [
  { id: "pilot", title: __("Pilot — Latest tenders"),
    meta: pilotAvailable.value ? `${pilotTotal.value} ${__("hits")}` : __("not available"),
    span: 7, action: pilotAvailable.value ? { label: __("Pilot Workbench →") } : null },
  { id: "phasen", title: __("Sales projects by phase"),
    meta: `${projectTotal.value} ${__("project(s)")}`, span: 5 },
  { id: "auftraege", title: __("Orders"), meta: __("Order status"), span: 5 },
  { id: "absprung", title: __("Shortcuts"), span: 7 },
]);

// Pilot-Tabelle (PpDataGrid).
const PILOT_COLS = [
  { key: "score", label: __("Score"), align: "right", width: 78 },
  { key: "titel", label: __("Tender"), minWidth: 200 },
  { key: "land", label: __("Country"), width: 120 },
  { key: "deadline_fmt", label: __("Deadline"), align: "right", width: 110 },
  { key: "status", label: __("Status"), width: 120 },
];
const pilotRows = computed(() => pilotNewest.value.map((t) => ({
  id: t.name,
  name: t.name,
  score: t.score != null ? Math.round(t.score) : null,
  titel: t.titel,
  land: t.land || "—",
  deadline_fmt: fmtDate(t.deadline),
  status: t.status,
  url: t.url,
})));

function fmtDate(val) {
  if (!val) return "—";
  const s = String(val).substring(0, 10);
  const [y, m, d] = s.split("-");
  return d ? `${d}.${m}.${y}` : s;
}

// ---- Navigation ----------------------------------------------------
function navigate(target) {
  if (!target || target === "#") return;
  if (/^https?:\/\//.test(target)) { window.open(target, "_blank", "noopener"); return; }
  if (window.frappe && window.frappe.set_route && target.startsWith("/app/")) {
    const parts = target.replace(/^\/app\//, "").split("/").filter(Boolean);
    window.frappe.set_route(...parts);
  } else {
    // /crm ist eine eigene SPA (kein Desk-Router) → harter Seitenwechsel.
    window.location.href = target;
  }
}
function goPilot() { navigate("/app/pilot-workbench"); }
function goAuftraege() {
  if (window.frappe && window.frappe.set_route) {
    window.frappe.set_route("List", "Project", { status: "Auftrag" });
  } else {
    window.location.href = "/app/project/view/list?status=Auftrag";
  }
}
function openTender(id) {
  const row = pilotRows.value.find((r) => r.id === id);
  if (!row) return;
  if (window.frappe && window.frappe.set_route) window.frappe.set_route("Form", "Pilot Tender", row.name);
  else if (row.url) window.open(row.url, "_blank", "noopener");
}
function onKpi(k) {
  if (k.key === "pilot") goPilot();
  else if (k.key === "projekte") navigate("/app/project");
  else if (k.key === "auftraege") goAuftraege();
  else if (k.key === "angebote") navigate("/app/quotation");
  else if (k.key === "kunden") navigate("/app/customer");
}
function onCardAction(c) {
  if (c.id === "pilot") goPilot();
}

// Absprung-Kacheln (reale Nav-Ziele aus der Vertriebs-SSOT).
const jumps = [
  { name: __("CRM (Network & Pipeline)"), desc: __("Leads, deals, contacts — Frappe CRM SPA"), target: "/crm" },
  { name: __("Pilot Workbench"), desc: __("Tender scout: rate hits & take them over"), target: "/app/pilot-workbench" },
  { name: __("Quotations"), desc: __("Quotation — binding customer offers"), target: "/app/quotation" },
  { name: __("Customers"), desc: __("Customer — customer master data"), target: "/app/customer" },
  { name: __("Requirement Spec"), desc: __("Requirement Spec — questionnaire filled in by the customer"), target: "/app/requirement-spec" },
  { name: __("Variants"), desc: __("Project Variant — technical & commercial variant comparison"), target: "/app/project-variant" },
];

async function load() {
  loading.value = true;
  errorMsg.value = "";
  try {
    let msg;
    if (window.frappe && window.frappe.call) {
      const r = await window.frappe.call({ method: "pilanda_sales.api.get_sales_dashboard" });
      msg = r && r.message;
    } else {
      const res = await fetch("/api/method/pilanda_sales.api.get_sales_dashboard", {
        headers: { Accept: "application/json" }, credentials: "same-origin",
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      msg = (await res.json()).message;
    }
    data.value = msg || {};
  } catch (e) {
    console.error("[sales-dashboard] load failed", e);
    errorMsg.value = (e && e.message) || __("Sales data could not be loaded.");
    data.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div v-if="errorMsg" class="svd-error">{{ errorMsg }}</div>
  <PpDashboard v-else-if="data" :eyebrow="__('Sales')" :title="__('Overview')"
               :kpis="kpis" :cards="cards"
               @kpi-click="onKpi" @card-action="onCardAction">
    <template #actions>
      <button class="svd-btn" @click="load" :disabled="loading" :title="__('Reload')">
        {{ loading ? __('Loading…') : __('Refresh') }}
      </button>
    </template>

    <!-- Pilot — neueste Ausschreibungen -->
    <template #card-pilot>
      <template v-if="pilotAvailable">
        <PpDataGrid v-if="pilotRows.length" :columns="PILOT_COLS" :rows="pilotRows" @row-click="openTender">
          <template #cell-score="{ value }">
            <span v-if="value != null" class="svd-score"
                  :class="value >= 75 ? 'is-high' : value >= 50 ? 'is-mid' : 'is-low'">{{ value }}</span>
            <span v-else>—</span>
          </template>
          <template #cell-status="{ value }">
            <span class="svd-pill">{{ value }}</span>
          </template>
        </PpDataGrid>
        <p v-else class="svd-empty">{{ __('No tenders imported yet.') }}</p>
      </template>
      <p v-else class="svd-empty svd-empty--wip">
        {{ __('The tender scout "Pilot" is not installed on this site — so there are no hits. (No placeholder/demo data.)') }}
      </p>
    </template>

    <!-- Vertriebsprojekte nach Phase -->
    <template #card-phasen>
      <ul v-if="phasen.length" class="svd-bars">
        <li v-for="p in phasen" :key="p.phase" class="svd-bars__row">
          <span class="svd-bars__label" :class="{ 'is-unset': p.unset }">{{ p.phase }}</span>
          <span class="svd-bars__track">
            <span class="svd-bars__fill" :class="{ 'is-unset': p.unset }"
                  :style="{ width: (p.n / phasenMax * 100) + '%' }"></span>
          </span>
          <span class="svd-bars__num">{{ p.n }}</span>
        </li>
      </ul>
      <p v-else class="svd-empty">{{ __('No sales projects.') }}</p>
    </template>

    <!-- Aufträge (gewonnene Projekte, Status Auftrag) -->
    <template #card-auftraege>
      <div class="svd-auf">
        <span class="svd-auf__num">{{ auftraegeTotal }}</span>
        <span class="svd-auf__cap">{{ __('project(s) with status "Order"') }}</span>
      </div>
      <button type="button" class="svd-link" @click="goAuftraege">{{ __('Open order list →') }}</button>
      <p class="svd-note">
        E3: {{ __('A won project') }} <strong>{{ __('is') }}</strong> {{ __('the order (not a separate object). Which field feeds the filter list in the future and the hidden sales-order automation are still open in the domain plan.') }}
      </p>
    </template>

    <!-- Absprünge (reale Nav-Ziele) -->
    <template #card-absprung>
      <div class="svd-jump">
        <button v-for="j in jumps" :key="j.name" type="button" class="svd-jump__tile"
                @click="navigate(j.target)">
          <span class="svd-jump__name">{{ j.name }}</span>
          <span class="svd-jump__desc">{{ j.desc }}</span>
        </button>
      </div>
    </template>
  </PpDashboard>
  <div v-else class="svd-empty svd-loading">{{ __('Loading …') }}</div>
</template>

<style scoped>
/* Nur --pp-*-Tokens; alles unter svd-* gescoped. hell + dunkel via Tokens. */
.svd-error {
  padding: var(--pp-space-3, 12px); margin: var(--pp-space-4, 16px);
  color: var(--pp-state-danger);
  background: color-mix(in oklab, var(--pp-state-danger) 12%, var(--pp-bg-surface));
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  font-size: var(--pp-fs-14, 14px);
}
.svd-empty { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.svd-empty--wip { color: var(--pp-text-tertiary); font-style: italic; line-height: 1.5; }
.svd-loading { padding: var(--pp-space-6, 24px); }
.svd-btn {
  padding: 6px 12px; font-size: var(--pp-fs-12, 12px); font-weight: 600;
  color: var(--pp-brand-primary); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); cursor: pointer;
}
.svd-btn:hover:not(:disabled) { border-color: var(--pp-brand-primary); }

/* Pilot-Score + Status-Pille */
.svd-score { font-weight: 700; font-variant-numeric: tabular-nums; }
.svd-score.is-high { color: var(--pp-state-success); }
.svd-score.is-mid { color: var(--pp-state-warning); }
.svd-score.is-low { color: var(--pp-text-tertiary); }
.svd-pill {
  display: inline-block; font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-medium, 500);
  padding: 1px 8px; border-radius: var(--pp-radius-full, 999px);
  background: var(--pp-bg-sunken); color: var(--pp-text-secondary);
  border: 1px solid var(--pp-border-subtle);
}

/* Phasen-Balken */
.svd-bars { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--pp-space-2, 8px); }
.svd-bars__row { display: grid; grid-template-columns: 130px 1fr auto; gap: var(--pp-space-2, 8px);
  align-items: center; font-size: var(--pp-fs-13, 13px); }
.svd-bars__label { color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.svd-bars__label.is-unset { color: var(--pp-text-tertiary); font-style: italic; }
.svd-bars__track { height: 8px; background: var(--pp-bg-sunken); border-radius: var(--pp-radius-full, 999px); overflow: hidden; }
.svd-bars__fill { display: block; height: 100%; background: var(--pp-brand-primary); border-radius: var(--pp-radius-full, 999px); min-width: 2px; }
.svd-bars__fill.is-unset { background: var(--pp-text-disabled, var(--pp-text-tertiary)); }
.svd-bars__num { font-variant-numeric: tabular-nums; color: var(--pp-text-secondary); font-weight: var(--pp-weight-semibold, 600); }

/* Aufträge */
.svd-auf { display: flex; align-items: baseline; gap: var(--pp-space-2, 8px); }
.svd-auf__num { font-size: var(--pp-fs-32, 32px); font-weight: var(--pp-weight-semibold, 600);
  color: var(--pp-text-primary); line-height: 1; font-variant-numeric: tabular-nums; }
.svd-auf__cap { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.svd-link { appearance: none; border: 0; background: none; cursor: pointer; padding: 0;
  align-self: flex-start; font: inherit; font-size: var(--pp-fs-13, 13px);
  font-weight: var(--pp-weight-semibold, 600); color: var(--pp-text-link, var(--pp-brand-primary)); }
.svd-link:hover { text-decoration: underline; }
.svd-note { margin: var(--pp-space-1, 4px) 0 0; font-size: var(--pp-fs-12, 12px);
  color: var(--pp-text-tertiary); line-height: 1.45; }
.svd-note strong { color: var(--pp-text-secondary); font-weight: var(--pp-weight-semibold, 600); }

/* Absprung-Kacheln */
.svd-jump { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-2, 8px); }
@media (max-width: 640px) { .svd-jump { grid-template-columns: 1fr; } }
.svd-jump__tile { appearance: none; cursor: pointer; text-align: left; display: flex;
  flex-direction: column; gap: 2px; padding: var(--pp-space-3, 12px);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); font: inherit; }
.svd-jump__tile:hover { border-color: var(--pp-brand-primary); }
.svd-jump__name { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold, 600); color: var(--pp-brand-primary); }
.svd-jump__desc { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
</style>
