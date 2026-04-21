<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Projects'), route: { name: 'LCS Projects' } }]" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Tooltip :text="__('Display preferences — choose what to show')">
          <Button
            variant="ghost"
            icon="sliders"
            @click="openPreferences"
            :aria-label="__('Open display preferences')"
          />
        </Tooltip>
        <!-- H7: Flexibility — keyboard shortcut hint -->
        <Tooltip :text="__('Ctrl+N')">
          <Button
            variant="solid"
            @click="showNewDialog = true"
            :label="__('New Project')"
            iconLeft="plus"
          />
        </Tooltip>
      </div>
    </template>
  </LayoutHeader>

  <div class="flex flex-1 flex-col overflow-hidden">
    <!-- H1: Visibility of system status — result count + active filters indicator -->
    <div class="flex items-center justify-between border-b bg-white px-5 py-3">
      <div class="flex items-center gap-4">
        <!-- My Projects toggle — personalized view -->
        <div class="flex rounded-lg border bg-white p-0.5">
          <Tooltip :text="__('Show all projects')">
            <button
              class="rounded-md px-3 py-1 text-xs font-medium transition"
              :class="!onlyMine ? 'bg-lcs-primary text-white' : 'text-gray-600 hover:bg-gray-50'"
              @click="onlyMine = false"
            >
              {{ __('All') }}
            </button>
          </Tooltip>
          <Tooltip :text="__('Show only projects assigned to me')">
            <button
              class="flex items-center gap-1 rounded-md px-3 py-1 text-xs font-medium transition"
              :class="onlyMine ? 'bg-lcs-primary text-white' : 'text-gray-600 hover:bg-gray-50'"
              @click="onlyMine = true"
            >
              <FeatherIcon name="user" class="h-3 w-3" />
              {{ __('Mine') }}
            </button>
          </Tooltip>
        </div>
        <!-- Filter bar — H6: Recognition rather than recall -->
        <FormControl
          type="select"
          :options="typeOptions"
          v-model="filters.project_type"
          class="w-36"
        >
          <template #prefix>
            <span class="text-xs text-gray-400">{{ __('Type') }}:</span>
          </template>
        </FormControl>
        <FormControl
          type="select"
          :options="phaseOptions"
          v-model="filters.phase"
          class="w-40"
        >
          <template #prefix>
            <span class="text-xs text-gray-400">{{ __('Phase') }}:</span>
          </template>
        </FormControl>
        <FormControl
          type="text"
          v-model="filters.country"
          :placeholder="__('Country filter...')"
          class="w-36"
          :debounce="300"
        />
        <!-- H3: User control — clear all filters -->
        <Button
          v-if="hasActiveFilters"
          variant="ghost"
          @click="clearFilters"
          iconLeft="x"
          :label="__('Reset')"
          class="text-gray-500"
        />
      </div>
      <!-- H1: System status — total count + cache indicator -->
      <div class="flex items-center gap-3 text-sm text-gray-500">
        <!-- Stale-data indicator when showing cached results -->
        <Tooltip v-if="projectsFromCache" :text="__('Showing cached results from') + ' ' + cacheAgeLabel">
          <span class="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-200">
            <FeatherIcon name="database" class="h-3 w-3" />
            {{ __('cached') }}
          </span>
        </Tooltip>
        <span v-if="!projectsLoading">
          {{ projectList.length }} {{ __('of') }} {{ totalCount }} {{ __('Projects') }}
        </span>
        <Tooltip :text="__('Refresh list (Ctrl+R)')">
          <Button variant="ghost" icon="refresh-cw" @click="reloadProjects()" :class="{ 'animate-spin': projectsLoading }" />
        </Tooltip>
      </div>
    </div>

    <!-- Main content area -->
    <div class="flex-1 overflow-y-auto">
      <!-- H1: Visibility — Loading state with skeleton -->
      <div v-if="projectsLoading && !projectList.length" class="p-5">
        <div v-for="i in 6" :key="i" class="mb-3 flex animate-pulse items-center gap-4 rounded-lg border p-4">
          <div class="h-4 w-28 rounded bg-gray-200" />
          <div class="h-4 w-40 rounded bg-gray-200" />
          <div class="h-4 w-16 rounded bg-gray-100" />
          <div class="h-4 w-24 rounded bg-gray-100" />
          <div class="ml-auto h-4 w-20 rounded bg-gray-100" />
        </div>
      </div>

      <!-- H9: Help recognize errors — Error state with recovery -->
      <div v-else-if="projectsError && !projectList.length" class="flex flex-col items-center justify-center p-16">
        <div class="rounded-full bg-red-50 p-4">
          <FeatherIcon name="alert-circle" class="h-8 w-8 text-red-400" />
        </div>
        <h3 class="mt-4 text-sm font-medium text-gray-900">{{ __('Failed to load projects') }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ projectsError }}</p>
        <Button class="mt-4" variant="outline" @click="reloadProjects()" :label="__('Try again')" iconLeft="refresh-cw" />
      </div>

      <!-- H10: Help — Empty state with guidance -->
      <div v-else-if="!projectList.length && !hasActiveFilters" class="flex flex-col items-center justify-center p-16">
        <div class="rounded-full bg-gray-50 p-4">
          <FeatherIcon name="folder" class="h-8 w-8 text-gray-300" />
        </div>
        <h3 class="mt-4 text-sm font-medium text-gray-900">{{ __('No projects yet') }}</h3>
        <p class="mt-2 max-w-sm text-center text-sm text-gray-500">
          {{ __('Create your first project to start tracking opportunities, phases, and team assignments.') }}
        </p>
        <Button class="mt-4" variant="solid" @click="showNewDialog = true" :label="__('Create first project')" iconLeft="plus" />
      </div>

      <!-- Empty after filter — H5: Error prevention hint -->
      <div v-else-if="!projectList.length && hasActiveFilters" class="flex flex-col items-center justify-center p-16">
        <div class="rounded-full bg-amber-50 p-4">
          <FeatherIcon name="search" class="h-8 w-8 text-amber-400" />
        </div>
        <h3 class="mt-4 text-sm font-medium text-gray-900">{{ __('No matching projects') }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ __('Try adjusting your filters or') }}
          <button class="font-medium text-lcs-secondary hover:underline" @click="clearFilters">{{ __('reset all filters') }}</button>.
        </p>
      </div>

      <!-- Data table — H2: Match real world (German currency, familiar table layout) -->
      <table v-else class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-gray-50">
          <tr class="border-b text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            <th
              class="px-5 py-3 cursor-pointer select-none transition hover:bg-gray-100 hover:text-gray-900"
              @click="toggleSort('project_number')"
              :title="__('Click to sort by project number')"
              :aria-sort="sortField === 'project_number' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'"
            >
              {{ __('Project #') }}
              <SortIcon :active="sortField === 'project_number'" :direction="sortDirection" />
            </th>
            <th
              class="px-4 py-3 cursor-pointer select-none transition hover:bg-gray-100 hover:text-gray-900"
              @click="toggleSort('project_name')"
              :title="__('Click to sort by name')"
              :aria-sort="sortField === 'project_name' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'"
            >
              {{ __('Name') }}
              <SortIcon :active="sortField === 'project_name'" :direction="sortDirection" />
            </th>
            <th class="px-4 py-3">{{ __('Type') }}</th>
            <th class="px-4 py-3">{{ __('Country') }}</th>
            <th class="px-4 py-3">{{ __('Phase') }}</th>
            <th class="px-4 py-3">{{ __('Status') }}</th>
            <th class="px-4 py-3">{{ __('Salesperson') }}</th>
            <th
              class="px-4 py-3 text-right cursor-pointer select-none transition hover:bg-gray-100 hover:text-gray-900"
              @click="toggleSort('probability')"
              :title="__('Click to sort by probability')"
              :aria-sort="sortField === 'probability' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'"
            >
              {{ __('Prob.') }}
              <SortIcon :active="sortField === 'probability'" :direction="sortDirection" />
            </th>
            <th
              class="px-4 py-3 text-right cursor-pointer select-none transition hover:bg-gray-100 hover:text-gray-900"
              @click="toggleSort('estimated_value')"
              :title="__('Click to sort by value')"
              :aria-sort="sortField === 'estimated_value' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'"
            >
              {{ __('Value') }}
              <SortIcon :active="sortField === 'estimated_value'" :direction="sortDirection" />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(p, index) in projectList"
            :key="p.name"
            class="group cursor-pointer border-b transition-colors hover:bg-gray-50"
            :class="{ 'bg-blue-50/50': selectedIndex === index }"
            @click="navigateToProject(p)"
            @keydown.enter="navigateToProject(p)"
            tabindex="0"
            :aria-label="`${p.project_name} — ${p.phase}`"
          >
            <td class="px-5 py-3.5 font-mono text-xs text-gray-500">{{ p.project_number }}</td>
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-900 group-hover:text-lcs-primary">{{ p.project_name }}</span>
                <!-- Notes indicator — visible sign that project has notes -->
                <Tooltip v-if="p.notes" :text="notesPreview(p.notes)">
                  <span class="flex items-center rounded-full bg-amber-100 px-1 py-0.5 text-amber-700" @click.stop>
                    <FeatherIcon name="edit-3" class="h-2.5 w-2.5" />
                  </span>
                </Tooltip>
              </div>
              <div v-if="p.organization" class="mt-0.5 text-xs text-gray-400">{{ p.organization }}</div>
            </td>
            <td class="px-4 py-3.5">
              <!-- H6: Recognition — type badge with tooltip showing full name -->
              <Tooltip :text="typeFullName(p.project_type)">
                <span
                  :class="typeClass(p.project_type)"
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
                >
                  {{ p.project_type }}
                </span>
              </Tooltip>
            </td>
            <td class="px-4 py-3.5 text-gray-600">{{ p.country || '—' }}</td>
            <td class="px-4 py-3.5">
              <span
                :class="phaseClass(p.phase)"
                class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold"
              >
                <span class="h-1.5 w-1.5 rounded-full" :class="phaseDotClass(p.phase)" />
                {{ __(p.phase) }}
              </span>
            </td>
            <td class="px-4 py-3.5">
              <span
                :class="statusClass(p.status)"
                class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
              >
                <span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass(p.status)" />
                {{ __(p.status || 'Open') }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-gray-600">{{ p.salesperson || '—' }}</td>
            <td class="px-4 py-3.5 text-right">
              <!-- H1: Visibility — color-coded probability -->
              <span v-if="p.probability" :class="probabilityClass(p.probability)" class="text-sm font-medium tabular-nums">
                {{ Math.round(p.probability) }}%
              </span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-4 py-3.5 text-right font-medium tabular-nums text-gray-900">
              <span v-if="p.estimated_value">{{ formatCurrency(p.estimated_value) }}</span>
              <span v-else class="text-gray-300">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- New Project Dialog — H4: Closure, H5: Error prevention (validation) -->
  <Dialog v-model="showNewDialog" :options="{ title: __('New Project'), size: 'lg' }">
    <template #body-content>
      <div class="space-y-5">
        <!-- H8: Reduce memory — group related fields logically -->
        <fieldset class="space-y-4">
          <legend class="text-xs font-semibold uppercase tracking-wide text-gray-400">{{ __('Basic Information') }}</legend>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <FormControl
                :label="__('Project Name')"
                v-model="newProject.project_name"
                type="text"
                :placeholder="__('e.g. Seilbahn Innsbruck Nord')"
                required
              />
              <!-- H5: Error prevention — inline validation -->
              <p v-if="validationErrors.project_name" class="mt-1 text-xs text-red-500">
                {{ validationErrors.project_name }}
              </p>
            </div>
            <FormControl
              :label="__('Project Type')"
              v-model="newProject.project_type"
              type="select"
              :options="typeOptionsRaw"
            />
            <FormControl
              :label="__('Project Abbreviation')"
              v-model="newProject.project_abbr"
              type="text"
              :placeholder="__('3-5 characters')"
              maxlength="5"
            />
            <FormControl
              :label="__('Country')"
              v-model="newProject.country"
              type="text"
              :placeholder="__('e.g. Austria')"
            />
          </div>
        </fieldset>

        <fieldset class="space-y-4">
          <legend class="text-xs font-semibold uppercase tracking-wide text-gray-400">{{ __('Assignment') }}</legend>
          <div class="grid grid-cols-2 gap-4">
            <FormControl :label="__('Salesperson')" v-model="newProject.salesperson" type="text" />
            <div class="flex items-end gap-2 pb-1">
              <input type="checkbox" v-model="newProject.is_gu" id="gu-check" class="rounded border-gray-300 text-lcs-primary focus:ring-lcs-secondary" />
              <label for="gu-check" class="text-sm text-gray-700">
                <!-- H6: Recognition — show abbreviation meaning -->
                {{ __('General Contractor') }}
                <span class="text-xs text-gray-400">(GU)</span>
              </label>
            </div>
          </div>
        </fieldset>

        <fieldset class="space-y-3">
          <legend class="text-xs font-semibold uppercase tracking-wide text-gray-400">{{ __('Pricing (optional)') }}</legend>
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              :label="__('Budget (Customer)')"
              v-model.number="newProject.budget_customer"
              type="number"
              :placeholder="__('What customer wants to spend')"
            />
            <FormControl
              :label="__('Richtpreis (Internal)')"
              v-model.number="newProject.richtpreis"
              type="number"
              :placeholder="__('Rough internal estimate')"
            />
          </div>
        </fieldset>

        <fieldset class="space-y-3">
          <legend class="text-xs font-semibold uppercase tracking-wide text-gray-400">{{ __('Details') }}</legend>
          <FormControl
            :label="__('Description')"
            v-model="newProject.project_description"
            type="textarea"
            :placeholder="__('Brief project description (optional)...')"
            rows="3"
          />
        </fieldset>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between">
        <!-- H3: User control — clear exit path -->
        <Button variant="ghost" @click="showNewDialog = false" :label="__('Cancel')" />
        <Button
          variant="solid"
          @click="createProject"
          :loading="creating"
          :disabled="!isNewProjectValid"
          :label="__('Create Project')"
          iconLeft="plus"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted, onUnmounted } from 'vue'
import { createResource, Breadcrumbs, Button, FormControl, Dialog, Tooltip, FeatherIcon, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { sessionStore } from '@/stores/session'
import { useOfflineList } from '@/composables/useOfflineList'
import LayoutHeader from '@/components/LayoutHeader.vue'

const session = sessionStore()

function openPreferences() {
  window.dispatchEvent(new CustomEvent('lcs-open-preferences'))
}

// H7: Flexibility — inline sort indicator component
const SortIcon = {
  props: ['active', 'direction'],
  template: `<span v-if="active" class="ml-0.5 inline-block text-lcs-secondary">{{ direction === 'asc' ? '↑' : '↓' }}</span>`,
}

const router = useRouter()

// State
const filters = reactive({ project_type: '', phase: '', country: '' })
// User preference persists across reloads
const onlyMine = useStorage('lcs-projects-only-mine', false)
const showNewDialog = ref(false)
const creating = ref(false)
const selectedIndex = ref(-1)
const sortField = ref('modified')
const sortDirection = ref('desc')

const newProject = reactive({
  project_name: '',
  project_type: 'SB',
  project_abbr: '',
  country: '',
  salesperson: '',
  is_gu: false,
  budget_customer: null,
  richtpreis: null,
  project_description: '',
})

const validationErrors = reactive({ project_name: '' })

// H6: Recognition — full type names visible on hover
const typeOptionsRaw = [
  { label: 'SB — Seilbahn (Cable Car)', value: 'SB' },
  { label: 'WI — Winde (Winch)', value: 'WI' },
  { label: 'LL — Liftanlage (Lift System)', value: 'LL' },
  { label: 'SK — Sonderkonstruktion (Special)', value: 'SK' },
  { label: 'Other', value: 'Other' },
]
const typeOptions = [{ label: __('All Types'), value: '' }, ...typeOptionsRaw]
const phaseOptions = [
  { label: __('All Phases'), value: '' },
  { label: __('Inquiry'), value: 'Inquiry' },
  { label: __('Offer'), value: 'Offer' },
  { label: __('Negotiation'), value: 'Negotiation' },
  { label: __('Order'), value: 'Order' },
  { label: __('Execution'), value: 'Execution' },
  { label: __('Completed'), value: 'Completed' },
  { label: __('Lost'), value: 'Lost' },
]

const hasActiveFilters = computed(() =>
  !!(filters.project_type || filters.phase || filters.country),
)

const activeFilters = computed(() => {
  const f = {}
  if (filters.project_type) f.project_type = filters.project_type
  if (filters.phase) f.phase = filters.phase
  if (filters.country) f.country = ['like', `%${filters.country}%`]
  if (onlyMine.value) f.salesperson = session.user
  return f
})

const orderBy = computed(() => `${sortField.value} ${sortDirection.value}`)

const {
  data: projectsData,
  loading: projectsLoading,
  error: projectsError,
  fromCache: projectsFromCache,
  lastCachedAt: projectsCachedAt,
  reload: reloadProjects,
} = useOfflineList({
  doctype: 'LCS Project',
  fields: [
    'name', 'project_name', 'project_number', 'project_type',
    'country', 'phase', 'status', 'salesperson', 'organization',
    'probability', 'estimated_value', 'notes', 'modified',
  ],
  filters: activeFilters,
  orderBy: orderBy,
  pageLength: 100,
})

const totalCount = computed(() => projectsData.value?.length || 0)
const projectList = computed(() => projectsData.value || [])

const cacheAgeLabel = computed(() => {
  if (!projectsCachedAt.value) return ''
  const s = Math.floor((Date.now() - projectsCachedAt.value) / 1000)
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.floor(s / 60)}m`
  if (s < 86400) return `${Math.floor(s / 3600)}h`
  return `${Math.floor(s / 86400)}d`
})

// H5: Error prevention — validate before enabling submit
const isNewProjectValid = computed(() => {
  return newProject.project_name.trim().length >= 3
})

watch(() => newProject.project_name, (val) => {
  if (val && val.trim().length < 3) {
    validationErrors.project_name = __('Name must be at least 3 characters')
  } else {
    validationErrors.project_name = ''
  }
})

// H2: Shortcuts — keyboard navigation
function handleKeyboard(e) {
  // Ctrl+N: New project
  if ((e.ctrlKey || e.metaKey) && e.key === 'n' && !showNewDialog.value) {
    e.preventDefault()
    showNewDialog.value = true
  }
  // Escape: Close dialog
  if (e.key === 'Escape' && showNewDialog.value) {
    showNewDialog.value = false
  }
  // Ctrl+R: Refresh
  if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
    e.preventDefault()
    reloadProjects()
  }
}

onMounted(() => document.addEventListener('keydown', handleKeyboard))
onUnmounted(() => document.removeEventListener('keydown', handleKeyboard))

function clearFilters() {
  filters.project_type = ''
  filters.phase = ''
  filters.country = ''
}

function toggleSort(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  reloadProjects()
}

function navigateToProject(p) {
  router.push({ name: 'LCS Project', params: { id: p.name } })
}

function typeFullName(type) {
  const map = { SB: 'Seilbahn (Cable Car)', WI: 'Winde (Winch)', LL: 'Liftanlage (Lift)', SK: 'Sonderkonstruktion (Special)' }
  return map[type] || type
}

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
    Inquiry: 'bg-sky-50 text-sky-700',
    Offer: 'bg-amber-50 text-amber-700',
    Negotiation: 'bg-orange-50 text-orange-700',
    Order: 'bg-green-50 text-green-700',
    Execution: 'bg-lcs-primary/5 text-lcs-primary',
    Completed: 'bg-gray-50 text-gray-600',
    Lost: 'bg-red-50 text-red-700',
  }
  return map[phase] || 'bg-gray-50 text-gray-600'
}

function phaseDotClass(phase) {
  const map = {
    Inquiry: 'bg-sky-500',
    Offer: 'bg-amber-500',
    Negotiation: 'bg-orange-500',
    Order: 'bg-green-500',
    Execution: 'bg-lcs-primary',
    Completed: 'bg-gray-400',
    Lost: 'bg-red-500',
  }
  return map[phase] || 'bg-gray-400'
}

// Status badge helpers — prominent status visibility
function statusClass(status) {
  const map = {
    Open: 'bg-blue-50 text-blue-700',
    Active: 'bg-green-50 text-green-700',
    'On Hold': 'bg-amber-50 text-amber-700',
    Completed: 'bg-gray-50 text-gray-600',
    Cancelled: 'bg-red-50 text-red-700',
  }
  return map[status] || 'bg-gray-50 text-gray-600'
}

function statusDotClass(status) {
  const map = {
    Open: 'bg-blue-500',
    Active: 'bg-green-500',
    'On Hold': 'bg-amber-500',
    Completed: 'bg-gray-400',
    Cancelled: 'bg-red-500',
  }
  return map[status] || 'bg-gray-400'
}

// Notes preview — first 100 chars for tooltip
function notesPreview(notes) {
  if (!notes) return ''
  const plain = notes.replace(/<[^>]+>/g, '').trim()
  return plain.length > 120 ? plain.slice(0, 120) + '...' : plain
}

// H1: Visibility — probability color reflects confidence level
function probabilityClass(val) {
  if (val >= 70) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}

function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(val)
}

// H4: Closure — clear feedback on success/failure
async function createProject() {
  if (!isNewProjectValid.value) return

  creating.value = true
  try {
    const res = createResource({
      url: 'frappe.client.insert',
      params: { doc: { doctype: 'LCS Project', ...newProject } },
    })
    const result = await res.submit()
    showNewDialog.value = false
    // Reset form
    Object.assign(newProject, {
      project_name: '', project_type: 'SB', project_abbr: '',
      country: '', salesperson: '', is_gu: false,
      budget_customer: null, richtpreis: null,
      project_description: '',
    })
    reloadProjects()
    // H4: Closure — success with navigation offer
    toast({
      title: __('Project created'),
      text: result.data?.project_number || '',
      icon: 'check-circle',
      iconClasses: 'text-green-500',
    })
  } catch (err) {
    // H9: Error recovery — specific message
    toast({
      title: __('Could not create project'),
      text: err.messages?.[0] || __('Please check your input and try again.'),
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
  } finally {
    creating.value = false
  }
}
</script>
