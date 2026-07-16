<!--
  LCSMarketAssignment
  ===================
  Assignment dashboard for the LCS market split ("Marktaufteilung", R03):
  who is responsible for which territory / segment, and how much live work
  (leads / deals / projects) each sales manager currently carries.
  Data from lcs_integrations.projects.api.get_market_assignment.
-->

<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Market Assignment'), route: { name: 'LCS Market Assignment' } }]" />
    </template>
    <template #right-header>
      <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="board.reload()" :loading="board.loading" />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto p-5">
    <div class="space-y-5">
      <!-- KPI row -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div class="rounded-xl border bg-white p-4">
          <div class="lcs-kpi-label">{{ __('Territories') }}</div>
          <div class="mt-1 text-xl font-bold text-lcs-primary tabular-nums">{{ summary.territories }}</div>
        </div>
        <div class="rounded-xl border bg-white p-4">
          <div class="lcs-kpi-label">{{ __('Countries covered') }}</div>
          <div class="mt-1 text-xl font-bold text-gray-900 tabular-nums">{{ summary.countries }}</div>
        </div>
        <div class="rounded-xl border bg-white p-4">
          <div class="lcs-kpi-label">{{ __('Sales managers') }}</div>
          <div class="mt-1 text-xl font-bold text-gray-900 tabular-nums">{{ summary.managers }}</div>
        </div>
        <div class="rounded-xl border bg-white p-4">
          <div class="lcs-kpi-label">{{ __('Segments') }}</div>
          <div class="mt-1 text-xl font-bold text-gray-900 tabular-nums">{{ summary.segments }}</div>
        </div>
      </div>

      <!-- Priority breakdown -->
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-semibold uppercase tracking-wide text-gray-400">{{ __('Priority') }}:</span>
        <span
          v-for="p in PRIORITIES"
          :key="p"
          class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"
          :class="prioClass(p)"
        >
          <span class="h-1.5 w-1.5 rounded-full" :class="prioDot(p)" />
          {{ prioLabel(p) }} · {{ (summary.priority && summary.priority[p]) || 0 }}
        </span>
      </div>

      <!-- Sales-manager cards -->
      <div>
        <div class="lcs-section-label mb-2">{{ __('Responsibility per sales manager') }}</div>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <button
            v-for="m in managers"
            :key="m.code"
            class="rounded-xl border bg-white p-4 text-left transition hover:border-lcs-primary hover:shadow-sm"
            :class="manager === m.code ? 'border-lcs-primary ring-1 ring-lcs-primary/30' : ''"
            @click="manager = manager === m.code ? '' : m.code"
          >
            <div class="flex items-center gap-2">
              <span class="flex h-9 w-9 items-center justify-center rounded-full bg-lcs-primary/10 text-xs font-bold text-lcs-primary">{{ m.code }}</span>
              <div class="min-w-0">
                <div class="truncate text-sm font-semibold text-gray-900">{{ m.user_name || m.code }}</div>
                <div class="text-[11px] text-gray-400">{{ m.territories }} {{ __('territories') }} · {{ m.countries }} {{ __('countries') }}</div>
              </div>
            </div>
            <!-- priority mini-bar -->
            <div class="mt-3 flex h-1.5 overflow-hidden rounded-full bg-gray-100">
              <div v-for="p in PRIORITIES" :key="p" :class="prioDot(p)" :style="{ width: barWidth(m, p) }" />
            </div>
            <!-- live work -->
            <div class="mt-3 grid grid-cols-3 gap-1 text-center">
              <div class="rounded-lg bg-amber-50 py-1.5">
                <div class="text-sm font-bold tabular-nums text-amber-700">{{ m.leads }}</div>
                <div class="text-[10px] uppercase tracking-wide text-amber-600/80">{{ __('Leads') }}</div>
              </div>
              <div class="rounded-lg bg-blue-50 py-1.5">
                <div class="text-sm font-bold tabular-nums text-blue-700">{{ m.deals }}</div>
                <div class="text-[10px] uppercase tracking-wide text-blue-600/80">{{ __('Offers') }}</div>
              </div>
              <div class="rounded-lg bg-green-50 py-1.5">
                <div class="text-sm font-bold tabular-nums text-green-700">{{ m.projects }}</div>
                <div class="text-[10px] uppercase tracking-wide text-green-600/80">{{ __('Projects') }}</div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-2">
        <FormControl type="text" v-model="search" :placeholder="__('Search territory / country...')" class="w-64">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-400" /></template>
        </FormControl>
        <FormControl type="select" :options="regionOptions" v-model="region" class="w-48">
          <template #prefix><span class="text-xs text-gray-400">{{ __('Region') }}:</span></template>
        </FormControl>
        <Button v-if="manager || region || search" variant="ghost" :label="__('Clear')" iconLeft="x" @click="clearFilters" />
        <span class="ml-auto text-xs text-gray-400">{{ filteredRows.length }} {{ __('of') }} {{ territories.length }}</span>
      </div>

      <!-- Territory table -->
      <div class="overflow-x-auto rounded-xl border bg-white">
        <div class="border-b bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          {{ __('Territory assignment') }}
        </div>
        <div class="overflow-x-auto"><table class="w-full min-w-[40rem] text-sm">
          <thead class="bg-gray-50/60">
            <tr class="border-b text-left text-[11px] font-medium uppercase text-gray-500">
              <th
                v-for="c in COLUMNS"
                :key="c.key"
                class="cursor-pointer select-none px-3 py-2 transition hover:text-gray-900"
                :class="c.right ? 'text-right' : ''"
                @click="toggleSort(c.key)"
              >
                {{ __(c.label) }}
                <span v-if="sortKey === c.key" class="text-lcs-primary">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in filteredRows" :key="r.territory" class="border-b align-top hover:bg-gray-50">
              <td class="px-3 py-2.5">
                <div class="font-medium text-gray-900">{{ r.territory }}</div>
                <div v-if="r.sub_region" class="text-[11px] text-gray-400">{{ r.sub_region }}</div>
              </td>
              <td class="px-3 py-2.5 text-gray-600">{{ __(r.region) }}</td>
              <td class="px-3 py-2.5">
                <FormControl
                  v-if="canManage"
                  type="select"
                  size="sm"
                  :options="managerOptions"
                  :modelValue="r.code"
                  class="min-w-[9rem]"
                  @update:modelValue="(v) => reassign(r, v)"
                />
                <div v-else class="flex items-center gap-1.5">
                  <span class="rounded bg-lcs-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-lcs-primary">{{ r.code }}</span>
                  <span class="text-xs text-gray-700">{{ r.user_name || shortUser(r.user) || '—' }}</span>
                </div>
              </td>
              <td class="px-3 py-2.5 text-xs text-gray-500">
                <span v-if="r.deputy_code">{{ r.deputy_code }}</span>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-3 py-2.5 text-xs text-gray-600">{{ r.agent || '—' }}</td>
              <td class="px-3 py-2.5">
                <span class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium" :class="prioClass(r.priority)">
                  <span class="h-1.5 w-1.5 rounded-full" :class="prioDot(r.priority)" />{{ prioLabel(r.priority) }}
                </span>
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums text-gray-600">{{ r.country_count }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums text-gray-600">{{ r.segment_count }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="r.leads ? 'text-amber-600' : 'text-gray-300'">{{ r.leads }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="r.deals ? 'text-blue-600' : 'text-gray-300'">{{ r.deals }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="r.projects ? 'text-green-600 font-medium' : 'text-gray-300'">{{ r.projects }}</td>
            </tr>
            <tr v-if="!filteredRows.length && !board.loading">
              <td colspan="11" class="px-4 py-12 text-center text-sm text-gray-400">{{ __('No territories match the filter.') }}</td>
            </tr>
          </tbody>
        </table></div>
      </div>

      <!-- Segment responsibility matrix -->
      <div class="overflow-hidden rounded-xl border bg-white">
        <div class="border-b bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          {{ __('Segment responsibility') }}
        </div>
        <div class="overflow-x-auto"><table class="w-full min-w-[40rem] text-sm">
          <thead class="bg-gray-50/60">
            <tr class="border-b text-left text-[11px] font-medium uppercase text-gray-500">
              <th class="px-3 py-2">{{ __('Segment') }}</th>
              <th class="px-3 py-2">{{ __('Lead') }}</th>
              <th class="px-3 py-2">{{ __('Deputy') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in segments" :key="s.segment" class="border-b hover:bg-gray-50">
              <td class="px-3 py-2.5 font-medium text-gray-900">{{ s.segment }}</td>
              <td class="px-3 py-2.5"><span class="rounded bg-lcs-primary/10 px-1.5 py-0.5 text-xs font-semibold text-lcs-primary">{{ s.lead_code }}</span></td>
              <td class="px-3 py-2.5 text-gray-600">{{ s.deputy_code || '—' }}</td>
            </tr>
          </tbody>
        </table></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { createResource, call, toast, Breadcrumbs, Button, FormControl, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
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

// Reassign a territory to a different sales manager inline. The dropdown
// offers the known market-split managers (code + user); picking one saves
// code + user together and re-aggregates the board.
const managerOptions = computed(() =>
  managers.value
    .filter((m) => m.code && m.code !== '—')
    .map((m) => ({ label: `${m.code} · ${m.user_name || m.code}`, value: m.code })),
)
async function reassign(row, code) {
  if (!code || code === row.code) return
  const m = managers.value.find((x) => x.code === code)
  const prev = { code: row.code, user: row.user, user_name: row.user_name }
  // optimistic
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
    toast.error(e?.messages?.[0] || __('Could not reassign the territory.'))
  }
}

const PRIORITIES = ['Go', 'Watch', 'Maintain', 'Exit']
// German labels for the market-split priorities. Kept local instead of __()
// because Frappe's generic de.po mistranslates "Go" as "Gehen".
const PRIORITY_LABELS = { Go: 'Aktiv verfolgen', Watch: 'Beobachten', Maintain: 'Halten', Exit: 'Rückzug' }
function prioLabel(p) {
  return PRIORITY_LABELS[p] || p
}
function prioClass(p) {
  return {
    Go: 'border-green-200 bg-green-50 text-green-700',
    Watch: 'border-blue-200 bg-blue-50 text-blue-700',
    Maintain: 'border-amber-200 bg-amber-50 text-amber-700',
    Exit: 'border-gray-200 bg-gray-50 text-gray-500',
  }[p] || 'border-gray-200 bg-gray-50 text-gray-500'
}
function prioDot(p) {
  return { Go: 'bg-green-500', Watch: 'bg-blue-500', Maintain: 'bg-amber-400', Exit: 'bg-gray-400' }[p] || 'bg-gray-400'
}
function barWidth(m, p) {
  const total = PRIORITIES.reduce((s, k) => s + (m.priority?.[k] || 0), 0) || 1
  return ((m.priority?.[p] || 0) / total) * 100 + '%'
}
function shortUser(u) {
  return (u || '').split('@')[0]
}

// Filters
const search = ref('')
const region = ref('')
const manager = ref('')
const regionOptions = computed(() => [
  { label: __('All regions'), value: '' },
  ...[...new Set(territories.value.map((t) => t.region).filter(Boolean))].map((r) => ({ label: __(r), value: r })),
])
function clearFilters() {
  search.value = ''
  region.value = ''
  manager.value = ''
}

// Sortable territory table (client-side — small dataset)
const COLUMNS = [
  { key: 'territory', label: 'Territory' },
  { key: 'region', label: 'Region' },
  { key: 'code', label: 'Sales manager' },
  { key: 'deputy_code', label: 'Deputy' },
  { key: 'agent', label: 'Agent' },
  { key: 'priority', label: 'Priority' },
  { key: 'country_count', label: 'Countries', right: true },
  { key: 'segment_count', label: 'Segments', right: true },
  { key: 'leads', label: 'Leads', right: true },
  { key: 'deals', label: 'Offers', right: true },
  { key: 'projects', label: 'Projects', right: true },
]
const sortKey = ref('region')
const sortDir = ref('asc')
function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  let list = territories.value.filter((t) => {
    if (region.value && t.region !== region.value) return false
    if (manager.value && t.code !== manager.value) return false
    if (!q) return true
    return [t.territory, t.sub_region, t.user_name, t.agent, t.code]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
  const k = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...list].sort((a, b) => {
    const va = a[k], vb = b[k]
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir
    return String(va ?? '').localeCompare(String(vb ?? '')) * dir
  })
})
</script>
