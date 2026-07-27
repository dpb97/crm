<!--
  LCSLeads — CRM-Interessenten (V2, Showcase #3 „Lead-Liste").
  ============================================================
  Pilanda-UX für die CRM-Kernfläche „Interessent" (Leads): PpPageHead +
  KPI-Strip (PpStatTile) + Filterleiste (Suche + Status) + PpDataGrid
  (Name/Firma/Status/E-Mail/Telefon/Zuletzt geändert). Klick auf eine Zeile
  öffnet den Detail-Drawer (PpDrawer) mit den Stammdaten und einem Übergang
  „Im CRM öffnen" auf Dominiks Detailseite (/crm/leads/<id>), bis der
  Detail-Umbau folgt.

  Präsentation 1:1 nach pilanda_theme-Showcase #3 (ThemePreviewCrmLeads),
  aber an ECHTE Daten verdrahtet — keine Demodaten:
    · Leads   → frappe.client.get_list  ('CRM Lead')
    · Status  → frappe.client.get_list  ('CRM Lead Status', mit Farbe)
  Leeres Ergebnis wird EHRLICH als Leerzustand gezeigt.

  Backend (Dominiks CRM) bleibt unangetastet; dies ist reine Präsentation.
  Verwendete Bausteine: PpPageHead · PpStatTile · PpDataGrid (#cell-Slots) ·
  PpEmptyState · PpDrawer.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Leads'), route: { name: 'Leads' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <PpPageHead
          :title="__('Leads')"
          :subtitle="__('click a row to open the profile')"
        />

        <!-- Filterleiste: Suche + Listen-/Board-Umschalter (Referenz: Calls) -->
        <PpFilterBar
          v-model:search="q"
          :placeholder="__('Search / filter by status') + ' …'"
        >
          <template #actions>
            <div class="crml-viewseg" role="tablist">
              <button
                v-for="v in VIEWS"
                :key="v.key"
                type="button"
                class="crml-viewseg-btn"
                :class="{ 'is-active': viewMode === v.key }"
                :aria-pressed="viewMode === v.key"
                :title="v.label"
                @click="viewMode = v.key"
              >
                <component :is="v.icon" class="crml-viewseg-ico" /><span>{{ v.label }}</span>
              </button>
            </div>
          </template>
        </PpFilterBar>

        <!-- KPI-Karten = klickbare Segment-Filter (Master Regel 9). -->
        <section class="crml-kpis">
          <button
            v-for="k in kpis"
            :key="k.seg"
            type="button"
            class="crml-kpi"
            :class="{ 'is-active': segment === k.seg }"
            @click="toggleSeg(k.seg)"
          >
            <PpStatTile :label="k.label" :value="k.value" :hint="k.hint" />
          </button>
        </section>

        <!-- Tabelle ODER ehrlicher Leerzustand -->
        <PpTableCard
          v-if="viewMode === 'list'"
          :title="__('Leads')"
          :shown="filtered.length"
          :total="leads.length"
        >
          <PpDataGrid v-if="rows.length" :columns="columns" :rows="pagedRows" @row-click="openLead">
            <template #cell-name="{ row }">
              <span class="pp-cell-strong">{{ row.name }}</span>
              <span class="pp-cell-sub">{{ row.id }}</span>
            </template>
            <template #cell-organization="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-status="{ row }">
              <PpPill v-if="row.status" :tone="statusTone(row.status)">{{ __(row.status) }}</PpPill>
              <span v-else class="pp-cell-muted">—</span>
            </template>
            <template #cell-email="{ value }">
              <span class="crml-contact-line">
                <IconMail v-if="value" class="crml-contact-ico" />{{ value || '—' }}
              </span>
            </template>
            <template #cell-mobile_no="{ value }">
              <span class="crml-contact-line crml-contact-line--muted">
                <IconPhone v-if="value" class="crml-contact-ico" />{{ value || '—' }}
              </span>
            </template>
            <template #cell-modified="{ value }">
              <span class="pp-cell-muted">{{ fmtDate(value) }}</span>
            </template>
          </PpDataGrid>

          <!-- Leerzustand: leer nach Filter vs. gar keine Daten -->
          <PpEmptyState
            v-else-if="hasFilter"
            :icon="IconSearchX"
            :title="__('No leads found')"
            :hint="__('No matches for the current filter/search.')"
          >
            <template #action>
              <button class="crml-btn crml-btn--primary" @click="resetFilter">{{ __('Reset filters') }}</button>
            </template>
          </PpEmptyState>
          <PpEmptyState
            v-else
            :icon="IconInbox"
            :title="loading ? __('Loading …') : __('No leads yet')"
            :hint="loading ? '' : __('Leads created in the CRM will appear here.')"
          />

          <template v-if="rows.length && rowTotal > 25" #footer>
            <LcsPagination
              :from="pgFrom" :to="pgTo" :total="rowTotal"
              :page="page" :page-count="pageCount" :page-size="pageSize"
              @prev="pgPrev" @next="pgNext" @page-size="setPageSize"
            />
          </template>
        </PpTableCard>

        <!-- Kanban nach Status (gleicher Abstiegs-Vertrag: Klick → Inspektor,
             Doppelklick → öffnen; Drag verschiebt den Status). -->
        <section v-else class="crml-board">
          <PpKanban
            v-if="kanbanColumns.length"
            :columns="kanbanColumns"
            :cards="kanbanCards"
            @card-click="openLead"
            @move="onLeadMove"
          />
          <PpEmptyState
            v-else
            :icon="IconInbox"
            :title="loading ? __('Loading …') : __('No lead statuses')"
            :hint="loading ? '' : __('Lead statuses configured in the CRM appear as columns here.')"
          />
        </section>
      </div>
    </div>

    <!-- Interessenten-Profil (Detail-Drawer, echte Felder aus get_list) -->
    <PpDrawer v-model:open="drawerOpen" :width="460" :title="sel ? sel.name : ''">
      <template v-if="sel" #title>
        <span class="crml-dh">{{ displayName(sel) }}</span>
      </template>
      <div v-if="sel" class="crml-detail">
        <div class="crml-detail-head">
          <h3 class="crml-detail-name">{{ displayName(sel) }}</h3>
          <PpPill v-if="sel.status" :tone="statusTone(sel.status)">{{ __(sel.status) }}</PpPill>
        </div>

        <dl class="crml-meta">
          <div><dt>{{ __('Organization') }}</dt><dd>{{ sel.organization || '—' }}</dd></div>
          <div><dt>{{ __('Status') }}</dt><dd>{{ sel.status ? __(sel.status) : '—' }}</dd></div>
          <div><dt>{{ __('Lead owner') }}</dt><dd>{{ sel.lead_owner || '—' }}</dd></div>
          <div><dt>{{ __('Last modified') }}</dt><dd>{{ fmtDate(sel.modified) }}</dd></div>
        </dl>

        <section class="crml-sec">
          <h4 class="crml-sec-title">{{ __('Contacts') }}</h4>
          <a v-if="sel.email" class="crml-contact-line" :href="`mailto:${sel.email}`">
            <IconMail class="crml-contact-ico" />{{ sel.email }}
          </a>
          <a v-if="sel.mobile_no" class="crml-contact-line crml-contact-line--muted" :href="`tel:${sel.mobile_no}`">
            <IconPhone class="crml-contact-ico" />{{ sel.mobile_no }}
          </a>
          <p v-if="!sel.email && !sel.mobile_no" class="pp-cell-muted">—</p>
        </section>
      </div>

      <template #footer>
        <Button
          v-if="sel"
          variant="solid"
          :label="__('Open in CRM')"
          iconLeft="external-link"
          @click="openInCrm"
        />
      </template>
    </PpDrawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { createResource, call, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpKanban from '@/components/pp/PpKanban.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpDrawer from '@/components/pp/PpDrawer.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpPill from '@/components/pp/PpPill.vue'
import LeadInspector from '@/components/lcs/LeadInspector.vue'
import LcsPagination from '@/components/lcs/LcsPagination.vue'
import IconSearchX from '~icons/lucide/search-x'
import IconInbox from '~icons/lucide/inbox'
import IconMail from '~icons/lucide/mail'
import IconPhone from '~icons/lucide/phone'
import IconList from '~icons/lucide/list'
import IconColumns from '~icons/lucide/columns-3'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { usePagination } from '@/composables/usePagination'

const router = useRouter()
const { pilandaMode } = usePilandaMode()
const { inspectPanel } = usePilandaInspect()

// --- Daten: echte CRM-Leads (Dominiks Backend, unverändert) ----------------
const leadsRes = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Lead',
    fields: [
      'name', 'lead_name', 'first_name', 'last_name', 'organization',
      'status', 'email', 'mobile_no', 'lead_owner', 'modified',
    ],
    order_by: 'modified desc',
    limit_page_length: 0,
  },
  auto: true,
})
// Mutable board clone so the Kanban can move cards optimistically; both the
// list and the board read from it, so a drag reflects in either view.
const boardLeads = ref([])
watch(() => leadsRes.data, (d) => { boardLeads.value = (d || []).map((x) => ({ ...x })) }, { immediate: true, deep: true })
const leads = computed(() => boardLeads.value)
const loading = computed(() => leadsRes.loading)
function reload() { leadsRes.reload(); statusRes.reload() }

// List ⇄ Kanban (Befund 18: SSOT-Liste, one renderer, same descent contract).
const viewMode = useStorage('lcs-leads-view-mode', 'list')
const VIEWS = [
  { key: 'list', label: __('List'), icon: IconList },
  { key: 'kanban', label: __('Board'), icon: IconColumns },
]

// --- Status-Stammdaten inkl. Farbe (für farbige Status-Pillen + Filter) ----
const statusRes = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Lead Status',
    fields: ['name', 'color', 'position'],
    order_by: 'position asc',
    limit_page_length: 0,
  },
  auto: true,
})
const statusList = computed(() => statusRes.data || [])
const statusByName = computed(() => {
  const m = {}
  for (const s of statusList.value) m[s.name] = s
  return m
})

// Frappe-Farbnamen → pp-Tonwert (token-only Pillen, keine Hex).
const COLOR_TONE = {
  green: 'success', teal: 'success', lime: 'success',
  blue: 'info', cyan: 'info', sky: 'info', 'light-blue': 'info',
  indigo: 'brand', purple: 'brand', violet: 'brand',
  red: 'danger', pink: 'danger',
  orange: 'warning', amber: 'warning', yellow: 'warning',
  gray: 'neutral', grey: 'neutral', black: 'neutral',
}
function statusTone(name) {
  const raw = (statusByName.value[name]?.color || '').toLowerCase()
  return COLOR_TONE[raw] || 'neutral'
}

// --- Anzeige-Helfer --------------------------------------------------------
function displayName(l) {
  return (
    l.lead_name ||
    [l.first_name, l.last_name].filter(Boolean).join(' ') ||
    l.organization ||
    l.name
  )
}
function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleDateString('de-DE')
}

// --- Filter: Suche (inkl. Status) + KPI-Segment (Master Regel 9) -----------
const q = ref('')
const segment = ref('') // '' | 'new' | 'qualified' | 'week'
const hasFilter = computed(() => q.value.trim() !== '' || segment.value !== '')
function resetFilter() { q.value = ''; segment.value = '' }
function toggleSeg(seg) { segment.value = seg === '' ? '' : (segment.value === seg ? '' : seg) }

const WEEK_MS = 7 * 24 * 3600 * 1000
const entryStatus = computed(() => statusList.value[0]?.name) // niedrigste position = Einstieg
function isNew(s) { return /new|neu/i.test(s || '') || (entryStatus.value && s === entryStatus.value) }
function isQualified(s) { return /qualif/i.test(s || '') }

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  const weekAgo = Date.now() - WEEK_MS
  return leads.value.filter((l) => {
    const qOk = !needle ||
      displayName(l).toLowerCase().includes(needle) ||
      (l.organization || '').toLowerCase().includes(needle) ||
      (l.email || '').toLowerCase().includes(needle) ||
      (l.status || '').toLowerCase().includes(needle)
    let sOk = true
    if (segment.value === 'new') sOk = isNew(l.status)
    else if (segment.value === 'qualified') sOk = isQualified(l.status)
    else if (segment.value === 'week') {
      const t = l.modified ? new Date(l.modified).getTime() : NaN
      sOk = !isNaN(t) && t >= weekAgo
    }
    return qOk && sOk
  })
})

// --- KPI-Karten (klickbare Segmente) --------------------------------------
const kpis = computed(() => {
  const list = leads.value
  const weekAgo = Date.now() - WEEK_MS
  const newCount = list.filter((l) => isNew(l.status)).length
  const qualCount = list.filter((l) => isQualified(l.status)).length
  const weekCount = list.filter((l) => {
    const t = l.modified ? new Date(l.modified).getTime() : NaN
    return !isNaN(t) && t >= weekAgo
  }).length
  return [
    { seg: '', label: __('Total leads'), value: String(list.length), hint: __('in the funnel') },
    { seg: 'new', label: __('New'), value: String(newCount), hint: __('awaiting first contact') },
    { seg: 'qualified', label: __('Qualified'), value: String(qualCount), hint: __('ready for offer stage') },
    { seg: 'week', label: __('Updated this week'), value: String(weekCount), hint: __('last 7 days') },
  ]
})

// --- Tabelle ---------------------------------------------------------------
const columns = [
  { key: 'name', label: __('Lead'), pin: true, width: 240 },
  { key: 'organization', label: __('Organization'), width: 220 },
  { key: 'status', label: __('Status'), width: 150 },
  { key: 'email', label: __('Email'), width: 220 },
  { key: 'mobile_no', label: __('Phone'), width: 160 },
  { key: 'modified', label: __('Last modified'), align: 'right', width: 150 },
]
const rows = computed(() =>
  filtered.value.map((l) => ({
    id: l.name,
    name: displayName(l),
    organization: l.organization,
    status: l.status,
    email: l.email,
    mobile_no: l.mobile_no,
    modified: l.modified,
  })),
)

// --- Kanban (nach Status; gefiltert wie die Liste) -------------------------
const kanbanColumns = computed(() => statusList.value.map((s) => ({ key: s.name, label: __(s.name) })))
const kanbanCards = computed(() =>
  filtered.value
    .filter((l) => l.status)
    .map((l) => ({
      id: l.name,
      col: l.status,
      title: displayName(l),
      badges: l.organization ? [{ label: l.organization, tone: 'neutral' }] : [],
      assignee: l.lead_owner || null,
    })),
)
// Drag → Status persistieren (optimistisch + Rollback + Toast). Lead-Status hat
// keinen Pflicht-Grund wie „Lost" bei Deals, daher direkte Ablage.
async function onLeadMove({ cardId, fromCol, toCol }) {
  if (fromCol === toCol) return
  const lead = boardLeads.value.find((l) => l.name === cardId)
  if (!lead) return
  lead.status = toCol
  try {
    await call('frappe.client.set_value', { doctype: 'CRM Lead', name: cardId, fieldname: { status: toCol } })
    toast({ title: __('Status updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
  } catch (e) {
    lead.status = fromCol
    toast({ title: __('Could not save. Please try again.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}

// --- Detail-Drawer (echt: Zeilenklick öffnet) ------------------------------
// Pagination (client-side; the list loads all rows).
const {
  paged: pagedRows, page, pageCount, total: rowTotal,
  from: pgFrom, to: pgTo, pageSize, next: pgNext, prev: pgPrev, setPageSize,
} = usePagination(rows)

const drawerOpen = ref(false)
const selId = ref(null)
const sel = computed(() => leads.value.find((l) => l.name === selId.value) || null)

// Pilanda: single-click → docked shell inspector (LeadInspector); double-click
// or "Open in CRM" → detail page. CRM-only mode keeps the local PpDrawer.
let lastClick = { id: null, t: 0 }
function openLead(id) {
  selId.value = id
  if (!pilandaMode.value) {
    drawerOpen.value = true
    return
  }
  const now = Date.now()
  if (lastClick.id === id && now - lastClick.t < 350) {
    lastClick = { id: null, t: 0 }
    openInCrm()
    return
  }
  lastClick = { id, t: now }
  inspectPanel({
    component: LeadInspector,
    props: { lead: sel.value },
    on: { open: openInCrm },
    title: __('Lead'),
  })
}
function openInCrm() {
  if (sel.value) router.push({ name: 'Lead', params: { leadId: sel.value.name } })
}
onBeforeUnmount(() => {
  if (pilandaMode.value) inspectPanel(null)
})
</script>

<style scoped>

/* Buttons */
.crml-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.crml-btn:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crml-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.crml-btn--primary:hover { filter: brightness(1.05); color: var(--pp-text-on-accent); }

/* KPI-Strip */
.crml-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

/* KPI-Karten als klickbare Segment-Filter (Regel 9) */
.crml-kpi { appearance: none; border: none; background: none; padding: 0; margin: 0; cursor: pointer;
  text-align: left; border-radius: var(--pp-radius-ui); outline: none; }
.crml-kpi > :deep(.pp-kpi) { transition: box-shadow .12s, border-color .12s; }
.crml-kpi:hover > :deep(.pp-kpi) { border-color: var(--pp-brand-primary); }
.crml-kpi.is-active > :deep(.pp-kpi) { border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--pp-brand-primary) 30%, transparent); }
.crml-kpi:focus-visible > :deep(.pp-kpi) { box-shadow: var(--pp-shadow-focus-ring, 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.3)); }

/* Ansicht-Umschalter Liste ⇄ Kanban (Befund 18) */
.crml-viewseg { display: inline-flex; gap: 2px; padding: 2px; border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-default); }
.crml-viewseg-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12, 12px);
  display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; border: none;
  border-radius: var(--pp-radius-ui); background: transparent; color: var(--pp-text-secondary); }
.crml-viewseg-btn:hover { color: var(--pp-brand-primary); }
.crml-viewseg-btn.is-active { background: var(--pp-bg-surface); color: var(--pp-brand-primary);
  font-weight: var(--pp-weight-semibold); box-shadow: var(--pp-shadow-xs); }
.crml-viewseg-ico { width: 14px; height: 14px; }

/* Kanban-Board (eigener Scroll-Bereich im fixierten Viewport-Layout) */
.crml-board { flex: 1; min-height: 0; overflow: auto; }




.crml-contact-line { display: inline-flex; align-items: center; gap: 5px; font-size: var(--pp-fs-12);
  color: var(--pp-text-secondary); text-decoration: none; font-variant-numeric: tabular-nums;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crml-contact-line--muted { color: var(--pp-text-tertiary); }
a.crml-contact-line:hover { color: var(--pp-brand-primary); }
.crml-contact-ico { width: 13px; height: 13px; flex-shrink: 0; }

/* Drawer-Detail */
.crml-dh { font-weight: var(--pp-weight-semibold); }
.crml-detail { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.crml-detail-head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3); }
.crml-detail-name { margin: 0; font-size: var(--pp-fs-20); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); font-family: var(--pp-font-heading); }
.crml-meta { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-2) var(--pp-space-4); margin: 0; }
.crml-meta dt { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.crml-meta dd { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.crml-sec { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crml-sec-title { margin: 0; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-text-tertiary); }

@media (max-width: 1080px) {
  .crml-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
