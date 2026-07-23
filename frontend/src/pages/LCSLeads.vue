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

    <div class="crml">
      <div class="crml-inner">
        <PpPageHead
          :title="__('Leads')"
          :subtitle="`${filtered.length} ${__('of')} ${leads.length} ${__('Leads')} · ${__('click a row to open the profile')}`"
        >
          <template #actions>
            <div class="crml-search-wrap">
              <IconSearch class="crml-search-ico" />
              <input v-model="q" type="search" class="crml-search" :placeholder="__('Search / filter by status') + ' …'" />
            </div>
          </template>
        </PpPageHead>

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
        <section class="crml-card">
          <template v-if="rows.length">
          <div class="crml-scroll">
          <PpDataGrid :columns="columns" :rows="pagedRows" @row-click="openLead">
            <template #cell-name="{ row }">
              <span class="crml-name">{{ row.name }}</span>
              <span class="crml-id">{{ row.id }}</span>
            </template>
            <template #cell-organization="{ value }">
              <span :class="{ 'crml-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-status="{ row }">
              <span v-if="row.status" class="crml-pill" :data-tone="statusTone(row.status)">
                <i class="crml-dot"></i>{{ __(row.status) }}
              </span>
              <span v-else class="crml-muted">—</span>
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
              <span class="crml-muted">{{ fmtDate(value) }}</span>
            </template>
          </PpDataGrid>
          </div>
          <LcsPagination
            v-if="rowTotal > 25"
            :from="pgFrom" :to="pgTo" :total="rowTotal"
            :page="page" :page-count="pageCount" :page-size="pageSize"
            @prev="pgPrev" @next="pgNext" @page-size="setPageSize"
          />
          </template>

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
          <span v-if="sel.status" class="crml-pill" :data-tone="statusTone(sel.status)">
            <i class="crml-dot"></i>{{ __(sel.status) }}
          </span>
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
          <p v-if="!sel.email && !sel.mobile_no" class="crml-muted">—</p>
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
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpDrawer from '@/components/pp/PpDrawer.vue'
import LeadInspector from '@/components/lcs/LeadInspector.vue'
import LcsPagination from '@/components/lcs/LcsPagination.vue'
import IconSearchX from '~icons/lucide/search-x'
import IconInbox from '~icons/lucide/inbox'
import IconMail from '~icons/lucide/mail'
import IconPhone from '~icons/lucide/phone'
import IconSearch from '~icons/lucide/search'
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
const leads = computed(() => leadsRes.data || [])
const loading = computed(() => leadsRes.loading)
function reload() { leadsRes.reload(); statusRes.reload() }

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
/* Vollbreiten-Canvas — KEIN zentrierendes max-width (Shell-2.0-Vorgabe). */
/* Fixed viewport-height layout: table scrolls in its own region (see LCSContacts). */
.crml { flex: 1; min-height: 0; overflow: hidden; background: var(--pp-bg-base); display: flex; flex-direction: column; }
.crml-inner { flex: 1; min-height: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-6);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }
.crml-scroll { flex: 1; min-height: 0; overflow: auto; }

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

/* Kompakte Kopf-Suche (statt Filterzeile) */
.crml-search-wrap { position: relative; display: flex; align-items: center; }
.crml-search-ico { position: absolute; left: 9px; width: 15px; height: 15px; color: var(--pp-text-tertiary); pointer-events: none; }
.crml-search { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px 11px 7px 30px; border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); min-width: 260px; }
.crml-search:focus { outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }

/* Karte um die Tabelle */
.crml-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-2);
  flex: 1; min-height: 0; display: flex; flex-direction: column; }

/* Zell-Renderer */
.crml-name { display: block; font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crml-id { display: block; font-size: 11px; color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.crml-muted { color: var(--pp-text-tertiary); }

.crml-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; }
.crml-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.crml-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent);    color: var(--pp-state-info); }
.crml-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.crml-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.crml-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crml-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
.crml-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

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
