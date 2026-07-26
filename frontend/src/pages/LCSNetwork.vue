<!--
  LCSNetwork — CRM-Netzwerk auf dem Theme-Baustein PpNetGraph.
  ============================================================
  Ein Kraft-Layout-Beziehungsgeflecht: Firmen + zugeordnete Personen in EINER
  Ansicht (wer arbeitet wo, Karriere-Historie, gemeinsame Personalwechsel).
  Klick auf einen Knoten → globaler Shell-Inspektor mit reicher View
  (usePilandaInspect). Echte Daten aus get_network_graph (keine Demodaten).
-->
<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Network'), route: { name: 'LCS Network' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="graph.reload()" />
      </template>
    </LayoutHeader>

    <div class="crmn">
      <div class="crmn-inner">
        <PpPageHead
          :title="__('Network')"
          :subtitle="__('Relationships between organizations and people · click a node to open the profile')"
        />

        <!-- Leer-/Ladezustand -->
        <section v-if="!nodes.length" class="crmn-graph crmn-empty">
          <PpEmptyState
            :title="graph.loading ? __('Loading network …') : __('No network data yet')"
            :hint="graph.loading ? '' : __('Once organizations with assigned contacts exist, the relationship graph appears here.')"
          />
        </section>

        <!-- Kraft-Layout-Graph (Theme SSOT PpNetGraph; eigene Legende + Zoom-
             to-fit). Re-Mount bei neuen Daten über :key. -->
        <section v-else class="crmn-graph crmn-graph--card">
          <PpNetGraph
            :key="netKey"
            :nodes="netNodes"
            :edges="netEdges"
            :selected="selId"
            @select="pick"
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
import PpNetGraph from '@/components/pp/PpNetGraph.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()

const graph = createResource({
  url: 'lcs_integrations.projects.api.get_network_graph',
  auto: true,
})
const nodes = computed(() => graph.data?.nodes || [])
const edges = computed(() => graph.data?.edges || [])
const companyEdges = computed(() => graph.data?.company_edges || [])

const orgLabel = (orgId) =>
  nodes.value.find((n) => n.id === orgId)?.label || String(orgId || '').replace('org::', '')

// --- PpNetGraph-Modell: Start-Koordinaten in Prozent (0–100); die Simulation
//     schwingt daraus ein. Firmen auf einem Kreis, ihre Personen im Ring drum. --
const netNodes = computed(() => {
  const comps = nodes.value.filter((n) => n.type === 'company')
  const people = nodes.value.filter((n) => n.type === 'person')
  const compPos = {}
  const out = []
  comps.forEach((c, i) => {
    const a = (i / Math.max(comps.length, 1)) * Math.PI * 2 - Math.PI / 2
    const x = 50 + 26 * Math.cos(a)
    const y = 50 + 30 * Math.sin(a)
    compPos[c.id] = { x, y }
    out.push({ id: c.id, t: 'firma', l: c.label, x, y })
  })
  const byOrg = {}
  people.forEach((p) => {
    const k = 'org::' + p.org
    ;(byOrg[k] = byOrg[k] || []).push(p)
  })
  Object.entries(byOrg).forEach(([orgId, ps]) => {
    const c = compPos[orgId] || { x: 50, y: 50 }
    ps.forEach((p, j) => {
      const a = (j / ps.length) * Math.PI * 2
      out.push({
        id: p.id,
        t: 'person',
        l: p.label,
        firma: orgLabel('org::' + p.org),
        rolle: p.role,
        x: Math.max(4, Math.min(96, c.x + 10 * Math.cos(a))),
        y: Math.max(4, Math.min(96, c.y + 12 * Math.sin(a))),
      })
    })
  })
  return out
})

const netEdges = computed(() => {
  const staff = edges.value.map((e) => ({
    a: e.source,
    b: e.target,
    type: e.kind === 'worked_at' ? 'beziehung' : 'arbeitet',
  }))
  const shared = companyEdges.value.map((e) => ({
    a: e.source,
    b: e.target,
    type: 'beziehung',
    strength: Math.min(3, e.weight || 1),
  }))
  return [...staff, ...shared]
})

// Neue Daten → PpNetGraph neu mounten (kein Laufzeit-Relayout).
const netKey = computed(() => `${netNodes.value.length}:${netEdges.value.length}`)

// --- Auswahl / reicher Inspektor ------------------------------------------
const selId = ref(null)
const selNode = computed(() => nodes.value.find((n) => n.id === selId.value) || null)

function pick(id) {
  selId.value = id
  const n = selNode.value
  if (!n) {
    inspectNode(null)
    return
  }
  const t = window.__
  const view =
    n.type === 'company'
      ? {
          title: n.label,
          badge: { label: t('Organization'), tone: 'brand' },
          rows: [
            { label: t('Type'), value: t('Organization') },
            { label: t('Contacts'), value: n.size || 0 },
          ],
          sections: [
            {
              title: t('People'),
              items: selPeople.value.map((p) => ({ text: p.label, muted: p.role || '' })),
              empty: t('No people assigned in the graph.'),
            },
            {
              title: t('Connected organizations'),
              items: selConnected.value.map((c) => ({
                text: c.label,
                muted: c.weight > 1 ? `${c.weight} ${t('moves')}` : '',
              })),
              empty: t('No cross-organization connections.'),
            },
          ],
          action: { label: t('Open organization'), onClick: openSelected },
        }
      : {
          title: n.label,
          badge: { label: t('Person'), tone: 'info' },
          rows: [
            { label: t('Role'), value: n.role || '—' },
            { label: t('Organization'), value: selPersonCompany.value || '—' },
          ],
          sections: [
            {
              title: t('Previously worked at'),
              items: selPersonPrev.value.map((c) => ({ text: c })),
              empty: t('No career history on record.'),
            },
          ],
          action: { label: t('Open contact'), onClick: openSelected },
        }
  inspectNode(view)
}

onBeforeUnmount(() => inspectNode(null))

const selPeople = computed(() => {
  if (!selNode.value || selNode.value.type !== 'company') return []
  const orgName = selNode.value.id.replace('org::', '')
  return nodes.value.filter((n) => n.type === 'person' && n.org === orgName)
})
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
</script>

<style scoped>
.crmn { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.crmn-inner { width: 100%; margin: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crmn-graph { min-width: 0; }
.crmn-empty { display: flex; align-items: center; justify-content: center;
  min-height: 320px; background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmn-graph--card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-3); }
</style>
