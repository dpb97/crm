<template>
  <LayoutHeader v-if="contact.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="contact._actions?.length"
        :actions="contact._actions"
      />
    </template>
  </LayoutHeader>
  <div v-if="contact.doc" ref="parentRef" class="flex h-full">
    <Resizer
      v-if="contact.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeContactImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5 ring-2 ring-lcs-secondary/25 ring-offset-2"
                    :label="contact.doc.full_name"
                    :image="contact.doc.image"
                  />
                  <component
                    :is="contact.doc.image ? Dropdown : 'div'"
                    v-bind="
                      contact.doc.image
                        ? {
                            options: [
                              {
                                icon: 'upload',
                                label: contact.doc.image
                                  ? __('Change Image')
                                  : __('Upload Image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'trash-2',
                                label: __('Remove Image'),
                                onClick: () => changeContactImage(''),
                              },
                            ],
                          }
                        : { onClick: openFileSelector }
                    "
                    class="!absolute bottom-0 left-0 right-0"
                  >
                    <div
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-md bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      "
                    >
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-2 truncate text-ink-gray-9">
                  <div class="truncate text-2xl font-medium">
                    <span v-if="contact.doc.salutation">
                      {{ contact.doc.salutation + ' ' }}
                    </span>
                    <span>{{ contact.doc.full_name }}</span>
                  </div>
                  <button
                    v-if="contact.doc.company_name"
                    type="button"
                    class="flex w-fit items-center gap-1.5 rounded-full bg-surface-gray-2 px-2.5 py-1 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-3 hover:text-lcs-secondary"
                    @click="goFirma(contact.doc.company_name)"
                  >
                    <FeatherIcon name="briefcase" class="h-3.5 w-3.5" />
                    {{ contact.doc.company_name }}
                  </button>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>
              <!-- LCS: quick communication actions — own full-width row below
                   the avatar so the narrow name column can't clip them -->
              <QuickContactActions
                class="w-full"
                :email="contact.doc.email_id"
                :phone="contact.doc.mobile_no"
              />
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled && contact.doc.mobile_no"
                  :label="__('Make Call')"
                  size="sm"
                  :iconLeft="PhoneIcon"
                  @click="callEnabled && makeCall(contact.doc.mobile_no)"
                />
                <Button
                  v-if="canDelete"
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  iconLeft="trash-2"
                  @click="deleteContact()"
                />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="parsedSections"
          doctype="Contact"
          :docname="contact.doc.name"
          @reload="sections.reload"
        />
      </div>
    </Resizer>
    <Tabs
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-item="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b-2 border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:text-ink-gray-9"
          :class="{ 'text-ink-gray-9 !border-lcs-secondary': selected }"
        >
          <component :is="tab.icon" v-if="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-surface-gray-7"
            :class="[selected ? 'bg-surface-gray-7' : 'bg-gray-600']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </template>
      <template #tab-panel="{ tab }">
        <!-- LCS: mailbox-synced emails -->
        <OrgEmailsTab
          v-if="tab.label === 'Emails'"
          :emails="contactEmails.data"
        />
        <!-- LCS: network — employment history + person relationships -->
        <div
          v-else-if="tab.label === 'Netzwerk'"
          class="mt-4 flex w-full flex-col gap-6 overflow-y-auto px-5 pb-6"
        >
          <RelationEditor
            :doctype="'Contact'" :name="contact.doc.name" fieldname="lcs_employment"
            :title="__('Employment history')" :columns="employmentColumns"
          />
          <RelationEditor
            :doctype="'Contact'" :name="contact.doc.name" fieldname="lcs_relations"
            :title="__('Relations / friends')" :columns="relationColumns"
          />
        </div>
        <template v-else>
          <DealsListView
            v-if="tab.label === 'Deals' && rows.length"
            class="mt-4"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <EmptyState v-if="!rows.length" :icon="tab.icon" name="Deals" />
        </template>
      </template>
    </Tabs>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'Contact'"
    :docname="contact.doc.name"
    name="Contacts"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import OrgEmailsTab from '@/components/lcs/OrgEmailsTab.vue'
import RelationEditor from '@/components/lcs/RelationEditor.vue'
import NetworkIcon from '~icons/lucide/share-2'
import CustomActions from '@/components/CustomActions.vue'
import {
  formatDate,
  timeAgo,
  validateIsImageFile,
  setupCustomizations,
} from '@/utils'
import { getView } from '@/utils/view'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Tabs,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
  FeatherIcon,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useTaskContext } from '@/composables/useTaskContext'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/components/ListViews/EmptyState.vue'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()
// LCS: jump from the contact to its company (Organization); company_name is the org docname.
function goFirma(name) {
  if (name) router.push({ name: 'Organization', params: { organizationId: name } })
}

const errorTitle = ref('')
const errorMessage = ref('')

const {
  document: contact,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

// Feed the shell task context so „Neue Aufgabe" links back to this contact.
const { setTaskContext } = useTaskContext()
watch(() => contact.doc, (d) => setTaskContext(d ? { doctype: 'Contact', name: props.contactId, title: d.full_name || props.contactId } : null), { immediate: true })
onUnmounted(() => setTaskContext(null))

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Contact', params: { contactId: props.contactId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})
const showDeleteLinkedDocModal = ref(false)

async function deleteContact() {
  showDeleteLinkedDocModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}

const tabIndex = ref(0)
// LCS: network relation columns (mirrors ContactInspector)
const employmentColumns = [
  { key: 'organization', type: 'link', options: 'CRM Organization', label: __('Company') },
  { key: 'role', type: 'text', label: __('Role') },
  { key: 'start_date', type: 'date', label: __('From') },
  { key: 'end_date', type: 'date', label: __('To') },
  { key: 'is_current', type: 'check', label: __('Current') },
]
const relationColumns = [
  { key: 'related_contact', type: 'link', options: 'Contact', label: __('Person') },
  { key: 'relation_type', type: 'select', opts: ['Freund', 'Kollege', 'Bekannt', 'Familie'], label: __('Relation') },
]
const tabs = [
  {
    label: 'Deals',
    icon: DealsIcon,
    count: computed(() => deals.data?.length),
  },
  // LCS: mailbox-synced emails linked to this contact
  {
    label: 'Emails',
    icon: EmailIcon,
    count: computed(() => contactEmails.data?.length),
  },
  // LCS: network — employment history + person relationships
  {
    label: 'Netzwerk',
    icon: NetworkIcon,
    count: computed(
      () => (contact.doc?.lcs_employment?.length || 0) + (contact.doc?.lcs_relations?.length || 0),
    ),
  },
]

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

// LCS: emails linked to this contact for the Emails tab
const contactEmails = createResource({
  url: 'lcs_integrations.projects.api.get_contact_emails',
  params: { contact: props.contactId },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data.map((section) => ({
    ...section,
    columns: section.columns.map((column) => ({
      ...column,
      fields: column.fields.map((field) => {
        field.label = fieldLabelMap[field.fieldname] || field.label
        field.placeholder =
          fieldPlaceholderMap[field.fieldname] || field.placeholder

        if (field.fieldname === 'email_id') {
          return {
            ...field,
            read_only: false,
            hidden: false,
            fieldtype: 'Dropdown',
            options: (contact.doc?.email_ids || []).map((email) => ({
              name: email.name,
              value: email.email_id,
              selected: email.email_id === contact.doc.email_id,
              placeholder: 'john@doe.com',
              onClick: () => setAsPrimary('email', email.email_id),
              onSave: (option, isNew) =>
                isNew
                  ? createNew('email', option.value)
                  : editOption(
                      'Contact Email',
                      option.name,
                      'email_id',
                      option.value,
                    ),
              onDelete: async (option, isNew) => {
                contact.doc.email_ids = contact.doc.email_ids.filter(
                  (e) => e.name !== option.name,
                )
                if (!isNew) await deleteOption('Contact Email', option.name)
              },
            })),
            create: () => {
              // Add a temporary new option locally (mirrors original behavior)
              contact.doc.email_ids = [
                ...(contact.doc.email_ids || []),
                {
                  name: 'new-1',
                  value: '',
                  selected: false,
                  isNew: true,
                },
              ]
            },
          }
        }
        if (field.fieldname === 'mobile_no') {
          // LCS: simple phone field — country dial-code dropdown + number input.
          return { ...field, read_only: false, hidden: false, fieldtype: 'PhoneInput' }
        }
        if (field.fieldname === 'address') {
          return {
            ...field,
            create: (_value, close) => {
              showAddressModal()
              close?.()
            },
            edit: (address) => showAddressModal(address),
          }
        }
        return field
      }),
    })),
  }))
})

const fieldLabelMap = {
  mobile_no: __('Mobile Number'),
  company_name: __('Organization'),
}

const fieldPlaceholderMap = {
  mobile_no: __('Add Mobile Number...'),
  company_name: __('Add Organization...'),
}

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: contact.doc.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact Updated'))
  }
}

async function createNew(field, value) {
  if (!value) return
  let d = await call('crm.api.contact.create_new', {
    contact: contact.doc.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact Updated'))
  }
}

async function editOption(doctype, name, fieldname, value) {
  let d = await call('frappe.client.set_value', {
    doctype,
    name,
    fieldname,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact Updated'))
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await contact.reload()
  toast.success(__('Contact Updated'))
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    annual_revenue: getFormattedCurrency('annual_revenue', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: {
      label: formatDate(deal.modified),
      timeAgo: __(timeAgo(deal.modified)),
    },
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'annual_revenue',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile No.'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField: contact.setValue.submit,
        createToast: toast.create,
        deleteDoc: deleteContact,
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
