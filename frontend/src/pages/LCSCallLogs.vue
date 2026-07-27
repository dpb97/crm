<!--
  LCSCallLogs — Calls-Seite (Vertrieb-Nav „Calls", klickdummy „Anrufe").
  ============================================================
  Anruf-Protokolle als Tabelle nach dem Klickdummy-Design: Filterleiste
  (Alle · ausgehend · eingehend + Suche), Karte „Anrufe" mit Kopf-Notiz
  (N von M · Zeile = Details im Inspektor) und die Spalten Datum · Person
  (+ Firma) · Richtung · Dauer · Ergebnis · Objekt. Einfachklick auf eine
  Zeile → angedockter Shell-Inspektor (Spec-Stil).

  „Ergebnis" = der Telefonie-Status (CRM Call Log hat keine Business-
  Disposition), deutsch übersetzt + farbige Pill. Echte Daten:
  lcs_integrations.projects.api.get_call_logs.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Calls'), route: { name: 'Call Logs' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
      </template>
    </LayoutHeader>

    <div class="crmc">
      <div class="crmc-inner">
        <!-- Filterleiste: Richtung-Segmente + Suche -->
        <section class="crmc-filter">
          <span class="crmc-filter-cap">{{ __('Filter') }}</span>
          <div class="crmc-seg" role="tablist">
            <button
              v-for="s in DIRS"
              :key="s.key"
              type="button"
              class="crmc-seg-btn"
              :class="{ 'is-active': dir === s.key }"
              :aria-pressed="dir === s.key"
              @click="dir = s.key"
            >{{ s.label }}</button>
          </div>
          <div class="crmc-search">
            <input v-model="q" type="search" class="crmc-input" :placeholder="__('Search person, company or object') + ' …'" />
          </div>
        </section>

        <!-- Karte „Anrufe" -->
        <section class="crmc-card">
          <header class="crmc-ch">
            <span class="crmc-ch-title">{{ __('Calls') }}</span>
            <span class="crmc-ch-note">
              {{ filtered.length }} {{ __('of') }} {{ rows.length }} · {{ __('row = details in the inspector') }}
            </span>
          </header>

          <PpDataGrid v-if="filtered.length" :columns="columns" :rows="filtered" @row-click="openCall">
            <template #cell-date="{ value }">{{ fmtDate(value) }}</template>
            <template #cell-person="{ row }">
              <span class="crmc-person">{{ row.person }}</span>
              <span v-if="row.company" class="crmc-company">{{ row.company }}</span>
            </template>
            <template #cell-direction="{ value }">
              <span class="crmc-dir">{{ value === 'ausgehend' ? __('outgoing') : __('incoming') }}</span>
            </template>
            <template #cell-duration="{ value }">{{ fmtDuration(value) }}</template>
            <template #cell-status="{ value }">
              <span class="crmc-pill" :data-tone="statusTone(value)"><i class="crmc-dot" />{{ statusLabel(value) }}</span>
            </template>
            <template #cell-object="{ value }">
              <span :class="{ 'crmc-muted': !value }">{{ value || '—' }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconPhone"
            :title="board.loading ? __('Loading calls …') : __('No calls')"
            :hint="board.loading ? '' : (q || dir !== 'all' ? __('No matches for the current filter/search.') : __('Call logs appear here as calls are made.'))"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconPhone from '~icons/lucide/phone'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()

const board = createResource({ url: 'lcs_integrations.projects.api.get_call_logs', auto: true })
const rows = computed(() => board.data?.rows || [])

// --- Filter: Richtung + Freitext -------------------------------------------
const DIRS = [
  { key: 'all', label: __('All') },
  { key: 'ausgehend', label: __('outgoing') },
  { key: 'eingehend', label: __('incoming') },
]
const dir = ref('all')
const q = ref('')
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (dir.value !== 'all' && r.direction !== dir.value) return false
    if (!needle) return true
    return [r.person, r.company, r.object].some((v) => (v || '').toLowerCase().includes(needle))
  })
})

const columns = [
  { key: 'date', label: __('Date'), width: 150 },
  { key: 'person', label: __('Person'), pin: true, width: 240 },
  { key: 'direction', label: __('Direction'), width: 140 },
  { key: 'duration', label: __('Duration'), align: 'right', width: 110 },
  { key: 'status', label: __('Result'), width: 180 },
  { key: 'object', label: __('Object'), width: 200 },
]

// --- Telefonie-Status → deutsche Pill + Ton --------------------------------
const STATUS = {
  Initiated: { label: __('Initiated'), tone: 'neutral' },
  Ringing: { label: __('Ringing'), tone: 'info' },
  'In Progress': { label: __('In progress'), tone: 'info' },
  InProgress: { label: __('In progress'), tone: 'info' },
  Completed: { label: __('Completed'), tone: 'success' },
  Busy: { label: __('Busy'), tone: 'warning' },
  'No Answer': { label: __('No answer'), tone: 'warning' },
  NoAnswer: { label: __('No answer'), tone: 'warning' },
  Failed: { label: __('Failed'), tone: 'danger' },
  Queued: { label: __('Queued'), tone: 'neutral' },
  Canceled: { label: __('Canceled'), tone: 'neutral' },
  Cancelled: { label: __('Canceled'), tone: 'neutral' },
}
function statusLabel(s) { return STATUS[s]?.label || s || '—' }
function statusTone(s) { return STATUS[s]?.tone || 'neutral' }

// --- Zeilen-Klick → angedockter Spec-Inspektor -----------------------------
function openCall(id) {
  const r = rows.value.find((x) => x.id === id)
  if (!r) return
  inspectNode({
    title: r.person || __('Call'),
    badge: { label: r.direction === 'ausgehend' ? __('outgoing') : __('incoming'), tone: 'brand' },
    rows: [
      { label: __('Company'), value: r.company || '—' },
      { label: __('Date'), value: fmtDate(r.date) },
      { label: __('Duration'), value: fmtDuration(r.duration) },
      { label: __('Result'), value: statusLabel(r.status) },
      { label: __('Object'), value: r.object || '—' },
    ],
    action: r.ref_name ? { label: __('Open object'), onClick: () => openRef(r) } : undefined,
  })
}
function openRef(r) {
  if (r.ref_doctype === 'CRM Lead') router.push({ name: 'Lead', params: { leadId: r.ref_name } })
  else if (r.ref_doctype === 'CRM Deal') router.push({ name: 'Deal', params: { dealId: r.ref_name } })
  else if (r.ref_doctype === 'LCS Project') router.push({ name: 'LCS Project', params: { id: r.ref_name } })
}
onBeforeUnmount(() => inspectNode(null))

// --- Formathelfer ----------------------------------------------------------
function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(String(v).replace(' ', 'T'))
  if (isNaN(d)) return String(v)
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(d)
}
function fmtDuration(sec) {
  const s = Number(sec) || 0
  if (!s) return '—'
  if (s < 60) return s + ' s'
  return Math.round(s / 60) + ' min'
}
</script>

<style scoped>
.crmc { flex: 1; min-height: 0; overflow: hidden; background: var(--pp-bg-base); display: flex; flex-direction: column; }
.crmc-inner { flex: 1; min-height: 0; padding: var(--pp-space-6);
  display: flex; flex-direction: column; gap: var(--pp-space-4); }

/* Filterleiste */
.crmc-filter { display: flex; align-items: center; gap: var(--pp-space-3); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmc-filter-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmc-seg { display: inline-flex; gap: 2px; padding: 2px; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-default); }
.crmc-seg-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 4px 14px; border: none; border-radius: var(--pp-radius-full); background: transparent; color: var(--pp-text-secondary); }
.crmc-seg-btn:hover { color: var(--pp-brand-primary); }
.crmc-seg-btn.is-active { background: var(--pp-brand-primary); color: var(--pp-text-on-accent); font-weight: var(--pp-weight-semibold); }
.crmc-search { flex: 1; min-width: 200px; }
.crmc-input { appearance: none; width: 100%; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.crmc-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }

/* Karte */
.crmc-card { flex: 1; min-height: 0; display: flex; flex-direction: column;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); overflow: hidden; }
.crmc-ch { display: flex; align-items: baseline; justify-content: space-between; gap: var(--pp-space-3);
  padding: var(--pp-space-3) var(--pp-space-4); border-bottom: 1px solid var(--pp-border-subtle); }
.crmc-ch-title { font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-bold); color: var(--pp-text-primary); }
.crmc-ch-note { font-size: 11px; color: var(--pp-text-tertiary); }

/* Zellen */
.crmc-person { display: block; font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crmc-company { display: block; font-size: 11px; color: var(--pp-text-tertiary); }
.crmc-dir { color: var(--pp-text-secondary); }
.crmc-muted { color: var(--pp-text-tertiary); }

.crmc-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; }
.crmc-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.crmc-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent);    color: var(--pp-state-info); }
.crmc-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.crmc-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmc-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
.crmc-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

/* Interner Tabellen-Scroll im fixierten Viewport-Layout */
.crmc-card :deep(.pp-datagrid) { flex: 1; min-height: 0; }
</style>
