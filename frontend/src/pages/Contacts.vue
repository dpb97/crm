<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Contacts" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showContactModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Contact"
  />
  <ContactsListView
    v-if="contacts.data && rows.length"
    ref="contactsListView"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
      onRowClick: rowInspect,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="contacts.data && !rows.length"
    name="Contacts"
    :icon="ContactsIcon"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{}"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import ContactInspector from '@/components/lcs/ContactInspector.vue'
import { getMeta } from '@/stores/meta'
import { organizationsStore } from '@/stores/organizations.js'
import { formatDate, timeAgo } from '@/utils'
import { call } from 'frappe-ui'
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()

// LCS (Pilanda): single-click a row → docked shell inspector (ContactInspector);
// double-click or the inspector's "Open" → full contact detail. In CRM-only
// mode there is no shell inspector, so a click navigates straight to detail.
const router = useRouter()
const { pilandaMode } = usePilandaMode()
const { inspectPanel } = usePilandaInspect()

let lastClick = { id: null, t: 0 }
function rowInspect(row) {
  const id = row?.name
  if (!id) return
  if (!pilandaMode.value) {
    openContact(id)
    return
  }
  const now = Date.now()
  if (lastClick.id === id && now - lastClick.t < 350) {
    lastClick = { id: null, t: 0 }
    openContact(id)
    return
  }
  lastClick = { id, t: now }
  inspectPanel({
    component: ContactInspector,
    props: { contactId: id },
    on: { open: openContact },
    title: __('Contact'),
  })
}
function openContact(id) {
  router.push({ name: 'Contact', params: { contactId: id } })
}
onBeforeUnmount(() => {
  if (pilandaMode.value) inspectPanel(null)
})

const showContactModal = ref(false)

const contactsListView = ref(null)

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// LCS: count of e-mails directly linked to each contact, shown as a column
const emailCounts = ref({})
watch(
  () => contacts.value?.data?.data,
  async (data) => {
    const names = (data || []).map((c) => c.name).filter(Boolean)
    if (!names.length) return
    try {
      emailCounts.value = await call(
        'lcs_integrations.projects.api.get_contact_email_counts',
        { contacts: names },
      )
    } catch (e) {
      // non-fatal: the column just shows 0
    }
  },
  { immediate: true },
)

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
    contacts.value?.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      let fieldType = contacts.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(contact[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, contact)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, contact)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, contact)
      }

      if (row == 'full_name') {
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(contact[row]),
          timeAgo: __(timeAgo(contact[row])),
        }
      }
    })
    // LCS: e-mail count per contact (string so a 0 still renders in the cell)
    _rows['email_count'] = String(emailCounts.value[contact.name] ?? 0)
    return _rows
  })
})

const columns = computed(() => {
  let _columns = contacts.value?.data?.columns || []

  // LCS: append an e-mail count column
  if (_columns.length) {
    _columns = [
      ..._columns,
      { label: __('Emails'), key: 'email_count', type: 'Data', width: '6rem' },
    ]
  }

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})
</script>
