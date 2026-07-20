<!--
  LCSNetwork — CRM-Netzwerk (V2, Showcase #6 „Netzwerk").
  ============================================================
  Beziehungsgraph zwischen Firmen und den ihnen zugeordneten Personen
  (wer arbeitet wo) plus Karriere-Historie (wo jemand vorher war).

  Präsentation nach pilanda_theme-Showcase #6: PpPageHead + Legende +
  PpNetworkGraph (Firmen-Ring) bzw. dichter Radial-Cluster (Personen) +
  PpDrawer-Profil beim Klick auf einen Knoten. Alle Drawer-Felder stammen
  ECHT aus der API-Antwort (get_network_graph) — keine Demodaten.

  Datenlogik unverändert produktiv:
    lcs_integrations.projects.api.get_network_graph
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Network'), route: { name: 'LCS Network' } }]" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-3">
          <div class="flex overflow-hidden rounded-md border">
            <button
              class="px-3 py-1 text-xs font-medium transition"
              :class="mode === 'people' ? 'bg-lcs-primary text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
              @click="mode = 'people'"
            >{{ __('People') }}</button>
            <button
              class="px-3 py-1 text-xs font-medium transition"
              :class="mode === 'companies' ? 'bg-lcs-primary text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
              @click="mode = 'companies'"
            >{{ __('Organizations') }}</button>
          </div>
          <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="graph.reload()" />
        </div>
      </template>
    </LayoutHeader>

    <div class="crmn">
      <div class="crmn-inner">
        <PpPageHead
          :eyebrow="__('Sales / CRM')"
          :title="__('Network')"
          :subtitle="__('Relationships between organizations and people · click a node to open the profile')"
        />

        <section class="crmn-legend" :aria-label="__('Legend')">
          <span class="crmn-legend-item"><i class="crmn-legend-dot is-brand" />{{ __('Organization') }}</span>
          <span class="crmn-legend-item"><i class="crmn-legend-dot crmn-legend-dot--ring" />{{ __('Person') }}</span>
          <span class="crmn-legend-item"><i class="crmn-legend-line" />{{ __('works at') }}</span>
          <span class="crmn-legend-item"><i class="crmn-legend-line crmn-legend-line--dashed" />{{ __('previously at') }}</span>
        </section>

        <!-- Leer-/Ladezustand -->
        <section v-if="!nodes.length" class="crmn-graph crmn-empty">
          <PpEmptyState
            :title="graph.loading ? __('Loading network …') : __('No network data yet')"
            :hint="graph.loading ? '' : __('Once organizations with assigned contacts exist, the relationship graph appears here.')"
          />
        </section>

        <!-- Firmen-Ansicht: Theme-Baustein PpNetworkGraph (Kunde ↔ Kunde) -->
        <section v-else-if="mode === 'companies'" class="crmn-graph">
          <PpNetworkGraph :nodes="ppNodes" :edges="ppEdges" :selected="selId" @node-click="pick" />
        </section>

        <!-- Personen-Ansicht: dichter Radial-Cluster (ein Ring kann die
             Personen-Wolken nicht fassen — bewusst eigenes Layout). -->
        <section v-else class="crmn-graph crmn-graph--svg">
          <svg :viewBox="`0 0 ${W} ${H}`" class="crmn-svg" preserveAspectRatio="xMidYMid meet">
            <g>
              <line
                v-for="(e, i) in companyEdgeLines"
                :key="'c' + i"
                :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2"
                class="crmn-edge crmn-edge--company"
                :stroke-width="Math.min(5, 2 + e.weight)"
              />
            </g>
            <g>
              <line
                v-for="(e, i) in edgeLines"
                :key="i"
                :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2"
                class="crmn-edge"
                :class="e.kind === 'worked_at' ? 'crmn-edge--prev' : 'crmn-edge--works'"
              />
            </g>
            <g
              v-for="n in positioned"
              :key="n.id"
              class="crmn-node"
              :class="{ 'is-selected': selId === n.id }"
              @click="pick(n.id)"
            >
              <template v-if="n.type === 'company'">
                <circle :cx="n.x" :cy="n.y" :r="companyR(n)" class="crmn-node-company" />
                <text :x="n.x" :y="n.y + 4" text-anchor="middle" class="crmn-node-company-abbr">{{ short(n.label) }}</text>
                <text :x="n.x" :y="n.y + companyR(n) + 14" text-anchor="middle" class="crmn-node-company-label">{{ n.label }}</text>
              </template>
              <template v-else>
                <circle :cx="n.x" :cy="n.y" r="6" class="crmn-node-person" />
                <text :x="n.x" :y="n.y - 9" text-anchor="middle" class="crmn-node-person-label">{{ n.label }}</text>
              </template>
            </g>
          </svg>
        </section>
      </div>
    </div>

    <!-- Knoten-Profil (echte Felder aus get_network_graph) -->
    <PpDrawer v-model:open="drawerOpen" :width="440" :title="selNode ? selNode.label : ''">
      <template v-if="selNode" #title>
        <span class="crmn-dh">{{ selNode.label }}</span>
      </template>
      <div v-if="selNode" class="crmn-detail">
        <div class="crmn-detail-head">
          <span class="crmn-role" :class="selNode.type === 'company' ? 'is-brand' : 'is-info'">
            <i class="crmn-legend-dot" :class="selNode.type === 'company' ? 'is-brand' : 'is-info'" />
            {{ selNode.type === 'company' ? __('Organization') : __('Person') }}
          </span>
        </div>

        <!-- Firma -->
        <template v-if="selNode.type === 'company'">
          <dl class="crmn-meta">
            <div><dt>{{ __('Type') }}</dt><dd>{{ __('Organization') }}</dd></div>
            <div><dt>{{ __('Contacts') }}</dt><dd>{{ selNode.size || 0 }}</dd></div>
          </dl>

          <section class="crmn-sec">
            <h4 class="crmn-sec-title">{{ __('People') }}</h4>
            <ul v-if="selPeople.length" class="crmn-proj">
              <li v-for="p in selPeople" :key="p.id">
                {{ p.label }}<span v-if="p.role" class="crmn-muted"> · {{ p.role }}</span>
              </li>
            </ul>
            <p v-else class="crmn-desc">{{ __('No people assigned in the graph.') }}</p>
          </section>

          <section class="crmn-sec">
            <h4 class="crmn-sec-title">{{ __('Connected organizations') }}</h4>
            <ul v-if="selConnected.length" class="crmn-proj">
              <li v-for="c in selConnected" :key="c.id">
                {{ c.label }}<span v-if="c.weight > 1" class="crmn-muted"> · {{ c.weight }} {{ __('moves') }}</span>
              </li>
            </ul>
            <p v-else class="crmn-desc">{{ __('No cross-organization connections.') }}</p>
          </section>
        </template>

        <!-- Person -->
        <template v-else>
          <dl class="crmn-meta">
            <div><dt>{{ __('Role') }}</dt><dd>{{ selNode.role || '—' }}</dd></div>
            <div><dt>{{ __('Organization') }}</dt><dd>{{ selPersonCompany || '—' }}</dd></div>
          </dl>

          <section class="crmn-sec">
            <h4 class="crmn-sec-title">{{ __('Previously worked at') }}</h4>
            <ul v-if="selPersonPrev.length" class="crmn-proj">
              <li v-for="c in selPersonPrev" :key="c">{{ c }}</li>
            </ul>
            <p v-else class="crmn-desc">{{ __('No career history on record.') }}</p>
          </section>
        </template>
      </div>

      <template #footer>
        <Button
          v-if="selNode"
          variant="solid"
          :label="selNode.type === 'company' ? __('Open organization') : __('Open contact')"
          iconLeft="external-link"
          @click="openSelected"
        />
      </template>
    </PpDrawer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpNetworkGraph from '@/components/pp/PpNetworkGraph.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpDrawer from '@/components/pp/PpDrawer.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'

const router = useRouter()
const W = 1400
const H = 900
const mode = ref('people') // 'people' (Detail) | 'companies' (Kunde ↔ Kunde)

const graph = createResource({
  url: 'lcs_integrations.projects.api.get_network_graph',
  auto: true,
})
const nodes = computed(() => graph.data?.nodes || [])
const edges = computed(() => graph.data?.edges || [])
const companyEdges = computed(() => graph.data?.company_edges || [])

// --- Radial-Cluster-Layout (Personen-Ansicht) ----------------------------
// Firmen auf einem großen Kreis, ihre Personen auf einem kleinen Ring um die
// jeweilige Firma. In der Firmen-Ansicht werden nur die Firmen-Hubs gezeigt.
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

const posById = computed(() => {
  const m = {}
  positioned.value.forEach((n) => { m[n.id] = n })
  return m
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

// --- Firmen-Ansicht → PpNetworkGraph-Props --------------------------------
// Größter Kunde in die Mitte, Rest auf den Ring; Kantenlabel = Zahl gemeinsamer
// Personalwechsel.
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

// --- Auswahl / Drawer -----------------------------------------------------
const selId = ref(null)
const drawerOpen = ref(false)
const selNode = computed(() => nodes.value.find((n) => n.id === selId.value) || null)

function pick(id) {
  selId.value = id
  drawerOpen.value = true
}

// Personen einer Firma (aus dem Graphen abgeleitet).
const selPeople = computed(() => {
  if (!selNode.value || selNode.value.type !== 'company') return []
  const orgName = selNode.value.id.replace('org::', '')
  return nodes.value.filter((n) => n.type === 'person' && n.org === orgName)
})

// Verbundene Firmen (company_edges, die den Knoten berühren).
const orgLabel = (orgId) => nodes.value.find((n) => n.id === orgId)?.label || orgId.replace('org::', '')
const selConnected = computed(() => {
  if (!selNode.value || selNode.value.type !== 'company') return []
  const id = selNode.value.id
  return companyEdges.value
    .filter((e) => e.source === id || e.target === id)
    .map((e) => {
      const other = e.source === id ? e.target : e.source
      return { id: other, label: orgLabel(other), weight: e.weight || 1 }
    })
})

// Person → Firma / Karriere-Historie.
const selPersonCompany = computed(() =>
  selNode.value?.type === 'person' ? orgLabel('org::' + selNode.value.org) : '',
)
const selPersonPrev = computed(() => {
  if (!selNode.value || selNode.value.type !== 'person') return []
  return edges.value
    .filter((e) => e.source === selNode.value.id && e.kind === 'worked_at')
    .map((e) => orgLabel(e.target))
})

function openSelected() {
  const n = selNode.value
  if (!n) return
  if (n.type === 'person' && n.contact) {
    router.push({ name: 'Contact', params: { contactId: n.contact } })
  } else if (n.type === 'company') {
    router.push({ name: 'Organization', params: { organizationId: n.id.replace('org::', '') } })
  }
}

function companyR(n) {
  return Math.min(40, 22 + (n.size || 0) * 1.5)
}
function short(label) {
  const w = (label || '').split(' ')
  return w.length > 1 ? (w[0][0] + w[1][0]).toUpperCase() : (label || '').slice(0, 3)
}
</script>

<style scoped>
.crmn { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.crmn-inner { width: 100%; margin: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crmn-legend { display: flex; flex-wrap: wrap; gap: var(--pp-space-2) var(--pp-space-4);
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmn-legend-item { display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crmn-legend-dot { width: 9px; height: 9px; border-radius: var(--pp-radius-full); flex-shrink: 0; }
.crmn-legend-dot.is-brand   { background: var(--pp-brand-primary); }
.crmn-legend-dot.is-info    { background: var(--pp-state-info); }
.crmn-legend-dot--ring { background: var(--pp-bg-surface); border: 2px solid var(--pp-brand-primary); }
.crmn-legend-line { width: 22px; height: 0; border-top: 2px solid var(--pp-brand-primary); flex-shrink: 0; }
.crmn-legend-line--dashed { border-top-style: dashed; border-top-color: var(--pp-state-warning); }

.crmn-graph { min-width: 0; }
.crmn-empty { display: flex; align-items: center; justify-content: center;
  min-height: 320px; background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmn-graph--svg { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-3); }
.crmn-svg { display: block; width: 100%; height: auto; max-height: 68vh; }

/* SVG-Kanten/Knoten (Personen-Ansicht), token-only */
.crmn-edge { stroke: var(--pp-border-default); }
.crmn-edge--company { stroke: var(--pp-brand-primary); stroke-opacity: 0.55; }
.crmn-edge--works { stroke: var(--pp-border-strong); stroke-width: 1; }
.crmn-edge--prev { stroke: var(--pp-state-warning); stroke-width: 1.5; stroke-dasharray: 5 4; }
.crmn-node { cursor: pointer; }
.crmn-node-company { fill: var(--pp-brand-primary); }
.crmn-node.is-selected .crmn-node-company { stroke: var(--pp-brand-700, var(--pp-brand-primary)); stroke-width: 3; }
.crmn-node-company-abbr { fill: var(--pp-text-on-accent); font-size: 13px; font-weight: var(--pp-weight-semibold); pointer-events: none; }
.crmn-node-company-label { fill: var(--pp-text-secondary); font-size: 11px; font-weight: var(--pp-weight-medium); pointer-events: none; }
.crmn-node-person { fill: var(--pp-bg-surface); stroke: var(--pp-brand-primary); stroke-width: 2; }
.crmn-node.is-selected .crmn-node-person { stroke-width: 3.5; }
.crmn-node-person-label { fill: var(--pp-text-tertiary); font-size: 10px; pointer-events: none; }

/* Drawer-Detail */
.crmn-dh { font-weight: var(--pp-weight-semibold); }
.crmn-detail { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.crmn-detail-head { display: flex; }
.crmn-role { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }
.crmn-meta { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-2) var(--pp-space-4); margin: 0; }
.crmn-meta dt { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.crmn-meta dd { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.crmn-sec { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crmn-sec-title { margin: 0; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmn-desc { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-secondary); line-height: var(--pp-lh-relaxed, 1.6); }
.crmn-proj { margin: 0; padding-left: var(--pp-space-4); font-size: var(--pp-fs-14); color: var(--pp-text-secondary);
  display: flex; flex-direction: column; gap: 2px; }
.crmn-muted { color: var(--pp-text-tertiary); }
</style>
