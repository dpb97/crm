<!--
  LCSCRMDashboard — Vertriebs-Landing-Dashboard nach dem Klickdummy-Design.
  ============================================================================
  Sechs KPI-Karten (Pilot · Chancen · Leads · Projekte · gewichtete Pipeline ·
  Keine Chance/Verloren) über frei anordbaren Inhalts-Widgets. „ANORDNUNG"
  schaltet zwischen Automatisch (feste Reihenfolge) und Manuell (per Drag & Drop
  umsortierbar, pro Nutzer im Browser gespeichert).

  Datenquellen (alle real, keine Demo-Zahlen):
    · KPIs + Pipeline-nach-Phase + Projekte-nach-Typ → get_sales_dashboard
    · Pilot · neueste Treffer                        → pilot.api.workbench
    · Aktivitäten (heute)                            → get_notes
    · Meine Märkte                                   → get_market_assignment
-->
<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: __('CRM Dashboard'), route: { name: 'Dashboard' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="dash.loading" @click="reloadAll" />
      </template>
    </LayoutHeader>

    <div class="sd">
      <!-- KPI-Zeile -->
      <section class="sd-kpis">
        <div
          v-for="k in kpiCards"
          :key="k.key"
          class="sd-kpi"
          :class="[`is-${k.tone}`, { 'is-link': k.route || k.href }]"
          :role="k.route || k.href ? 'button' : undefined"
          :tabindex="k.route || k.href ? 0 : undefined"
          @click="onKpi(k)"
          @keydown.enter="onKpi(k)"
        >
          <span class="sd-kpi-cap">{{ k.label }}</span>
          <span class="sd-kpi-val">{{ k.value }}</span>
          <span class="sd-kpi-link">{{ k.hint }}<template v-if="k.route || k.href"> →</template></span>
        </div>
      </section>

      <!-- ANORDNUNG -->
      <div class="sd-arrange">
        <span class="sd-arrange-cap">{{ __('Arrangement') }}</span>
        <div class="sd-seg">
          <button
            v-for="m in ARRANGE_MODES"
            :key="m.key"
            type="button"
            class="sd-seg-btn"
            :class="{ 'is-active': arrange === m.key }"
            @click="arrange = m.key"
          >{{ m.label }}</button>
        </div>
      </div>

      <!-- Widget-Raster (im Manuell-Modus per Drag & Drop sortierbar) -->
      <section class="sd-grid" :class="{ 'is-manual': isManual }">
        <article
          v-for="id in widgetOrder"
          :key="id"
          class="sd-card"
          :class="[widgetMeta[id].wide ? 'sd-card--wide' : '', { 'is-drag': dragId === id }]"
          :draggable="isManual"
          @dragstart="onDragStart(id)"
          @dragover.prevent
          @drop="onDrop(id)"
          @dragend="dragId = null"
        >
          <header class="sd-card-head">
            <FeatherIcon v-if="isManual" name="move" class="sd-card-grip" />
            <h3 class="sd-card-title">{{ widgetMeta[id].title }}</h3>
            <span class="sd-card-sub">{{ widgetMeta[id].sub }}</span>
          </header>

          <!-- Pipeline nach Phase -->
          <div v-if="id === 'pipeline'" class="sd-bars">
            <div v-for="b in pipelineBars" :key="b.label" class="sd-bar-row">
              <span class="sd-bar-label">{{ b.label }}</span>
              <span class="sd-bar-track"><i :style="{ width: b.pct + '%', background: b.color }" /></span>
              <span class="sd-bar-val">{{ b.money }}</span>
            </div>
            <p v-if="!pipelineBars.length" class="sd-empty">{{ __('No data yet.') }}</p>
          </div>

          <!-- Projekte nach Typ (Donut) -->
          <div v-else-if="id === 'types'" class="sd-donut-wrap">
            <svg v-if="typeTotal" class="sd-donut" viewBox="0 0 42 42">
              <circle class="sd-donut-hole" cx="21" cy="21" r="15.915" />
              <circle
                v-for="seg in donutSegments"
                :key="seg.label"
                class="sd-donut-seg"
                cx="21" cy="21" r="15.915"
                :stroke="seg.color"
                :stroke-dasharray="`${seg.pct} ${100 - seg.pct}`"
                :stroke-dashoffset="seg.offset"
              />
            </svg>
            <ul class="sd-legend">
              <li v-for="seg in donutSegments" :key="seg.label">
                <span class="sd-legend-dot" :style="{ background: seg.color }" />
                {{ seg.label }} <b>— {{ seg.count }}</b>
              </li>
              <li v-if="!typeTotal" class="sd-empty">{{ __('No data yet.') }}</li>
            </ul>
          </div>

          <!-- Pilot · neueste Treffer -->
          <ul v-else-if="id === 'pilot'" class="sd-list">
            <li v-for="t in pilotHits" :key="t.name" class="sd-pilot">
              <a class="sd-pilot-title" href="/app/pilot-workbench">{{ t.titel || t.title }}</a>
              <span class="sd-pilot-meta">
                <span v-if="t.land">{{ t.land }}</span>
                <span v-if="t.score" class="sd-chip">{{ __('Score') }} {{ Math.round(t.score) }}</span>
              </span>
            </li>
            <li v-if="!pilotHits.length" class="sd-empty">{{ __('No hits yet.') }}</li>
          </ul>

          <!-- Aktivitäten -->
          <ul v-else-if="id === 'activities'" class="sd-acts">
            <li v-for="a in activities" :key="a.id" class="sd-act">
              <span class="sd-avatar">{{ a.initials }}</span>
              <span class="sd-act-body">
                <span class="sd-act-title">{{ a.title }}</span>
                <span class="sd-act-meta">{{ a.author }} · {{ a.when }}</span>
              </span>
            </li>
            <li v-if="!activities.length" class="sd-empty">{{ __('No activities today.') }}</li>
          </ul>

          <!-- Meine Märkte -->
          <div v-else-if="id === 'markets'" class="sd-market-wrap">
            <table class="sd-market">
              <thead>
                <tr>
                  <th>{{ __('Territory') }}</th><th>{{ __('Region') }}</th>
                  <th>{{ __('Responsible') }}</th><th class="ta-r">{{ __('Projects') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in markets" :key="m.territory">
                  <td class="sd-market-name">{{ m.territory }}</td>
                  <td>{{ m.region || '—' }}</td>
                  <td>{{ m.user_name || m.code || '—' }}</td>
                  <td class="ta-r">{{ m.projects || 0 }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="!markets.length" class="sd-empty">{{ __('No territories found.') }}</p>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button, FeatherIcon } from 'frappe-ui'
import { useProfileSetting } from '@/composables/useProfileSetting'
import { sessionStore } from '@/stores/session'
import LayoutHeader from '@/components/LayoutHeader.vue'

const router = useRouter()
const session = sessionStore()
const currentUser = computed(() => session.user)

// KPI card navigation — external href (Desk) or an SPA route.
function onKpi(k) {
  if (k.href) window.location.href = k.href
  else if (k.route) router.push({ name: k.route })
}

// --- Datenquellen (alle real) ----------------------------------------------
const dash = createResource({ url: 'lcs_integrations.projects.api.get_sales_dashboard', auto: true })
const pilot = createResource({ url: 'pilot.api.workbench', auto: true })
const notes = createResource({ url: 'lcs_integrations.projects.api.get_notes', auto: true })
const market = createResource({ url: 'lcs_integrations.projects.api.get_market_assignment', auto: true })
function reloadAll() { dash.reload(); pilot.reload(); notes.reload(); market.reload() }

const kpis = computed(() => dash.data?.kpis || {})

function moneyShort(v) {
  const n = Number(v) || 0
  if (!n) return '0 €'
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' M€'
  if (Math.abs(n) >= 1_000) return Math.round(n / 1_000).toLocaleString('de-DE') + ' k€'
  return Math.round(n).toLocaleString('de-DE') + ' €'
}

// --- KPI-Karten -------------------------------------------------------------
const kpiCards = computed(() => [
  { key: 'pilot', tone: 'brand', label: __('Pilot hits'), value: String(kpis.value.pilot_hits ?? 0), hint: __('Rate in Pilot'), href: '/app/pilot-workbench' },
  { key: 'chances', tone: 'brand', label: __('Open chances'), value: String(kpis.value.chances_open ?? 0), hint: __('Open chances list'), route: 'LCS Chances' },
  { key: 'leads', tone: 'brand', label: __('Leads active'), value: String(kpis.value.leads_active ?? 0), hint: __('Open leads list'), route: 'Leads' },
  { key: 'projects', tone: 'brand', label: __('Sales projects'), value: String(kpis.value.projects_total ?? 0), hint: __('Open phase board'), route: 'LCS Projects' },
  { key: 'pipeline', tone: 'success', label: __('Weighted pipeline'), value: moneyShort(kpis.value.pipeline_weighted), hint: __('Open forecast'), route: 'LCS Projects' },
  { key: 'lost', tone: 'warning', label: __('No chance / Lost'), value: `${kpis.value.no_chance ?? 0} / ${kpis.value.lost ?? 0}`, hint: __('this quarter — reasons captured') },
])

// --- Widget-Metadaten + Reihenfolge (Automatisch ⇄ Manuell) ----------------
const widgetMeta = {
  pipeline: { title: __('Pipeline by phase (weighted, visible projects)'), sub: __('live from the phase board'), wide: false },
  types: { title: __('Visible projects by type'), sub: '', wide: false },
  pilot: { title: __('Pilot · latest hits'), sub: __("Salesperson's rating in Pilot"), wide: false },
  activities: { title: __('Activities'), sub: __('today'), wide: false },
  markets: { title: __('My markets'), sub: __('Territory assignment'), wide: true },
}
const ALL_WIDGETS = ['pipeline', 'types', 'pilot', 'activities', 'markets']
const ARRANGE_MODES = [
  { key: 'auto', label: __('Automatic') },
  { key: 'manual', label: __('Manual') },
]
const arrange = useProfileSetting('lcs_dashboard', 'arrange', 'auto')
const isManual = computed(() => arrange.value === 'manual')

// Persisted manual order (per browser/user); always reconciled with ALL_WIDGETS
// so a newly added widget shows up and a removed one drops out.
const savedOrder = useProfileSetting('lcs_dashboard', 'widget_order', [...ALL_WIDGETS])
const widgetOrder = computed(() => {
  if (!isManual.value) return ALL_WIDGETS
  const kept = savedOrder.value.filter((id) => ALL_WIDGETS.includes(id))
  return [...kept, ...ALL_WIDGETS.filter((id) => !kept.includes(id))]
})

const dragId = ref(null)
function onDragStart(id) { if (isManual.value) dragId.value = id }
function onDrop(targetId) {
  if (!isManual.value || !dragId.value || dragId.value === targetId) return
  const cur = [...widgetOrder.value]
  const from = cur.indexOf(dragId.value)
  const to = cur.indexOf(targetId)
  if (from < 0 || to < 0) return
  cur.splice(from, 1)
  cur.splice(to, 0, dragId.value)
  savedOrder.value = cur
  dragId.value = null
}

// --- Pipeline-Balken --------------------------------------------------------
const PIPE_COLORS = { Gewonnen: 'var(--pp-state-success)' }
const pipelineBars = computed(() => {
  const rows = (dash.data?.pipeline_by_phase || []).map((r) => ({ ...r, weighted: Math.max(0, r.weighted || 0) }))
  const max = Math.max(1, ...rows.map((r) => r.weighted))
  return rows.map((r) => ({
    label: r.label,
    money: moneyShort(r.weighted),
    pct: Math.round((r.weighted / max) * 100),
    color: PIPE_COLORS[r.label] || 'var(--pp-brand-primary)',
  }))
})

// --- Typ-Donut --------------------------------------------------------------
const DONUT_COLORS = ['var(--pp-brand-primary)', 'var(--pp-state-info)', 'var(--pp-accent-amber)', 'var(--pp-state-success)', 'var(--pp-state-danger)']
const typeTotal = computed(() => (dash.data?.projects_by_type || []).reduce((s, t) => s + (t.count || 0), 0))
const donutSegments = computed(() => {
  const items = dash.data?.projects_by_type || []
  const total = typeTotal.value || 1
  let acc = 0
  return items.map((t, i) => {
    const pct = (t.count / total) * 100
    // dashoffset: start at top (25) and walk backwards by the accumulated share
    const seg = { label: t.label, count: t.count, color: DONUT_COLORS[i % DONUT_COLORS.length], pct: +pct.toFixed(2), offset: +(25 - acc).toFixed(2) }
    acc += pct
    return seg
  })
})

// --- Pilot · neueste Treffer -----------------------------------------------
const pilotHits = computed(() => {
  const rows = Array.isArray(pilot.data?.tenders) ? pilot.data.tenders : []
  return [...rows].sort((a, b) => String(b.published_am || '').localeCompare(String(a.published_am || ''))).slice(0, 5)
})

// --- Aktivitäten (aus den Notizen) -----------------------------------------
function initials(name) {
  return String(name || '').trim().split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase() || '—'
}
function relTime(v) {
  if (!v) return '—'
  const d = new Date(String(v).replace(' ', 'T')).getTime()
  if (isNaN(d)) return String(v)
  const min = Math.floor((Date.now() - d) / 60000)
  if (min < 1) return 'vor wenigen Minuten'
  if (min < 60) return `vor ${min} Min.`
  const h = Math.floor(min / 60)
  if (h < 24) return `vor ${h} Std.`
  const days = Math.floor(h / 24)
  if (days === 1) return 'gestern'
  if (days < 7) return `vor ${days} Tagen`
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}
const activities = computed(() =>
  (notes.data?.rows || []).slice(0, 6).map((r) => ({
    id: r.id,
    title: r.title,
    author: r.author || '—',
    initials: initials(r.author),
    when: relTime(r.time),
  })),
)

// --- Meine Märkte -----------------------------------------------------------
const markets = computed(() => {
  const all = market.data?.territories || []
  const mine = all.filter((t) => t.user === currentUser.value || t.deputy_user === currentUser.value)
  return (mine.length ? mine : all).slice(0, 6)
})
</script>

<style scoped>
.sd { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base);
  padding: var(--pp-space-5) var(--pp-space-5) var(--pp-space-10);
  display: flex; flex-direction: column; gap: var(--pp-space-4); }

/* KPI-Zeile */
.sd-kpis { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: var(--pp-space-3); }
.sd-kpi { appearance: none; text-align: left; font-family: inherit; cursor: default;
  display: flex; flex-direction: column; gap: 6px; min-width: 0;
  padding: var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-top: 3px solid var(--pp-brand-primary);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); text-decoration: none; }
.sd-kpi.is-link { cursor: pointer; }
.sd-kpi.is-link:hover { border-color: var(--pp-brand-primary); }
.sd-kpi.is-success { border-top-color: var(--pp-state-success); }
.sd-kpi.is-warning { border-top-color: var(--pp-state-warning); }
.sd-kpi-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.sd-kpi-val { font-size: 28px; font-weight: var(--pp-weight-bold); color: var(--pp-text-primary);
  line-height: 1.1; font-variant-numeric: tabular-nums; }
.sd-kpi-link { font-size: 11px; color: var(--pp-text-tertiary); }
.sd-kpi.is-link:hover .sd-kpi-link { color: var(--pp-brand-primary); }

/* ANORDNUNG */
.sd-arrange { display: flex; align-items: center; justify-content: flex-end; gap: var(--pp-space-2); }
.sd-arrange-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.sd-seg { display: inline-flex; gap: 2px; padding: 2px; border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-subtle); }
.sd-seg-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12, 12px);
  padding: 4px 12px; border: none; border-radius: var(--pp-radius-ui); background: transparent; color: var(--pp-text-secondary); }
.sd-seg-btn:hover { color: var(--pp-brand-primary); }
.sd-seg-btn.is-active { background: var(--pp-brand-primary); color: var(--pp-text-on-accent); font-weight: var(--pp-weight-semibold); }

/* Widget-Raster */
.sd-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--pp-space-4); align-items: start; }
.sd-card { display: flex; flex-direction: column; gap: var(--pp-space-3);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.sd-card--wide { grid-column: 1 / -1; }
.sd-grid.is-manual .sd-card { cursor: grab; }
.sd-card.is-drag { opacity: 0.5; outline: 2px dashed var(--pp-brand-primary); }
.sd-card-head { display: flex; align-items: baseline; gap: var(--pp-space-2); flex-wrap: wrap; }
.sd-card-grip { width: 14px; height: 14px; color: var(--pp-text-tertiary); align-self: center; }
.sd-card-title { margin: 0; font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.sd-card-sub { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); margin-left: auto; }

/* Pipeline-Balken */
.sd-bars { display: flex; flex-direction: column; gap: var(--pp-space-3); }
.sd-bar-row { display: grid; grid-template-columns: 120px 1fr auto; align-items: center; gap: var(--pp-space-3); }
.sd-bar-label { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.sd-bar-track { height: 12px; border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); overflow: hidden; }
.sd-bar-track i { display: block; height: 100%; border-radius: var(--pp-radius-full); }
.sd-bar-val { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium); color: var(--pp-text-primary);
  font-variant-numeric: tabular-nums; }

/* Typ-Donut */
.sd-donut-wrap { display: flex; align-items: center; gap: var(--pp-space-5); }
.sd-donut { width: 140px; height: 140px; flex-shrink: 0; transform: rotate(0deg); }
.sd-donut-hole { fill: transparent; }
.sd-donut-seg { fill: transparent; stroke-width: 5; }
.sd-legend { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--pp-space-2); }
.sd-legend li { display: inline-flex; align-items: center; gap: 8px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.sd-legend-dot { width: 10px; height: 10px; border-radius: var(--pp-radius-full); flex-shrink: 0; }

/* Pilot-Liste */
.sd-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.sd-pilot { display: flex; flex-direction: column; gap: 3px; padding: var(--pp-space-2) 0;
  border-bottom: 1px solid var(--pp-border-subtle); }
.sd-pilot:last-child { border-bottom: 0; }
.sd-pilot-title { font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); text-decoration: none; }
.sd-pilot-title:hover { color: var(--pp-brand-primary); text-decoration: underline; }
.sd-pilot-meta { display: inline-flex; align-items: center; gap: var(--pp-space-2); font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.sd-chip { padding: 1px var(--pp-space-2); border-radius: var(--pp-radius-full); color: var(--pp-brand-primary);
  background: color-mix(in oklab, var(--pp-brand-primary) 12%, transparent); font-variant-numeric: tabular-nums; }

/* Aktivitäten */
.sd-acts { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.sd-act { display: flex; align-items: flex-start; gap: var(--pp-space-3); padding: var(--pp-space-3) 0;
  border-bottom: 1px solid var(--pp-border-subtle); }
.sd-act:last-child { border-bottom: 0; }
.sd-avatar { flex-shrink: 0; width: 30px; height: 30px; border-radius: var(--pp-radius-full);
  display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: var(--pp-weight-bold);
  color: var(--pp-brand-primary); background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); }
.sd-act-body { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.sd-act-title { font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.sd-act-meta { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }

/* Meine Märkte */
.sd-market-wrap { overflow-x: auto; }
.sd-market { width: 100%; border-collapse: collapse; }
.sd-market th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  font-weight: var(--pp-weight-semibold); color: var(--pp-text-tertiary); padding: 0 var(--pp-space-3) var(--pp-space-2); }
.sd-market td { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: var(--pp-space-2) var(--pp-space-3); border-top: 1px solid var(--pp-border-subtle); }
.sd-market-name { font-weight: var(--pp-weight-medium); }
.sd-market .ta-r { text-align: right; font-variant-numeric: tabular-nums; }

.sd-empty { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-tertiary); }

@media (max-width: 1200px) { .sd-kpis { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .sd-grid { grid-template-columns: 1fr; } .sd-card--wide { grid-column: auto; } }
@media (max-width: 640px) { .sd-kpis { grid-template-columns: repeat(2, 1fr); } }
</style>
