<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Forecasting'), route: { name: 'LCS Forecasting' } }]" />
    </template>
    <template #right-header>
      <!-- Period selector — H7: Flexibility -->
      <div class="flex items-center gap-2">
        <div class="flex rounded-lg border bg-white p-0.5">
          <button
            v-for="p in periodOptions"
            :key="p.value"
            class="rounded-md px-3 py-1 text-xs font-medium transition"
            :class="period === p.value ? 'bg-lcs-primary text-white' : 'text-gray-600 hover:bg-gray-50'"
            @click="period = p.value"
          >
            {{ __(p.label) }}
          </button>
        </div>
        <Tooltip :text="__('Toggle: show only my projects')">
          <div class="flex rounded-lg border bg-white p-0.5">
            <button
              class="rounded-md px-3 py-1 text-xs font-medium transition"
              :class="!onlyMine ? 'bg-lcs-primary text-white' : 'text-gray-600 hover:bg-gray-50'"
              @click="onlyMine = false"
            >
              {{ __('All') }}
            </button>
            <button
              class="rounded-md px-3 py-1 text-xs font-medium transition"
              :class="onlyMine ? 'bg-lcs-primary text-white' : 'text-gray-600 hover:bg-gray-50'"
              @click="onlyMine = true"
            >
              {{ __('My Projects') }}
            </button>
          </div>
        </Tooltip>
      </div>
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto p-5">
    <!-- Loading -->
    <div v-if="forecast.loading" class="space-y-4">
      <div class="h-48 animate-pulse rounded-xl border bg-gray-50" />
      <div class="h-72 animate-pulse rounded-xl border bg-gray-50" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!filteredBuckets.length" class="flex flex-col items-center rounded-xl border border-dashed border-gray-200 py-16">
      <FeatherIcon name="trending-up" class="h-10 w-10 text-gray-300" />
      <h3 class="mt-4 text-sm font-medium text-gray-900">{{ __('No forecast data') }}</h3>
      <p class="mt-1 max-w-sm text-center text-sm text-gray-500">
        {{ __('Set expected close dates on projects to see the forecast.') }}
      </p>
    </div>

    <div v-else class="space-y-6">
      <!-- Summary row -->
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KpiCard :label="__('Pipeline Total')" :value="formatCurrency(summary.total)" icon="trending-up" color="blue" />
        <KpiCard :label="__('Weighted Forecast')" :value="formatCurrency(summary.weighted)" icon="target" color="green" :sublabel="__('probability-adjusted')" />
        <KpiCard :label="__('Projects')" :value="summary.count" icon="folder" color="gray" :sublabel="__('active')" />
        <KpiCard :label="__('Next Close')" :value="summary.nextClose" icon="calendar" color="amber" :sublabel="summary.nextCloseLabel" />
      </div>

      <!-- Forecast bar chart -->
      <div class="rounded-xl border bg-white p-5">
        <h3 class="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <FeatherIcon name="bar-chart-2" class="h-3.5 w-3.5" />
          {{ __('Weighted Revenue Forecast') }}
          <span class="ml-2 font-normal normal-case text-gray-400">
            ({{ __(periodLabel) }}, {{ filteredBuckets.length }} {{ __('periods') }})
          </span>
        </h3>

        <!-- Chart -->
        <div class="relative h-64">
          <div class="flex h-full items-end gap-2">
            <div
              v-for="(bucket, idx) in filteredBuckets"
              :key="bucket.period"
              class="group relative flex flex-1 flex-col justify-end"
            >
              <!-- Tooltip on hover — H3: Feedback -->
              <div class="absolute -top-14 left-1/2 z-10 hidden -translate-x-1/2 whitespace-nowrap rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-lg group-hover:block">
                <div class="font-semibold">{{ bucket.period }}</div>
                <div class="mt-1">{{ __('Total') }}: {{ formatCurrency(bucket.total_value) }}</div>
                <div class="text-green-300">{{ __('Weighted') }}: {{ formatCurrency(bucket.weighted_value) }}</div>
                <div class="text-gray-300">{{ bucket.projects.length }} {{ __('projects') }}</div>
              </div>
              <!-- Total value (light background) -->
              <div
                class="w-full rounded-t-lg bg-gray-200 transition"
                :style="{ height: `${(bucket.total_value / chartMax) * 100}%` }"
              >
                <!-- Weighted value (darker overlay) -->
                <div
                  class="w-full rounded-t-lg bg-lcs-primary transition"
                  :style="{ height: `${(bucket.weighted_value / (bucket.total_value || 1)) * 100}%` }"
                />
              </div>
              <!-- Period label -->
              <div class="mt-2 text-center text-[10px] font-medium text-gray-500">{{ formatPeriod(bucket.period) }}</div>
            </div>
          </div>
        </div>
        <!-- Legend -->
        <div class="mt-4 flex justify-end gap-4 text-xs text-gray-500">
          <span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-gray-200" /> {{ __('Total pipeline') }}</span>
          <span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-lcs-primary" /> {{ __('Weighted (prob. adjusted)') }}</span>
        </div>
      </div>

      <!-- Top Opportunities table -->
      <div class="rounded-xl border bg-white">
        <div class="border-b px-5 py-3">
          <h3 class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
            <FeatherIcon name="zap" class="h-3.5 w-3.5" />
            {{ __('Top Weighted Opportunities') }}
          </h3>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
              <th class="px-4 py-2">{{ __('Project') }}</th>
              <th class="px-4 py-2">{{ __('Phase') }}</th>
              <th class="px-4 py-2 text-right">{{ __('Value') }}</th>
              <th class="px-4 py-2 text-right">{{ __('Prob.') }}</th>
              <th class="px-4 py-2 text-right">{{ __('Weighted') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in topOpportunities"
              :key="p.name"
              class="cursor-pointer border-b hover:bg-gray-50"
              @click="$router.push({ name: 'LCS Project', params: { id: p.name } })"
            >
              <td class="px-4 py-2.5">
                <div class="font-medium text-gray-900">{{ p.project_name }}</div>
                <div class="text-xs text-gray-400">{{ p.project_number }} • {{ p.project_type }}</div>
              </td>
              <td class="px-4 py-2.5 text-gray-600">{{ __(p.phase) }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums text-gray-700">{{ formatCurrency(p.value) }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums" :class="probabilityClass(p.probability)">{{ Math.round(p.probability || 0) }}%</td>
              <td class="px-4 py-2.5 text-right tabular-nums font-semibold text-lcs-primary">{{ formatCurrency(p.weighted) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Source analytics donut -->
      <div v-if="sourceData.length" class="rounded-xl border bg-white p-5">
        <h3 class="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <FeatherIcon name="git-branch" class="h-3.5 w-3.5" />
          {{ __('Pipeline by Source Channel') }}
        </h3>
        <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <!-- Donut chart -->
          <div class="flex items-center justify-center">
            <svg viewBox="0 0 200 200" class="h-44 w-44">
              <circle cx="100" cy="100" r="75" fill="none" stroke="#f3f4f6" stroke-width="28" />
              <circle
                v-for="seg in sourceSegments"
                :key="seg.source"
                cx="100"
                cy="100"
                r="75"
                fill="none"
                :stroke="seg.color"
                stroke-width="28"
                :stroke-dasharray="`${seg.arc} ${circumference - seg.arc}`"
                :stroke-dashoffset="-seg.offset"
              />
              <text x="100" y="94" text-anchor="middle" class="fill-gray-900 text-lg font-bold">
                {{ formatCurrency(sourceTotal, true) }}
              </text>
              <text x="100" y="112" text-anchor="middle" class="fill-gray-400 text-[10px]">
                {{ __('Total') }}
              </text>
            </svg>
          </div>
          <!-- Source breakdown -->
          <div class="space-y-2">
            <div v-for="seg in sourceSegments" :key="'row-' + seg.source" class="flex items-center justify-between rounded-lg bg-gray-50 p-2.5">
              <div class="flex items-center gap-2">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: seg.color }" />
                <span class="text-sm font-medium text-gray-700">{{ seg.source || __('Unknown') }}</span>
              </div>
              <div class="text-right">
                <div class="text-sm font-semibold tabular-nums text-gray-900">{{ formatCurrency(seg.value || 0) }}</div>
                <div class="text-[10px] text-gray-500">{{ seg.count }} {{ __('proj.') }} • {{ seg.percentage }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource, Breadcrumbs, Tooltip, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { sessionStore } from '@/stores/session'

// Inline KPI card
const KpiCard = {
  props: ['label', 'value', 'icon', 'color', 'sublabel'],
  template: `
    <div class="rounded-xl border bg-white p-4 transition hover:shadow-sm">
      <div class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">
        <span v-if="icon" class="inline-flex h-3.5 w-3.5 items-center"><FeatherIconProxy :name="icon" /></span>
        {{ label }}
      </div>
      <div class="mt-2 text-xl font-bold tabular-nums" :class="colorClass">{{ value }}</div>
      <div v-if="sublabel" class="mt-0.5 text-xs text-gray-400">{{ sublabel }}</div>
    </div>
  `,
  computed: {
    colorClass() {
      const m = { blue: 'text-lcs-primary', green: 'text-green-600', amber: 'text-amber-600', gray: 'text-gray-900' }
      return m[this.color] || m.gray
    },
  },
  components: { FeatherIconProxy: FeatherIcon },
}

const session = sessionStore()

const period = ref('month')
const onlyMine = ref(false)

const periodOptions = [
  { label: 'Month', value: 'month' },
  { label: 'Quarter', value: 'quarter' },
  { label: 'Year', value: 'year' },
]

const periodLabel = computed(() => {
  const m = { month: 'Monthly', quarter: 'Quarterly', year: 'Yearly' }
  return m[period.value] || 'Monthly'
})

const forecast = createResource({
  url: 'lcs_integrations.projects.api.get_forecast',
  params: { period: period.value, months_ahead: 18 },
  auto: true,
})

watch(period, () => { forecast.update({ params: { period: period.value, months_ahead: 18 } }); forecast.reload() })

const sourceResource = createResource({
  url: 'lcs_integrations.projects.api.get_source_analytics',
  auto: true,
})

// Filter buckets by user if onlyMine
const filteredBuckets = computed(() => {
  const buckets = forecast.data || []
  if (!onlyMine.value) return buckets
  return buckets.map(b => {
    const mine = b.projects.filter(p => p.salesperson === session.user)
    return mine.length
      ? { ...b, projects: mine, total_value: mine.reduce((s,p) => s+(p.value||0),0), weighted_value: mine.reduce((s,p) => s+(p.weighted||0),0) }
      : null
  }).filter(Boolean)
})

const chartMax = computed(() => {
  const max = Math.max(...filteredBuckets.value.map(b => b.total_value || 0), 1)
  return max * 1.1
})

const summary = computed(() => {
  const buckets = filteredBuckets.value
  const total = buckets.reduce((s, b) => s + (b.total_value || 0), 0)
  const weighted = buckets.reduce((s, b) => s + (b.weighted_value || 0), 0)
  const count = buckets.reduce((s, b) => s + b.projects.length, 0)
  const next = buckets[0]
  return {
    total,
    weighted,
    count,
    nextClose: next ? formatPeriod(next.period) : '—',
    nextCloseLabel: next ? `${next.projects.length} ${__('projects')}` : '',
  }
})

const topOpportunities = computed(() => {
  const all = []
  filteredBuckets.value.forEach(b => all.push(...b.projects))
  return all.sort((a, b) => (b.weighted || 0) - (a.weighted || 0)).slice(0, 8)
})

// Source analytics
const sourceData = computed(() => sourceResource.data || [])
const sourceTotal = computed(() => sourceData.value.reduce((s, r) => s + (r.value || 0), 0))
const circumference = 2 * Math.PI * 75

const sourceColorMap = {
  Direct: '#1E78C2', Referral: '#10b981', Website: '#0ea5e9', 'Trade Fair': '#f59e0b',
  Partner: '#a855f7', 'Email Campaign': '#ec4899', 'Cold Call': '#6b7280',
  'Existing Customer': '#16a34a', Other: '#94a3b8',
}

const sourceSegments = computed(() => {
  const total = sourceData.value.reduce((s, r) => s + (r.count || 0), 0) || 1
  let offset = 0
  return sourceData.value
    .sort((a, b) => (b.value || 0) - (a.value || 0))
    .map(r => {
      const arc = (r.count / total) * circumference
      const percentage = Math.round((r.count / total) * 100)
      const seg = { source: r.source, count: r.count, value: r.value || 0, color: sourceColorMap[r.source] || '#94a3b8', arc, offset, percentage }
      offset += arc
      return seg
    })
})

function probabilityClass(val) {
  if (val >= 70) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}

function formatCurrency(val, compact = false) {
  const opts = { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }
  if (compact || val >= 1000000) {
    opts.notation = 'compact'
    opts.maximumFractionDigits = 1
  }
  return new Intl.NumberFormat('de-DE', opts).format(val || 0)
}

function formatPeriod(key) {
  if (!key) return ''
  if (key.includes('Q')) return key // 2026-Q2
  if (/^\d{4}$/.test(key)) return key // 2026
  // 2026-04 → Apr 2026
  const [year, month] = key.split('-')
  const date = new Date(parseInt(year), parseInt(month) - 1, 1)
  return new Intl.DateTimeFormat('de-DE', { month: 'short', year: 'numeric' }).format(date)
}
</script>
