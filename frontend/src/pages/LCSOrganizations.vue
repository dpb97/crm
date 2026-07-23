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
        <Breadcrumbs :items="[{ label: __('Organizations'), route: { name: 'Organizations' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" />
      </template>
    </LayoutHeader>

    <div class="crmo">
      <div class="crmo-inner">
        <PpPageHead
          :eyebrow="__('Sales / CRM')"
          :title="__('Organizations')"
          :subtitle="`${filtered.length} ${__('of')} ${orgs.length} ${__('Organizations')} · ${__('click a row to open the profile')}`"
        />

        <section class="crmo-kpis">
          <PpStatTile v-for="k in kpis" :key="k.label" v-bind="k" />
        </section>

        <section class="crmo-filter">
          <div class="crmo-field crmo-field--search">
            <label class="crmo-field-cap">{{ __('Search') }}</label>
            <input v-model="q" type="search" class="crmo-input" :placeholder="__('Search') + ' …'" />
          </div>
          <div class="crmo-field">
            <label class="crmo-field-cap">{{ __('Industry') }}</label>
            <select v-model="fIndustry" class="crmo-input">
              <option value="alle">{{ __('All industries') }}</option>
              <option v-for="i in industryList" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
          <button v-if="hasFilter" class="crmo-btn crmo-reset" @click="resetFilter">{{ __('Reset filters') }}</button>
        </section>

        <section class="crmo-card">
          <template v-if="rows.length">
          <div class="crmo-scroll">
          <PpDataGrid :columns="columns" :rows="pagedRows" @row-click="openOrg">
            <template #cell-name="{ row }">
              <span class="crmo-name">{{ row.name }}</span>
              <span class="crmo-id">{{ row.industry || '—' }}</span>
            </template>
            <template #cell-website="{ value }">
              <span v-if="value" class="crmo-link">{{ value }}</span>
              <span v-else class="crmo-muted">—</span>
            </template>
            <template #cell-territory="{ value }">
              <span :class="{ 'crmo-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-no_of_employees="{ value }">
              <span class="crmo-num">{{ value || '—' }}</span>
            </template>
            <template #cell-modified="{ value }">
              <span class="crmo-muted">{{ fmtDate(value) }}</span>
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
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import OrganizationInspector from '@/components/lcs/OrganizationInspector.vue'
import LcsPagination from '@/components/lcs/LcsPagination.vue'
import IconSearchX from '~icons/lucide/search-x'
import IconInbox from '~icons/lucide/inbox'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
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

function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleDateString('de-DE')
}
function prettyUrl(u) {
  return String(u || '').replace(/^https?:\/\//, '').replace(/\/$/, '')
}

const q = ref('')
const fIndustry = ref('alle')
const hasFilter = computed(() => q.value.trim() !== '' || fIndustry.value !== 'alle')
function resetFilter() { q.value = ''; fIndustry.value = 'alle' }

const industryList = computed(() =>
  [...new Set(orgs.value.map((o) => o.industry).filter(Boolean))].sort(),
)

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return orgs.value.filter((o) => {
    const qOk = !needle ||
      (o.organization_name || o.name || '').toLowerCase().includes(needle) ||
      (o.industry || '').toLowerCase().includes(needle) ||
      (o.territory || '').toLowerCase().includes(needle)
    const iOk = fIndustry.value === 'alle' || o.industry === fIndustry.value
    return qOk && iOk
  })
})

const kpis = computed(() => {
  const list = orgs.value
  const withWeb = list.filter((o) => o.website).length
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000
  const weekCount = list.filter((o) => {
    const t = o.modified ? new Date(o.modified).getTime() : NaN
    return !isNaN(t) && t >= weekAgo
  }).length
  return [
    { label: __('Total organizations'), value: String(list.length), hint: __('in the CRM') },
    { label: __('Industries'), value: String(industryList.value.length), hint: __('distinct sectors') },
    { label: __('With website'), value: String(withWeb), hint: __('online presence') },
    { label: __('Updated this week'), value: String(weekCount), hint: __('last 7 days') },
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
/* Fixed viewport-height layout: table scrolls in its own region (see LCSContacts). */
.crmo { flex: 1; min-height: 0; overflow: hidden; background: var(--pp-bg-base); display: flex; flex-direction: column; }
.crmo-inner { flex: 1; min-height: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-6);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }
.crmo-scroll { flex: 1; min-height: 0; overflow: auto; }

.crmo-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.crmo-btn:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crmo-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.crmo-btn--primary:hover { filter: brightness(1.05); color: var(--pp-text-on-accent); }

.crmo-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

.crmo-filter { display: flex; align-items: flex-end; gap: var(--pp-space-3); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmo-field { display: flex; flex-direction: column; gap: 3px; }
.crmo-field--search { flex: 1 1 240px; min-width: 200px; }
.crmo-field-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmo-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 6px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); min-width: 150px; }
.crmo-input:focus { outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crmo-reset { margin-left: auto; }

.crmo-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-2);
  flex: 1; min-height: 0; display: flex; flex-direction: column; }

.crmo-name { display: block; font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crmo-id { display: block; font-size: 11px; color: var(--pp-text-tertiary); }
.crmo-muted { color: var(--pp-text-tertiary); }
.crmo-link { color: var(--pp-brand-primary); font-size: var(--pp-fs-12);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmo-num { font-variant-numeric: tabular-nums; color: var(--pp-text-primary); }

@media (max-width: 1080px) {
  .crmo-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
