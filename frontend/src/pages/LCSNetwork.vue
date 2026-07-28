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
        <Button :label="__('New company')" iconLeft="building-2" @click="openOrg" />
        <Button variant="solid" :label="__('New contact')" iconLeft="user-plus" @click="openContact" />
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

    <!-- Neuer Kontakt (Firma aus Bestand ODER neu über den Link-Picker) -->
    <PpModal v-model:open="contactOpen" :title="__('New contact')" :width="520">
      <form class="crmn-form" @submit.prevent="saveContact">
        <div class="crmn-form-row">
          <label class="crmn-fld"><span class="crmn-fld-cap">{{ __('First name') }}</span>
            <input v-model="cForm.first_name" type="text" class="crmn-input" autofocus /></label>
          <label class="crmn-fld"><span class="crmn-fld-cap">{{ __('Last name') }}</span>
            <input v-model="cForm.last_name" type="text" class="crmn-input" /></label>
        </div>
        <label class="crmn-fld"><span class="crmn-fld-cap">{{ __('Email') }}</span>
          <input v-model="cForm.email" type="email" class="crmn-input" /></label>
        <div class="crmn-fld">
          <span class="crmn-fld-cap">{{ __('Company') }}</span>
          <Link doctype="CRM Organization" v-model="cForm.company" :placeholder="__('Select from existing or create new')" :onCreate="onCreateOrg" />
        </div>
      </form>
      <template #footer>
        <Button :label="__('Cancel')" @click="contactOpen = false" />
        <Button variant="solid" :label="__('Save')" :loading="saving" @click="saveContact" />
      </template>
    </PpModal>

    <!-- Neue Firma -->
    <PpModal v-model:open="orgOpen" :title="__('New company')" :width="440">
      <label class="crmn-fld"><span class="crmn-fld-cap">{{ __('Company') }}</span>
        <input v-model="oName" type="text" class="crmn-input" autofocus @keydown.enter.prevent="saveOrg" /></label>
      <template #footer>
        <Button :label="__('Cancel')" @click="orgOpen = false" />
        <Button variant="solid" :label="__('Save')" :loading="saving" @click="saveOrg" />
      </template>
    </PpModal>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpNetGraph from '@/components/pp/PpNetGraph.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpModal from '@/components/pp/PpModal.vue'
import Link from '@/components/Controls/Link.vue'
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

// --- Neue Firma / Neuer Kontakt --------------------------------------------
const saving = ref(false)

const orgOpen = ref(false)
const oName = ref('')
function openOrg() { oName.value = ''; orgOpen.value = true }
function saveOrg() {
  const name = oName.value.trim()
  if (!name) return
  saving.value = true
  call('frappe.client.insert', { doc: { doctype: 'CRM Organization', organization_name: name } })
    .then(() => { orgOpen.value = false; toast.success(__('Company created') + ': ' + name); graph.reload() })
    .catch((e) => toast.error(e?.messages?.[0] || e?.message || __('Could not save.')))
    .finally(() => { saving.value = false })
}

const contactOpen = ref(false)
const cForm = ref({ first_name: '', last_name: '', email: '', company: '' })
function openContact() { cForm.value = { first_name: '', last_name: '', email: '', company: '' }; contactOpen.value = true }
// Firma inline neu anlegen (Link-Picker „Create new") → setzt sie im Formular.
async function onCreateOrg(value, close) {
  try {
    const res = await call('frappe.client.insert', { doc: { doctype: 'CRM Organization', organization_name: value } })
    const name = res?.message?.name || res?.name || value
    cForm.value.company = name
    toast.success(__('Company created') + ': ' + name)
    close && close()
  } catch (e) { toast.error(e?.messages?.[0] || e?.message || __('Could not save.')) }
}
function saveContact() {
  const fn = cForm.value.first_name.trim()
  const ln = cForm.value.last_name.trim()
  if (!fn && !ln) { toast.error(__('Please enter a name.')); return }
  saving.value = true
  const doc = {
    doctype: 'Contact',
    first_name: fn || ln,
    last_name: fn ? ln : '',
    company_name: cForm.value.company || '',
  }
  const email = cForm.value.email.trim()
  if (email) doc.email_ids = [{ email_id: email, is_primary: 1 }]
  call('frappe.client.insert', { doc })
    .then(() => { contactOpen.value = false; toast.success(__('Contact created')); graph.reload() })
    .catch((e) => toast.error(e?.messages?.[0] || e?.message || __('Could not save.')))
    .finally(() => { saving.value = false })
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

/* Anlage-Formulare (Neuer Kontakt / Neue Firma) */
.crmn-form { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.crmn-form-row { display: flex; gap: var(--pp-space-3); }
.crmn-fld { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.crmn-fld-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmn-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.crmn-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
</style>
