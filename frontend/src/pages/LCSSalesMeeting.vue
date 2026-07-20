<!--
  LCSSalesMeeting — Sales Meeting (V2, Showcase #7 „Sales Meeting").
  ============================================================
  Besprechungsfläche „Angebote in Bearbeitung": eine Zeile je offener
  Verkaufschance mit Forecast-Spalten (Wahrscheinlichkeit, Wert, gewichteter
  Wert) und verantwortlichem Vertriebler.

  Präsentation nach pilanda_theme-Showcase #7: PpPageHead + PpStatTile
  (gewichtete Pipeline) + PpDataGrid (Forecast-Spalten mit Summen-Fußzeile
  via agg) + PpEmptyState. Datenlogik unverändert produktiv:
    lcs_integrations.projects.api.get_sales_meeting_data
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Sales Meeting'), route: { name: 'LCS Sales Meeting' } }]" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-2">
          <Button :label="__('Insights')" iconLeft="bar-chart-2" @click="$router.push({ name: 'LCS Forecasting' })" />
          <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="board.reload()" :loading="board.loading" />
        </div>
      </template>
    </LayoutHeader>

    <div class="crmm">
      <div class="crmm-inner">
        <PpPageHead
          :eyebrow="__('Sales / CRM')"
          :title="__('Sales Meeting')"
          :subtitle="`${__('Offers in progress')} · ${filteredRows.length} ${__('of')} ${rows.length} ${__('opportunities')} · ${money(kpiWeighted)} ${__('weighted pipeline')}`"
        />

        <!-- KPI-Zeile — reaktiv aus dem (gefilterten) Meeting-Stand -->
        <section class="crmm-kpis">
          <PpStatTile v-for="k in kpis" :key="k.label" v-bind="k" />
        </section>

        <!-- Filter: verantwortlicher Vertriebler + Suche -->
        <section class="crmm-filter">
          <div class="crmm-field crmm-field--grow">
            <label class="crmm-field-cap">{{ __('Search') }}</label>
            <div class="crmm-search">
              <FeatherIcon name="search" class="crmm-search-ico" />
              <input v-model="search" type="search" class="crmm-input crmm-input--search" :placeholder="__('Opportunity, number, country, note …')" />
            </div>
          </div>
          <div class="crmm-field">
            <label class="crmm-field-cap">{{ __('Responsible') }}</label>
            <select v-model="person" class="crmm-input">
              <option value="">{{ __('All salespeople') }}</option>
              <option v-for="v in vertriebler" :key="v" :value="v">{{ shortUser(v) }}</option>
            </select>
          </div>
          <span class="crmm-count">{{ filteredRows.length }} von {{ rows.length }}</span>
        </section>

        <!-- Wichtig markiert (entitätsübergreifend, echte Sternflags) -->
        <section v-if="important.length" class="crmm-important">
          <div class="crmm-important-head">
            <FeatherIcon name="star" class="crmm-important-star" /> {{ __('Flagged important') }}
          </div>
          <div class="crmm-important-list">
            <button
              v-for="it in important"
              :key="it.entity + it.name"
              type="button"
              class="crmm-important-row"
              @click="openItem(it)"
            >
              <span class="crmm-ent" :data-ent="it.entity">{{ entityLabel(it.entity) }}</span>
              <span class="crmm-important-main">
                <span class="crmm-important-title">{{ it.label }}</span>
                <span class="crmm-important-sub">{{ it.sub }}<template v-if="it.person"> · {{ shortUser(it.person) }}</template></span>
              </span>
              <span v-if="it.status" class="crmm-pill" data-tone="info"><i class="crmm-dot" />{{ it.status }}</span>
              <span v-if="it.value" class="crmm-important-val">{{ money(it.value) }}</span>
            </button>
          </div>
        </section>

        <!-- Meeting-Tabelle: Forecast-Spalten + Summen-Fußzeile -->
        <section class="crmm-card">
          <PpDataGrid v-if="filteredRows.length" :columns="columns" :rows="gridRows" @row-click="openProject">
            <template #cell-chance="{ row }">
              <span class="crmm-title">
                <FeatherIcon v-if="row.is_important" name="star" class="crmm-title-star" />{{ row.chance }}
              </span>
              <span class="crmm-id">{{ row.project_number }}<template v-if="row.sub"> · {{ row.sub }}</template></span>
            </template>
            <template #cell-vertrieb="{ value }">
              <span :class="{ 'crmm-muted': !value }">{{ value ? shortUser(value) : __('unassigned') }}</span>
            </template>
            <template #cell-phase="{ value }">
              <span class="crmm-pill" :data-tone="phaseTone(value)"><i class="crmm-dot" />{{ phaseLabel(value) }}</span>
            </template>
            <template #cell-wahrsch="{ value }">
              <span :class="chanceClass(value)">{{ Math.round(value) }} %</span>
            </template>
            <template #cell-beschluss="{ row }">
              <span class="crmm-beschluss">{{ row.beschluss || '—' }}</span>
            </template>
            <template #cell-due="{ value, row }">
              <span :class="dueClass(row.due_raw)">{{ value || '—' }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconInbox"
            :title="board.loading ? __('Loading opportunities …') : __('No open opportunities')"
            :hint="board.loading ? '' : (person || search ? __('No matches for the current filter/search.') : __('Once offers are in progress, they appear here.'))"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconInbox from '~icons/lucide/inbox'

const router = useRouter()
const board = createResource({
  url: 'lcs_integrations.projects.api.get_sales_meeting_data',
  auto: true,
})
const rows = computed(() => board.data?.rows || [])
const important = computed(() => board.data?.important || [])

// Phase → deutsche Bezeichnung + Ton (Funnel-Reihenfolge der LCS-Phasen).
const PHASE = {
  Qualified:   { label: __('Qualified'),   tone: 'info' },
  Budget:      { label: __('Budget'),      tone: 'info' },
  Richtpreis:  { label: __('Richtpreis'),  tone: 'brand' },
  Offer:       { label: __('Offer'),       tone: 'brand' },
  Negotiation: { label: __('Negotiation'), tone: 'warning' },
  Won:         { label: __('Won'),         tone: 'success' },
  Execution:   { label: __('Execution'),   tone: 'success' },
  Completed:   { label: __('Completed'),   tone: 'success' },
}
function phaseLabel(p) { return PHASE[p]?.label || p || '—' }
function phaseTone(p) { return PHASE[p]?.tone || 'info' }

// Filter (verantwortlicher Vertriebler + Freitext) — echt, clientseitig.
const search = ref('')
const person = ref('')
const vertriebler = computed(() => [...new Set(rows.value.map((r) => r.salesperson).filter(Boolean))])

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (person.value && r.salesperson !== person.value) return false
    if (!q) return true
    return [r.project_name, r.project_number, r.country, r.comment, r.next_action, r.salesperson]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
})

// Tabellen-Zeilen: Wert + gewichteter Wert in k€ (saubere Summen-Fußzeile).
const gridRows = computed(() => filteredRows.value.map((r) => {
  const prob = Number(r.probability) || 0
  const val = Number(r.value) || 0
  return {
    id: r.name,
    chance: r.project_name,
    project_number: r.project_number,
    sub: [r.type, r.country].filter(Boolean).join(' · '),
    vertrieb: r.salesperson,
    phase: r.phase,
    wahrsch: prob,
    wertk: Math.round(val / 1000),
    gewichtetk: Math.round((val * prob / 100) / 1000),
    beschluss: stripEmoji(r.comment) || r.next_action,
    due: r.kw || (r.due ? formatDue(r.due) : ''),
    due_raw: r.due,
    is_important: r.is_important,
  }
}))

const columns = [
  { key: 'chance',     label: __('Opportunity'), pin: true, width: 240 },
  { key: 'vertrieb',   label: __('Sales'), width: 130 },
  { key: 'phase',      label: __('Phase'), width: 150 },
  { key: 'wahrsch',    label: __('P(win)'), align: 'right', width: 90 },
  { key: 'wertk',      label: __('Value (k€)'), align: 'right', width: 120, agg: 'sum' },
  { key: 'gewichtetk', label: __('Weighted (k€)'), align: 'right', width: 150, agg: 'sum' },
  { key: 'beschluss',  label: __('Decision / note'), width: 280 },
  { key: 'due',        label: __('Due'), width: 110 },
]

// KPIs reaktiv aus den gefilterten Zeilen (immer konsistent mit der Tabelle).
const kpiTotal = computed(() => filteredRows.value.reduce((a, r) => a + (Number(r.value) || 0), 0))
const kpiWeighted = computed(() => filteredRows.value.reduce((a, r) => a + (Number(r.value) || 0) * (Number(r.probability) || 0) / 100, 0))
const kpiAvgProb = computed(() => filteredRows.value.length
  ? Math.round(filteredRows.value.reduce((a, r) => a + (Number(r.probability) || 0), 0) / filteredRows.value.length) : 0)
const kpiDueSoon = computed(() => filteredRows.value.filter((r) => {
  if (!r.due) return false
  const days = (new Date(String(r.due).replace(' ', 'T')).getTime() - Date.now()) / 86400000
  return days <= 7
}).length)

const kpis = computed(() => [
  { label: __('Pipeline (weighted)'), value: money(kpiWeighted.value), hint: __('Σ value × P(win)') },
  { label: __('Open opportunities'),  value: String(filteredRows.value.length), hint: money(kpiTotal.value) + ' ' + __('volume') },
  { label: __('Ø win probability'),   value: kpiAvgProb.value + ' %', hint: __('across open phases') },
  { label: __('Actions due (7 d)'),   value: String(kpiDueSoon.value), hint: __('in the next 7 days'), ...(kpiDueSoon.value ? { delta: __('open'), dir: 'up' } : {}) },
])

// Entitäts-übergreifende „Wichtig"-Sprünge (echte Sternflags).
const ENTITY = {
  project: { label: __('Project'), route: 'LCS Project', param: 'id' },
  lead:    { label: __('Lead'),    route: 'Lead',        param: 'leadId' },
  deal:    { label: __('Offer'),   route: 'Deal',        param: 'dealId' },
}
function entityLabel(e) { return ENTITY[e]?.label || e }
function openItem(it) {
  const cfg = ENTITY[it.entity]
  if (cfg) router.push({ name: cfg.route, params: { [cfg.param]: it.name } })
}
function openProject(id) {
  router.push({ name: 'LCS Project', params: { id } })
}

// --- Formathelfer -----------------------------------------------------------
function money(v) {
  const n = Number(v) || 0
  if (n >= 1_000_000) return '€' + (n / 1_000_000).toFixed(1) + ' Mio'
  if (n >= 1_000) return '€' + Math.round(n / 1_000) + 'k'
  return '€' + Math.round(n)
}
function shortUser(u) { return (u || '').split('@')[0] }
function stripEmoji(s) { return (s || '').replace(/📝|📋|🎤|🤖|\*\*/g, '').trim() }
function formatDue(due) {
  try {
    return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit' }).format(new Date(String(due).replace(' ', 'T')))
  } catch { return String(due) }
}
function chanceClass(p) {
  if (p >= 70) return 'crmm-chance crmm-chance--high'
  if (p >= 40) return 'crmm-chance crmm-chance--mid'
  return 'crmm-chance crmm-chance--low'
}
function dueClass(due) {
  if (!due) return 'crmm-due'
  const days = (new Date(String(due).replace(' ', 'T')).getTime() - Date.now()) / 86400000
  if (days < 0) return 'crmm-due crmm-due--over'
  if (days <= 7) return 'crmm-due crmm-due--soon'
  return 'crmm-due'
}
</script>

<style scoped>
.crmm { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.crmm-inner { max-width: 1560px; margin: 0 auto; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crmm-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

.crmm-filter { display: flex; align-items: flex-end; gap: var(--pp-space-3); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmm-field { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.crmm-field--grow { flex: 1 1 220px; }
.crmm-field-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmm-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 6px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); min-width: 160px; }
.crmm-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crmm-search { position: relative; display: flex; align-items: center; }
.crmm-search-ico { position: absolute; left: 9px; width: 15px; height: 15px; color: var(--pp-text-tertiary); pointer-events: none; }
.crmm-input--search { width: 100%; padding-left: 30px; }
.crmm-count { margin-left: auto; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }

.crmm-important { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); overflow: hidden; }
.crmm-important-head { display: flex; align-items: center; gap: 6px; padding: var(--pp-space-2) var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle); background: color-mix(in oklab, var(--pp-state-warning) 8%, transparent);
  font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-state-warning); }
.crmm-important-star { width: 14px; height: 14px; }
.crmm-important-list { display: flex; flex-direction: column; }
.crmm-important-row { appearance: none; cursor: pointer; text-align: left; font-family: inherit;
  display: flex; align-items: center; gap: var(--pp-space-3); padding: var(--pp-space-2) var(--pp-space-4);
  border: 0; border-top: 1px solid var(--pp-border-subtle); background: transparent; }
.crmm-important-row:first-child { border-top: 0; }
.crmm-important-row:hover { background: var(--pp-bg-hover); }
.crmm-important-main { min-width: 0; flex: 1; display: flex; flex-direction: column; }
.crmm-important-title { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmm-important-sub { font-size: 11px; color: var(--pp-text-tertiary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmm-important-val { flex-shrink: 0; font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium);
  color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; }
.crmm-ent { flex-shrink: 0; font-size: 10px; font-weight: var(--pp-weight-bold); text-transform: uppercase;
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-ui); }
.crmm-ent[data-ent="project"] { background: color-mix(in oklab, var(--pp-state-success) 14%, transparent); color: var(--pp-state-success); }
.crmm-ent[data-ent="lead"]    { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmm-ent[data-ent="deal"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }

.crmm-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-2); }

.crmm-title { display: flex; align-items: center; gap: 5px; font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crmm-title-star { width: 13px; height: 13px; color: var(--pp-state-warning); flex-shrink: 0; }
.crmm-id { display: block; font-size: 11px; color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.crmm-muted { color: var(--pp-text-tertiary); font-style: italic; }
.crmm-beschluss { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crmm-chance { font-variant-numeric: tabular-nums; }
.crmm-chance--high { color: var(--pp-state-success); font-weight: var(--pp-weight-semibold); }
.crmm-chance--mid  { color: var(--pp-state-warning); }
.crmm-chance--low  { color: var(--pp-text-tertiary); }
.crmm-due { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-secondary); white-space: nowrap; }
.crmm-due--soon { color: var(--pp-state-warning); font-weight: var(--pp-weight-medium); }
.crmm-due--over { color: var(--pp-state-danger); font-weight: var(--pp-weight-medium); }

.crmm-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; }
.crmm-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.crmm-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }
.crmm-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.crmm-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmm-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }

@media (max-width: 1080px) {
  .crmm-kpis { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .crmm-inner { padding: var(--pp-space-4) var(--pp-space-4) var(--pp-space-10); }
  .crmm-kpis { grid-template-columns: 1fr; }
  .crmm-field--grow { flex-basis: 100%; }
  .crmm-count { margin-left: 0; }
}
</style>
