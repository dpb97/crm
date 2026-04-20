<template>
  <LayoutHeader>
    <template #left-header>
      <!-- H1: Visibility — clear breadcrumb navigation path -->
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="doc.name" #right-header>
      <div class="flex items-center gap-3">
        <!-- H1: Visibility — last saved indicator -->
        <span v-if="lastSaved" class="text-xs text-gray-400">
          {{ __('Saved') }} {{ lastSaved }}
        </span>
        <!-- H6: Reversal — phase dropdown with confirmation for backward moves -->
        <Dropdown v-if="phaseDropdownOptions.length" :options="phaseDropdownOptions" placement="right">
          <template #default="{ open }">
            <Button :iconRight="open ? 'chevron-up' : 'chevron-down'">
              <template #prefix>
                <span class="h-2 w-2 rounded-full" :class="phaseDotClass(doc.phase)" />
              </template>
              {{ __(doc.phase || 'Set Phase') }}
            </Button>
          </template>
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>

  <!-- H1: Visibility — Loading state -->
  <div v-if="project.loading && !doc.name" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center gap-3">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
      <span class="text-sm text-gray-400">{{ __('Loading project...') }}</span>
    </div>
  </div>

  <!-- H9: Error recovery — Not found state with navigation -->
  <div v-else-if="!doc.name && !project.loading" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center text-center">
      <div class="rounded-full bg-red-50 p-4">
        <FeatherIcon name="alert-circle" class="h-8 w-8 text-red-400" />
      </div>
      <h2 class="mt-4 text-lg font-medium text-gray-900">{{ __('Project Not Found') }}</h2>
      <p class="mt-1 max-w-sm text-sm text-gray-500">
        {{ __('This project may have been deleted or you may not have permission to view it.') }}
      </p>
      <!-- H3: User control — clear escape path -->
      <Button class="mt-4" variant="outline" @click="$router.push({ name: 'LCS Projects' })" :label="__('Back to Projects')" iconLeft="arrow-left" />
    </div>
  </div>

  <!-- Main content -->
  <div v-else class="flex h-full overflow-hidden">
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
            <!-- H8: Aesthetic — clean layout with visual hierarchy -->
            <section>
              <h3 class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                <FeatherIcon name="file-text" class="h-3.5 w-3.5" />
                {{ __('Description') }}
              </h3>
              <div v-if="editingDescription" class="space-y-2">
                <textarea
                  v-model="editDescriptionValue"
                  class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-800 focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
                  rows="4"
                  :placeholder="__('Add a project description...')"
                  ref="descriptionInput"
                />
                <div class="flex gap-2">
                  <Button variant="solid" size="sm" @click="saveDescription" :label="__('Save')" />
                  <!-- H6: Reversal — cancel edit -->
                  <Button variant="ghost" size="sm" @click="cancelDescriptionEdit" :label="__('Cancel')" />
                </div>
              </div>
              <div v-else @click="startDescriptionEdit" class="group cursor-pointer">
                <p v-if="doc.project_description" class="whitespace-pre-wrap text-sm text-gray-800 group-hover:bg-gray-50 rounded-lg p-2 -m-2 transition">
                  {{ doc.project_description }}
                </p>
                <!-- H10: Help — guidance for empty state -->
                <p v-else class="rounded-lg border border-dashed border-gray-200 p-4 text-center text-sm text-gray-400 hover:border-gray-300 hover:text-gray-500 transition">
                  {{ __('Click to add a description') }}
                </p>
              </div>
            </section>

            <!-- Notes section with same edit pattern -->
            <section v-if="doc.notes">
              <h3 class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                <FeatherIcon name="edit-3" class="h-3.5 w-3.5" />
                {{ __('Notes') }}
              </h3>
              <div class="whitespace-pre-wrap rounded-lg bg-amber-50/50 p-3 text-sm text-gray-800">
                {{ doc.notes }}
              </div>
            </section>

            <!-- H1: Visibility — key metrics summary at glance -->
            <section v-if="doc.estimated_value || doc.probability">
              <h3 class="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                <FeatherIcon name="bar-chart-2" class="h-3.5 w-3.5" />
                {{ __('Key Metrics') }}
              </h3>
              <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <div v-if="doc.estimated_value" class="rounded-lg border bg-white p-3">
                  <div class="text-xs text-gray-500">{{ __('Value') }}</div>
                  <div class="mt-1 text-lg font-bold text-gray-900">{{ formatCurrency(doc.estimated_value) }}</div>
                </div>
                <div v-if="doc.probability != null" class="rounded-lg border bg-white p-3">
                  <div class="text-xs text-gray-500">{{ __('Probability') }}</div>
                  <div class="mt-1 text-lg font-bold" :class="probabilityClass(doc.probability)">
                    {{ Math.round(doc.probability) }}%
                  </div>
                </div>
                <div class="rounded-lg border bg-white p-3">
                  <div class="text-xs text-gray-500">{{ __('Weighted Value') }}</div>
                  <div class="mt-1 text-lg font-bold text-gray-700">
                    {{ formatCurrency((doc.estimated_value || 0) * (doc.probability || 0) / 100) }}
                  </div>
                </div>
              </div>
            </section>
          </div>

          <!-- Contacts Tab -->
          <div v-if="activeTab === 'Contacts'" class="space-y-3">
            <div v-if="contactsList.loading" class="flex items-center justify-center py-12">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            </div>
            <div v-else-if="contactsData.length">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                    <th class="px-3 py-2">{{ __('Name') }}</th>
                    <th class="px-3 py-2">{{ __('Role') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in contactsData" :key="c.name" class="border-b hover:bg-gray-50">
                    <td class="px-3 py-2.5 font-medium text-gray-900">{{ c.full_name || c.name }}</td>
                    <td class="px-3 py-2.5 text-gray-600">{{ c.designation || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- H10: Help — empty state with action -->
            <div v-else class="flex flex-col items-center py-12">
              <FeatherIcon name="users" class="h-8 w-8 text-gray-300" />
              <p class="mt-3 text-sm text-gray-500">{{ __('No contacts linked to this project yet.') }}</p>
              <p class="mt-1 text-xs text-gray-400">{{ __('Link contacts via the Contact doctype or the form below.') }}</p>
            </div>
          </div>

          <!-- Opportunity Matrix Tab -->
          <div v-if="activeTab === 'Matrix'">
            <OpportunityMatrix
              :technical-fit="matrixValues.technical_fit"
              :commercial-fit="matrixValues.commercial_fit"
              :relationship="matrixValues.relationship_strength"
              :competition="matrixValues.competition_level"
              :strategic-importance="matrixValues.strategic_importance"
              @update="onMatrixUpdate"
            />
          </div>

          <!-- Activity Tab -->
          <div v-if="activeTab === 'Activity'" class="space-y-3">
            <div v-if="activities.loading" class="flex items-center justify-center py-12">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            </div>
            <div v-else-if="!activities.data?.length" class="flex flex-col items-center py-12">
              <FeatherIcon name="clock" class="h-8 w-8 text-gray-300" />
              <p class="mt-3 text-sm text-gray-500">{{ __('No activities recorded yet.') }}</p>
              <p class="mt-1 text-xs text-gray-400">{{ __('Activities appear here when comments or communications are added.') }}</p>
            </div>
            <div v-else class="space-y-3">
              <!-- H2: Match real world — timeline metaphor -->
              <div class="relative pl-6">
                <div class="absolute bottom-0 left-2.5 top-0 w-px bg-gray-200" />
                <div
                  v-for="a in activities.data"
                  :key="a.name"
                  class="relative mb-4"
                >
                  <div class="absolute -left-3.5 top-1.5 h-2 w-2 rounded-full border-2 border-white bg-lcs-secondary" />
                  <div class="rounded-lg border bg-white p-3 shadow-sm">
                    <div class="flex items-center justify-between">
                      <span class="text-sm font-medium text-gray-900">{{ a.subject || a.content }}</span>
                      <span class="text-xs text-gray-400">{{ formatRelativeTime(a.creation) }}</span>
                    </div>
                    <p v-if="a.content && a.subject" class="mt-1 text-sm text-gray-600">{{ a.content }}</p>
                    <p class="mt-1 text-xs text-gray-400">{{ a.owner }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Tabs>

    <!-- Side panel — H8: Reduce memory (all context visible at once) -->
    <Resizer side="right" class="flex flex-col justify-between border-l bg-white">
      <!-- Project identity header -->
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9 hover:bg-gray-50 transition"
        @click="copyId"
        :title="__('Click to copy project ID')"
      >
        {{ projectId }}
        <!-- H3: Feedback — copy confirmation -->
        <FeatherIcon v-if="justCopied" name="check" class="ml-2 h-4 w-4 text-green-500" />
      </div>

      <div class="flex items-center gap-4 border-b px-5 py-4">
        <div class="flex flex-col gap-1 truncate">
          <div class="truncate text-2xl font-medium text-ink-gray-9">
            {{ doc.project_name || projectId }}
          </div>
          <!-- H8: Reduce memory — project number always visible -->
          <div v-if="doc.project_number" class="flex items-center gap-2 text-sm font-mono text-gray-500">
            <span>{{ doc.project_number }}</span>
            <!-- H6: Recognition — type badge inline -->
            <Tooltip :text="typeFullName(doc.project_type)">
              <span :class="typeClass(doc.project_type)" class="rounded-full px-1.5 py-0.5 text-[10px] font-bold">
                {{ doc.project_type }}
              </span>
            </Tooltip>
          </div>
        </div>
      </div>

      <!-- H1: Visibility — abas sync status always visible -->
      <div v-if="doc.name" class="flex flex-wrap items-center gap-2 border-b px-5 py-3">
        <SyncStatusBadge
          :status="doc.abas_id ? 'synced' : 'disabled'"
          system="abas"
          :detail="doc.abas_id ? `abas ID: ${doc.abas_id}` : __('Not synced to abas')"
        />
        <AbasDeepLink
          v-if="doc.abas_id"
          :entity="doc.abas_id"
          kind="order"
          :label="__('Open in abas')"
        />
      </div>

      <!-- Side panel fields — H8: Grouped logically -->
      <div class="flex-1 overflow-y-auto">
        <div class="divide-y">
          <!-- Status group -->
          <div class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Status') }}</h4>
            <SideField :label="__('Phase')">
              <span :class="phaseClass(doc.phase)" class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold">
                <span class="h-1.5 w-1.5 rounded-full" :class="phaseDotClass(doc.phase)" />
                {{ __(doc.phase) }}
              </span>
            </SideField>
            <SideField :label="__('Status')">
              <span class="text-sm text-gray-800">{{ __(doc.status) || '—' }}</span>
            </SideField>
          </div>

          <!-- Classification group -->
          <div class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Classification') }}</h4>
            <SideField :label="__('Type')">
              <Tooltip :text="typeFullName(doc.project_type)">
                <span :class="typeClass(doc.project_type)" class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold">
                  {{ doc.project_type }}
                </span>
              </Tooltip>
            </SideField>
            <SideField :label="__('Country')">
              <span class="text-sm text-gray-800">{{ doc.country || '—' }}</span>
            </SideField>
            <SideField :label="__('GU')">
              <!-- H6: Recognition — clear yes/no with icon -->
              <span v-if="doc.is_gu" class="flex items-center gap-1 text-sm text-green-600">
                <FeatherIcon name="check-circle" class="h-3.5 w-3.5" /> {{ __('Yes') }}
              </span>
              <span v-else class="text-sm text-gray-400">{{ __('No') }}</span>
            </SideField>
          </div>

          <!-- People group -->
          <div class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('People') }}</h4>
            <SideField :label="__('Salesperson')">
              <span class="text-sm text-gray-800">{{ doc.salesperson || '—' }}</span>
            </SideField>
            <SideField :label="__('Organization')">
              <span class="text-sm text-gray-800">{{ doc.organization || '—' }}</span>
            </SideField>
          </div>

          <!-- Commercial group -->
          <div class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Commercial') }}</h4>
            <SideField :label="__('Probability')">
              <span v-if="doc.probability != null" class="text-sm font-medium" :class="probabilityClass(doc.probability)">
                {{ Math.round(doc.probability) }}%
              </span>
              <span v-else class="text-sm text-gray-400">—</span>
            </SideField>
            <SideField :label="__('Value')">
              <span v-if="doc.estimated_value" class="text-sm font-medium text-gray-900">{{ formatCurrency(doc.estimated_value) }}</span>
              <span v-else class="text-sm text-gray-400">—</span>
            </SideField>
          </div>

          <!-- Links group -->
          <div v-if="doc.team_link || doc.sharepoint_link" class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('External Links') }}</h4>
            <div class="flex flex-col gap-2">
              <a
                v-if="doc.team_link"
                :href="doc.team_link"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 text-sm text-lcs-secondary hover:text-lcs-primary hover:underline"
              >
                <FeatherIcon name="message-square" class="h-3.5 w-3.5" />
                {{ __('Teams Channel') }}
              </a>
              <a
                v-if="doc.sharepoint_link"
                :href="doc.sharepoint_link"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 text-sm text-lcs-secondary hover:text-lcs-primary hover:underline"
              >
                <FeatherIcon name="folder" class="h-3.5 w-3.5" />
                {{ __('SharePoint Folder') }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </Resizer>
  </div>

  <!-- H6: Reversal — phase change confirmation dialog -->
  <Dialog v-model="showPhaseConfirm" :options="{ title: __('Confirm Phase Change'), size: 'sm' }">
    <template #body-content>
      <p class="text-sm text-gray-600">
        {{ __('Move this project from') }}
        <strong>{{ __(doc.phase) }}</strong>
        {{ __('to') }}
        <strong>{{ __(pendingPhase) }}</strong>?
      </p>
      <p v-if="isBackwardPhaseMove" class="mt-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-700">
        <FeatherIcon name="alert-triangle" class="mr-1 inline h-3.5 w-3.5" />
        {{ __('This moves the project backward in the pipeline. This may affect reporting.') }}
      </p>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="showPhaseConfirm = false" :label="__('Cancel')" />
        <Button variant="solid" @click="confirmPhaseChange" :label="__('Confirm')" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  createDocumentResource,
  createListResource,
  createResource,
  Breadcrumbs,
  Button,
  Dropdown,
  Dialog,
  Tabs,
  Tooltip,
  FeatherIcon,
  toast,
  usePageMeta,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Resizer from '@/components/Resizer.vue'
import SyncStatusBadge from '@/components/lcs/SyncStatusBadge.vue'
import AbasDeepLink from '@/components/lcs/AbasDeepLink.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'
import { copyToClipboard } from '@/utils'
import { timeAgo } from '@/utils'

// H8: Reduce memory — reusable side field component
const SideField = {
  props: ['label'],
  template: `<div class="flex items-center justify-between"><label class="text-xs text-gray-500">{{ label }}</label><slot /></div>`,
}

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
      toast({ title: __('Project not found'), icon: 'alert-circle', iconClasses: 'text-red-500' })
    }
  },
})

if (!project.doc) project.get.fetch()

const doc = computed(() => project.doc || {})

usePageMeta(() => ({
  title: doc.value.project_name || projectId.value,
}))

// H1: Visibility — breadcrumbs for orientation
const breadcrumbs = computed(() => [
  { label: __('Projects'), route: { name: 'LCS Projects' } },
  { label: doc.value.project_name || projectId.value, route: { name: 'LCS Project', params: { id: projectId.value } } },
])

// H1: Visibility — last saved timestamp
const lastSaved = computed(() => {
  if (!doc.value.modified) return ''
  return timeAgo ? timeAgo(doc.value.modified) : ''
})

// Tabs — H7: Flexibility (keyboard-accessible tabs)
const tabIndex = ref(0)
const tabs = computed(() => [
  { name: 'Overview', label: __('Overview'), icon: 'file-text' },
  { name: 'Contacts', label: __('Contacts'), icon: 'users' },
  { name: 'Matrix', label: __('Opportunity Matrix'), icon: 'target' },
  { name: 'Activity', label: __('Activity'), icon: 'clock' },
])
const activeTab = computed(() => tabs.value[tabIndex.value]?.name || 'Overview')

// Phase change — H6: Reversal with confirmation
const phases = ['Inquiry', 'Offer', 'Negotiation', 'Order', 'Execution', 'Completed', 'Lost']
const showPhaseConfirm = ref(false)
const pendingPhase = ref('')

const isBackwardPhaseMove = computed(() => {
  const currentIdx = phases.indexOf(doc.value.phase)
  const newIdx = phases.indexOf(pendingPhase.value)
  return newIdx < currentIdx && pendingPhase.value !== 'Lost'
})

const phaseDropdownOptions = computed(() =>
  phases.map((phase) => ({
    label: __(phase),
    icon: doc.value.phase === phase ? 'check' : undefined,
    onClick: () => initiatePhaseChange(phase),
  })),
)

function initiatePhaseChange(phase) {
  if (phase === doc.value.phase) return
  pendingPhase.value = phase
  // H6: Backward moves need confirmation; forward is safe
  if (isBackwardPhaseMove.value) {
    showPhaseConfirm.value = true
  } else {
    confirmPhaseChange()
  }
}

function confirmPhaseChange() {
  showPhaseConfirm.value = false
  updateField('phase', pendingPhase.value)
}

// Description inline edit — H7: Locus of control
const editingDescription = ref(false)
const editDescriptionValue = ref('')
const descriptionInput = ref(null)

function startDescriptionEdit() {
  editDescriptionValue.value = doc.value.project_description || ''
  editingDescription.value = true
  nextTick(() => descriptionInput.value?.focus())
}

function cancelDescriptionEdit() {
  editingDescription.value = false
}

function saveDescription() {
  updateField('project_description', editDescriptionValue.value)
  editingDescription.value = false
}

// Copy ID — H3: Feedback
const justCopied = ref(false)
function copyId() {
  copyToClipboard(projectId.value)
  justCopied.value = true
  setTimeout(() => { justCopied.value = false }, 2000)
  toast({ title: __('Copied to clipboard'), icon: 'check', iconClasses: 'text-green-500' })
}

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
  if (!contactsList.data) return []
  return contactsList.data.map((d) => ({ name: d.parent, full_name: d.parent }))
})

// Opportunity Matrix values from linked matrix document
const matrixValues = ref({
  technical_fit: 0,
  commercial_fit: 0,
  relationship_strength: 0,
  competition_level: 0,
  strategic_importance: 0,
})

const matrixResource = createResource({
  url: 'lcs_integrations.projects.api.get_opportunity_matrix',
  params: { project: projectId.value },
  auto: true,
  onSuccess: (data) => {
    if (data && data.length) {
      const m = data[0]
      matrixValues.value = {
        technical_fit: m.technical_fit || 0,
        commercial_fit: m.commercial_fit || 0,
        relationship_strength: m.relationship_strength || 0,
        competition_level: m.competition_level || 0,
        strategic_importance: m.strategic_importance || 0,
      }
    }
  },
})

function onMatrixUpdate({ field, value }) {
  matrixValues.value[field] = value
  // Debounced save would go here for the matrix document
}

// Activities
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

// Field updates — H4: Closure with feedback
function updateField(fieldname, value) {
  project.setValue.submit({ [fieldname]: value }).then(() => {
    toast({ title: __('Updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
  }).catch((err) => {
    toast({
      title: __('Update failed'),
      text: err.messages?.[0] || __('Please try again.'),
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
  })
}

// Style helpers — H1: Consistency across pages
function typeClass(type) {
  const map = { SB: 'bg-blue-100 text-blue-800', WI: 'bg-purple-100 text-purple-800', LL: 'bg-emerald-100 text-emerald-800', SK: 'bg-amber-100 text-amber-800' }
  return map[type] || 'bg-gray-100 text-gray-800'
}

function typeFullName(type) {
  const map = { SB: 'Seilbahn (Cable Car)', WI: 'Winde (Winch)', LL: 'Liftanlage (Lift)', SK: 'Sonderkonstruktion (Special)' }
  return map[type] || type
}

function phaseClass(phase) {
  const map = { Inquiry: 'bg-sky-50 text-sky-700', Offer: 'bg-amber-50 text-amber-700', Negotiation: 'bg-orange-50 text-orange-700', Order: 'bg-green-50 text-green-700', Execution: 'bg-lcs-primary/5 text-lcs-primary', Completed: 'bg-gray-50 text-gray-600', Lost: 'bg-red-50 text-red-700' }
  return map[phase] || 'bg-gray-50 text-gray-600'
}

function phaseDotClass(phase) {
  const map = { Inquiry: 'bg-sky-500', Offer: 'bg-amber-500', Negotiation: 'bg-orange-500', Order: 'bg-green-500', Execution: 'bg-lcs-primary', Completed: 'bg-gray-400', Lost: 'bg-red-500' }
  return map[phase] || 'bg-gray-400'
}

function probabilityClass(val) {
  if (val >= 70) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}

function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(val)
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  if (timeAgo) return timeAgo(dateStr)
  return dateStr
}
</script>
