<!--
  LCSCRMDashboard — CRM-Dashboard in Pilanda-UX (CRM-Integration Teil 3/3).
  ============================================================================
  Ersetzt Dominiks Frappe-CRM-Dashboard-Oberfläche (/crm/dashboard) durch die
  PpDashboard-Komposition (Kopf → KPI-Zeile → 12-Spalten-Karten-Raster). Die
  DATENLOGIK bleibt zu 100 % Dominiks Backend — EINZIGE Quelle ist sein
  bestehender, whitelisted Endpunkt:

      crm.api.dashboard.get_dashboard(from_date, to_date, user)

  Er liefert die Dashboard-Items (Manager-Dashboard-Layout) je mit fertigem,
  SERVERSEITIG berechnetem und übersetztem Chart-Config in `item.data`:
    · type "number_chart" → KPI-Kachel  (Interessenten gesamt · Laufende
      Verkaufschancen · Gewonnene · Ø-Wert · Ø-Abschlusszeit)
    · type "axis_chart"   → Karte mit frappe-ui <AxisChart>  (Umsatztrend,
      Prognostizierter Umsatz, Funnel-Konversion …)
    · type "donut_chart"  → Karte mit frappe-ui <DonutChart> (Verkaufschancen
      je Phase …)
    · type "spacer"       → ignoriert
  Kein zweiter Endpoint, keine Schatten-/Demo-Daten. Zahlen werden für die
  KPI-Zeile über Intl in der User-Sprache formatiert (Einheit € für Geldwerte,
  Server-Suffix z. B. für Tage). KPI-/Chart-TITEL kommen bereits übersetzt aus
  dem Backend (dashboard.py _()) und werden direkt angezeigt.

  Zeitraum-Filter (Letzte 7/30/60/90 Tage) + Nutzer-Filter (nur Manager/Admin,
  wie Upstream) reichen die gleichen Parameter an get_dashboard weiter, sodass
  alle Zahlen konsistent zum gewählten Fenster stehen.

  Charts: die im Bestand etablierte frappe-ui-Chart-Lösung (AxisChart/
  DonutChart) — dieselbe, die Dominiks DashboardItem verwendet. Keine neue
  Chart-Bibliothek. Bausteine: PpDashboard@2 (Kopie in components/pp/).
  VOLLE Canvas-Breite (Marco: „ERP, kein zentrierter Blog" → maxWidth=0).
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('CRM Dashboard'), route: { name: 'Dashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="cd">
      <!-- Fehlerzustand ehrlich: sichtbare Meldung statt leerer Karten -->
      <div v-if="dashboard.error" class="cd-error" role="alert">
        <FeatherIcon name="alert-triangle" class="cd-error__ico" />
        <div>
          <strong>{{ __('The CRM dashboard could not be loaded.') }}</strong>
          <p class="cd-error__detail">{{ errorText }}</p>
          <button type="button" class="cd-error__retry" @click="dashboard.reload()">
            {{ __('Try again') }}
          </button>
        </div>
      </div>

      <PpDashboard
        v-else
        :eyebrow="__('Sales')"
        :title="__('CRM Dashboard')"
        :kpis="kpis"
        :cards="cards"
      >
        <!-- Kopf-Aktionen: Zeitraum-Filter + (nur Manager) Nutzer-Filter + Refresh -->
        <template #actions>
          <div class="cd-filters">
            <label class="cd-field">
              <span class="cd-field__cap">{{ __('Time range') }}</span>
              <select v-model.number="range" class="cd-input" @change="dashboard.reload()">
                <option v-for="o in rangeOptions" :key="o.days" :value="o.days">{{ o.label }}</option>
              </select>
            </label>

            <label v-if="canFilterUser" class="cd-field">
              <span class="cd-field__cap">{{ __('Sales User') }}</span>
              <select v-model="userFilter" class="cd-input" @change="dashboard.reload()">
                <option :value="null">{{ __('All salespeople') }}</option>
                <option v-for="u in crmUsers" :key="u.name" :value="u.name">
                  {{ getUser(u.name)?.full_name || u.name }}
                </option>
              </select>
            </label>

            <button
              type="button"
              class="cd-refresh"
              :disabled="dashboard.loading"
              :title="__('Refresh')"
              @click="dashboard.reload()"
            >
              <FeatherIcon name="refresh-cw" class="cd-refresh__ico" :class="{ 'is-spin': dashboard.loading }" />
              {{ dashboard.loading ? __('Loading …') : __('Refresh') }}
            </button>
          </div>
        </template>

        <!-- Charts: Dominiks Server-Config unverändert in die frappe-ui-Charts -->
        <template v-for="c in chartCards" :key="c.id" #[c.slot]>
          <div class="cd-chart">
            <AxisChart v-if="c.type === 'axis_chart'" :config="c.data" />
            <DonutChart v-else-if="c.type === 'donut_chart'" :config="c.data" />
            <FunnelChart v-else-if="c.type === 'funnel_chart'" :config="c.data" />
            <p v-else class="cd-empty">{{ __('No data for the selected period.') }}</p>
          </div>
        </template>
      </PpDashboard>

      <!-- Erstladung: dezenter Hinweis, solange noch keine Daten da sind -->
      <p v-if="dashboard.loading && !hasData && !dashboard.error" class="cd-loading">
        {{ __('Loading dashboard …') }}
      </p>
      <p v-else-if="hasData && !numberItems.length && !chartItems.length" class="cd-empty cd-empty--page">
        {{ __('No charts configured for this dashboard.') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource, usePageMeta, AxisChart, DonutChart, FunnelChart, Breadcrumbs, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpDashboard from '@/components/pp/PpDashboard.vue'
import { usersStore } from '@/stores/users'
import { getLastXDays } from '@/utils/dashboard'

const { users, getUser, isManager, isAdmin } = usersStore()
const canFilterUser = computed(() => isManager() || isAdmin())
const crmUsers = computed(() => users.data?.crmUsers || [])

// --- Filter (reichen die Parameter 1:1 an Dominiks get_dashboard weiter) -----
const range = ref(30)
const userFilter = ref(null)
const rangeOptions = [
  { days: 7, label: __('Last 7 Days') },
  { days: 30, label: __('Last 30 Days') },
  { days: 60, label: __('Last 60 Days') },
  { days: 90, label: __('Last 90 Days') },
]
const period = computed(() => getLastXDays(range.value)) // "YYYY-MM-DD,YYYY-MM-DD"
const fromDate = computed(() => period.value?.split(',')[0] || null)
const toDate = computed(() => period.value?.split(',')[1] || null)

// --- EINZIGE Datenquelle: Dominiks bestehender Dashboard-Endpunkt -----------
const dashboard = createResource({
  url: 'crm.api.dashboard.get_dashboard',
  makeParams() {
    return { from_date: fromDate.value, to_date: toDate.value, user: userFilter.value }
  },
  auto: true,
})

const items = computed(() => (Array.isArray(dashboard.data) ? dashboard.data : []))
const hasData = computed(() => dashboard.data != null)
const numberItems = computed(() => items.value.filter((i) => i?.type === 'number_chart' && i.data))

// frappe-ui-AxisChart nutzt series[].name gleichzeitig als Legenden-Label UND
// als Daten-Key (row[s.name]) — ein Label-Feld gibt es nicht. Für übersetzte
// Legenden müssen daher Serien-Name UND Row-Keys gemeinsam umgeschlüsselt
// werden (Fork bleibt unangetastet; Keys = Stand crm/api/dashboard.py).
const SERIES_LABELS = {
  leads: () => __('Leads'),
  deals: () => __('Deals'),
  won_deals: () => __('Won deals'),
  forecasted: () => __('Forecasted'),
  actual: () => __('Actual'),
  count: () => __('Count'),
  value: () => __('Value'),
}

function localizeAxisChart(cfg) {
  const names = (cfg?.series || []).map((s) => s?.name).filter((n) => SERIES_LABELS[n])
  if (!names.length) return cfg
  const rename = Object.fromEntries(names.map((n) => [n, SERIES_LABELS[n]()]))
  return {
    ...cfg,
    series: cfg.series.map((s) => (rename[s.name] ? { ...s, name: rename[s.name] } : s)),
    data: (cfg.data || []).map((row) => {
      const out = { ...row }
      for (const [key, label] of Object.entries(rename)) {
        if (key in out) {
          out[label] = out[key]
          delete out[key]
        }
      }
      return out
    }),
  }
}

const chartItems = computed(() =>
  items.value
    .filter((i) => ['axis_chart', 'donut_chart', 'funnel_chart'].includes(i?.type) && i.data)
    .map((i) => (i.type === 'axis_chart' ? { ...i, data: localizeAxisChart(i.data) } : i)),
)

const errorText = computed(() => {
  const e = dashboard.error
  if (!e) return ''
  return e.messages?.join(' ') || e.message || String(e)
})

// --- Locale/Formatierung -----------------------------------------------------
function currentLocale() {
  const lang =
    (typeof window !== 'undefined' && (window.frappe?.boot?.lang || window.boot?.lang)) || 'de'
  return String(lang).startsWith('de') ? 'de-DE' : lang
}
const locale = currentLocale()

function fmtNumber(n) {
  const num = Number(n) || 0
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: Number.isInteger(num) ? 0 : 1,
  }).format(num)
}
// Geldwert: number_chart mit gesetztem prefix (Währungssymbol) → Einheit €
// (LCS-Standardwährung EUR). Sonst Server-Suffix (z. B. Tage) anhängen.
function isMoney(cfg) {
  return !!(cfg.prefix && String(cfg.prefix).trim())
}
// Server-Suffixe kommen roh aus dashboard.py (kein _()); bekannte
// Einheiten hier übersetzen statt den Fork anzufassen.
function translateSuffix(raw) {
  const SUFFIX_LABELS = { days: __('days'), day: __('day') }
  const suffix = String(raw || '').trim()
  return SUFFIX_LABELS[suffix.toLowerCase()] || suffix
}
function kpiValue(cfg) {
  const num = fmtNumber(cfg.value)
  if (isMoney(cfg)) return `${num} €`
  const translated = translateSuffix(cfg.suffix)
  return translated ? `${num} ${translated}` : num
}
// Delta neutral als Hinweis (kein falsches Grün/Rot bei „weniger ist besser").
function kpiHint(cfg) {
  if (cfg.delta == null || cfg.delta === '') return cfg.tooltip || ''
  const d = Number(cfg.delta) || 0
  const arrow = d >= 0 ? '▲' : '▼'
  const suffix = translateSuffix(cfg.deltaSuffix)
  return `${arrow} ${cfg.deltaPrefix || ''}${fmtNumber(Math.abs(d))}${suffix ? ' ' + suffix : ''}`.trim()
}

function slugify(s) {
  return String(s || 'item').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'item'
}

// --- KPI-Zeile (number_charts, Reihenfolge = Server-Layout) ------------------
const kpis = computed(() =>
  numberItems.value.map((it, idx) => ({
    key: slugify(it.name) + '-' + idx,
    label: it.data.title, // serverseitig übersetzt
    value: kpiValue(it.data),
    hint: kpiHint(it.data),
    tone: 'neutral',
  })),
)

// --- Karten (axis_chart/donut_chart) ----------------------------------------
const chartCards = computed(() =>
  chartItems.value.map((it, idx) => {
    const id = slugify(it.name) + '-' + idx
    return { id, slot: 'card-' + id, type: it.type, data: it.data, title: it.data.title || it.name }
  }),
)
const cards = computed(() =>
  chartCards.value.map((c) => ({
    id: c.id,
    title: c.title,
    // Umsatzreihen (axis) breiter, Verteilungen (donut) schmaler
    span: c.type === 'axis_chart' ? 8 : 4,
  })),
)

usePageMeta(() => ({ title: __('CRM Dashboard') }))
</script>

<style scoped>
.cd { flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--pp-bg-base); }

/* Filterleiste im PpDashboard-Kopf (rechts, #actions) */
.cd-filters { display: inline-flex; align-items: flex-end; gap: var(--pp-space-3); flex-wrap: wrap; }
.cd-field { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.cd-field__cap {
  font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary);
}
.cd-input {
  appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 6px var(--pp-space-3); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-surface); min-width: 150px;
}
.cd-input:focus {
  outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15);
}
.cd-refresh {
  appearance: none; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  font: inherit; font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-semibold, 600);
  color: var(--pp-brand-primary); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  padding: 7px var(--pp-space-3);
}
.cd-refresh:hover:not(:disabled) { border-color: var(--pp-brand-primary); }
.cd-refresh:disabled { opacity: 0.6; cursor: default; }
.cd-refresh__ico { width: 14px; height: 14px; }
.cd-refresh__ico.is-spin { animation: cd-spin 0.9s linear infinite; }
@keyframes cd-spin { to { transform: rotate(360deg); } }

/* Chart-Bühne je Karte — feste Höhe, damit die frappe-ui-Charts Raum haben */
.cd-chart { height: clamp(240px, 32vh, 340px); width: 100%; min-width: 0; }
.cd-chart :deep(svg) { max-width: 100%; }

.cd-empty { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.cd-empty--page { padding: var(--pp-space-6); }
.cd-loading { padding: var(--pp-space-6); margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-tertiary); }

/* Fehlerbanner (ehrlich, sichtbar) */
.cd-error {
  display: flex; align-items: flex-start; gap: var(--pp-space-3);
  margin: var(--pp-space-6); padding: var(--pp-space-4);
  color: var(--pp-state-danger);
  background: color-mix(in oklab, var(--pp-state-danger) 10%, var(--pp-bg-surface));
  border: 1px solid color-mix(in oklab, var(--pp-state-danger) 30%, var(--pp-border-subtle));
  border-radius: var(--pp-radius-ui); font-size: var(--pp-fs-14, 14px);
}
.cd-error__ico { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; }
.cd-error__detail { margin: 4px 0 8px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.cd-error__retry {
  appearance: none; cursor: pointer; font: inherit; font-size: var(--pp-fs-12, 12px);
  font-weight: var(--pp-weight-semibold, 600); color: var(--pp-brand-primary);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); padding: 5px var(--pp-space-3);
}
.cd-error__retry:hover { border-color: var(--pp-brand-primary); }
</style>
