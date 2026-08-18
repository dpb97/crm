<!--
  LCSPilot — Pilot (Vertrieb-Nav „Pilot", Klickdummy Karten-Variante).
  ============================================================
  Ausschreibungs-Scout „Pilot" (pilanda_salesbot). Zeigt NUR Scout-TREFFER als
  Karten mit Mini-Landkarte, Scoutbewertung und Score. Entscheid des Verkäufers:
  „Als Chance werten" (→ erscheint in Chancen) oder „Keine Chance" (→ Archiv).
  Nichts erscheint doppelt — gewertete Treffer wandern in den Vertriebsfluss
  (Chancen → Leads → Vertriebsprojekte). Archiv unten: endgültiges Löschen.

  Echte Daten: lcs_integrations.projects.api.get_pilot_hits
  (+ pilot_rate_as_chance / chance_dismiss / pilot_delete). Sync aus dem Salesbot:
  lcs_integrations.salesbot.sync.sync_salesbot_tenders.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Pilot'), route: { name: 'LCS Pilot' } }]" />
      </template>
      <template #right-header>
        <div class="plt-toggle">
          <button type="button" class="plt-toggle-btn" :class="{ on: viewMode === 'cards' }" @click="viewMode = 'cards'">{{ __('Cards') }}</button>
          <button type="button" class="plt-toggle-btn" :class="{ on: viewMode === 'table' }" @click="viewMode = 'table'">{{ __('Table') }}</button>
        </div>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <PpFilterBar
          v-model="statusFilter"
          v-model:search="q"
          :caption="__('Filter')"
          :segments="STATUSES"
          :placeholder="__('Search hit or buyer') + ' …'"
        />

        <div class="plt-scroll">
        <div class="plt-head">
          <span class="plt-head-title">{{ __('Scout hits · only the salespersons rating turns one into a chance') }}</span>
          <span class="plt-head-meta">{{ filtered.length }} {{ __('of') }} {{ rows.length }} · {{ __('No chance (quarter)') }}: {{ dismissedQuarter }} · {{ __('card = details in the inspector') }} · {{ __('double click = open hit') }}</span>
        </div>

        <!-- Tabellen-Ansicht -->
        <PpTableCard v-if="viewMode === 'table' && filtered.length" :grow="false" :title="__('Pilot hits')" :note="''">
          <PpDataGrid table-key="lcs_pilot_tbl" :columns="tableCols" :rows="filtered" :page-size="50" @row-click="onRowClickId" @row-dblclick="openDetail">
            <template #cell-hit="{ row }">
              <span class="pp-cell-strong">{{ row.title }}</span>
              <span class="pp-cell-sub">{{ row.chance_no }}<template v-if="row.company || row.client"> · {{ row.company || row.client }}</template></span>
            </template>
            <template #cell-order_value="{ value }">{{ eur(value) }}</template>
            <template #cell-deadline="{ value }">
              <span v-if="value" :class="dueClass(value)">{{ fmtDate(value) }}</span>
              <span v-else class="pp-cell-muted">—</span>
            </template>
            <template #cell-score="{ value }">
              <span class="plt-score plt-score--tbl" :class="scoreClass(value)"><span class="plt-score-bar"><i :style="{ width: Math.min(100, value) + '%' }" /></span><b>{{ value }}</b></span>
            </template>
            <template #cell-relevance="{ value }">
              <PpPill v-if="value" :tone="relToneTbl(value)">{{ value }}</PpPill>
              <span v-else class="pp-cell-muted">—</span>
            </template>
            <template #cell-status="{ value }"><PpPill :tone="statusTone(value)">{{ value }}</PpPill></template>
            <template #cell-entscheid="{ row }">
              <span class="plt-decide" @click.stop>
                <button type="button" class="plt-btn is-primary" :disabled="busy === row.id" @click="rate(row)">{{ __('Rate as chance') }}</button>
                <button type="button" class="plt-btn" :disabled="busy === row.id" @click="dismiss(row)">{{ __('No chance') }}</button>
              </span>
            </template>
          </PpDataGrid>
        </PpTableCard>

        <!-- Karten-Ansicht -->
        <div v-else-if="viewMode === 'cards' && filtered.length" class="plt-cards">
          <article
            v-for="r in filtered"
            :key="r.id"
            class="plt-card"
            :class="{ 'is-sel': selId === r.id }"
            @click="onSelect(r)"
            @dblclick="openDetail(r.id)"
          >
            <header class="plt-card-head">
              <span class="plt-card-title">{{ r.title }}</span>
              <span class="plt-card-src">{{ r.chance_no }}<template v-if="r.company || r.client"> · {{ r.company || r.client }}</template><template v-if="r.source_detail"> · {{ r.source_detail }}</template></span>
              <PpPill :tone="statusTone(r.status)">{{ r.status }}</PpPill>
            </header>

            <div class="plt-card-body">
              <div class="plt-map" @click.stop>
                <LcsMiniMap :lat="r.latitude" :lon="r.longitude" @open="openDetail(r.id)" />
              </div>

              <div class="plt-main">
                <p v-if="r.summary_de" class="plt-sum">{{ r.summary_de }}</p>
                <p v-if="r.description_original" class="plt-desc">{{ r.description_original }}</p>
                <div class="plt-pills">
                  <span class="plt-pill"><i class="pd" /><template v-if="flag(r.country)">{{ flag(r.country) }} </template>{{ r.country || '—' }}</span>
                  <span class="plt-pill"><i class="pd" />{{ eur(r.order_value) }}</span>
                  <span class="plt-pill" :class="dueClass(r.deadline)"><i class="pd" />{{ deadlineText(r) }}</span>
                  <span v-if="r.category" class="plt-pill plt-pill--cat"><i class="pd" />{{ r.category }}</span>
                  <span v-if="r.geo_confidence" class="plt-pill plt-pill--geo"><i class="pd" />{{ __('Geo') }}: {{ r.geo_confidence }}</span>
                </div>
                <div v-if="r.reasoning" class="plt-reason">{{ r.reasoning }}</div>
              </div>

              <div class="plt-actions" @click.stop>
                <div class="plt-score" :class="scoreClass(r.score)">
                  <span class="plt-score-bar"><i :style="{ width: Math.min(100, r.score) + '%' }" /></span>
                  <b>{{ r.score }}</b>
                </div>
                <button type="button" class="plt-btn is-primary" :disabled="busy === r.id" @click="rate(r)">{{ __('Rate as chance') }}</button>
                <button type="button" class="plt-btn" :disabled="busy === r.id" @click="dismiss(r)">{{ __('No chance') }}</button>
              </div>
            </div>
          </article>
        </div>

        <PpEmptyState
          v-else
          :icon="IconRadar"
          :title="board.loading ? __('Loading hits …') : __('No open hits')"
          :hint="board.loading ? '' : (q || statusFilter !== 'Alle' ? __('No matches for the current filter/search.') : __('New tenders from the scout appear here. Run “Pilot sync” to pull the latest.'))"
        />

        <!-- Archiv: verworfene Treffer, endgültiges Löschen nur hier -->
        <div class="plt-arch">
          <button type="button" class="plt-arch-head" @click="archOpen = !archOpen">
            <span class="plt-arch-chev" :class="{ open: archOpen }">›</span>
            {{ __('Archive') }}
            <span class="plt-arch-meta">{{ archived.length }} {{ __('entries') }} · {{ __('final deletion only here') }}</span>
          </button>
          <div v-if="archOpen" class="plt-arch-body">
            <div v-for="a in archived" :key="a.id" class="plt-arch-row">
              <span class="plt-arch-title">{{ a.title }}</span>
              <span class="plt-arch-sub">{{ a.chance_no }}<template v-if="a.country"> · {{ a.country }}</template> · Score {{ a.score }}</span>
              <button type="button" class="plt-btn plt-btn--danger" :disabled="busy === a.id" @click="del(a)">{{ __('Delete') }}</button>
            </div>
            <div v-if="!archived.length" class="plt-arch-empty">{{ __('No archived hits.') }}</div>
          </div>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpPill from '@/components/pp/PpPill.vue'
import LcsMiniMap from '@/components/lcs/LcsMiniMap.vue'
import PilotHitInspector from '@/components/lcs/PilotHitInspector.vue'
import IconRadar from '~icons/lucide/radar'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { usePilandaFuncbar } from '@/composables/usePilandaFuncbar'

const router = useRouter()
const { inspectNode, inspectPanel } = usePilandaInspect()
const { registerFuncbar, clearFuncbar } = usePilandaFuncbar()

const board = createResource({ url: 'lcs_integrations.projects.api.get_pilot_hits', auto: true })
const rows = computed(() => board.data?.rows || [])
const archived = computed(() => board.data?.archived || [])
const ratedQuarter = computed(() => board.data?.rated_quarter || 0)
const dismissedQuarter = computed(() => board.data?.dismissed_quarter || 0)

// Ansicht: Karten (Klickdummy-Default) ↔ Tabelle, pro Nutzer gemerkt.
const viewMode = ref(localStorage.getItem('lcs_pilot_view') === 'table' ? 'table' : 'cards')
watch(viewMode, (v) => localStorage.setItem('lcs_pilot_view', v))

const tableCols = [
  { key: 'hit', label: __('Hit'), pin: true, width: 260 },
  { key: 'country', label: __('Country'), width: 70 },
  { key: 'order_value', label: __('Value'), align: 'right', width: 90 },
  { key: 'deadline', label: __('Deadline'), width: 120 },
  { key: 'score', label: __('Score'), width: 120 },
  { key: 'relevance', label: __('Relevance'), width: 100 },
  { key: 'status', label: __('Status'), width: 120 },
  { key: 'entscheid', label: __('Sales decision'), width: 240 },
]
function onRowClickId(id) {
  const r = rows.value.find((x) => x.id === id)
  if (r) onSelect(r)
}
function relToneTbl(r) {
  if (/hoch|high/i.test(r)) return 'success'
  if (/mittel|medium/i.test(r)) return 'warning'
  if (/niedrig|low/i.test(r)) return 'neutral'
  return 'info'
}

// --- Filter: Status + Freitext ---------------------------------------------
const STATUSES = [
  { key: 'Alle', label: __('All') },
  { key: 'Neu', label: __('New') },
  { key: 'Relevant', label: __('Relevant') },
  { key: 'In Bearbeitung', label: __('In progress') },
]
const statusFilter = ref('Alle')
const q = ref('')
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (statusFilter.value !== 'Alle' && r.status !== statusFilter.value) return false
    if (!needle) return true
    return [r.title, r.company, r.client, r.country, r.chance_no].some((v) => (v || '').toLowerCase().includes(needle))
  })
})

// --- Darstellung -----------------------------------------------------------
function statusTone(s) {
  if (/relevant/i.test(s)) return 'success'
  if (/bearbeitung/i.test(s)) return 'warning'
  if (/keine/i.test(s)) return 'neutral'
  return 'info'
}
function scoreClass(v) { return v < 50 ? 'is-low' : v < 70 ? 'is-warn' : '' }
function flag(cc) {
  const c = String(cc || '').trim().toUpperCase()
  if (!/^[A-Z]{2}$/.test(c)) return ''
  return String.fromCodePoint(...[...c].map((ch) => 0x1f1e6 + ch.charCodeAt(0) - 65))
}

// --- Aktionen: Als Chance werten / Keine Chance / Löschen ------------------
const busy = ref(null)
function rate(row) {
  busy.value = row.id
  call('lcs_integrations.projects.api.pilot_rate_as_chance', { name: row.id })
    .then(() => { toast({ title: `${__('Rated as chance')} — ${row.title}`, icon: 'check-circle', iconClasses: 'text-green-500' }); board.reload() })
    .catch((e) => toast({ title: __('Could not save.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { busy.value = null })
}
function dismiss(row) {
  busy.value = row.id
  call('lcs_integrations.projects.api.chance_dismiss', { name: row.id })
    .then(() => { toast({ title: `${__('Dismissed')} — ${row.title}`, icon: 'check-circle', iconClasses: 'text-green-500' }); board.reload() })
    .catch((e) => toast({ title: __('Could not save.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { busy.value = null })
}
function del(row) {
  busy.value = row.id
  call('lcs_integrations.projects.api.pilot_delete', { name: row.id })
    .then(() => { toast({ title: `${__('Deleted')} — ${row.title}`, icon: 'check-circle', iconClasses: 'text-green-500' }); board.reload() })
    .catch((e) => toast({ title: __('Could not delete.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { busy.value = null })
}

// --- Auswahl → Inspektor / Doppelklick → Detail ----------------------------
const selId = ref(null)
function onSelect(r) {
  selId.value = r.id
  // Interactive panel in the shell inspector: scout facts + assign-to-person +
  // comment thread (klickdummy rule: actions/details live in the inspector).
  inspectPanel({
    component: PilotHitInspector,
    props: { hit: r },
    on: { open: () => openDetail(r.id), changed: () => board.reload() },
    title: __('Hit'),
    ref: { doctype: 'LCS Chance', name: r.name, title: r.title },
  })
}
function openDetail(id) {
  router.push({ name: 'LCS Chance', params: { id } })
}

// --- Archiv-Aufklappen -----------------------------------------------------
const archOpen = ref(false)

// --- Funcbar ---------------------------------------------------------------
const pilotSyncing = ref(false)
const pilotSync = createResource({ url: 'lcs_integrations.salesbot.sync.sync_salesbot_tenders' })
function runPilotSync() {
  if (pilotSyncing.value) return
  pilotSyncing.value = true
  registerFuncbar(buildGroups(), onFuncAction)
  pilotSync.submit({})
    .then((r) => {
      toast({ title: `${__('Pilot sync')}: ${r?.created || 0} ${__('new')}, ${r?.updated || 0} ${__('updated')}`, icon: 'check-circle', iconClasses: 'text-green-500' })
      board.reload()
    })
    .catch((e) => toast({ title: __('Pilot sync failed'), text: e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { pilotSyncing.value = false; registerFuncbar(buildGroups(), onFuncAction) })
}
function buildGroups() {
  return {
    aktionen: [
      { id: 'sync', label: __('Pilot sync'), primary: true, loading: pilotSyncing.value },
      { id: 'refresh', label: __('Refresh') },
    ],
  }
}
function onFuncAction(id) {
  if (id === 'refresh') board.reload()
  else if (id === 'sync') runPilotSync()
}
function showDefaultInspector() {
  inspectNode({
    title: __('Pilot'),
    badge: { label: __('scout'), tone: 'brand' },
    rows: [
      { label: __('Open hits'), value: String(rows.value.length) },
      { label: __('Rated (quarter)'), value: String(ratedQuarter.value) },
      { label: __('No chance (quarter)'), value: String(dismissedQuarter.value) },
    ],
    sections: [
      { title: __('Meaning'), items: [{ text: __('Scout hits only. Rating a hit as a chance moves it into the sales flow (Chances → Leads → Sales projects) — nothing appears twice.') }], empty: '—' },
    ],
  })
}

onMounted(() => { registerFuncbar(buildGroups(), onFuncAction); showDefaultInspector() })
onBeforeUnmount(() => { inspectPanel(null); inspectNode(null); clearFuncbar() })

// --- Formathelfer ----------------------------------------------------------
function eur(v) {
  const n = Number(v) || 0
  if (n >= 1_000_000) return (n / 1_000_000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' M€'
  if (n >= 1_000) return Math.round(n / 1_000).toLocaleString('de-DE') + ' k€'
  return '€' + Math.round(n)
}
function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(String(v).replace(' ', 'T'))
  return isNaN(d) ? String(v) : new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}
function daysTo(v) {
  const d = new Date(String(v).replace(' ', 'T')).getTime()
  return Math.round((d - Date.now()) / 86400000)
}
function deadlineText(r) {
  if (!r.deadline) return `${__('Deadline')}: —`
  const n = daysTo(r.deadline)
  if (isNaN(n)) return `${__('Deadline')}: ${fmtDate(r.deadline)}`
  const suffix = n < 0 ? `${__('overdue by')} ${-n} ${__('days')}` : `${__('in')} ${n} ${__('days')}`
  return `${__('Deadline')}: ${fmtDate(r.deadline)} (${suffix})`
}
function dueClass(v) {
  if (!v) return ''
  const n = daysTo(v)
  if (isNaN(n)) return ''
  if (n < 0) return 'is-over'
  if (n <= 30) return 'is-soon'
  return 'is-ok'
}
</script>

<style scoped>
/* Ansicht-Umschalter (Kopf) */
.plt-toggle { display: inline-flex; border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  overflow: hidden; margin-right: var(--pp-space-2); }
.plt-toggle-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: 12px; font-weight: var(--pp-weight-medium);
  padding: 5px 12px; border: 0; background: var(--pp-bg-surface); color: var(--pp-text-secondary); }
.plt-toggle-btn + .plt-toggle-btn { border-left: 1px solid var(--pp-border-default); }
.plt-toggle-btn.on { background: var(--pp-brand-primary); color: var(--pp-text-on-accent); }

/* Scroll-Container: EINZIGER Scroll-Besitzer der Seite (Karten liefen sonst über
   das overflow:hidden von .pp-listpage hinaus und ließen sich nicht scrollen).
   Scrollbalken versteckt (Klickdummy: keine sichtbaren Balken, Funktion bleibt). */
.plt-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; display: flex; flex-direction: column;
  gap: var(--pp-space-3); scrollbar-width: none; }
.plt-scroll::-webkit-scrollbar { width: 0; height: 0; }

/* Tabellen-Aktionen + Inline-Score in der Tabellenzelle */
.plt-decide { display: inline-flex; gap: 6px; }
.plt-score--tbl { min-width: 90px; }

/* Kopfzeile über den Karten */
.plt-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--pp-space-4);
  padding: 0 var(--pp-space-1) var(--pp-space-1); }
.plt-head-title { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.plt-head-meta { font-size: 11px; color: var(--pp-text-tertiary); text-align: right; }

.plt-cards { display: flex; flex-direction: column; gap: var(--pp-space-3); }

.plt-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); overflow: hidden; cursor: pointer;
  transition: border-color .12s, box-shadow .12s; }
.plt-card:hover { border-color: var(--pp-border-default); }
.plt-card.is-sel { border-color: var(--pp-brand-primary); box-shadow: 0 0 0 1px var(--pp-brand-primary); }

.plt-card-head { display: flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-2) var(--pp-space-3); border-bottom: 1px solid var(--pp-border-subtle);
  background: var(--pp-bg-base); }
.plt-card-title { font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.plt-card-src { margin-left: auto; font-size: 11px; color: var(--pp-text-tertiary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 46%; }

.plt-card-body { display: grid; grid-template-columns: 300px 1fr 240px; align-items: stretch; }
.plt-map { min-height: 180px; border-right: 1px solid var(--pp-border-subtle); }
.plt-main { min-width: 0; padding: var(--pp-space-3); display: flex; flex-direction: column; gap: var(--pp-space-2); }
.plt-sum { margin: 0; font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.plt-desc { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-secondary); line-height: 1.45; }

.plt-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px; }
.plt-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: var(--pp-text-secondary);
  padding: 2px 8px; border-radius: var(--pp-radius-full); background: var(--pp-bg-base); border: 1px solid var(--pp-border-subtle); }
.plt-pill .pd { width: 6px; height: 6px; border-radius: 50%; background: var(--pp-brand-primary); flex-shrink: 0; }
.plt-pill--cat { color: var(--pp-brand-primary); }
.plt-pill--geo .pd { background: var(--pp-accent-amber, #d08700); }
.plt-pill--geo { color: var(--pp-accent-amber, #d08700); }
.plt-pill.is-ok .pd { background: var(--pp-state-success); }
.plt-pill.is-soon { color: var(--pp-state-warning); } .plt-pill.is-soon .pd { background: var(--pp-state-warning); }
.plt-pill.is-over { color: var(--pp-state-danger); } .plt-pill.is-over .pd { background: var(--pp-state-danger); }

.plt-reason { margin-top: auto; font-size: 11.5px; color: var(--pp-text-secondary);
  padding: var(--pp-space-2) var(--pp-space-3); background: var(--pp-bg-base); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-subtle); }

.plt-actions { display: flex; flex-direction: column; gap: var(--pp-space-2);
  padding: var(--pp-space-3); border-left: 1px solid var(--pp-border-subtle); background: var(--pp-bg-base); }
.plt-score { display: flex; align-items: center; gap: var(--pp-space-2); }
.plt-score-bar { flex: 1; height: 6px; border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); overflow: hidden; }
.plt-score-bar i { display: block; height: 100%; background: var(--pp-state-success); }
.plt-score b { font-size: var(--pp-fs-14, 14px); font-variant-numeric: tabular-nums; color: var(--pp-text-primary); min-width: 24px; text-align: right; }
.plt-score.is-warn .plt-score-bar i { background: var(--pp-state-warning); }
.plt-score.is-low .plt-score-bar i { background: var(--pp-state-danger); }

.plt-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: 12px; font-weight: var(--pp-weight-medium);
  padding: 7px 10px; border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-secondary); white-space: nowrap; }
.plt-btn:hover:not(:disabled) { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.plt-btn.is-primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.plt-btn.is-primary:hover:not(:disabled) { color: var(--pp-text-on-accent); filter: brightness(1.05); }
.plt-btn--danger:hover:not(:disabled) { border-color: var(--pp-state-danger); color: var(--pp-state-danger); }
.plt-btn:disabled { opacity: .5; cursor: default; }

/* Archiv */
.plt-arch { margin-top: var(--pp-space-3); border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); overflow: hidden; }
.plt-arch-head { display: flex; align-items: center; gap: var(--pp-space-2); width: 100%; appearance: none; border: 0;
  cursor: pointer; background: var(--pp-bg-base); padding: var(--pp-space-2) var(--pp-space-3); font: inherit;
  font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); text-align: left; }
.plt-arch-chev { display: inline-block; transition: transform .12s; color: var(--pp-text-tertiary); }
.plt-arch-chev.open { transform: rotate(90deg); }
.plt-arch-meta { margin-left: auto; font-size: 11px; font-weight: var(--pp-weight-regular); color: var(--pp-text-tertiary); }
.plt-arch-body { display: flex; flex-direction: column; }
.plt-arch-row { display: flex; align-items: center; gap: var(--pp-space-3); padding: var(--pp-space-2) var(--pp-space-3);
  border-top: 1px solid var(--pp-border-subtle); }
.plt-arch-title { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.plt-arch-sub { font-size: 11px; color: var(--pp-text-tertiary); white-space: nowrap; }
.plt-arch-row .plt-btn { margin-left: auto; }
.plt-arch-empty { padding: var(--pp-space-3); font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }

@media (max-width: 900px) {
  .plt-card-body { grid-template-columns: 1fr; }
  .plt-map { min-height: 150px; border-right: 0; border-bottom: 1px solid var(--pp-border-subtle); }
  .plt-actions { border-left: 0; border-top: 1px solid var(--pp-border-subtle); }
}
</style>
