<!--
  LCSChances — Chancen-Seite (Vertrieb-Nav „Chancen", klickdummy).
  ============================================================
  Trichter-Einstieg: Chancen aus dem Pilot-Scout / Anfragen / Empfehlungen /
  Notizen. Quelle-Filter + Suche, Tabelle mit Score-Balken, Status-Pill und
  dem „Entscheid des Verkäufers" (Kontakt aufgenommen → Lead · Keine Chance).
  Einfachklick → angedockter Inspektor (Details), Doppelklick → Chance öffnen.
  Fluss: Chance → Lead → Vertriebsprojekt.

  Echte Daten: lcs_integrations.projects.api.get_chances (+ chance_to_lead /
  chance_dismiss). Datenmodell: LCS Chance (bis der Pilot/pilanda_salesbot live ist).
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Chancen'), route: { name: 'LCS Chances' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <PpFilterBar
          v-model="source"
          v-model:search="q"
          :caption="__('Source')"
          :segments="SOURCES"
          :placeholder="__('Search person, company or object') + ' …'"
        />

        <PpTableCard :title="__('Chancen')" :note="headerNote">
          <PpDataGrid
            v-if="filtered.length"
            :columns="columns"
            :rows="filtered"
            pickable
            v-model:pick-mode="selectMode"
            v-model:picked="picked"
            @row-click="onRowClick"
            @row-dblclick="openDetail"
          >
            <template #cell-chance="{ row }">
              <span class="pp-cell-strong">{{ row.title }}</span>
              <span class="pp-cell-sub">{{ row.chance_no }}<template v-if="row.company"> · {{ row.company }}</template></span>
            </template>
            <template #cell-quelle="{ row }">
              <span class="pp-cell-strong">{{ row.source }}</span>
              <span v-if="row.source_detail" class="pp-cell-sub">{{ row.source_detail }}</span>
            </template>
            <template #cell-order_value="{ value }">{{ eur(value) }}</template>
            <template #cell-deadline="{ value }">
              <template v-if="value">
                {{ fmtDate(value) }}<span class="pp-cell-sub" :class="dueClass(value)">{{ dueLabel(value) }}</span>
              </template>
              <span v-else class="pp-cell-muted">—</span>
            </template>
            <template #cell-score="{ value }">
              <span class="chc-score">
                <span class="chc-score-track"><i :style="{ width: Math.min(100, value) + '%', background: scoreColor(value) }" /></span>
                <b>{{ value }}</b>
              </span>
            </template>
            <template #cell-status="{ value }">
              <PpPill :tone="statusTone(value)">{{ value }}</PpPill>
            </template>
            <template #cell-entscheid="{ row }">
              <span class="chc-decide">
                <button type="button" class="chc-btn is-primary" :disabled="busy === row.id" @click.stop="toLead(row)">
                  {{ __('Contact made') }} → Lead
                </button>
                <button type="button" class="chc-btn" :disabled="busy === row.id" @click.stop="dismiss(row)">
                  {{ __('No chance') }}
                </button>
              </span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconTarget"
            :title="board.loading ? __('Loading chances …') : __('No chances')"
            :hint="board.loading ? '' : (q || source !== 'Alle' ? __('No matches for the current filter/search.') : __('Chances from the Pilot scout, enquiries and referrals appear here.'))"
          />
        </PpTableCard>
      </div>
    </div>

    <!-- Chance erfassen (Funktionsbar-Aktion) -->
    <PpModal v-model:open="createOpen" :title="__('Capture chance')" :width="520">
      <form class="chc-form" @submit.prevent="submitCreate">
        <label class="chc-fld">
          <span class="chc-fld-cap">{{ __('Title') }}</span>
          <input v-model="form.title" type="text" class="chc-input" required autofocus />
        </label>
        <label class="chc-fld">
          <span class="chc-fld-cap">{{ __('Source') }}</span>
          <select v-model="form.source" class="chc-input">
            <option v-for="s in SOURCES.filter((x) => x.key !== 'Alle')" :key="s.key" :value="s.key">{{ s.label }}</option>
          </select>
        </label>
        <div class="chc-form-row">
          <label class="chc-fld">
            <span class="chc-fld-cap">{{ __('Company') }}</span>
            <input v-model="form.company" type="text" class="chc-input" />
          </label>
          <label class="chc-fld chc-fld--sm">
            <span class="chc-fld-cap">{{ __('Country') }}</span>
            <input v-model="form.country" type="text" class="chc-input" placeholder="CH" />
          </label>
          <label class="chc-fld chc-fld--sm">
            <span class="chc-fld-cap">{{ __('Value') }} (€)</span>
            <input v-model.number="form.order_value" type="number" class="chc-input" />
          </label>
        </div>
      </form>
      <template #footer>
        <Button :label="__('Cancel')" @click="createOpen = false" />
        <Button variant="solid" :label="__('Save')" :loading="creating" @click="submitCreate" />
      </template>
    </PpModal>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpPill from '@/components/pp/PpPill.vue'
import PpModal from '@/components/pp/PpModal.vue'
import IconTarget from '~icons/lucide/target'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { usePilandaFuncbar } from '@/composables/usePilandaFuncbar'

const router = useRouter()
const { inspectNode } = usePilandaInspect()
const { registerFuncbar, clearFuncbar } = usePilandaFuncbar()

const board = createResource({ url: 'lcs_integrations.projects.api.get_chances', auto: true })
const rows = computed(() => board.data?.rows || [])
const dismissedQuarter = computed(() => board.data?.dismissed_quarter || 0)

// --- Filter: Quelle + Freitext ---------------------------------------------
const SOURCES = [
  { key: 'Alle', label: __('All') },
  { key: 'Pilot-Scout', label: 'Pilot-Scout' },
  { key: 'Anfrage (Mail/Telefon)', label: __('Enquiry (mail/phone)') },
  { key: 'Empfehlung', label: __('Referral') },
  { key: 'Notiz (intern)', label: __('Note (internal)') },
]
const source = ref('Alle')
const q = ref('')
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (source.value !== 'Alle' && r.source !== source.value) return false
    if (!needle) return true
    return [r.title, r.company, r.client, r.chance_no].some((v) => (v || '').toLowerCase().includes(needle))
  })
})

const headerNote = computed(() =>
  `${filtered.value.length} ${__('of')} ${rows.value.length} · ${__('No chance (quarter)')}: ${dismissedQuarter.value}`
  + ` · ${__('row = details in the inspector')} · ${__('double click = open chance')}`,
)

const columns = [
  { key: 'chance', label: __('Chance'), pin: true, width: 260 },
  { key: 'quelle', label: __('Source'), width: 220 },
  { key: 'country', label: __('Country'), width: 70 },
  { key: 'order_value', label: __('Value'), align: 'right', width: 90 },
  { key: 'deadline', label: __('Deadline'), width: 140 },
  { key: 'score', label: __('Score'), width: 120 },
  { key: 'status', label: __('Status'), width: 110 },
  { key: 'entscheid', label: __('Sales decision'), width: 260 },
]

// --- Status / Score-Darstellung --------------------------------------------
function statusTone(s) {
  if (/relevant/i.test(s)) return 'success'
  if (/kontakt/i.test(s)) return 'brand'
  if (/keine/i.test(s)) return 'neutral'
  return 'info'
}
function scoreColor(v) { return v >= 70 ? 'var(--pp-state-success)' : v >= 40 ? 'var(--pp-state-warning)' : 'var(--pp-state-danger)' }

// --- Aktionen: → Lead / Keine Chance ---------------------------------------
const busy = ref(null)
function toLead(row) {
  busy.value = row.id
  call('lcs_integrations.projects.api.chance_to_lead', { name: row.id })
    .then((res) => {
      toast({ title: `${__('Lead created')} — ${row.title}`, icon: 'check-circle', iconClasses: 'text-green-500' })
      if (res?.lead) router.push({ name: 'Lead', params: { leadId: res.lead } })
      else board.reload()
    })
    .catch((e) => toast({ title: __('Could not create the lead.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { busy.value = null })
}
function dismiss(row) {
  busy.value = row.id
  call('lcs_integrations.projects.api.chance_dismiss', { name: row.id })
    .then(() => { toast({ title: `${__('Dismissed')} — ${row.title}`, icon: 'check-circle', iconClasses: 'text-green-500' }); board.reload() })
    .catch((e) => toast({ title: __('Could not save.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { busy.value = null })
}

// --- Zeilen-Klick → Inspektor / Doppelklick → Detail -----------------------
function onRowClick(id) {
  const r = rows.value.find((x) => x.id === id)
  if (!r) return
  inspectNode({
    title: r.title,
    badge: { label: r.status, tone: statusTone(r.status) },
    rows: [
      { label: __('Chance No'), value: r.chance_no },
      { label: __('Client'), value: r.client || r.company || '—' },
      { label: __('Country'), value: r.country || '—' },
      { label: __('Value'), value: eur(r.order_value) },
      { label: __('Score'), value: `${r.score}/100` },
      { label: __('Deadline'), value: r.deadline ? fmtDate(r.deadline) : '—' },
    ],
    sections: [
      { title: __('Source'), items: [{ text: r.source, muted: r.source_detail || '' }], empty: '—' },
    ],
    action: { label: __('Open chance'), onClick: () => openDetail(id) },
  })
}
function openDetail(id) {
  router.push({ name: 'LCS Chance', params: { id } })
}

// --- Auswahl-Modus (Werkzeug „Auswählen") ----------------------------------
const selectMode = ref(false)
const picked = ref([])

// --- Zentrale Funktionsbar (Burger im Inspektor-Kopf) ----------------------
function buildGroups() {
  const n = picked.value.length
  return {
    aktionen: [
      { id: 'export', label: n ? `${n} ${__('selected')} · ${__('Export')}` : __('Export'), primary: true },
      { id: 'create', label: __('Capture chance') },
      { id: 'refresh', label: __('Refresh') },
    ],
    werkzeuge: [{ id: 'select', label: __('Select') }],
  }
}
function onFuncAction(id) {
  if (id === 'select') { selectMode.value = !selectMode.value; if (!selectMode.value) picked.value = [] }
  else if (id === 'refresh') board.reload()
  else if (id === 'export') exportRows()
  else if (id === 'create') openCreate()
}
// Re-register when the selection count changes so the „N ausgewählt"-Label updates.
watch([picked, selectMode], () => registerFuncbar(buildGroups(), onFuncAction), { deep: true })

// Standard-Inspektorinhalt, damit der Kopf (mit Burger) auf der Seite immer da ist.
function showDefaultInspector() {
  inspectNode({
    title: __('Chancen'),
    badge: { label: __('planned'), tone: 'brand' },
    rows: [
      { label: __('Open'), value: String(rows.value.length) },
      { label: __('No chance (quarter)'), value: String(dismissedQuarter.value) },
    ],
    sections: [
      { title: __('Meaning'), items: [{ text: __('All chances with their source (Pilot · tender · enquiry by mail/phone) — leads grow from them.') }], empty: '—' },
    ],
  })
}
watch(() => board.data, () => showDefaultInspector())

// --- Export der (ausgewählten) Zeilen als CSV ------------------------------
function exportRows() {
  const src = picked.value.length ? filtered.value.filter((r) => picked.value.includes(r.id)) : filtered.value
  if (!src.length) { toast({ title: __('Nothing to export.'), icon: 'alert-circle' }); return }
  const head = ['Chance', 'Titel', 'Quelle', 'Land', 'Wert', 'Frist', 'Score', 'Status']
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [head.map(esc).join(',')]
  src.forEach((r) => lines.push([r.chance_no, r.title, r.source, r.country, r.order_value, r.deadline || '', r.score, r.status].map(esc).join(',')))
  const blob = new Blob(['﻿' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'chancen.csv'
  a.click()
  URL.revokeObjectURL(a.href)
  toast({ title: `${src.length} ${__('chances exported')}`, icon: 'check-circle', iconClasses: 'text-green-500' })
}

// --- „Chance erfassen" (Modal → LCS Chance anlegen) ------------------------
const createOpen = ref(false)
const creating = ref(false)
const form = ref({ title: '', source: 'Notiz (intern)', company: '', country: '', order_value: null })
function openCreate() { form.value = { title: '', source: 'Notiz (intern)', company: '', country: '', order_value: null }; createOpen.value = true }
function submitCreate() {
  if (!form.value.title.trim()) return
  creating.value = true
  call('frappe.client.insert', { doc: {
    doctype: 'LCS Chance',
    chance_no: 'CH-' + Date.now().toString().slice(-6),
    title: form.value.title.trim(),
    source: form.value.source,
    company: form.value.company.trim() || null,
    client: form.value.company.trim() || null,
    country: form.value.country.trim() || null,
    order_value: form.value.order_value || 0,
    status: 'Neu',
  } })
    .then(() => { createOpen.value = false; toast({ title: __('Chance captured'), icon: 'check-circle', iconClasses: 'text-green-500' }); board.reload() })
    .catch((e) => toast({ title: __('Could not save.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
    .finally(() => { creating.value = false })
}

onMounted(() => { registerFuncbar(buildGroups(), onFuncAction); showDefaultInspector() })
onBeforeUnmount(() => { inspectNode(null); clearFuncbar() })

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
function dueLabel(v) {
  const n = daysTo(v)
  if (isNaN(n)) return ''
  if (n < 0) return `${__('overdue by')} ${-n} ${__('days')}`
  return `${__('in')} ${n} ${__('days')}`
}
function dueClass(v) {
  const n = daysTo(v)
  if (isNaN(n)) return ''
  if (n < 0) return 'chc-due--over'
  if (n <= 30) return 'chc-due--soon'
  return ''
}
</script>

<style scoped>
/* Score-Balken */
.chc-score { display: inline-flex; align-items: center; gap: var(--pp-space-2); min-width: 90px; }
.chc-score-track { flex: 1; height: 6px; border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); overflow: hidden; }
.chc-score-track i { display: block; height: 100%; }
.chc-score b { font-size: var(--pp-fs-12, 12px); font-variant-numeric: tabular-nums; color: var(--pp-text-secondary); }

.chc-due--soon { color: var(--pp-state-warning); }
.chc-due--over { color: var(--pp-state-danger); }

/* Entscheid-Buttons */
.chc-decide { display: inline-flex; gap: 6px; }
.chc-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: 11px; font-weight: var(--pp-weight-medium);
  padding: 4px 10px; border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); color: var(--pp-text-secondary); white-space: nowrap; }
.chc-btn:hover:not(:disabled) { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.chc-btn.is-primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.chc-btn.is-primary:hover:not(:disabled) { color: var(--pp-text-on-accent); filter: brightness(1.05); }
.chc-btn:disabled { opacity: 0.5; cursor: default; }

/* Erfassen-Modal */
.chc-form { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.chc-form-row { display: flex; gap: var(--pp-space-3); }
.chc-fld { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.chc-fld--sm { flex: 0 0 90px; }
.chc-fld-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.chc-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.chc-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
</style>
