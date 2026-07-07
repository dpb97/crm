<!--
  LCSSalesMeeting
  ===============
  Sales-meeting board mirroring the LCS Excel protocol ("Angebote in
  Bearbeitung"): one row per active opportunity with PL/PN, last comment,
  responsible (Wer), next action + due (KW), status, chance %, value.
  Data from lcs_integrations.projects.api.get_sales_meeting_data.
-->

<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Sales Meeting'), route: { name: 'LCS Sales Meeting' } }]" />
    </template>
    <template #right-header>
      <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="board.reload()" :loading="board.loading" />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto p-5">
    <div class="space-y-4">
      <!-- KPI row -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div class="rounded-xl border bg-white p-4">
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Pipeline total') }}</div>
          <div class="mt-1 text-xl font-bold text-lcs-primary tabular-nums">{{ money(summary.total) }}</div>
        </div>
        <div class="rounded-xl border bg-white p-4">
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Weighted') }}</div>
          <div class="mt-1 text-xl font-bold text-green-600 tabular-nums">{{ money(summary.weighted) }}</div>
        </div>
        <div class="rounded-xl border bg-white p-4">
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Opportunities') }}</div>
          <div class="mt-1 text-xl font-bold text-gray-900 tabular-nums">{{ summary.count }}</div>
        </div>
        <div class="rounded-xl border bg-white p-4">
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Actions due (7d)') }}</div>
          <div class="mt-1 text-xl font-bold tabular-nums" :class="summary.due_actions ? 'text-amber-600' : 'text-gray-900'">{{ summary.due_actions }}</div>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-2">
        <FormControl type="text" v-model="search" :placeholder="__('Search...')" class="w-56">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-400" /></template>
        </FormControl>
        <FormControl type="select" :options="personOptions" v-model="person" class="w-52">
          <template #prefix><span class="text-xs text-gray-400">{{ __('Responsible') }}:</span></template>
        </FormControl>
        <span class="ml-auto text-xs text-gray-400">{{ filteredRows.length }} {{ __('of') }} {{ rows.length }}</span>
      </div>

      <!-- Important across entities (star-flagged) -->
      <div v-if="important.length" class="overflow-hidden rounded-xl border bg-white">
        <div class="border-b bg-amber-50/60 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-amber-700">
          <FeatherIcon name="star" class="mr-1 inline h-3.5 w-3.5 text-amber-400" /> {{ __('Marked important') }}
        </div>
        <div class="divide-y">
          <div
            v-for="it in important"
            :key="it.entity + it.name"
            class="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-amber-50/40"
            @click="openItem(it)"
          >
            <span class="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase" :class="entityClass(it.entity)">{{ entityLabel(it.entity) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-gray-900">{{ it.label }}</p>
              <p class="truncate text-xs text-gray-400">{{ it.sub }}<span v-if="it.person"> · {{ shortUser(it.person) }}</span></p>
            </div>
            <span class="shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] text-blue-700">{{ __(it.status) }}</span>
            <span v-if="it.value" class="shrink-0 text-sm font-medium tabular-nums text-gray-800">{{ money(it.value) }}</span>
          </div>
        </div>
      </div>

      <!-- Meeting board -->
      <div class="overflow-x-auto rounded-xl border bg-white">
        <div class="border-b bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          {{ __('Offers in progress') }}
        </div>
        <div class="overflow-x-auto"><table class="w-full min-w-[40rem] text-sm">
          <thead>
            <tr class="border-b bg-gray-50/60 text-left text-[11px] font-medium uppercase text-gray-500">
              <th class="px-3 py-2"></th>
              <th class="px-3 py-2">{{ __('PL/PN') }}</th>
              <th class="px-3 py-2">{{ __('Project') }}</th>
              <th class="px-3 py-2">{{ __('Responsible') }}</th>
              <th class="px-3 py-2">{{ __('Status') }}</th>
              <th class="px-3 py-2">{{ __('Progress') }}</th>
              <th class="px-3 py-2 text-right">{{ __('Win chance') }}</th>
              <th class="px-3 py-2 text-right">{{ __('Value') }}</th>
              <th class="px-3 py-2">{{ __('Last comment') }}</th>
              <th class="px-3 py-2">{{ __('Next action') }}</th>
              <th class="px-3 py-2">{{ __('Due') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in filteredRows"
              :key="r.name"
              class="cursor-pointer border-b align-top hover:bg-gray-50"
              @click="$router.push({ name: 'LCS Project', params: { id: r.name } })"
            >
              <td class="px-3 py-2.5">
                <FeatherIcon v-if="r.is_important" name="star" class="h-3.5 w-3.5 text-amber-400" />
              </td>
              <td class="px-3 py-2.5 font-mono text-xs text-gray-500">{{ r.project_number }}</td>
              <td class="px-3 py-2.5">
                <div class="font-medium text-gray-900">{{ r.project_name }}</div>
                <div class="text-[11px] text-gray-400">{{ r.type }} · {{ r.country }}</div>
              </td>
              <td class="px-3 py-2.5 text-xs text-gray-600">{{ shortUser(r.salesperson) }}</td>
              <td class="px-3 py-2.5">
                <span class="rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700">{{ __(r.phase) }}</span>
              </td>
              <td class="px-3 py-2.5">
                <div class="flex items-center gap-2">
                  <div class="h-1.5 w-20 overflow-hidden rounded-full bg-gray-100">
                    <div class="h-full rounded-full" :class="progressClass(phaseProgress(r.phase))" :style="{ width: phaseProgress(r.phase) + '%' }" />
                  </div>
                  <span class="text-[11px] tabular-nums text-gray-500">{{ phaseProgress(r.phase) }}%</span>
                </div>
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="chanceClass(r.probability)">{{ Math.round(r.probability) }}%</td>
              <td class="px-3 py-2.5 text-right font-medium tabular-nums text-gray-800">{{ money(r.value) }}</td>
              <td class="px-3 py-2.5 max-w-[18rem]">
                <span class="line-clamp-2 text-xs text-gray-600">{{ stripEmoji(r.comment) || '—' }}</span>
              </td>
              <td class="px-3 py-2.5 max-w-[12rem]">
                <span class="line-clamp-2 text-xs text-gray-700">{{ r.next_action || '—' }}</span>
              </td>
              <td class="px-3 py-2.5 whitespace-nowrap text-xs" :class="dueClass(r.due)">{{ r.kw || (r.due ? r.due : '—') }}</td>
            </tr>
            <tr v-if="!filteredRows.length && !board.loading">
              <td colspan="10" class="px-4 py-12 text-center text-sm text-gray-400">{{ __('No active opportunities.') }}</td>
            </tr>
          </tbody>
        </table></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button, FormControl, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'

const router = useRouter()
const board = createResource({
  url: 'lcs_integrations.projects.api.get_sales_meeting_data',
  auto: true,
})
const rows = computed(() => board.data?.rows || [])
const important = computed(() => board.data?.important || [])

// Progress toward the sale — how far along the funnel this opportunity is.
const STAGE_PCT = { Qualified: 20, Budget: 35, Richtpreis: 50, Offer: 65, Negotiation: 85, Won: 100, Execution: 100, Completed: 100 }
function phaseProgress(phase) {
  return STAGE_PCT[phase] ?? 10
}
function progressClass(pct) {
  if (pct >= 85) return 'bg-green-500'
  if (pct >= 50) return 'bg-lcs-secondary'
  return 'bg-amber-400'
}

const ENTITY = {
  project: { label: 'Projekt', route: 'LCS Project', param: 'id', cls: 'bg-green-50 text-green-700' },
  lead: { label: 'Lead', route: 'Lead', param: 'leadId', cls: 'bg-amber-50 text-amber-700' },
  deal: { label: 'Angebot', route: 'Deal', param: 'dealId', cls: 'bg-blue-50 text-blue-700' },
}
function entityLabel(e) { return __(ENTITY[e]?.label || e) }
function entityClass(e) { return ENTITY[e]?.cls || 'bg-gray-100 text-gray-600' }
function openItem(it) {
  const cfg = ENTITY[it.entity]
  if (cfg) router.push({ name: cfg.route, params: { [cfg.param]: it.name } })
}
const summary = computed(() => board.data?.summary || { total: 0, weighted: 0, count: 0, due_actions: 0 })

const search = ref('')
const person = ref('')
const personOptions = computed(() => [
  { label: __('All responsible'), value: '' },
  ...[...new Set(rows.value.map((r) => r.salesperson).filter(Boolean))].map((u) => ({ label: shortUser(u), value: u })),
])

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (person.value && r.salesperson !== person.value) return false
    if (!q) return true
    return [r.project_name, r.project_number, r.country, r.comment, r.next_action, r.salesperson]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
})

function money(v) {
  const n = Number(v) || 0
  if (n >= 1_000_000) return '€' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return '€' + Math.round(n / 1_000) + 'k'
  return '€' + n
}
function shortUser(u) {
  return (u || '').split('@')[0]
}
function stripEmoji(s) {
  return (s || '').replace(/📝|📋|\*\*/g, '').trim()
}
function chanceClass(p) {
  if (p >= 70) return 'text-green-600 font-semibold'
  if (p >= 40) return 'text-amber-600'
  return 'text-gray-500'
}
function dueClass(due) {
  if (!due) return 'text-gray-400'
  const d = new Date(String(due).replace(' ', 'T'))
  const days = (d.getTime() - Date.now()) / 86400000
  if (days < 0) return 'font-medium text-red-600'
  if (days <= 7) return 'font-medium text-amber-600'
  return 'text-gray-600'
}
</script>
