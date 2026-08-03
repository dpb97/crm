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
        <Button :label="isMobile ? '' : __('New company')" iconLeft="building-2" :title="__('New company')" @click="openOrg" />
        <Button variant="solid" :label="isMobile ? '' : __('New contact')" iconLeft="user-plus" :title="__('New contact')" @click="openContact" />
        <Button :label="isMobile ? '' : __('Refresh')" iconLeft="refresh-cw" :title="__('Refresh')" @click="graph.reload()" />
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
             to-fit). Re-Mount bei neuen Daten über :key. Desktop only — a
             spatial force graph is unusable on a phone. -->
        <section v-else-if="!isMobile" class="crmn-graph crmn-graph--card">
          <PpNetGraph
            :key="netKey"
            :nodes="netNodes"
            :edges="netEdges"
            :selected="selId"
            @select="pick"
          />
        </section>

        <!-- Mobile: node-focused explorer over the SAME data. Pick a focus,
             then tap related people/companies to drill through the network. -->
        <section v-else class="crmn-explorer">
          <div class="crmn-ex-search">
            <FeatherIcon name="search" class="crmn-ex-search-ic" />
            <input v-model="focusQuery" type="text" class="crmn-ex-search-in" :placeholder="__('Search person or company …')" />
            <button v-if="focusQuery" type="button" class="crmn-ex-search-x" @click="focusQuery = ''"><FeatherIcon name="x" class="h-4 w-4" /></button>
          </div>
          <div v-if="searchResults.length" class="crmn-ex-results">
            <button v-for="n in searchResults" :key="n.id" type="button" class="crmn-ex-result" @click="pickFocus(n)">
              <span class="crmn-ex-dot" :class="n.type === 'company' ? 'is-org' : 'is-person'" />
              <span class="crmn-ex-row-l">{{ n.label }}</span>
              <span class="crmn-ex-row-m">{{ n.type === 'company' ? __('Company') : __('Person') }}</span>
            </button>
          </div>

          <template v-if="focusNode">
            <div class="crmn-ex-focus">
              <span class="crmn-ex-badge" :class="focusNode.type === 'company' ? 'is-org' : 'is-person'">
                {{ focusNode.type === 'company' ? __('Company') : __('Person') }}
              </span>
              <h3 class="crmn-ex-name">{{ focusNode.label }}</h3>
              <div v-if="focusNode.type === 'person'" class="crmn-ex-sub">
                <span v-if="focusRole">{{ focusRole }}</span>
                <button v-if="focusCompany && hasNode(focusCompany.id)" type="button" class="crmn-ex-inline-link" @click="focusOn(focusCompany.id)">{{ focusCompany.label }}</button>
                <span v-else-if="focusCompany">{{ focusCompany.label }}</span>
              </div>
              <button type="button" class="crmn-ex-open" @click="openNode(focusNode)">
                <FeatherIcon name="external-link" class="h-3.5 w-3.5" /> {{ __('Open profile') }}
              </button>
            </div>

            <template v-if="focusNode.type === 'company'">
              <div class="crmn-ex-group">
                <div class="crmn-ex-group-h">{{ __('People') }} <span class="crmn-ex-count">{{ focusPeople.length }}</span></div>
                <button v-for="p in focusPeople" :key="p.id" type="button" class="crmn-ex-row" @click="focusOn(p.id)">
                  <span class="crmn-ex-dot is-person" />
                  <span class="crmn-ex-row-l">{{ p.label }}</span>
                  <span v-if="p.role" class="crmn-ex-row-m">{{ p.role }}</span>
                  <FeatherIcon name="chevron-right" class="crmn-ex-chev" />
                </button>
                <div v-if="!focusPeople.length" class="crmn-ex-empty">{{ __('No people assigned in the graph.') }}</div>
              </div>
              <div class="crmn-ex-group">
                <div class="crmn-ex-group-h">{{ __('Connected organizations') }} <span class="crmn-ex-count">{{ focusConnected.length }}</span></div>
                <button v-for="c in focusConnected" :key="c.id" type="button" class="crmn-ex-row" @click="focusOn(c.id)">
                  <span class="crmn-ex-dot is-org" />
                  <span class="crmn-ex-row-l">{{ c.label }}</span>
                  <span v-if="c.weight > 1" class="crmn-ex-row-m">{{ c.weight }} {{ __('moves') }}</span>
                  <FeatherIcon name="chevron-right" class="crmn-ex-chev" />
                </button>
                <div v-if="!focusConnected.length" class="crmn-ex-empty">{{ __('No cross-organization connections.') }}</div>
              </div>
            </template>

            <template v-else>
              <div class="crmn-ex-group">
                <div class="crmn-ex-group-h">{{ __('Previously worked at') }} <span class="crmn-ex-count">{{ focusPrev.length }}</span></div>
                <button v-for="c in focusPrev" :key="c.id" type="button" class="crmn-ex-row" :class="{ 'is-static': !hasNode(c.id) }" @click="focusOn(c.id)">
                  <span class="crmn-ex-dot is-org" />
                  <span class="crmn-ex-row-l">{{ c.label }}</span>
                  <FeatherIcon v-if="hasNode(c.id)" name="chevron-right" class="crmn-ex-chev" />
                </button>
                <div v-if="!focusPrev.length" class="crmn-ex-empty">{{ __('No career history on record.') }}</div>
              </div>
            </template>
          </template>
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
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, toast, Breadcrumbs, Button, FeatherIcon } from 'frappe-ui'
import { useViewport } from '@/composables/useViewport'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpNetGraph from '@/components/pp/PpNetGraph.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpModal from '@/components/pp/PpModal.vue'
import Link from '@/components/Controls/Link.vue'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()
const { isMobile } = useViewport()

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
  openNode(selNode.value)
}
function openNode(n) {
  if (!n) return
  if (n.type === 'person' && n.contact) {
    router.push({ name: 'Contact', params: { contactId: n.contact } })
  } else if (n.type === 'company') {
    router.push({ name: 'Organization', params: { organizationId: n.id.replace('org::', '') } })
  }
}

// --- Mobile explorer: node-focused, tap to drill through relationships -------
// A spatial force-graph is unusable on a phone, so on mobile we render the same
// data as a focus node + its grouped, tappable relationships. Tapping a related
// node re-centres on it (drill-through).
const focusId = ref(null)
const focusNode = computed(() => nodes.value.find((n) => n.id === focusId.value) || null)
watch(
  nodes,
  (ns) => {
    if ((!focusId.value || !ns.some((n) => n.id === focusId.value)) && ns.length) {
      focusId.value = (ns.find((n) => n.type === 'company') || ns[0]).id
    }
  },
  { immediate: true },
)
function focusOn(id) {
  if (id && nodes.value.some((n) => n.id === id)) focusId.value = id
}
const hasNode = (id) => nodes.value.some((n) => n.id === id)

// Company focus → its people + connected organizations.
const focusPeople = computed(() => {
  if (focusNode.value?.type !== 'company') return []
  const orgName = focusNode.value.id.replace('org::', '')
  return nodes.value.filter((n) => n.type === 'person' && n.org === orgName)
})
const focusConnected = computed(() => {
  if (focusNode.value?.type !== 'company') return []
  const id = focusNode.value.id
  return companyEdges.value
    .filter((e) => e.source === id || e.target === id)
    .map((e) => {
      const other = e.source === id ? e.target : e.source
      return { id: other, label: orgLabel(other), weight: e.weight || 1 }
    })
})
// Person focus → current company + previous companies (worked_at).
const focusCompany = computed(() => {
  if (focusNode.value?.type !== 'person') return null
  const id = 'org::' + focusNode.value.org
  return { id, label: orgLabel(id) }
})
const focusPrev = computed(() => {
  if (focusNode.value?.type !== 'person') return []
  return edges.value
    .filter((e) => e.source === focusNode.value.id && e.kind === 'worked_at')
    .map((e) => ({ id: e.target, label: orgLabel(e.target) }))
})
const focusRole = computed(() => focusNode.value?.role || '')

// Focus picker search.
const focusQuery = ref('')
const searchResults = computed(() => {
  const q = focusQuery.value.trim().toLowerCase()
  if (!q) return []
  return nodes.value
    .filter((n) => (n.label || '').toLowerCase().includes(q))
    .slice(0, 12)
})
function pickFocus(n) { focusOn(n.id); focusQuery.value = '' }
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

/* --- Mobile node-focused explorer --- */
.crmn-explorer { display: flex; flex-direction: column; gap: var(--pp-space-3); }
.crmn-ex-search { position: relative; display: flex; align-items: center; }
.crmn-ex-search-ic { position: absolute; left: 10px; width: 16px; height: 16px; color: var(--pp-text-tertiary); pointer-events: none; }
.crmn-ex-search-in { width: 100%; appearance: none; font-family: inherit; font-size: var(--pp-fs-14, 14px);
  color: var(--pp-text-primary); padding: 10px 34px; border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-surface); }
.crmn-ex-search-in:focus { outline: none; border-color: var(--pp-brand-primary); }
.crmn-ex-search-x { position: absolute; right: 6px; width: 28px; height: 28px; display: grid; place-items: center;
  border: 0; background: transparent; color: var(--pp-text-tertiary); cursor: pointer; }
.crmn-ex-results { display: flex; flex-direction: column; background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); overflow: hidden; box-shadow: var(--pp-shadow-xs); }
.crmn-ex-result { display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 8px 12px;
  border: 0; border-bottom: 1px solid var(--pp-border-subtle); background: transparent; cursor: pointer; text-align: left; }
.crmn-ex-result:last-child { border-bottom: 0; }
.crmn-ex-result:hover { background: var(--pp-bg-hover); }

.crmn-ex-focus { display: flex; flex-direction: column; gap: 6px; background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); padding: var(--pp-space-4); box-shadow: var(--pp-shadow-xs); }
.crmn-ex-badge { align-self: flex-start; font-size: 10px; font-weight: var(--pp-weight-bold); text-transform: uppercase;
  letter-spacing: 0.04em; padding: 2px 8px; border-radius: var(--pp-radius-full); }
.crmn-ex-badge.is-org { background: color-mix(in srgb, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary-d); }
.crmn-ex-badge.is-person { background: color-mix(in srgb, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }
.crmn-ex-name { margin: 0; font-size: var(--pp-fs-17, 17px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crmn-ex-sub { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crmn-ex-inline-link { border: 0; background: transparent; padding: 0; font: inherit; color: var(--pp-brand-primary); cursor: pointer; text-decoration: underline; }
.crmn-ex-open { align-self: flex-start; margin-top: 4px; display: inline-flex; align-items: center; gap: 6px; min-height: 40px;
  padding: 0 14px; border: 1px solid var(--pp-brand-primary); border-radius: var(--pp-radius-ui);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent); font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); cursor: pointer; }

.crmn-ex-group { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); overflow: hidden; box-shadow: var(--pp-shadow-xs); }
.crmn-ex-group-h { display: flex; align-items: center; gap: 8px; padding: 8px 12px; font-size: 10px; font-weight: var(--pp-weight-bold);
  text-transform: uppercase; letter-spacing: 0.06em; color: var(--pp-text-tertiary); background: var(--pp-bg-sunken); border-bottom: 1px solid var(--pp-border-subtle); }
.crmn-ex-count { font-variant-numeric: tabular-nums; color: var(--pp-text-secondary); }
.crmn-ex-row { display: flex; align-items: center; gap: 8px; width: 100%; min-height: 48px; padding: 10px 12px;
  border: 0; border-bottom: 1px solid var(--pp-border-subtle); background: transparent; cursor: pointer; text-align: left; }
.crmn-ex-row:last-child { border-bottom: 0; }
.crmn-ex-row:hover { background: var(--pp-bg-hover); }
.crmn-ex-row.is-static { cursor: default; }
.crmn-ex-row-l { flex: 1; min-width: 0; font-size: var(--pp-fs-14, 14px); color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmn-ex-row-m { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); white-space: nowrap; }
.crmn-ex-chev { width: 16px; height: 16px; color: var(--pp-text-tertiary); flex-shrink: 0; }
.crmn-ex-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.crmn-ex-dot.is-org { background: var(--pp-brand-primary); }
.crmn-ex-dot.is-person { background: var(--pp-state-info); }
.crmn-ex-empty { padding: 12px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-tertiary); }

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
