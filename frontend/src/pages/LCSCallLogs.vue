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

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <!-- Filterleiste: Richtung-Segmente + Suche -->
        <PpFilterBar
          v-model="dir"
          v-model:search="q"
          :segments="DIRS"
          :placeholder="__('Search person, company or object') + ' …'"
        />

        <!-- Karte „Anrufe" -->
        <PpTableCard :title="__('Calls')" :shown="filtered.length" :total="rows.length">
          <PpDataGrid v-if="filtered.length" :columns="columns" :rows="filtered" @row-click="openCall">
            <template #cell-date="{ value }">{{ fmtDate(value) }}</template>
            <template #cell-person="{ row }">
              <span class="pp-cell-strong">{{ row.person }}</span>
              <span v-if="row.company" class="pp-cell-sub">{{ row.company }}</span>
            </template>
            <template #cell-direction="{ value }">
              <span class="pp-cell-soft">{{ value === 'ausgehend' ? __('outgoing') : __('incoming') }}</span>
            </template>
            <template #cell-duration="{ value }">{{ fmtDuration(value) }}</template>
            <template #cell-status="{ value }">
              <PpPill :tone="statusTone(value)">{{ statusLabel(value) }}</PpPill>
            </template>
            <template #cell-object="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value || '—' }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconPhone"
            :title="board.loading ? __('Loading calls …') : __('No calls')"
            :hint="board.loading ? '' : (q || dir !== 'all' ? __('No matches for the current filter/search.') : __('Call logs appear here as calls are made.'))"
          />
        </PpTableCard>
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
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpPill from '@/components/pp/PpPill.vue'
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

