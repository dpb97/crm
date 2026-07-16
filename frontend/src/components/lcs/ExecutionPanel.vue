<!--
  ExecutionPanel — pulls Tasks + Time Logs + Costing from the linked
  ERPNext Project and renders them inside the LCS Project detail
  page, so users see one consolidated project view without navigating
  to /app/project/PROJ-XXXX.

  All execution data lives in ERPNext Project (single source of truth
  for execution); this is a read-mostly mirror.
-->

<template>
  <div v-if="loading" class="space-y-3">
    <div class="h-24 animate-pulse rounded-xl border bg-gray-50" />
    <div class="h-32 animate-pulse rounded-xl border bg-gray-50" />
  </div>

  <div v-else-if="!data?.linked" class="rounded-xl border border-dashed border-gray-200 p-8 text-center">
    <FeatherIcon name="briefcase" class="mx-auto h-8 w-8 text-gray-300" />
    <p class="mt-3 text-sm text-gray-500">{{ __('No ERPNext Project linked yet.') }}</p>
    <p class="mt-1 text-xs text-gray-400">
      {{ __('An ERPNext Project is auto-created when this project enters Order or Execution phase.') }}
    </p>
  </div>

  <div v-else class="space-y-5">
    <!-- KPI strip -->
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <KpiCard :label="__('Progress')" :value="data.totals.percent_complete + '%'" :tone="progressTone" icon="check-circle" />
      <KpiCard :label="__('Estimated')" :value="formatCurrency(data.totals.estimated)" tone="blue" icon="trending-up" />
      <KpiCard :label="__('Billed')" :value="formatCurrency(data.totals.billed)" tone="green" icon="dollar-sign" />
      <KpiCard :label="__('Material Cost')" :value="formatCurrency(data.totals.costing)" tone="amber" icon="package" />
    </div>

    <!-- ERPNext Project header link -->
    <div class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <FeatherIcon name="briefcase" class="h-4 w-4 text-blue-700" />
          <span class="font-mono font-semibold text-blue-900">{{ data.erpnext_project }}</span>
          <span :class="erpStatusClass" class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase">
            {{ data.erpnext_status }}
          </span>
        </div>
        <a
          :href="`/app/project/${data.erpnext_project}`"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:underline"
        >
          {{ __('Open in ERPNext') }}
          <FeatherIcon name="external-link" class="h-3 w-3" />
        </a>
      </div>
      <div v-if="data.expected_start_date || data.expected_end_date" class="mt-1 text-xs text-blue-700">
        {{ __('Planned') }}:
        <span v-if="data.expected_start_date">{{ formatDate(data.expected_start_date) }}</span>
        <span v-if="data.expected_start_date && data.expected_end_date"> → </span>
        <span v-if="data.expected_end_date">{{ formatDate(data.expected_end_date) }}</span>
      </div>
    </div>

    <!-- Tasks -->
    <section>
      <h3 class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        <FeatherIcon name="check-square" class="h-3.5 w-3.5" />
        {{ __('Tasks') }}
        <span class="rounded-full bg-gray-100 px-1.5 py-0 text-[10px] font-bold text-gray-600">
          {{ data.tasks.length }}
        </span>
      </h3>
      <div v-if="!data.tasks.length" class="rounded-lg border border-dashed border-gray-200 p-4 text-center text-xs text-gray-400">
        {{ __('No tasks yet — add some in the ERPNext Project view.') }}
      </div>
      <div v-else class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr class="border-b text-left text-xs font-medium uppercase text-gray-500">
              <th class="px-3 py-2">{{ __('Subject') }}</th>
              <th class="px-3 py-2">{{ __('Status') }}</th>
              <th class="px-3 py-2">{{ __('Priority') }}</th>
              <th class="px-3 py-2">{{ __('Due') }}</th>
              <th class="px-3 py-2 text-right">{{ __('Progress') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in data.tasks"
              :key="t.name"
              class="cursor-pointer border-b last:border-0 hover:bg-gray-50"
              @click="openTask(t.name)"
            >
              <td class="px-3 py-2 font-medium text-gray-900">{{ t.subject }}</td>
              <td class="px-3 py-2">
                <span :class="taskStatusClass(t.status)" class="rounded-full px-2 py-0.5 text-[10px] font-semibold">
                  {{ t.status }}
                </span>
              </td>
              <td class="px-3 py-2 text-gray-600">{{ t.priority || '—' }}</td>
              <td class="px-3 py-2 text-gray-600">{{ formatDate(t.exp_end_date) || '—' }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-gray-700">
                {{ t.progress != null ? Math.round(t.progress) + '%' : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Time Logs -->
    <section v-if="data.time_logs.length">
      <h3 class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        <FeatherIcon name="clock" class="h-3.5 w-3.5" />
        {{ __('Time Logs') }}
        <span class="rounded-full bg-gray-100 px-1.5 py-0 text-[10px] font-bold text-gray-600">
          {{ data.time_logs.length }}
        </span>
      </h3>
      <div class="overflow-hidden rounded-lg border bg-white">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr class="border-b text-left text-xs font-medium uppercase text-gray-500">
              <th class="px-3 py-2">{{ __('Employee') }}</th>
              <th class="px-3 py-2">{{ __('Activity') }}</th>
              <th class="px-3 py-2">{{ __('From') }}</th>
              <th class="px-3 py-2 text-right">{{ __('Hours') }}</th>
              <th class="px-3 py-2 text-right">{{ __('Cost') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in data.time_logs" :key="l.name" class="border-b last:border-0 hover:bg-gray-50">
              <td class="px-3 py-2 font-medium text-gray-900">{{ l.employee_name || l.employee || '—' }}</td>
              <td class="px-3 py-2 text-gray-600">{{ l.activity_type || '—' }}</td>
              <td class="px-3 py-2 text-xs text-gray-500">{{ formatDateTime(l.from_time) }}</td>
              <td class="px-3 py-2 text-right tabular-nums">{{ Number(l.hours || 0).toFixed(2) }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-gray-700">
                {{ formatCurrency(l.costing_amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'

const KpiCard = {
  props: ['label', 'value', 'tone', 'icon'],
  components: { FeatherIcon },
  computed: {
    classes() {
      const m = {
        green: 'border-green-200 bg-green-50 text-green-800',
        blue: 'border-blue-200 bg-blue-50 text-blue-800',
        amber: 'border-amber-200 bg-amber-50 text-amber-800',
        red: 'border-red-200 bg-red-50 text-red-800',
        gray: 'border-gray-200 bg-white text-gray-800',
      }
      return m[this.tone] || m.gray
    },
  },
  template: `
    <div class="rounded-xl border p-3" :class="classes">
      <div class="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider opacity-70">
        <FeatherIcon :name="icon" class="h-3 w-3" />
        {{ label }}
      </div>
      <div class="mt-1 text-lg font-bold tabular-nums">{{ value }}</div>
    </div>
  `,
}

const props = defineProps({ project: { type: String, required: true } })

const data = ref(null)
const loading = ref(false)

async function load() {
  if (!props.project) return
  loading.value = true
  try {
    const res = await call('lcs_integrations.projects.api.get_execution_summary', {
      project: props.project,
    })
    data.value = res.message || res
  } catch (err) {
    console.warn('execution summary failed:', err)
    data.value = { linked: false, tasks: [], time_logs: [], totals: {} }
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.project, load)

const progressTone = computed(() => {
  const p = data.value?.totals?.percent_complete || 0
  if (p >= 80) return 'green'
  if (p >= 40) return 'amber'
  return 'gray'
})

const erpStatusClass = computed(() => {
  const m = {
    Open: 'bg-blue-100 text-blue-800',
    Completed: 'bg-green-100 text-green-800',
    Cancelled: 'bg-red-100 text-red-800',
  }
  return m[data.value?.erpnext_status] || 'bg-gray-100 text-gray-700'
})

function taskStatusClass(s) {
  const m = {
    Open: 'bg-gray-100 text-gray-700',
    Working: 'bg-blue-100 text-blue-800',
    'Pending Review': 'bg-amber-100 text-amber-800',
    Overdue: 'bg-red-100 text-red-700',
    Completed: 'bg-green-100 text-green-800',
    Cancelled: 'bg-gray-100 text-gray-500',
  }
  return m[s] || 'bg-gray-100 text-gray-700'
}

function openTask(taskName) {
  window.open(`/app/task/${taskName}`, '_blank', 'noopener')
}

function formatCurrency(v) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v || 0)
}

function formatDate(d) {
  if (!d) return ''
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(d))
}

function formatDateTime(d) {
  if (!d) return ''
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(d))
}
</script>
