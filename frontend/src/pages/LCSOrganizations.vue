<!--
  LCSOrganizations — CRM-Firmen (Pilanda-UX, Analog zu LCSLeads/LCSContacts).
  ===========================================================================
  Bespoke Pilanda-Seite für „Firmen" (CRM Organization): PpPageHead + KPI-Strip
  + Filterleiste (Suche + Branche) + PpDataGrid (Name/Website/Territorium/
  Mitarbeiter/Zuletzt geändert). Einfachklick öffnet den angedockten Shell-
  Inspektor (OrganizationInspector); Doppelklick/„Öffnen" → Detailseite.
  Ersetzt die generische Upstream-Liste (bleibt als /organizations-upstream).
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Organizations'), route: { name: 'Organizations' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <PpPageHead
          :title="__('Organizations')"
          :subtitle="__('click a row to open the profile')"
        />

        <!-- Filterleiste (Referenz: Calls) -->
        <PpFilterBar
          v-model:search="q"
          :placeholder="__('Search / filter by industry') + ' …'"
        />

        <!-- KPI-Karten = klickbare Segment-Filter (Master Regel 9). -->
        <section class="crmo-kpis">
          <button
            v-for="k in kpis"
            :key="k.seg"
            type="button"
            class="crmo-kpi"
            :class="{ 'is-active': segment === k.seg }"
            @click="toggleSeg(k.seg)"
          >
            <PpStatTile :label="k.label" :value="k.value" :hint="k.hint" />
          </button>
        </section>

        <PpTableCard :title="__('Organizations')" :shown="filtered.length" :total="orgs.length">
          <PpDataGrid v-if="rows.length" :columns="columns" :rows="pagedRows" pickable v-model:pick-mode="selectMode" v-model:picked="picked" @row-click="openOrg">
            <template #cell-name="{ row }">
              <span class="pp-cell-strong">{{ row.name }}</span>
              <span class="pp-cell-sub">{{ row.industry || '—' }}</span>
            </template>
            <template #cell-website="{ value }">
              <span v-if="value" class="crmo-link">{{ value }}</span>
              <span v-else class="pp-cell-muted">—</span>
            </template>
            <template #cell-territory="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-no_of_employees="{ value }">
              <span class="crmo-num">{{ value || '—' }}</span>
            </template>
            <template #cell-modified="{ value }">
              <span class="pp-cell-muted">{{ fmtDate(value) }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else-if="hasFilter"
            :icon="IconSearchX"
            :title="__('No organizations found')"
            :hint="__('No matches for the current filter/search.')"
          >
            <template #action>
              <button class="crmo-btn crmo-btn--primary" @click="resetFilter">{{ __('Reset filters') }}</button>
            </template>
          </PpEmptyState>
          <PpEmptyState
            v-else
            :icon="IconInbox"
            :title="loading ? __('Loading …') : __('No organizations yet')"
            :hint="loading ? '' : __('Companies created in the CRM will appear here.')"
          />

          <template v-if="rows.length && rowTotal > 25" #footer>
            <LcsPagination
              :from="pgFrom" :to="pgTo" :total="rowTotal"
              :page="page" :page-count="pageCount" :page-size="pageSize"
              @prev="pgPrev" @next="pgNext" @page-size="setPageSize"
            />
          </template>
        </PpTableCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import OrganizationInspector from '@/components/lcs/OrganizationInspector.vue'
import LcsPagination from '@/components/lcs/LcsPagination.vue'
import IconSearchX from '~icons/lucide/search-x'
import IconInbox from '~icons/lucide/inbox'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { useListFuncbar } from '@/composables/useListFuncbar'
import { usePagination } from '@/composables/usePagination'

const router = useRouter()
const { pilandaMode } = usePilandaMode()
const { inspectPanel } = usePilandaInspect()

const orgsRes = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Organization',
    fields: [
      'name', 'organization_name', 'website', 'industry', 'territory',
      'no_of_employees', 'annual_revenue', 'modified',
    ],
    order_by: 'modified desc',
    limit_page_length: 0,
  },
  auto: true,
})
const orgs = computed(() => orgsRes.data || [])
const loading = computed(() => orgsRes.loading)
function reload() { orgsRes.reload() }

const selectMode = ref(false)
const picked = ref([])
function exportRows() {
  const src = picked.value.length ? rows.value.filter((r) => picked.value.includes(r.id)) : rows.value
  if (!src.length) { toast({ title: __('Nothing to export.'), icon: 'alert-circle' }); return }
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [['Firma', 'Branche', 'Territorium', 'Website', 'Mitarbeiter'].map(esc).join(',')]
  src.forEach((r) => lines.push([r.name, r.industry, r.territory, r.website, r.no_of_employees].map(esc).join(',')))
  const blob = new Blob(['﻿' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'firmen.csv'; a.click(); URL.revokeObjectURL(a.href)
  toast({ title: `${src.length} ${__('exported')}`, icon: 'check-circle', iconClasses: 'text-green-500' })
}
useListFuncbar({ title: __('Organizations'), meaning: __('Companies in the CRM.'), count: () => orgs.value.length, reload, exportRows, selectMode, pickedCount: () => picked.value.length })

function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleDateString('de-DE')
}
function prettyUrl(u) {
  return String(u || '').replace(/^https?:\/\//, '').replace(/\/$/, '')
}

// Suche (inkl. Branche/Territorium) + KPI-Segment (Master Regel 9).
const q = ref('')
const segment = ref('') // '' | 'website' | 'territory' | 'week'
const hasFilter = computed(() => q.value.trim() !== '' || segment.value !== '')
function resetFilter() { q.value = ''; segment.value = '' }
function toggleSeg(seg) { segment.value = seg === '' ? '' : (segment.value === seg ? '' : seg) }

const WEEK_MS = 7 * 24 * 3600 * 1000
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  const weekAgo = Date.now() - WEEK_MS
  return orgs.value.filter((o) => {
    const qOk = !needle ||
      (o.organization_name || o.name || '').toLowerCase().includes(needle) ||
      (o.industry || '').toLowerCase().includes(needle) ||
      (o.territory || '').toLowerCase().includes(needle)
    let sOk = true
    if (segment.value === 'website') sOk = !!o.website
    else if (segment.value === 'territory') sOk = !!o.territory
    else if (segment.value === 'week') {
      const t = o.modified ? new Date(o.modified).getTime() : NaN
      sOk = !isNaN(t) && t >= weekAgo
    }
    return qOk && sOk
  })
})

const kpis = computed(() => {
  const list = orgs.value
  const withWeb = list.filter((o) => o.website).length
  const withTerr = list.filter((o) => o.territory).length
  const weekAgo = Date.now() - WEEK_MS
  const weekCount = list.filter((o) => {
    const t = o.modified ? new Date(o.modified).getTime() : NaN
    return !isNaN(t) && t >= weekAgo
  }).length
  return [
    { seg: '', label: __('Total organizations'), value: String(list.length), hint: __('in the CRM') },
    { seg: 'website', label: __('With website'), value: String(withWeb), hint: __('online presence') },
    { seg: 'territory', label: __('With territory'), value: String(withTerr), hint: __('assigned market') },
    { seg: 'week', label: __('Updated this week'), value: String(weekCount), hint: __('last 7 days') },
  ]
})

const columns = [
  { key: 'name', label: __('Organization'), pin: true, width: 280 },
  { key: 'website', label: __('Website'), width: 220 },
  { key: 'territory', label: __('Territory'), width: 180 },
  { key: 'no_of_employees', label: __('Employees'), align: 'right', width: 120 },
  { key: 'modified', label: __('Last modified'), align: 'right', width: 150 },
]
const rows = computed(() =>
  filtered.value.map((o) => ({
    id: o.name,
    name: o.organization_name || o.name,
    industry: o.industry,
    website: prettyUrl(o.website),
    territory: o.territory,
    no_of_employees: o.no_of_employees,
    modified: o.modified,
  })),
)

// Pagination (client-side; the list loads all rows).
const {
  paged: pagedRows, page, pageCount, total: rowTotal,
  from: pgFrom, to: pgTo, pageSize, next: pgNext, prev: pgPrev, setPageSize,
} = usePagination(rows)

let lastClick = { id: null, t: 0 }
function openOrg(id) {
  if (!id) return
  if (!pilandaMode.value) {
    openDetail(id)
    return
  }
  const now = Date.now()
  if (lastClick.id === id && now - lastClick.t < 350) {
    lastClick = { id: null, t: 0 }
    openDetail(id)
    return
  }
  lastClick = { id, t: now }
  inspectPanel({
    component: OrganizationInspector,
    props: { organizationId: id },
    on: { open: openDetail },
    title: __('Company'),
  })
}
function openDetail(id) {
  router.push({ name: 'Organization', params: { organizationId: id } })
}
onBeforeUnmount(() => {
  if (pilandaMode.value) inspectPanel(null)
})
</script>

<style scoped>
/* Reset-Filter button in the empty state. */
.crmo-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.crmo-btn:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crmo-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.crmo-btn--primary:hover { filter: brightness(1.05); color: var(--pp-text-on-accent); }

.crmo-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

/* KPI-Karten als klickbare Segment-Filter (Regel 9) */
.crmo-kpi { appearance: none; border: none; background: none; padding: 0; margin: 0; cursor: pointer;
  text-align: left; border-radius: var(--pp-radius-ui); outline: none; }
.crmo-kpi > :deep(.pp-kpi) { transition: box-shadow .12s, border-color .12s; }
.crmo-kpi:hover > :deep(.pp-kpi) { border-color: var(--pp-brand-primary); }
.crmo-kpi.is-active > :deep(.pp-kpi) { border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--pp-brand-primary) 30%, transparent); }
.crmo-kpi:focus-visible > :deep(.pp-kpi) { box-shadow: var(--pp-shadow-focus-ring, 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.3)); }

/* Zell-Renderer, die über die gemeinsamen pp-cell-* Rollen hinausgehen. */
.crmo-link { color: var(--pp-brand-primary); font-size: var(--pp-fs-12);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmo-num { font-variant-numeric: tabular-nums; color: var(--pp-text-primary); }

@media (max-width: 1080px) {
  .crmo-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
