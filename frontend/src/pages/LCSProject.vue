<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="doc.name" #right-header>
      <Dropdown v-if="phaseDropdownOptions.length" :options="phaseDropdownOptions" placement="right">
        <template #default="{ open }">
          <Button :label="__(doc.phase || 'Set Phase')" :iconRight="open ? 'chevron-up' : 'chevron-down'">
            <template #prefix>
              <span
                class="h-2 w-2 rounded-full"
                :class="phaseDotClass(doc.phase)"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <!-- Tabbed content area -->
    <Tabs
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel>
        <div class="flex-1 overflow-y-auto p-5">
          <!-- Overview Tab -->
          <div v-if="activeTab === 'Overview'" class="space-y-6">
            <div>
              <h3 class="mb-2 text-sm font-medium text-gray-500">{{ __('Description') }}</h3>
              <p v-if="doc.project_description" class="text-sm text-gray-800 whitespace-pre-wrap">
                {{ doc.project_description }}
              </p>
              <p v-else class="text-sm text-gray-400">{{ __('No description') }}</p>
            </div>
            <div v-if="doc.notes">
              <h3 class="mb-2 text-sm font-medium text-gray-500">{{ __('Notes') }}</h3>
              <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ doc.notes }}</p>
            </div>
          </div>

          <!-- Contacts Tab -->
          <div v-if="activeTab === 'Contacts'" class="space-y-3">
            <div v-if="contactsList.loading" class="py-8 text-center text-gray-400">
              {{ __('Loading...') }}
            </div>
            <div v-else-if="contactsData.length">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b text-left text-xs font-medium uppercase text-gray-500">
                    <th class="px-3 py-2">{{ __('Name') }}</th>
                    <th class="px-3 py-2">{{ __('Email') }}</th>
                    <th class="px-3 py-2">{{ __('Phone') }}</th>
                    <th class="px-3 py-2">{{ __('Role') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in contactsData" :key="c.name" class="border-b">
                    <td class="px-3 py-2 font-medium text-gray-900">{{ c.full_name || c.name }}</td>
                    <td class="px-3 py-2 text-gray-600">{{ c.email_id }}</td>
                    <td class="px-3 py-2 text-gray-600">{{ c.mobile_no || c.phone }}</td>
                    <td class="px-3 py-2 text-gray-600">{{ c.designation }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="py-8 text-center text-gray-400">
              {{ __('No contacts linked') }}
            </div>
          </div>

          <!-- Opportunity Matrix Tab -->
          <div v-if="activeTab === 'Matrix'">
            <OpportunityMatrix
              :technical-fit="doc.technical_fit || 0"
              :commercial-fit="doc.commercial_fit || 0"
              :relationship="doc.relationship || 0"
              :competition="doc.competition || 0"
              :strategic-importance="doc.strategic_importance || 0"
              @update="updateMatrixField"
            />
          </div>

          <!-- Activity Tab -->
          <div v-if="activeTab === 'Activity'" class="space-y-3">
            <div v-if="!activities.data?.length" class="py-8 text-center text-gray-400">
              {{ __('No activities yet') }}
            </div>
            <div v-else class="space-y-3">
              <div
                v-for="a in activities.data"
                :key="a.name"
                class="rounded-lg border p-3"
              >
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-gray-900">{{ a.subject || a.content }}</span>
                  <span class="text-xs text-gray-400">{{ a.creation }}</span>
                </div>
                <p v-if="a.content && a.subject" class="mt-1 text-sm text-gray-600">{{ a.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Tabs>

    <!-- Side panel -->
    <Resizer side="right" class="flex flex-col justify-between border-l">
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(projectId)"
      >
        {{ projectId }}
      </div>
      <div class="flex items-center gap-4 border-b px-5 py-4">
        <div class="flex flex-col gap-1 truncate">
          <div class="truncate text-2xl font-medium text-ink-gray-9">
            {{ doc.project_name || projectId }}
          </div>
          <div v-if="doc.project_number" class="text-sm text-gray-500 font-mono">
            {{ doc.project_number }}
          </div>
        </div>
      </div>

      <!-- abas Sync Status -->
      <div v-if="doc.name" class="flex flex-wrap items-center gap-2 border-b px-5 py-3">
        <SyncStatusBadge
          :status="doc.abas_id ? 'synced' : 'disabled'"
          system="abas"
          :detail="doc.abas_id ? `abas ID: ${doc.abas_id}` : __('Project — not yet synced to abas')"
        />
        <AbasDeepLink
          v-if="doc.abas_id"
          :entity="doc.abas_id"
          kind="order"
          :label="__('Open in abas')"
        />
      </div>

      <!-- Side panel fields -->
      <div class="flex-1 overflow-y-auto">
        <div class="space-y-4 p-5">
          <!-- Phase -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Phase') }}</label>
            <div class="mt-1">
              <span
                :class="phaseClass(doc.phase)"
                class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
              >
                {{ __(doc.phase) }}
              </span>
            </div>
          </div>

          <!-- Type -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Type') }}</label>
            <div class="mt-1">
              <span
                :class="typeClass(doc.project_type)"
                class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
              >
                {{ doc.project_type }}
              </span>
            </div>
          </div>

          <!-- Country -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Country') }}</label>
            <p class="mt-1 text-sm text-gray-800">{{ doc.country || '—' }}</p>
          </div>

          <!-- Salesperson -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Salesperson') }}</label>
            <p class="mt-1 text-sm text-gray-800">{{ doc.salesperson || '—' }}</p>
          </div>

          <!-- Organization -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Organization') }}</label>
            <p class="mt-1 text-sm text-gray-800">{{ doc.organization || '—' }}</p>
          </div>

          <!-- GU Flag -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('General Contractor (GU)') }}</label>
            <p class="mt-1 text-sm text-gray-800">{{ doc.is_gu ? __('Yes') : __('No') }}</p>
          </div>

          <!-- Probability -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Probability') }}</label>
            <p class="mt-1 text-sm text-gray-800">
              {{ doc.probability != null ? `${Math.round(doc.probability)}%` : '—' }}
            </p>
          </div>

          <!-- Estimated Value -->
          <div>
            <label class="text-xs font-medium text-gray-500">{{ __('Estimated Value') }}</label>
            <p class="mt-1 text-sm font-medium text-gray-900">
              {{ doc.estimated_value ? formatCurrency(doc.estimated_value) : '—' }}
            </p>
          </div>

          <!-- Links -->
          <div v-if="doc.teams_link || doc.sharepoint_link" class="space-y-2">
            <label class="text-xs font-medium text-gray-500">{{ __('Links') }}</label>
            <div class="flex flex-col gap-1">
              <a
                v-if="doc.teams_link"
                :href="doc.teams_link"
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm text-lcs-secondary hover:text-lcs-primary hover:underline"
              >
                {{ __('Teams Channel') }}
              </a>
              <a
                v-if="doc.sharepoint_link"
                :href="doc.sharepoint_link"
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm text-lcs-secondary hover:text-lcs-primary hover:underline"
              >
                {{ __('SharePoint Folder') }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </Resizer>
  </div>
  <div v-else-if="project.loading" class="flex h-full items-center justify-center">
    <div class="text-gray-400">{{ __('Loading...') }}</div>
  </div>
  <div v-else class="flex h-full items-center justify-center">
    <div class="text-center">
      <h2 class="text-lg font-medium text-gray-900">{{ __('Project Not Found') }}</h2>
      <p class="mt-1 text-sm text-gray-500">{{ __('The project you are looking for does not exist.') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createDocumentResource,
  createListResource,
  Breadcrumbs,
  Button,
  Dropdown,
  Tabs,
  toast,
  usePageMeta,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Resizer from '@/components/Resizer.vue'
import SyncStatusBadge from '@/components/lcs/SyncStatusBadge.vue'
import AbasDeepLink from '@/components/lcs/AbasDeepLink.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'
import { copyToClipboard } from '@/utils'

const route = useRoute()
const router = useRouter()

const props = defineProps({
  id: { type: String, required: true },
})

const projectId = computed(() => props.id)

const project = createDocumentResource({
  doctype: 'LCS Project',
  name: projectId.value,
  onError: (err) => {
    if (err.exc_type === 'DoesNotExistError') {
      toast.error(__('Project does not exist'))
    }
  },
})

if (!project.doc) project.get.fetch()

const doc = computed(() => project.doc || {})

usePageMeta(() => ({
  title: doc.value.project_name || projectId.value,
}))

const breadcrumbs = computed(() => [
  { label: __('Projects'), route: { name: 'LCS Projects' } },
  { label: doc.value.project_name || projectId.value, route: { name: 'LCS Project', params: { id: projectId.value } } },
])

// Tabs
const tabIndex = ref(0)
const tabs = computed(() => [
  { name: 'Overview', label: __('Overview') },
  { name: 'Contacts', label: __('Contacts') },
  { name: 'Matrix', label: __('Opportunity Matrix') },
  { name: 'Activity', label: __('Activity') },
])

const activeTab = computed(() => tabs.value[tabIndex.value]?.name || 'Overview')

// Phase selector
const phases = ['Inquiry', 'Offer', 'Negotiation', 'Order', 'Execution', 'Completed', 'Lost']
const phaseDropdownOptions = computed(() =>
  phases.map((phase) => ({
    label: __(phase),
    onClick: () => updateField('phase', phase),
  })),
)

// Contacts
const contactsList = createListResource({
  doctype: 'Dynamic Link',
  fields: ['parent'],
  filters: {
    parenttype: 'Contact',
    link_doctype: 'LCS Project',
    link_name: projectId.value,
  },
  auto: true,
})

const contactsData = computed(() => {
  // This is a simplified contacts list; in production
  // you would join through Contact for full details
  if (!contactsList.data) return []
  return contactsList.data.map((d) => ({
    name: d.parent,
    full_name: d.parent,
  }))
})

// Activities (comments, communications on this project)
const activities = createListResource({
  doctype: 'Comment',
  fields: ['name', 'subject', 'content', 'creation', 'owner'],
  filters: {
    reference_doctype: 'LCS Project',
    reference_name: projectId.value,
  },
  orderBy: 'creation desc',
  pageLength: 20,
  auto: true,
})

// Field updates
function updateField(fieldname, value) {
  project.setValue.submit({ [fieldname]: value }).then(() => {
    toast.success(__('Updated'))
  }).catch((err) => {
    toast.error(err.messages?.[0] || __('Error updating field'))
  })
}

function updateMatrixField({ field, value }) {
  updateField(field, value)
}

// Style helpers
function typeClass(type) {
  const map = {
    SB: 'bg-blue-100 text-blue-800',
    WI: 'bg-purple-100 text-purple-800',
    LL: 'bg-emerald-100 text-emerald-800',
    SK: 'bg-amber-100 text-amber-800',
  }
  return map[type] || 'bg-gray-100 text-gray-800'
}

function phaseClass(phase) {
  const map = {
    Inquiry: 'bg-sky-100 text-sky-700',
    Offer: 'bg-amber-100 text-amber-700',
    Negotiation: 'bg-orange-100 text-orange-700',
    Order: 'bg-green-100 text-green-700',
    Execution: 'bg-lcs-primary/10 text-lcs-primary',
    Completed: 'bg-gray-100 text-gray-600',
    Lost: 'bg-red-100 text-red-700',
  }
  return map[phase] || 'bg-gray-100 text-gray-600'
}

function phaseDotClass(phase) {
  const map = {
    Inquiry: 'bg-sky-500',
    Offer: 'bg-amber-500',
    Negotiation: 'bg-orange-500',
    Order: 'bg-green-500',
    Execution: 'bg-lcs-primary',
    Completed: 'bg-gray-500',
    Lost: 'bg-red-500',
  }
  return map[phase] || 'bg-gray-400'
}

function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(val)
}
</script>
