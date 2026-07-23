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
        <Breadcrumbs :items="[{ label: __('Contacts'), route: { name: 'Contacts' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" />
      </template>
    </LayoutHeader>

    <div class="crmc">
      <div class="crmc-inner">
        <PpPageHead
          :eyebrow="__('Sales / CRM')"
          :title="__('Contacts')"
          :subtitle="`${filtered.length} ${__('of')} ${contacts.length} ${__('Contacts')} · ${__('click a row to open the profile')}`"
        />

        <!-- KPI-Strip -->
        <section class="crmc-kpis">
          <PpStatTile v-for="k in kpis" :key="k.label" v-bind="k" />
        </section>

        <!-- Filterleiste -->
        <section class="crmc-filter">
          <div class="crmc-field crmc-field--search">
            <label class="crmc-field-cap">{{ __('Search') }}</label>
            <input v-model="q" type="search" class="crmc-input" :placeholder="__('Search') + ' …'" />
          </div>
          <div class="crmc-field">
            <label class="crmc-field-cap">{{ __('Company') }}</label>
            <select v-model="fCompany" class="crmc-input">
              <option value="alle">{{ __('All companies') }}</option>
              <option v-for="c in companyList" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <button v-if="hasFilter" class="crmc-btn crmc-reset" @click="resetFilter">{{ __('Reset filters') }}</button>
        </section>

        <!-- Tabelle ODER Leerzustand -->
        <section class="crmc-card">
          <template v-if="rows.length">
          <div class="crmc-scroll">
          <PpDataGrid :columns="columns" :rows="pagedRows" @row-click="openContact">
            <template #cell-name="{ row }">
              <span class="crmc-name">{{ row.name }}</span>
              <span class="crmc-id">{{ row.email || '—' }}</span>
            </template>
            <template #cell-company_name="{ value }">
              <span :class="{ 'crmc-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-mobile_no="{ value }">
              <span class="crmc-contact-line crmc-contact-line--muted">
                <IconPhone v-if="value" class="crmc-contact-ico" />{{ value || '—' }}
              </span>
            </template>
            <template #cell-email_count="{ value }">
              <span class="crmc-count" :data-zero="value === '0' ? 'true' : 'false'">{{ value }}</span>
            </template>
            <template #cell-modified="{ value }">
              <span class="crmc-muted">{{ fmtDate(value) }}</span>
            </template>
          </PpDataGrid>
          </div>
          <LcsPagination
            v-if="rowTotal > 25"
            :from="pgFrom" :to="pgTo" :total="rowTotal"
            :page="page" :page-count="pageCount" :page-size="pageSize"
            @prev="pgPrev" @next="pgNext" @page-size="setPageSize"
          />
          </template>

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
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import ContactInspector from '@/components/lcs/ContactInspector.vue'
import LcsPagination from '@/components/lcs/LcsPagination.vue'
import IconSearchX from '~icons/lucide/search-x'
import IconInbox from '~icons/lucide/inbox'
import IconPhone from '~icons/lucide/phone'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { usePagination } from '@/composables/usePagination'

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

// --- Filter ----------------------------------------------------------------
const q = ref('')
const fCompany = ref('alle')
const hasFilter = computed(() => q.value.trim() !== '' || fCompany.value !== 'alle')
function resetFilter() { q.value = ''; fCompany.value = 'alle' }

const companyList = computed(() =>
  [...new Set(contacts.value.map((c) => c.company_name).filter(Boolean))].sort(),
)

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return contacts.value.filter((c) => {
    const qOk = !needle ||
      displayName(c).toLowerCase().includes(needle) ||
      (c.company_name || '').toLowerCase().includes(needle) ||
      (c.email_id || '').toLowerCase().includes(needle)
    const cOk = fCompany.value === 'alle' || c.company_name === fCompany.value
    return qOk && cOk
  })
})

// --- KPI-Strip -------------------------------------------------------------
const kpis = computed(() => {
  const list = contacts.value
  const withCompany = list.filter((c) => c.company_name).length
  const withEmail = list.filter((c) => c.email_id).length
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000
  const weekCount = list.filter((c) => {
    const t = c.modified ? new Date(c.modified).getTime() : NaN
    return !isNaN(t) && t >= weekAgo
  }).length
  return [
    { label: __('Total contacts'), value: String(list.length), hint: __('in the CRM') },
    { label: __('With company'), value: String(withCompany), hint: __('assigned to a Firma') },
    { label: __('With email'), value: String(withEmail), hint: __('reachable by mail') },
    { label: __('Updated this week'), value: String(weekCount), hint: __('last 7 days') },
  ]
})

// --- Tabelle ---------------------------------------------------------------
const columns = [
  { key: 'name', label: __('Contact'), pin: true, width: 260 },
  { key: 'company_name', label: __('Company'), width: 220 },
  { key: 'mobile_no', label: __('Phone'), width: 170 },
  { key: 'email_count', label: __('Emails'), align: 'right', width: 100 },
  { key: 'modified', label: __('Last modified'), align: 'right', width: 150 },
]
const rows = computed(() =>
  filtered.value.map((c) => ({
    id: c.name,
    name: displayName(c),
    email: c.email_id,
    company_name: c.company_name,
    mobile_no: c.mobile_no || c.phone,
    email_count: String(emailCounts.value[c.name] ?? 0),
    modified: c.modified,
  })),
)

// --- Pagination (client-side; the list loads all rows) ---------------------
const {
  paged: pagedRows, page, pageCount, total: rowTotal,
  from: pgFrom, to: pgTo, pageSize, next: pgNext, prev: pgPrev, setPageSize,
} = usePagination(rows)

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
  inspectPanel({
    component: ContactInspector,
    props: { contactId: id },
    on: { open: openDetail },
    title: __('Contact'),
  })
}
function openDetail(id) {
  router.push({ name: 'Contact', params: { contactId: id } })
}
onBeforeUnmount(() => {
  if (pilandaMode.value) inspectPanel(null)
})
</script>

<style scoped>
/* Vollbreiten-Canvas (kein max-width), token-only — Idiom von LCSLeads. */
/* Fixed viewport-height layout: header/KPIs/filter stay put, the table scrolls
   inside its own region so the page never grows taller than the screen. */
.crmc { flex: 1; min-height: 0; overflow: hidden; background: var(--pp-bg-base); display: flex; flex-direction: column; }
.crmc-inner { flex: 1; min-height: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-6);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }
.crmc-scroll { flex: 1; min-height: 0; overflow: auto; }

.crmc-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.crmc-btn:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crmc-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.crmc-btn--primary:hover { filter: brightness(1.05); color: var(--pp-text-on-accent); }

.crmc-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

.crmc-filter { display: flex; align-items: flex-end; gap: var(--pp-space-3); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmc-field { display: flex; flex-direction: column; gap: 3px; }
.crmc-field--search { flex: 1 1 240px; min-width: 200px; }
.crmc-field-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmc-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 6px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); min-width: 150px; }
.crmc-input:focus { outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crmc-reset { margin-left: auto; }

.crmc-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-2);
  flex: 1; min-height: 0; display: flex; flex-direction: column; }

.crmc-name { display: block; font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crmc-id { display: block; font-size: 11px; color: var(--pp-text-tertiary); }
.crmc-muted { color: var(--pp-text-tertiary); }
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
</style>
