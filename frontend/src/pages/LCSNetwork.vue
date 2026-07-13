<!--
  LCSNetwork
  ==========
  Relationship graph: companies as hubs, their people clustered around them
  (who works with whom), and dashed edges for career history (where a person
  worked before). Click a node to open the contact / customer.
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Network'), route: { name: 'LCS Network' } }]" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-4 text-xs text-gray-500">
          <div class="flex overflow-hidden border">
            <button class="px-3 py-1 font-medium transition" :class="mode === 'people' ? 'bg-lcs-primary text-white' : 'bg-white text-gray-600 hover:bg-gray-50'" @click="mode = 'people'">{{ __('People') }}</button>
            <button class="px-3 py-1 font-medium transition" :class="mode === 'companies' ? 'bg-lcs-primary text-white' : 'bg-white text-gray-600 hover:bg-gray-50'" @click="mode = 'companies'">{{ __('Companies') }}</button>
          </div>
          <span class="flex items-center gap-1"><span class="h-0 w-6 border-t-2 border-lcs-secondary" /> {{ __('connected') }}</span>
          <span class="flex items-center gap-1"><span class="h-0 w-6 border-t-2 border-dashed border-amber-400" /> {{ __('worked at') }}</span>
          <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="graph.reload()" />
        </div>
      </template>
    </LayoutHeader>

    <div class="min-h-0 flex-1 overflow-auto bg-gray-50/50">
      <div v-if="!nodes.length" class="flex h-full items-center justify-center text-sm text-gray-400">
        {{ graph.loading ? __('Loading...') : __('No network data yet.') }}
      </div>
      <!-- Companies mode: pilanda_theme SSOT block (ring layout, token
           colors, light/dark). The dense people clusters stay on the
           bespoke radial layout below — a plain ring cannot hold them. -->
      <div v-else-if="mode === 'companies'" class="mx-auto h-full max-w-4xl p-6">
        <PpNetworkGraph :nodes="ppNodes" :edges="ppEdges" @node-click="openCompany" />
      </div>
      <svg v-else :viewBox="`0 0 ${W} ${H}`" class="h-full w-full" preserveAspectRatio="xMidYMid meet">
        <!-- company ↔ company links (Kunde X arbeitet mit Kunde Y) -->
        <g>
          <line
            v-for="(e, i) in companyEdgeLines"
            :key="'c' + i"
            :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2"
            stroke="#1E78C2"
            :stroke-width="Math.min(5, 2 + e.weight)"
            stroke-opacity="0.55"
          />
        </g>
        <!-- person edges -->
        <g>
          <line
            v-for="(e, i) in edgeLines"
            :key="i"
            :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2"
            :stroke="e.kind === 'worked_at' ? '#fbbf24' : '#d1d5db'"
            :stroke-width="e.kind === 'worked_at' ? 1.5 : 1"
            :stroke-dasharray="e.kind === 'worked_at' ? '5 4' : ''"
          />
        </g>
        <!-- nodes -->
        <g v-for="n in positioned" :key="n.id" class="cursor-pointer" @click="open(n)">
          <template v-if="n.type === 'company'">
            <circle :cx="n.x" :cy="n.y" :r="companyR(n)" fill="#0B3A6F" />
            <text :x="n.x" :y="n.y + 4" text-anchor="middle" class="fill-white text-[13px] font-semibold" style="pointer-events:none">{{ short(n.label) }}</text>
            <text :x="n.x" :y="n.y + companyR(n) + 14" text-anchor="middle" class="fill-gray-700 text-[11px] font-medium" style="pointer-events:none">{{ n.label }}</text>
          </template>
          <template v-else>
            <circle :cx="n.x" :cy="n.y" r="6" fill="#fff" stroke="#1E78C2" stroke-width="2" />
            <text :x="n.x" :y="n.y - 9" text-anchor="middle" class="fill-gray-600 text-[10px]" style="pointer-events:none">{{ n.label }}</text>
          </template>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpNetworkGraph from '@/components/pp/PpNetworkGraph.vue'

const router = useRouter()
const W = 1400
const H = 900
const mode = ref('people') // 'people' (detail) | 'companies' (Kunde ↔ Kunde)

const graph = createResource({
  url: 'lcs_integrations.projects.api.get_network_graph',
  auto: true,
})
const nodes = computed(() => graph.data?.nodes || [])
const edges = computed(() => graph.data?.edges || [])
const companyEdges = computed(() => graph.data?.company_edges || [])

// Deterministic radial-cluster layout: companies on a big circle, their
// people on a small ring around each company. In 'companies' mode only the
// company hubs are shown (Kunde ↔ Kunde links).
const positioned = computed(() => {
  const cx = W / 2
  const cy = H / 2
  const companies = nodes.value.filter((n) => n.type === 'company')
  const people = mode.value === 'companies' ? [] : nodes.value.filter((n) => n.type === 'person')
  const Rc = Math.min(cx, cy) - 150
  const out = []
  const compPos = {}
  companies.forEach((c, i) => {
    const a = (i / Math.max(companies.length, 1)) * Math.PI * 2 - Math.PI / 2
    const x = cx + Rc * Math.cos(a)
    const y = cy + Rc * Math.sin(a)
    compPos[c.id] = { x, y }
    out.push({ ...c, x, y })
  })
  const byOrg = {}
  people.forEach((p) => {
    byOrg['org::' + p.org] = byOrg['org::' + p.org] || []
    byOrg['org::' + p.org].push(p)
  })
  Object.entries(byOrg).forEach(([orgId, ps]) => {
    const c = compPos[orgId]
    if (!c) return
    const Rp = Math.min(120, 50 + ps.length * 9)
    ps.forEach((p, j) => {
      const a = (j / ps.length) * Math.PI * 2
      out.push({ ...p, x: c.x + Rp * Math.cos(a), y: c.y + Rp * Math.sin(a) })
    })
  })
  return out
})

const companyEdgeLines = computed(() =>
  companyEdges.value
    .map((e) => {
      const s = posById.value[e.source]
      const t = posById.value[e.target]
      if (!s || !t) return null
      return { x1: s.x, y1: s.y, x2: t.x, y2: t.y, weight: e.weight || 1 }
    })
    .filter(Boolean),
)

const posById = computed(() => {
  const m = {}
  positioned.value.forEach((n) => { m[n.id] = n })
  return m
})

const edgeLines = computed(() =>
  edges.value
    .map((e) => {
      const s = posById.value[e.source]
      const t = posById.value[e.target]
      if (!s || !t) return null
      return { x1: s.x, y1: s.y, x2: t.x, y2: t.y, kind: e.kind }
    })
    .filter(Boolean),
)

// Companies mode → PpNetworkGraph props: biggest customer in the center,
// the rest on the ring; edge label carries the shared-project weight.
const ppNodes = computed(() => {
  const companies = nodes.value.filter((n) => n.type === 'company')
  const maxSize = Math.max(...companies.map((c) => c.size || 0), 0)
  let centerTaken = false
  return companies.map((c) => {
    const isCenter = !centerTaken && maxSize > 0 && (c.size || 0) === maxSize
    if (isCenter) centerTaken = true
    return { id: c.id, label: c.label, kind: 'brand', center: isCenter }
  })
})
const ppEdges = computed(() =>
  companyEdges.value.map((e) => ({
    from: e.source,
    to: e.target,
    label: (e.weight || 1) > 1 ? `${e.weight}×` : '',
  })),
)
function openCompany(id) {
  router.push({ name: 'Organization', params: { organizationId: String(id).replace('org::', '') } })
}

function companyR(n) {
  return Math.min(40, 22 + (n.size || 0) * 1.5)
}
function short(label) {
  const w = (label || '').split(' ')
  return w.length > 1 ? (w[0][0] + w[1][0]).toUpperCase() : (label || '').slice(0, 3)
}
function open(n) {
  if (n.type === 'person' && n.contact) {
    router.push({ name: 'Contact', params: { contactId: n.contact } })
  } else if (n.type === 'company') {
    router.push({ name: 'Organization', params: { organizationId: n.id.replace('org::', '') } })
  }
}
</script>
