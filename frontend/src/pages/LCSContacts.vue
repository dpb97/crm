<!--
  LCSContacts — CRM-Personen (Pilanda-UX, Analog zu LCSLeads).
  ============================================================
  Bespoke Pilanda-Seite für „Personen" (Contacts): PpPageHead + KPI-Strip
  (PpStatTile) + Filterleiste (Suche + Firma) + PpDataGrid (Name/Firma/Telefon/
  E-Mails/Zuletzt geändert). Einfachklick öffnet den angedockten Shell-Inspektor
  (ContactInspector); Doppelklick oder „Öffnen" → volle Detailseite. Ersetzt die
  generische Upstream-Liste (die als /contacts-upstream erreichbar bleibt).

  Echte Daten (kein Demo): frappe.client.get_list('Contact') +
  lcs_integrations.projects.api.get_contact_email_counts.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Contacts'), route: { name: 'Contacts' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <PpPageHead
          :title="__('Contacts')"
          :subtitle="__('click a row to open the profile')"
        />

        <!-- Filterleiste: Suche + Listen-/Karten-Umschalter (Referenz: Calls) -->
        <PpFilterBar
          v-model:search="q"
          :placeholder="__('Search / filter by company') + ' …'"
        >
          <template #actions>
            <div class="crmc-viewtoggle">
              <button type="button" class="crmc-vt-btn" :class="{ 'is-active': viewMode === 'list' }" :title="__('List')" @click="viewMode = 'list'"><IconList /></button>
              <button type="button" class="crmc-vt-btn" :class="{ 'is-active': viewMode === 'cards' }" :title="__('Cards')" @click="viewMode = 'cards'"><IconGrid /></button>
            </div>
          </template>
        </PpFilterBar>

        <!-- KPI-Karten = klickbare Segment-Filter (Master Regel 9: keine
             separate Deko-Filterzeile; Firma-Filtern via Suche). -->
        <section class="crmc-kpis">
          <button
            v-for="k in kpis"
            :key="k.seg"
            type="button"
            class="crmc-kpi"
            :class="{ 'is-active': segment === k.seg }"
            @click="toggleSeg(k.seg)"
          >
            <PpStatTile :label="k.label" :value="k.value" :hint="k.hint" />
          </button>
        </section>

        <!-- Tabelle ODER Leerzustand -->
        <PpTableCard :title="__('Contacts')" :shown="filtered.length" :total="contacts.length">
          <PpDataGrid table-key="lcs_contacts" v-if="rows.length && viewMode === 'list'" :columns="columns" :rows="rows" :page-size="25" pickable v-model:pick-mode="selectMode" v-model:picked="picked" @row-click="openContact">
            <template #cell-name="{ row }">
              <span class="pp-cell-strong">{{ row.name }}</span>
              <span class="pp-cell-sub">{{ row.email || '—' }}</span>
            </template>
            <template #cell-company_name="{ value }">
              <a v-if="value" class="crmc-firma-link" @click.stop.prevent="openFirma(value)">{{ value }}</a>
              <span v-else class="pp-cell-muted">—</span>
            </template>
            <template #cell-mobile_no="{ value }">
              <span class="crmc-contact-line crmc-contact-line--muted">
                <IconPhone v-if="value" class="crmc-contact-ico" />{{ value || '—' }}
              </span>
            </template>
            <template #cell-email_count="{ value }">
              <span class="crmc-count" :data-zero="value === '0' ? 'true' : 'false'">{{ value }}</span>
            </template>
            <template #cell-last_contact="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value ? fmtDate(value) : '—' }}</span>
            </template>
            <template #cell-modified="{ value }">
              <span class="pp-cell-muted">{{ fmtDate(value) }}</span>
            </template>
          </PpDataGrid>

          <!-- Karten-Ansicht (Theme PpContactCards als reiner Renderer; eigene
               Toolbar per CSS aus, meine Suche/KPI/Pagination bleiben). -->
          <div v-else-if="rows.length" class="crmc-scroll">
            <PpContactCards
              class="crmc-cards"
              :people="cardPeople"
              view="cards"
              :searchable="false"
              :action-label="__('Open record')"
              @select="(p) => openContact(p.id)"
              @action="(p) => openDetail(p.id)"
            />
          </div>

          <PpEmptyState
            v-else-if="hasFilter"
            :icon="IconSearchX"
            :title="__('No contacts found')"
            :hint="__('No matches for the current filter/search.')"
          >
            <template #action>
              <button class="crmc-btn crmc-btn--primary" @click="resetFilter">{{ __('Reset filters') }}</button>
            </template>
          </PpEmptyState>
          <PpEmptyState
            v-else
            :icon="IconInbox"
            :title="loading ? __('Loading …') : __('No contacts yet')"
            :hint="loading ? '' : __('Contacts created in the CRM will appear here.')"
          />

          <!-- Card view keeps the external pager; the list view paginates inside PpDataGrid. -->
          <template v-if="viewMode === 'cards' && rows.length && rowTotal > 25" #footer>
            <LcsPagination
              :from="pgFrom" :to="pgTo" :total="rowTotal"
              :page="page" :page-count="pageCount" :page-size="pageSize"
              @prev="pgPrev" @next="pgNext" @page-size="setPageSize"
            />
          </template>
        </PpTableCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpContactCards from '@/components/pp/PpContactCards.vue'
import ContactInspector from '@/components/lcs/ContactInspector.vue'
import LcsPagination from '@/components/lcs/LcsPagination.vue'
import IconSearchX from '~icons/lucide/search-x'
import IconInbox from '~icons/lucide/inbox'
import IconPhone from '~icons/lucide/phone'
import IconList from '~icons/lucide/list'
import IconGrid from '~icons/lucide/layout-grid'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { useListFuncbar } from '@/composables/useListFuncbar'
import { usePagination } from '@/composables/usePagination'
import { useProfileSetting } from '@/composables/useProfileSetting'

const router = useRouter()
const { pilandaMode } = usePilandaMode()
const { inspectPanel } = usePilandaInspect()

// --- Daten: echte CRM-Kontakte --------------------------------------------
const contactsRes = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Contact',
    fields: [
      'name', 'full_name', 'first_name', 'last_name', 'company_name',
      'email_id', 'mobile_no', 'phone', 'modified',
    ],
    order_by: 'modified desc',
    limit_page_length: 0,
  },
  auto: true,
})
const contacts = computed(() => contactsRes.data || [])
const loading = computed(() => contactsRes.loading)
function reload() { contactsRes.reload() }

const selectMode = ref(false)
const picked = ref([])
function exportRows() {
  const src = picked.value.length ? rows.value.filter((r) => picked.value.includes(r.id)) : rows.value
  if (!src.length) { toast({ title: __('Nothing to export.'), icon: 'alert-circle' }); return }
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [['Person', 'Firma', 'E-Mail', 'Telefon'].map(esc).join(',')]
  src.forEach((r) => lines.push([r.name, r.company_name, r.email, r.mobile_no].map(esc).join(',')))
  const blob = new Blob(['﻿' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'personen.csv'; a.click(); URL.revokeObjectURL(a.href)
  toast({ title: `${src.length} ${__('exported')}`, icon: 'check-circle', iconClasses: 'text-green-500' })
}
// Ausgewählte Kontakte löschen (z.B. interne Mitarbeiter / Fehlimporte raus).
async function deleteSelected() {
  const ids = picked.value.slice()
  if (!ids.length) { toast({ title: __('Nothing selected.'), icon: 'alert-circle' }); return }
  if (!window.confirm(__('Delete {0} contact(s)? This cannot be undone.').replace('{0}', ids.length))) return
  let ok = 0
  const failed = []
  for (const id of ids) {
    try { await call('frappe.client.delete', { doctype: 'Contact', name: id }); ok++ }
    catch (e) { failed.push(id) }
  }
  picked.value = []
  selectMode.value = false
  reload()
  toast(failed.length
    ? { title: `${ok} ${__('deleted')} · ${failed.length} ${__('failed (still linked)')}`, icon: 'alert-circle' }
    : { title: `${ok} ${__('deleted')}`, icon: 'check-circle', iconClasses: 'text-green-500' })
}
// Selected person (inspector), so „Neue Aufgabe" links to that contact, not the page.
const selectedId = ref(null)
useListFuncbar({ title: __('Contacts'), meaning: __('Contacts in the CRM.'), count: () => contacts.value.length, reload, exportRows, selectMode, pickedCount: () => picked.value.length,
  taskRef: () => { const c = rows.value.find((r) => r.id === selectedId.value); return c ? { doctype: 'Contact', name: c.id, title: c.name } : null },
  actions: [{ id: 'delete-selected', label: __('Delete selected'), group: 'werkzeuge', run: deleteSelected }] })

// --- E-Mail-Anzahl je Kontakt (LCS-API) -----------------------------------
const emailCounts = ref({})
watch(
  contacts,
  async (list) => {
    const names = (list || []).map((c) => c.name).filter(Boolean)
    if (!names.length) return
    try {
      emailCounts.value = await call(
        'lcs_integrations.projects.api.get_contact_email_counts',
        { contacts: names },
      )
    } catch (e) {
      /* non-fatal — column shows 0 */
    }
  },
  { immediate: true },
)

// --- Anzeige-Helfer --------------------------------------------------------
function displayName(c) {
  return (
    c.full_name ||
    [c.first_name, c.last_name].filter(Boolean).join(' ') ||
    c.email_id ||
    c.name
  )
}
function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleDateString('de-DE')
}

// --- Filter: Suche (inkl. Firma) + KPI-Segment (Master Regel 9) ------------
const q = ref('')
const segment = ref('') // '' | 'company' | 'email' | 'week'
const hasFilter = computed(() => q.value.trim() !== '' || segment.value !== '')
function resetFilter() { q.value = ''; segment.value = '' }
function toggleSeg(seg) { segment.value = seg === '' ? '' : (segment.value === seg ? '' : seg) }

const WEEK_MS = 7 * 24 * 3600 * 1000
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  const weekAgo = Date.now() - WEEK_MS
  return contacts.value.filter((c) => {
    const qOk = !needle ||
      displayName(c).toLowerCase().includes(needle) ||
      (c.company_name || '').toLowerCase().includes(needle) ||
      (c.email_id || '').toLowerCase().includes(needle)
    let sOk = true
    if (segment.value === 'company') sOk = !!c.company_name
    else if (segment.value === 'email') sOk = !!c.email_id
    else if (segment.value === 'week') {
      const t = c.modified ? new Date(c.modified).getTime() : NaN
      sOk = !isNaN(t) && t >= weekAgo
    }
    return qOk && sOk
  })
})

// --- KPI-Karten (klickbare Segmente) --------------------------------------
const kpis = computed(() => {
  const list = contacts.value
  const withCompany = list.filter((c) => c.company_name).length
  const withEmail = list.filter((c) => c.email_id).length
  const weekAgo = Date.now() - WEEK_MS
  const weekCount = list.filter((c) => {
    const t = c.modified ? new Date(c.modified).getTime() : NaN
    return !isNaN(t) && t >= weekAgo
  }).length
  return [
    { seg: '', label: __('Total contacts'), value: String(list.length), hint: __('in the CRM') },
    { seg: 'company', label: __('With company'), value: String(withCompany), hint: __('assigned to a Firma') },
    { seg: 'email', label: __('With email'), value: String(withEmail), hint: __('reachable by mail') },
    { seg: 'week', label: __('Updated this week'), value: String(weekCount), hint: __('last 7 days') },
  ]
})

// --- Tabelle ---------------------------------------------------------------
const columns = [
  { key: 'name', label: __('Contact'), pin: true, width: 260 },
  { key: 'company_name', label: __('Company'), width: 220 },
  { key: 'mobile_no', label: __('Phone'), width: 170 },
  { key: 'email_count', label: __('Emails'), align: 'right', width: 100 },
  { key: 'last_contact', label: __('Last contact'), align: 'right', width: 150 },
  { key: 'modified', label: __('Last modified'), align: 'right', width: 150 },
]
const lastContactRes = createResource({ url: 'lcs_integrations.projects.api.get_last_contact_dates', params: { doctype: 'Contact' }, auto: true })
const lastContact = computed(() => lastContactRes.data || {})
const rows = computed(() =>
  filtered.value.map((c) => ({
    id: c.name,
    name: displayName(c),
    email: c.email_id,
    company_name: c.company_name,
    mobile_no: c.mobile_no || c.phone,
    last_contact: lastContact.value[c.name] || '',
    email_count: String(emailCounts.value[c.name] ?? 0),
    modified: c.modified,
  })),
)

// --- Pagination (client-side; the list loads all rows) ---------------------
const {
  paged: pagedRows, page, pageCount, total: rowTotal,
  from: pgFrom, to: pgTo, pageSize, next: pgNext, prev: pgPrev, setPageSize,
} = usePagination(rows)

// Listen-/Karten-Umschalter (Karten via PpContactCards, gefüttert aus den
// paginierten Zeilen — KPI-Filter + Pagination gelten in beiden Ansichten).
const viewMode = useProfileSetting('lcs_contacts', 'view', 'list')
const cardPeople = computed(() =>
  pagedRows.value.map((r) => ({
    id: r.id,
    name: r.name,
    company: r.company_name,
    email: r.email,
    phone: r.mobile_no,
  })),
)

// --- Klick → Inspektor -----------------------------------------------------
let lastClick = { id: null, t: 0 }
function openContact(id) {
  if (!id) return
  if (!pilandaMode.value) {
    openDetail(id)
    return
  }
  const now = Date.now()
  if (lastClick.id === id && now - lastClick.t < 350) {
    lastClick = { id: null, t: 0 }
    openDetail(id)
    return
  }
  lastClick = { id, t: now }
  selectedId.value = id
  inspectPanel({
    component: ContactInspector,
    props: { contactId: id },
    on: { open: openDetail },
    title: __('Contact'),
    ref: { doctype: 'Contact', name: id, title: rows.value.find((r) => r.id === id)?.name || id },
  })
}
function openDetail(id) {
  router.push({ name: 'Contact', params: { contactId: id } })
}
// Absprungpunkt zur Firma: company_name ist der CRM-Organization-Docname.
function openFirma(name) {
  if (name) router.push({ name: 'Organization', params: { organizationId: name } })
}
onBeforeUnmount(() => {
  if (pilandaMode.value) inspectPanel(null)
})
</script>

<style scoped>
/* Karten-Ansicht scrollt in ihrem eigenen Bereich (die Tabelle bringt ihren mit). */
.crmc-scroll { flex: 1; min-height: 0; overflow: auto; }

.crmc-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.crmc-btn:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crmc-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.crmc-btn--primary:hover { filter: brightness(1.05); color: var(--pp-text-on-accent); }

.crmc-firma-link { color: var(--pp-brand-primary); cursor: pointer; text-decoration: none; }
.crmc-firma-link:hover { text-decoration: underline; }
.crmc-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); flex-shrink: 0; }

/* Scroll-Fix: auf kurzen Viewports fressen die KPI-Kacheln die Tabellenhöhe →
   die Seite scrollt jetzt, die Tabelle behält eine nutzbare Mindesthöhe
   (interner Datagrid-Scroll mit fixem Kopf bleibt). Scrollbalken versteckt. */
.pp-listpage__inner { overflow-y: auto; scrollbar-width: none; }
.pp-listpage__inner::-webkit-scrollbar { width: 0; height: 0; }
:deep(.pp-tablecard) { min-height: 360px; }

/* KPI-Karten als klickbare Segment-Filter (Regel 9) */
.crmc-kpi { appearance: none; border: none; background: none; padding: 0; margin: 0; cursor: pointer;
  text-align: left; border-radius: var(--pp-radius-ui); outline: none; }
.crmc-kpi > :deep(.pp-kpi) { transition: box-shadow .12s, border-color .12s; }
.crmc-kpi:hover > :deep(.pp-kpi) { border-color: var(--pp-brand-primary); }
.crmc-kpi.is-active > :deep(.pp-kpi) { border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--pp-brand-primary) 30%, transparent); }
.crmc-kpi:focus-visible > :deep(.pp-kpi) { box-shadow: var(--pp-shadow-focus-ring, 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.3)); }

/* Listen-/Karten-Umschalter */
.crmc-viewtoggle { display: inline-flex; gap: 2px; padding: 2px; border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-subtle); }
.crmc-vt-btn { appearance: none; cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 28px; border: none; border-radius: var(--pp-radius-ui); background: transparent; color: var(--pp-text-tertiary); }
.crmc-vt-btn:hover { color: var(--pp-brand-primary); }
.crmc-vt-btn.is-active { background: var(--pp-bg-surface); color: var(--pp-brand-primary); box-shadow: var(--pp-shadow-xs); }
.crmc-vt-btn :deep(svg) { width: 15px; height: 15px; }
/* PpContactCards als reiner Karten-Renderer: eigene Toolbar aus. */
.crmc-cards :deep(.pp-contacts__bar) { display: none; }

/* Zell-Renderer, die über die gemeinsamen pp-cell-* Rollen hinausgehen. */
.crmc-contact-line { display: inline-flex; align-items: center; gap: 5px; font-size: var(--pp-fs-12);
  color: var(--pp-text-secondary); font-variant-numeric: tabular-nums;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmc-contact-line--muted { color: var(--pp-text-tertiary); }
.crmc-contact-ico { width: 13px; height: 13px; flex-shrink: 0; }
.crmc-count { font-variant-numeric: tabular-nums; font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary); }
.crmc-count[data-zero="true"] { color: var(--pp-text-tertiary); font-weight: var(--pp-weight-regular); }

@media (max-width: 1080px) {
  .crmc-kpis { grid-template-columns: repeat(2, 1fr); }
}

/* Kleiner Bildschirm (kurz oder schmal): KPI-Kacheln ausblenden, damit die
   Tabelle die volle Höhe bekommt (Zählungen stehen weiter in der Karten-Kopfzeile). */
@media (max-height: 820px), (max-width: 900px) {
  .crmc-kpis { display: none; }
}
</style>
