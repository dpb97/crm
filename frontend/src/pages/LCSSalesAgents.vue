<!--
  LCSSalesAgents — „Verkäufer & Agenten" (Vertrieb-Nav, Unterpunkt von
  Markteinteilung).
  ============================================================
  Wer verkauft wo: je Territorium der verantwortliche Verkäufer, sein
  Stellvertreter und der Agent/JV vor Ort. Der Klickdummy führt den Punkt als
  Platzhalter („#") mit dem Hinweis „Verkäufer, Agenten und JV je Territorium —
  LCS India JV wirkt als EIN Verkäufer für Südostasien".

  Zwei Sichten auf denselben Datenstand:
    · „Nach Verkäufer" — je Person die Territorien und die Arbeitslast.
    · „Nach Agent"     — je Agent/JV die Territorien, in denen er auftritt.
  Ohne Agent geführte Territorien werden als solche ausgewiesen (nicht
  weggefiltert), damit Lücken in der Abdeckung sichtbar bleiben.

  Daten: lcs_integrations.projects.api.get_market_assignment — dieselbe API wie
  die Markteinteilung, hier nur nach Person/Agent statt nach Gebiet gebündelt.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[
          { label: 'Vertrieb' },
          { label: __('Market Assignment'), route: { name: 'LCS Market Assignment' } },
          { label: __('Sales reps & agents') },
        ]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <PpFilterBar
          v-model="view"
          v-model:search="q"
          :segments="VIEWS"
          :placeholder="__('Search rep, agent or territory') + ' …'"
        />

        <PpTableCard
          :title="view === 'agent' ? __('By agent') : __('By sales rep')"
          :shown="filtered.length"
          :total="rows.length"
        >
          <PpDataGrid v-if="filtered.length" :columns="columns" :rows="filtered" @row-click="openRow">
            <template #cell-name="{ row }">
              <span class="pp-cell-strong">{{ row.name }}</span>
              <span class="pp-cell-sub">{{ row.sub }}</span>
            </template>
            <template #cell-territories="{ row }">
              <span class="pp-cell-soft">{{ row.territories.join(' · ') }}</span>
            </template>
            <template #cell-coverage="{ row }">
              <PpPill :tone="row.coverageTone">{{ row.coverage }}</PpPill>
            </template>
            <template #cell-countries="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-leads="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value }}</span>
            </template>
            <template #cell-deals="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value }}</span>
            </template>
            <template #cell-projects="{ value }">
              <span :class="value ? 'lcssa-strong' : 'pp-cell-muted'">{{ value }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconUsers"
            :title="board.loading ? __('Loading …') : __('No sales reps or agents')"
            :hint="board.loading ? '' : (q ? __('No matches for the current filter/search.')
              : __('Sales reps and agents come from the territories in the market assignment.'))"
          />
        </PpTableCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpPill from '@/components/pp/PpPill.vue'
import IconUsers from '~icons/lucide/users'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()

const board = createResource({ url: 'lcs_integrations.projects.api.get_market_assignment', auto: true })
const territories = computed(() => board.data?.territories || [])

const VIEWS = [
  { key: 'rep', label: __('By sales rep') },
  { key: 'agent', label: __('By agent') },
]
const view = ref('rep')
const q = ref('')

/* Group the territory rows by sales rep or by agent. Both sides aggregate the
   same workload figures, so switching the view never changes the totals. */
function group(keyOf, labelOf, subOf) {
  const map = new Map()
  for (const t of territories.value) {
    const key = keyOf(t) || '—'
    let g = map.get(key)
    if (!g) {
      g = {
        id: key,
        name: labelOf(t, key),
        sub: subOf(t, key),
        territories: [],
        countries: 0,
        leads: 0,
        deals: 0,
        projects: 0,
      }
      map.set(key, g)
    }
    g.territories.push(t.territory)
    g.countries += t.country_count || 0
    g.leads += t.leads || 0
    g.deals += t.deals || 0
    g.projects += t.projects || 0
  }
  return [...map.values()].sort((a, b) => b.territories.length - a.territories.length)
}

const rows = computed(() => {
  const list = view.value === 'agent'
    ? group(
        (t) => t.agent,
        (t, key) => (key === '—' ? __('No agent') : key),
        (t, key) => (key === '—' ? __('handled directly by LCS') : __('Agent / JV')),
      )
    : group(
        (t) => t.code,
        (t, key) => t.user_name || t.user || key,
        (t, key) => (key === '—' ? __('unassigned') : key),
      )

  // Territories without an agent are a coverage gap, not a person — mark them
  // so the row reads as a gap instead of looking like just another agent.
  return list.map((g) => {
    const gap = g.id === '—'
    return {
      ...g,
      coverage: gap
        ? (view.value === 'agent' ? __('direct') : __('unassigned'))
        : `${g.territories.length} ${g.territories.length === 1 ? __('territory') : __('territories')}`,
      coverageTone: gap ? (view.value === 'agent' ? 'neutral' : 'danger') : 'success',
    }
  })
})

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  if (!needle) return rows.value
  return rows.value.filter((r) =>
    [r.name, r.sub, ...r.territories].some((v) => (v || '').toLowerCase().includes(needle)),
  )
})

const columns = computed(() => [
  { key: 'name', label: view.value === 'agent' ? __('Agent / JV') : __('Sales rep'), pin: true, width: 240 },
  { key: 'coverage', label: __('Coverage'), width: 140 },
  { key: 'territories', label: __('Territories'), width: 320 },
  { key: 'countries', label: __('Countries'), align: 'right', width: 110 },
  { key: 'leads', label: __('Leads'), align: 'right', width: 100 },
  { key: 'deals', label: __('Offers'), align: 'right', width: 100 },
  { key: 'projects', label: __('Projects'), align: 'right', width: 110 },
])

function openRow(id) {
  const r = rows.value.find((x) => x.id === id)
  if (!r) return
  inspectNode({
    title: r.name,
    badge: { label: r.coverage, tone: r.coverageTone },
    rows: [
      { label: view.value === 'agent' ? __('Agent / JV') : __('Sales rep'), value: r.sub || '—' },
      { label: __('Territories'), value: r.territories.join(', ') || '—' },
      { label: __('Countries'), value: String(r.countries) },
      { label: __('Leads'), value: String(r.leads) },
      { label: __('Offers'), value: String(r.deals) },
      { label: __('Projects'), value: String(r.projects) },
    ],
    action: {
      label: __('Open market assignment'),
      onClick: () => router.push({ name: 'LCS Market Assignment' }),
    },
  })
}
onBeforeUnmount(() => inspectNode(null))
</script>

<style scoped>
.lcssa-strong { font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary, #008b8b); }
</style>
