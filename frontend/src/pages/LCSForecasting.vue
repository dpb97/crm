<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Forecasting'), route: { name: 'LCS Forecasting' } }]" />
    </template>
    <template #right-header>
      <!-- Period selector — H7: Flexibility -->
      <div class="lcs-fc-controls flex items-center gap-2">
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

  <div class="lcsfc flex-1 overflow-y-auto">
    <div class="lcsfc-inner">
      <PpPageHead
        :title="__('Forecasting')"
        :subtitle="__('Weighted revenue outlook across the pipeline')"
      />

      <!-- Access denied state — admin profile hides this page -->
      <div v-if="accessDenied" class="lcsfc-denied">
        <FeatherIcon name="lock" class="lcsfc-denied-ico" />
        <h3 class="lcsfc-denied-title">{{ __('Forecasting is not available for your role') }}</h3>
        <p class="lcsfc-denied-text">
          {{ __('Your access profile does not include forecasting. Contact your administrator to request access.') }}
        </p>
      </div>

      <!-- Loading -->
      <div v-else-if="forecast.loading" class="lcsfc-skel">
        <div class="lcsfc-skel-box" style="height: 12rem" />
        <div class="lcsfc-skel-box" style="height: 18rem" />
      </div>

      <!-- Empty state -->
      <PpEmptyState
        v-else-if="!filteredBuckets.length"
        :icon="IconTrendingUp"
        :title="__('No forecast data')"
        :hint="__('Set expected close dates on projects to see the forecast.')"
      />

      <div v-else class="lcs-fc-body flex flex-col gap-6">
        <!-- Summary row -->
        <div class="lcsfc-kpis">
          <PpStatTile :label="__('Pipeline Total')" :value="formatCurrency(summary.total)" :hint="__('open pipeline')" />
          <PpStatTile :label="__('Weighted Forecast')" :value="formatCurrency(summary.weighted)" :hint="__('probability-adjusted')" />
          <PpStatTile :label="__('Projects')" :value="String(summary.count)" :hint="__('active')" />
          <PpStatTile :label="__('Next Close')" :value="summary.nextClose" :hint="summary.nextCloseLabel" />
        </div>

        <!-- Forecast bar chart -->
        <div class="lcs-fc-chart lcsfc-card">
          <h3 class="lcsfc-card-title">
            <FeatherIcon name="bar-chart-2" class="h-3.5 w-3.5" />
            {{ __('Weighted Revenue Forecast') }}
            <span class="lcsfc-card-title-sub">({{ __(periodLabel) }}, {{ filteredBuckets.length }} {{ __('periods') }})</span>
          </h3>

          <!-- Chart -->
          <div class="lcs-fc-chart__plot relative h-64">
            <div class="flex h-full items-end gap-2">
              <div
                v-for="(bucket, idx) in filteredBuckets"
                :key="bucket.period"
                class="group relative flex flex-1 flex-col justify-end rounded focus:outline-none"
                role="img"
                tabindex="0"
                :aria-label="`${formatPeriod(bucket.period)}: ${bucket.projects.length} ${__('projects')}, ${formatCurrency(bucket.total_value)} ${__('pipeline')}, ${formatCurrency(bucket.weighted_value)} ${__('weighted')}`"
              >
                <!-- Tooltip on hover — H3: Feedback -->
                <div class="lcsfc-tip group-hover:block">
                  <div class="font-semibold">{{ bucket.period }}</div>
                  <div class="mt-1">{{ __('Total') }}: {{ formatCurrency(bucket.total_value) }}</div>
                  <div class="lcsfc-tip-hi">{{ __('Weighted') }}: {{ formatCurrency(bucket.weighted_value) }}</div>
                  <div class="lcsfc-tip-mut">{{ bucket.projects.length }} {{ __('projects') }}</div>
                </div>
                <!-- Total value (light background) -->
                <div class="lcsfc-bar-bg" :style="{ height: `${(bucket.total_value / chartMax) * 100}%` }">
                  <!-- Weighted value (brand overlay) -->
                  <div class="lcsfc-bar-fill" :style="{ height: `${(bucket.weighted_value / (bucket.total_value || 1)) * 100}%` }" />
                </div>
                <!-- Period label -->
                <div class="lcsfc-bar-label">{{ formatPeriod(bucket.period) }}</div>
              </div>
            </div>
          </div>
          <!-- Legend -->
          <div class="lcsfc-legend">
            <span><i class="lcsfc-sw lcsfc-sw--bg" /> {{ __('Total pipeline') }}</span>
            <span><i class="lcsfc-sw lcsfc-sw--fill" /> {{ __('Weighted (prob. adjusted)') }}</span>
          </div>
        </div>

        <!-- Top Opportunities table -->
        <div class="lcsfc-card lcsfc-card--flush">
          <div class="lcsfc-card-head">
            <h3 class="lcsfc-card-title">
              <FeatherIcon name="zap" class="h-3.5 w-3.5" />
              {{ __('Top Weighted Opportunities') }}
            </h3>
          </div>
          <div class="overflow-x-auto"><table class="lcsfc-table w-full min-w-[40rem] text-sm">
            <thead>
              <tr class="lcsfc-thead text-left text-xs font-medium uppercase">
                <th>{{ __('Project') }}</th>
                <th>{{ __('Phase') }}</th>
                <th>{{ __('Responsible') }}</th>
                <th class="text-right">{{ __('Value') }}</th>
                <th class="text-right">{{ __('Prob.') }}</th>
                <th class="text-right">{{ __('Weighted') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in topOpportunities"
                :key="p.name"
                class="lcsfc-row cursor-pointer"
                @click="$router.push({ name: 'LCS Project', params: { id: p.name } })"
              >
                <td>
                  <div class="lcsfc-proj-name">{{ p.project_name }}</div>
                  <div class="lcsfc-proj-meta">{{ p.project_number }} • {{ p.project_type }}</div>
                </td>
                <td class="lcsfc-td-mut">{{ __(p.phase) }}</td>
                <td class="lcsfc-td-mut">{{ shortUser(p.salesperson) }}</td>
                <td class="text-right tabular-nums lcsfc-td-num">{{ formatCurrency(p.value) }}</td>
                <td class="text-right tabular-nums" :class="probabilityClass(p.probability)">{{ Math.round(p.probability || 0) }}%</td>
                <td class="text-right tabular-nums lcsfc-td-strong">{{ formatCurrency(p.weighted) }}</td>
              </tr>
            </tbody>
          </table></div>
        </div>

        <!-- Source analytics donut -->
        <div v-if="sourceData.length" class="lcsfc-card">
          <h3 class="lcsfc-card-title">
            <FeatherIcon name="git-branch" class="h-3.5 w-3.5" />
            {{ __('Pipeline by Source Channel') }}
          </h3>
          <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <!-- Donut chart -->
            <div class="flex items-center justify-center">
              <svg viewBox="0 0 200 200" class="h-44 w-44">
                <circle class="lcsfc-donut-track" cx="100" cy="100" r="75" fill="none" stroke-width="28" />
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
                <text x="100" y="94" text-anchor="middle" class="lcsfc-donut-total">
                  {{ formatCurrency(sourceTotal, true) }}
                </text>
                <text x="100" y="112" text-anchor="middle" class="lcsfc-donut-cap">
                  {{ __('Total') }}
                </text>
              </svg>
            </div>
            <!-- Source breakdown -->
            <div class="space-y-2">
              <div v-for="seg in sourceSegments" :key="'row-' + seg.source" class="lcsfc-src-row">
                <div class="flex items-center gap-2">
                  <span class="lcsfc-src-dot" :style="{ backgroundColor: seg.color }" />
                  <span class="lcsfc-src-name">{{ seg.source || __('Unknown') }}</span>
                </div>
                <div class="text-right">
                  <div class="lcsfc-src-val">{{ formatCurrency(seg.value || 0) }}</div>
                  <div class="lcsfc-src-meta">{{ seg.count }} {{ __('proj.') }} • {{ seg.percentage }}%</div>
                </div>
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
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconTrendingUp from '~icons/lucide/trending-up'
import { sessionStore } from '@/stores/session'
import { useUserPreferences } from '@/composables/useUserPreferences'

const session = sessionStore()
const userPrefs = useUserPreferences()

const period = ref(userPrefs.state.prefs.default_period_forecasting || 'month')
const onlyMine = ref(!!userPrefs.state.prefs.default_show_only_mine)

const accessDenied = computed(() => userPrefs.state.accessProfile?.hide_forecasting)

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

// Diverging Quellen-Palette (unterscheidbare Datentoene, bewusst als Hex):
// die Werte werden als SVG-:stroke-Attribut des Donut gesetzt -> var() loest
// dort NICHT auf. 'Direct' ist der Marken-Ton = Brand-Cyan (SSOT: pp-tokens
// --pp-brand-primary / --pp-brand-700 = #008B8B); vormals Fremd-Blau.
const sourceColorMap = {
  Direct: '#008B8B', Referral: '#10b981', Website: '#0ea5e9', 'Trade Fair': '#f59e0b',
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

function shortUser(u) {
  return (u || '').split('@')[0] || '—'
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

<style scoped>
/* ---- Pilanda design system (token-only) ------------------------------- */
.lcsfc { background: var(--pp-bg-base); }
.lcsfc-inner { padding: var(--pp-space-5) var(--pp-space-5) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.lcsfc-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

/* Access-denied (warning-toned card) */
.lcsfc-denied { display: flex; flex-direction: column; align-items: center; text-align: center;
  padding: var(--pp-space-12) var(--pp-space-5); border-radius: var(--pp-radius-ui);
  border: 1px dashed color-mix(in oklab, var(--pp-state-warning) 35%, transparent);
  background: color-mix(in oklab, var(--pp-state-warning) 10%, transparent); }
.lcsfc-denied-ico { width: 40px; height: 40px; color: var(--pp-state-warning); }
.lcsfc-denied-title { margin: var(--pp-space-4) 0 0; font-size: var(--pp-fs-14);
  font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.lcsfc-denied-text { margin: var(--pp-space-1) 0 0; max-width: 24rem; font-size: var(--pp-fs-14);
  color: var(--pp-text-secondary); }

/* Skeleton */
.lcsfc-skel { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.lcsfc-skel-box { border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-border-subtle);
  background: var(--pp-bg-sunken); animation: lcsfc-pulse 1.4s ease-in-out infinite; }
@keyframes lcsfc-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Cards */
.lcsfc-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-5); }
.lcsfc-card--flush { padding: 0; }
.lcsfc-card-head { padding: var(--pp-space-3) var(--pp-space-5); border-bottom: 1px solid var(--pp-border-subtle); }
.lcsfc-card-title { margin: 0 0 var(--pp-space-4); display: flex; align-items: center; gap: var(--pp-space-2);
  font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.lcsfc-card--flush .lcsfc-card-title { margin: 0; }
.lcsfc-card-title-sub { margin-left: var(--pp-space-2); font-weight: var(--pp-weight-regular);
  text-transform: none; letter-spacing: 0; color: var(--pp-text-tertiary); }

/* Bar chart */
.lcsfc-bar-bg { width: 100%; border-radius: var(--pp-radius-ui) var(--pp-radius-ui) 0 0;
  background: var(--pp-bg-sunken); transition: height var(--pp-duration-base) var(--pp-ease-standard); }
.lcsfc-bar-fill { width: 100%; border-radius: var(--pp-radius-ui) var(--pp-radius-ui) 0 0;
  background: var(--pp-brand-primary); transition: height var(--pp-duration-base) var(--pp-ease-standard); }
.lcsfc-bar-label { margin-top: var(--pp-space-2); text-align: center; font-size: 10px;
  font-weight: var(--pp-weight-medium); color: var(--pp-text-tertiary); }
.lcsfc-tip { position: absolute; top: -3.5rem; left: 50%; z-index: 10; display: none;
  transform: translateX(-50%); white-space: nowrap; border-radius: var(--pp-radius-ui);
  padding: var(--pp-space-2) var(--pp-space-3); font-size: var(--pp-fs-12);
  background: var(--pp-text-primary); color: var(--pp-bg-surface); box-shadow: var(--pp-shadow-lg); }
.lcsfc-tip-hi { color: color-mix(in oklab, var(--pp-state-success) 60%, white); }
.lcsfc-tip-mut { opacity: 0.7; }
.lcsfc-legend { margin-top: var(--pp-space-4); display: flex; justify-content: flex-end; gap: var(--pp-space-4);
  font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.lcsfc-legend span { display: inline-flex; align-items: center; gap: 6px; }
.lcsfc-sw { width: 12px; height: 12px; border-radius: var(--pp-radius-xs); }
.lcsfc-sw--bg { background: var(--pp-bg-sunken); }
.lcsfc-sw--fill { background: var(--pp-brand-primary); }

/* Top opportunities table */
.lcsfc-table th { padding: var(--pp-space-2) var(--pp-space-4); }
.lcsfc-table td { padding: 10px var(--pp-space-4); }
.lcsfc-thead { border-bottom: 1px solid var(--pp-border-subtle); background: var(--pp-bg-sunken);
  color: var(--pp-text-tertiary); }
.lcsfc-row { border-bottom: 1px solid var(--pp-border-subtle); }
.lcsfc-row:hover { background: var(--pp-bg-hover); }
.lcsfc-proj-name { font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.lcsfc-proj-meta { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.lcsfc-td-mut { color: var(--pp-text-secondary); }
.lcsfc-td-num { color: var(--pp-text-primary); }
.lcsfc-td-strong { font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary); }

/* Donut + source breakdown */
.lcsfc-donut-track { stroke: var(--pp-bg-sunken); }
.lcsfc-donut-total { fill: var(--pp-text-primary); font-size: 18px; font-weight: var(--pp-weight-bold); }
.lcsfc-donut-cap { fill: var(--pp-text-tertiary); font-size: 10px; }
.lcsfc-src-row { display: flex; align-items: center; justify-content: space-between;
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-sunken); padding: 10px; }
.lcsfc-src-dot { width: 12px; height: 12px; border-radius: var(--pp-radius-full); flex-shrink: 0; }
.lcsfc-src-name { font-size: var(--pp-fs-14); font-weight: var(--pp-weight-medium); color: var(--pp-text-secondary); }
.lcsfc-src-val { font-size: var(--pp-fs-14); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); font-variant-numeric: tabular-nums; }
.lcsfc-src-meta { font-size: 10px; color: var(--pp-text-tertiary); }

@media (max-width: 900px) { .lcsfc-kpis { grid-template-columns: repeat(2, 1fr); } }

/*
 * Mobile fixes (390px), CSS-only — no logic change. Spacing via --pp tokens.
 * 1) Header period/scope segmented controls ran off the right edge: let the
 *    control cluster scroll horizontally with a visible affordance instead of
 *    overflowing the viewport. Each control group keeps its size (no squish).
 * 2) The bar chart dominated the fold while reading near-empty. Below 480px
 *    shrink it and move it below the concrete numbers (KPIs + Top Weighted
 *    Opportunities table) via flex order, so actionable data comes first.
 */
@media (max-width: 480px) {
  .lcs-fc-controls {
    max-width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    padding-bottom: var(--pp-space-1);
  }
  .lcs-fc-controls > * {
    flex: 0 0 auto;
  }
  .lcs-fc-chart {
    order: 10; /* push the chart below the KPI row + opportunities table */
  }
  .lcs-fc-chart__plot {
    height: 12rem; /* was h-64 (16rem) — reclaim above-the-fold space */
  }
}
</style>
