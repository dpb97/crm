<!--
  LCSMarketAssignment — Marktaufteilung + Projektkarte (V2, Showcase #8).
  ============================================================
  Wer ist für welches Territorium / Segment zuständig (Marktaufteilung R03)
  und wie viel Arbeit (Leads / Angebote / Projekte) trägt jeder Sales-Manager.

  Präsentation nach pilanda_theme-Showcase #8: PpPageHead + PpStatTile +
  PpDataGrid (Territorien + Segmente). Reine Tabellen-Übersicht — die
  Gebiets-KARTE lebt auf der Projektlandkarte (LCS Projects Map), damit die
  Marktaufteilung eine kompakte „wer ist wofür zuständig"-Sicht bleibt.
  Datenlogik unverändert produktiv:
    lcs_integrations.projects.api.get_market_assignment
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Market Assignment'), route: { name: 'LCS Market Assignment' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="board.reload()" :loading="board.loading" />
      </template>
    </LayoutHeader>

    <div class="crmt">
      <div class="crmt-inner">
        <PpPageHead
          :title="__('Market Assignment')"
          :subtitle="__('Territories and segments by sales manager · who is responsible for what')"
        />

        <section class="crmt-kpis">
          <PpStatTile v-for="k in kpis" :key="k.label" v-bind="k" />
        </section>

        <!-- Prioritäten-Verteilung (echt, aggregiert) -->
        <section class="crmt-prios" :aria-label="__('Priorities')">
          <span class="crmt-prios-cap">{{ __('Priority') }}</span>
          <span v-for="p in PRIORITIES" :key="p" class="crmt-prio-chip" :data-tone="PRIO_TONE[p]">
            <i class="crmt-legend-dot" :class="'is-' + PRIO_TONE[p]" />{{ prioLabel(p) }} · {{ (summary.priority && summary.priority[p]) || 0 }}
          </span>
        </section>

        <!-- Sales-Manager (Legende + Filter + Auslastung) -->
        <section class="crmt-section">
          <div class="crmt-section-head">
            <h3 class="crmt-section-title">{{ __('Responsibility by sales manager') }}</h3>
            <button v-if="manager || region || search" type="button" class="crmt-btn" @click="clearFilters">{{ __('Reset filters') }}</button>
          </div>
          <div class="crmt-mgrs">
            <button
              v-for="m in managers"
              :key="m.code"
              type="button"
              class="crmt-mgr-card"
              :class="{ 'is-active': manager === m.code }"
              @click="manager = manager === m.code ? '' : m.code"
            >
              <div class="crmt-mgr-top">
                <span class="crmt-mgr-badge" :class="'is-' + mgrKind(m.code)">{{ m.code }}</span>
                <div class="crmt-mgr-id">
                  <span class="crmt-mgr-name">{{ m.user_name || m.code }}</span>
                  <span class="crmt-mgr-sub">{{ m.territories }} {{ __('territories') }} · {{ m.countries }} {{ __('countries') }}</span>
                </div>
              </div>
              <div class="crmt-mgr-work">
                <span class="crmt-work-cell" data-kind="leads"><b>{{ m.leads }}</b>{{ __('Leads') }}</span>
                <span class="crmt-work-cell" data-kind="deals"><b>{{ m.deals }}</b>{{ __('Offers') }}</span>
                <span class="crmt-work-cell" data-kind="projects"><b>{{ m.projects }}</b>{{ __('Projects') }}</span>
              </div>
            </button>
          </div>
        </section>

        <!-- Hinweis: die Karte lebt auf der Projektlandkarte (Gebiete + Projekte). -->
        <p class="crmt-maplink">
          {{ __('The territory map lives on the') }}
          <a class="crmt-link" @click="$router.push({ name: 'LCS Projects Map' })">{{ __('Project Map') }}</a>.
        </p>

        <!-- Territorien -->
        <PpFilterBar v-model:search="search" :placeholder="__('Territory / country …')">
          <template #actions>
            <select v-model="region" class="crmt-input">
              <option value="">{{ __('All regions') }}</option>
              <option v-for="r in regionOptions" :key="r" :value="r">{{ r }}</option>
            </select>
          </template>
        </PpFilterBar>

        <PpTableCard
          :title="__('Territories')"
          :shown="filteredRows.length"
          :total="territories.length"
          :grow="false"
        >
            <PpDataGrid v-if="filteredRows.length" :columns="columns" :rows="gridRows">
              <template #cell-territory="{ row }">
                <span class="pp-cell-strong">{{ row.territory }}</span>
                <span v-if="row.sub_region" class="pp-cell-sub">{{ row.sub_region }}</span>
              </template>
              <template #cell-manager="{ row }">
                <div v-if="canManage" class="crmt-reassign" @click.stop>
                  <FormControl
                    type="select"
                    size="sm"
                    :options="managerOptions"
                    :modelValue="row.code"
                    @update:modelValue="(v) => reassign(row, v)"
                  />
                </div>
                <span v-else class="crmt-mgr">
                  <i class="crmt-legend-dot" :class="'is-' + mgrKind(row.code)" />{{ row.code || '—' }}
                  <span v-if="row.user_name" class="crmt-mgr-inline">· {{ row.user_name }}</span>
                </span>
              </template>
              <template #cell-priority="{ value }">
                <PpPill :tone="PRIO_TONE[value]">{{ prioLabel(value) }}</PpPill>
              </template>
              <template #cell-leads="{ value }"><span :class="{ 'crmt-zero': !value }">{{ value }}</span></template>
              <template #cell-deals="{ value }"><span :class="{ 'crmt-zero': !value }">{{ value }}</span></template>
              <template #cell-projects="{ value }"><span :class="value ? 'crmt-strong' : 'crmt-zero'">{{ value }}</span></template>
            </PpDataGrid>
            <PpEmptyState
              v-else
              :icon="IconMapPin"
              :title="board.loading ? __('Loading territories …') : __('No territories')"
              :hint="board.loading ? '' : __('No matches for the current filter/search.')"
            />
        </PpTableCard>

        <!-- Segment-Zuständigkeit -->
        <PpTableCard
          v-if="segments.length"
          :title="__('Segment Responsibility')"
          :shown="segRows.length"
          :total="segRows.length"
          :hint="''"
        >
          <PpDataGrid :columns="segColumns" :rows="segRows">
            <template #cell-lead_code="{ value }"><span class="crmt-mgr"><i class="crmt-legend-dot" :class="'is-' + mgrKind(value)" />{{ value || '—' }}</span></template>
            <template #cell-deputy_code="{ value }"><span :class="{ 'crmt-zero': !value }">{{ value || '—' }}</span></template>
          </PpDataGrid>
        </PpTableCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { createResource, call, toast, Breadcrumbs, Button, FormControl, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconMapPin from '~icons/lucide/map-pin'
import { usersStore } from '@/stores/users'

const { isManager } = usersStore()
const canManage = computed(() => isManager())

const board = createResource({
  url: 'lcs_integrations.projects.api.get_market_assignment',
  auto: true,
})

const summary = computed(() => board.data?.summary || { territories: 0, countries: 0, managers: 0, segments: 0, priority: {} })
const managers = computed(() => board.data?.managers || [])
const territories = computed(() => board.data?.territories || [])
const segments = computed(() => board.data?.segments || [])

const kpis = computed(() => [
  { label: __('Territories'),      value: String(summary.value.territories), hint: __('Market Assignment') },
  { label: __('Countries covered'), value: String(summary.value.countries), hint: __('assigned countries') },
  { label: __('Sales managers'),   value: String(summary.value.managers), hint: __('with responsibility') },
  { label: __('Segments'),         value: String(summary.value.segments), hint: __('responsibility matrix') },
])

// Sales-Manager ↔ Marker-/Legendenfarbe. Deterministisch aus der (nach
// Territorienzahl sortierten) Manager-Liste — echte Codes, feste Zuordnung.
const PALETTE = ['brand', 'info', 'success', 'warning', 'danger', 'neutral']
const mgrKindMap = computed(() => {
  const map = {}
  managers.value.forEach((m, i) => { if (m.code && m.code !== '—') map[m.code] = PALETTE[i % PALETTE.length] })
  return map
})
function mgrKind(code) { return mgrKindMap.value[code] || 'neutral' }

// Prioritäten (deutsche Labels lokal — Frappes de.po übersetzt „Go" falsch).
const PRIORITIES = ['Go', 'Watch', 'Maintain', 'Exit']
const PRIORITY_LABELS = { Go: __('Actively pursue'), Watch: __('Watch'), Maintain: __('Maintain'), Exit: __('Withdraw') }
const PRIO_TONE = { Go: 'success', Watch: 'info', Maintain: 'warning', Exit: 'neutral' }
function prioLabel(p) { return PRIORITY_LABELS[p] || p }

// Filter (Manager-Karte + Region + Suche) — echt, clientseitig.
const search = ref('')
const region = ref('')
const manager = ref('')
const regionOptions = computed(() => [...new Set(territories.value.map((t) => t.region).filter(Boolean))])
function clearFilters() { search.value = ''; region.value = ''; manager.value = '' }

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return territories.value.filter((t) => {
    if (region.value && t.region !== region.value) return false
    if (manager.value && t.code !== manager.value) return false
    if (!q) return true
    return [t.territory, t.sub_region, t.user_name, t.agent, t.code].some((v) => (v || '').toLowerCase().includes(q))
  })
})
const gridRows = computed(() => filteredRows.value.map((t) => ({ ...t, id: t.territory })))

// Territorien-Tabelle.
const columns = [
  { key: 'territory', label: __('Territory'), pin: true, width: 200 },
  { key: 'region',    label: __('Region'), width: 150 },
  { key: 'manager',   label: __('Sales manager'), width: canManage.value ? 190 : 200 },
  { key: 'priority',  label: __('Priority'), width: 150 },
  { key: 'country_count', label: __('Countries'), align: 'right', width: 90, agg: 'sum' },
  { key: 'segment_count', label: __('Segments'), align: 'right', width: 100 },
  { key: 'leads',     label: __('Leads'), align: 'right', width: 90, agg: 'sum' },
  { key: 'deals',     label: __('Offers'), align: 'right', width: 100, agg: 'sum' },
  { key: 'projects',  label: __('Projects'), align: 'right', width: 100, agg: 'sum' },
]
const segColumns = [
  { key: 'segment',     label: __('Segment'), pin: true, width: 260 },
  { key: 'lead_code',   label: __('Responsible'), width: 160 },
  { key: 'deputy_code', label: __('Deputy'), width: 160 },
]
const segRows = computed(() => segments.value.map((s, i) => ({ ...s, id: s.segment || ('seg-' + i) })))

// Inline-Umverteilung eines Territoriums (echt, nur Manager).
const managerOptions = computed(() => managers.value
  .filter((m) => m.code && m.code !== '—')
  .map((m) => ({ label: `${m.code} · ${m.user_name || m.code}`, value: m.code })))
async function reassign(row, code) {
  if (!code || code === row.code) return
  const m = managers.value.find((x) => x.code === code)
  const prev = { code: row.code, user: row.user, user_name: row.user_name }
  row.code = code
  row.user = m?.user || null
  row.user_name = m?.user_name || code
  try {
    await call('lcs_integrations.projects.api.reassign_territory', {
      territory: row.territory,
      sales_manager_code: code,
      sales_manager: m?.user || null,
    })
    toast.success(__('Territory reassigned to') + ' ' + code)
    board.reload()
  } catch (e) {
    Object.assign(row, prev)
    toast.error(e?.messages?.[0] || __('Territory could not be reassigned.'))
  }
}
</script>

<style scoped>
.crmt { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.crmt-inner { width: 100%; margin: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crmt-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12, 12px);
  padding: 5px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-secondary); }
.crmt-btn:hover { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); background: var(--pp-bg-hover); }

.crmt-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

.crmt-prios { display: flex; align-items: center; flex-wrap: wrap; gap: var(--pp-space-2) var(--pp-space-3); }
.crmt-prios-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }

.crmt-section { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crmt-section-head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3); flex-wrap: wrap; }
.crmt-section-title { margin: 0; font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crmt-hint { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }

.crmt-mgrs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }
.crmt-mgr-card { appearance: none; cursor: pointer; text-align: left; font-family: inherit;
  display: flex; flex-direction: column; gap: var(--pp-space-3);
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs);
  transition: border-color var(--pp-duration-fast, 120ms) ease; }
.crmt-mgr-card:hover { border-color: var(--pp-brand-primary); }
.crmt-mgr-card.is-active { border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crmt-mgr-top { display: flex; align-items: center; gap: var(--pp-space-2); min-width: 0; }
.crmt-mgr-badge { flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center;
  min-width: 34px; height: 26px; padding: 0 6px; border-radius: var(--pp-radius-ui);
  font-size: 11px; font-weight: var(--pp-weight-bold); color: var(--pp-text-on-accent); }
.crmt-mgr-badge.is-brand { background: var(--pp-brand-primary); }
.crmt-mgr-badge.is-info { background: var(--pp-state-info); }
.crmt-mgr-badge.is-success { background: var(--pp-state-success); }
.crmt-mgr-badge.is-warning { background: var(--pp-state-warning); }
.crmt-mgr-badge.is-danger { background: var(--pp-state-danger); }
.crmt-mgr-badge.is-neutral { background: var(--pp-text-tertiary); }
.crmt-mgr-id { min-width: 0; display: flex; flex-direction: column; }
.crmt-mgr-name { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmt-mgr-sub { font-size: 11px; color: var(--pp-text-tertiary); }
.crmt-mgr-work { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
.crmt-work-cell { display: flex; flex-direction: column; align-items: center; gap: 1px; padding: 4px 0;
  border-radius: var(--pp-radius-ui); font-size: 9px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--pp-text-tertiary); }
.crmt-work-cell b { font-size: var(--pp-fs-14, 14px); font-variant-numeric: tabular-nums; }
.crmt-work-cell[data-kind="leads"] { background: color-mix(in oklab, var(--pp-state-warning) 10%, transparent); }
.crmt-work-cell[data-kind="leads"] b { color: var(--pp-state-warning); }
.crmt-work-cell[data-kind="deals"] { background: color-mix(in oklab, var(--pp-state-info) 10%, transparent); }
.crmt-work-cell[data-kind="deals"] b { color: var(--pp-state-info); }
.crmt-work-cell[data-kind="projects"] { background: color-mix(in oklab, var(--pp-state-success) 10%, transparent); }
.crmt-work-cell[data-kind="projects"] b { color: var(--pp-state-success); }

.crmt-legend-dot { width: 9px; height: 9px; border-radius: var(--pp-radius-full); flex-shrink: 0; }
.crmt-legend-dot.is-brand { background: var(--pp-brand-primary); }
.crmt-legend-dot.is-info { background: var(--pp-state-info); }
.crmt-legend-dot.is-success { background: var(--pp-state-success); }
.crmt-legend-dot.is-warning { background: var(--pp-state-warning); }
.crmt-legend-dot.is-danger { background: var(--pp-state-danger); }
.crmt-legend-dot.is-neutral { background: var(--pp-text-tertiary); }

.crmt-active { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crmt-active strong { color: var(--pp-text-primary); font-weight: var(--pp-weight-semibold); }

.crmt-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 6px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.crmt-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crmt-input--search { padding-left: 30px; min-width: 180px; }

.crmt-maplink { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crmt-link { cursor: pointer; color: var(--pp-brand-primary); font-weight: var(--pp-weight-medium); }
.crmt-link:hover { text-decoration: underline; }

.crmt-mgr { display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.crmt-mgr-inline { color: var(--pp-text-secondary); }
.crmt-reassign { min-width: 9rem; }
.crmt-zero { color: var(--pp-text-tertiary); }
.crmt-strong { font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crmt-prio-chip { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; }
.crmt-prio-chip[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 14%, transparent); color: var(--pp-state-success); }
.crmt-prio-chip[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }
.crmt-prio-chip[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmt-prio-chip[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

@media (max-width: 1080px) {
  .crmt-kpis { grid-template-columns: repeat(2, 1fr); }
  .crmt-mgrs { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .crmt-inner { padding: var(--pp-space-4) var(--pp-space-4) var(--pp-space-10); }
  .crmt-kpis { grid-template-columns: 1fr; }
  .crmt-mgrs { grid-template-columns: 1fr; }
  .crmt-input--search { min-width: 0; width: 100%; }
  }
</style>
