<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Sales Projects'), route: { name: 'LCS Projects' } }]" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <!-- Admin-only: import existing BSM construction sites -->
        <Tooltip v-if="canManageImport" :text="__('Import running BSM construction sites as LCS Projects')">
          <Button
            variant="ghost"
            icon="download-cloud"
            @click="showImportDialog = true"
            :aria-label="__('Import from BSM')"
          />
        </Tooltip>
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

  <div class="lcsp-canvas flex flex-1 flex-col overflow-hidden">
    <div class="lcsp-head">
      <PpPageHead
        :eyebrow="__('Sales / CRM')"
        :title="__('Sales Projects')"
        :subtitle="viewMode === 'list' && !projectsLoading ? `${projectList.length} ${__('of')} ${totalCount} ${__('Projects')}` : ''"
      />
    </div>
    <!-- H1: Visibility of system status — result count + active filters indicator -->
    <div class="lcsp-filterbar flex flex-wrap items-center justify-between gap-y-2 border-b px-5 py-3">
      <div class="flex flex-wrap items-center gap-2 sm:gap-4">
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
      <div class="flex flex-wrap items-center gap-3 text-sm text-gray-500">
        <!-- Stale-data indicator when showing cached results -->
        <Tooltip v-if="projectsFromCache" :text="__('Showing cached results from') + ' ' + cacheAgeLabel">
          <span class="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-200">
            <FeatherIcon name="database" class="h-3 w-3" />
            {{ __('cached') }}
          </span>
        </Tooltip>
        <span v-if="viewMode === 'list' && !projectsLoading">
          {{ projectList.length }} {{ __('of') }} {{ totalCount }} {{ __('Projects') }}
        </span>
        <!-- View toggle: list | map | dashboard -->
        <div class="flex items-center rounded-lg border bg-gray-50 p-0.5">
          <Tooltip v-for="view in VIEW_MODES" :key="view.key" :text="view.label">
            <button
              class="flex items-center rounded-md px-2 py-1 transition"
              :class="viewMode === view.key ? 'bg-white text-lcs-primary shadow-sm' : 'text-gray-400 hover:text-gray-600'"
              :aria-pressed="viewMode === view.key"
              @click="viewMode = view.key"
            >
              <FeatherIcon :name="view.icon" class="h-3.5 w-3.5" />
            </button>
          </Tooltip>
        </div>
        <Tooltip :text="__('Refresh list (Ctrl+R)')">
          <Button
            variant="ghost"
            icon="refresh-cw"
            @click="viewMode === 'list' ? reloadProjects() : mapData.reload()"
            :class="{ 'animate-spin': viewMode === 'list' ? projectsLoading : mapData.loading }"
          />
        </Tooltip>
        <!-- Per-user column selection — persisted in LCS User Preferences -->
        <ColumnPicker
          v-if="viewMode === 'list'"
          table-key="lcs_projects"
          :catalog="COLUMN_CATALOG"
          :defaults="DEFAULT_COLUMNS"
          v-model="selectedColumns"
        />
      </div>
    </div>

    <!-- Main content area -->
    <div class="flex-1 overflow-y-auto overflow-x-auto">
      <!-- Map / Dashboard views (full portfolio, independent of list filters) -->
      <div v-if="viewMode !== 'list'" class="p-5">
        <div v-if="mapData.loading && !mapProjects.length" class="flex items-center justify-center py-16">
          <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-primary" />
        </div>
        <ProjectMap v-else-if="viewMode === 'map'" :projects="mapProjects" />
        <ProjectDashboard v-else :projects="mapProjects" :loading="mapData.loading" />
      </div>

      <!-- List view: KPI strip + states + table -->
      <template v-else>
      <!-- KPI overview strip -->
      <section v-if="projectList.length" class="lcsp-kpis">
        <PpStatTile :label="__('Execution')" :value="String(overview.execution)" :hint="__('active builds')" />
        <PpStatTile :label="__('Won')" :value="String(overview.won)" :hint="__('order booked')" />
        <PpStatTile :label="__('Completed')" :value="String(overview.completed)" :hint="__('closed out')" />
        <PpStatTile :label="__('Total value')" :value="overviewMoney" :hint="__('estimated pipeline')" />
      </section>

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
      <div v-else-if="projectsError && !projectList.length" class="lcsp-state">
        <PpEmptyState :icon="IconAlertCircle" :title="__('Failed to load projects')" :hint="projectsError">
          <template #action>
            <Button variant="outline" @click="reloadProjects()" :label="__('Try again')" iconLeft="refresh-cw" />
          </template>
        </PpEmptyState>
      </div>

      <!-- H10: Help — Empty state with guidance -->
      <div v-else-if="!projectList.length && !hasActiveFilters" class="lcsp-state">
        <PpEmptyState :icon="IconFolder" :title="__('No projects yet')" :hint="__('Create your first project to start tracking opportunities, phases, and team assignments.')">
          <template #action>
            <Button variant="solid" @click="showNewDialog = true" :label="__('Create first project')" iconLeft="plus" />
          </template>
        </PpEmptyState>
      </div>

      <!-- Empty after filter — H5: Error prevention hint -->
      <div v-else-if="!projectList.length && hasActiveFilters" class="lcsp-state">
        <PpEmptyState :icon="IconSearchX" :title="__('No matching projects')" :hint="__('Try adjusting your filters.')">
          <template #action>
            <Button variant="subtle" @click="clearFilters" :label="__('Reset all filters')" iconLeft="x" />
          </template>
        </PpEmptyState>
      </div>

      <!-- Data table — H2: Match real world (German currency, familiar table layout) -->
      <table v-else class="w-full text-sm">
        <thead class="lcsp-thead sticky top-0 z-10">
          <tr class="border-b text-left text-xs font-medium uppercase tracking-wide">
            <th
              v-for="col in visibleColumns"
              :key="col.key"
              class="px-4 py-3 select-none"
              :class="[
                col.align === 'right' ? 'text-right' : '',
                col.sortable ? 'cursor-pointer transition hover:bg-gray-100 hover:text-gray-900' : '',
                col.key === 'project_number' ? 'px-5' : '',
              ]"
              :title="col.sortable ? __('Click to sort') : undefined"
              :aria-sort="col.sortable && sortField === col.key ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'"
              @click="col.sortable && toggleSort(col.key)"
            >
              {{ col.label }}
              <SortIcon v-if="col.sortable" :active="sortField === col.key" :direction="sortDirection" />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(p, index) in projectList"
            :key="p.name"
            class="lcsp-row group cursor-pointer border-b transition-colors"
            :class="{ 'lcsp-row--sel': selectedIndex === index || selectedProject?.name === p.name }"
            @click="selectProject(p)"
            @dblclick="navigateToProject(p)"
            @keydown.enter="navigateToProject(p)"
            tabindex="0"
            :aria-label="`${p.project_name} — ${p.phase}`"
          >
            <template v-for="col in visibleColumns" :key="col.key">
              <!-- Bespoke cells keep their original renderers -->
              <td v-if="col.key === 'project_number'" class="px-5 py-3.5 font-mono text-xs text-gray-500">{{ p.project_number }}</td>

              <td v-else-if="col.key === 'project_name'" class="px-4 py-3.5">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-gray-900 group-hover:text-lcs-primary">{{ p.project_name }}</span>
                  <Tooltip v-if="p.notes" :text="notesPreview(p.notes)">
                    <span class="flex items-center rounded-full bg-amber-100 px-1 py-0.5 text-amber-700" @click.stop>
                      <FeatherIcon name="edit-3" class="h-2.5 w-2.5" />
                    </span>
                  </Tooltip>
                </div>
                <div v-if="p.organization && !selectedColumns.includes('organization')" class="mt-0.5 text-xs text-gray-400">{{ p.organization }}</div>
              </td>

              <td v-else-if="col.key === 'project_type'" class="px-4 py-3.5">
                <Tooltip :text="typeFullName(p.project_type)">
                  <span class="lcsp-pill" :data-tone="typeTone(p.project_type)">{{ p.project_type }}</span>
                </Tooltip>
              </td>

              <td v-else-if="col.key === 'phase'" class="px-4 py-3.5">
                <span class="lcsp-pill" :data-tone="phaseTone(p.phase)">
                  <i class="lcsp-dot" />{{ __(p.phase) }}
                </span>
              </td>

              <td v-else-if="col.key === 'status'" class="px-4 py-3.5">
                <span class="lcsp-pill" :data-tone="statusTone(p.status)">
                  <i class="lcsp-dot" />{{ __(p.status || 'Open') }}
                </span>
              </td>

              <td v-else-if="col.key === 'probability'" class="px-4 py-3.5 text-right">
                <span v-if="p.probability" :class="probabilityClass(p.probability)" class="text-sm font-medium tabular-nums">
                  {{ Math.round(p.probability) }}%
                </span>
                <span v-else class="text-gray-300">—</span>
              </td>

              <td v-else-if="col.key === 'estimated_value'" class="px-4 py-3.5 text-right font-medium tabular-nums text-gray-900">
                <span v-if="p.estimated_value">{{ formatCurrency(p.estimated_value) }}</span>
                <span v-else class="text-gray-300">—</span>
              </td>

              <!-- Generic cell: dates formatted, everything else as text -->
              <td v-else class="px-4 py-3.5 text-gray-600" :class="col.align === 'right' ? 'text-right' : ''">
                {{ col.date ? formatDateCell(p[col.key]) : (p[col.key] || '—') }}
              </td>
            </template>
          </tr>
        </tbody>
      </table>
      </template>
    </div>
  </div>

  <!-- Inspector — CRM-only fixed overlay (Pilanda mode uses the docked shell
       inspector, fed via inspectPanel in selectProject). -->
  <div
    v-if="selectedProject && !pilandaMode"
    class="fixed right-0 top-0 z-40 flex h-screen w-full flex-col border-l bg-white shadow-2xl sm:w-[22rem]"
  >
    <div class="flex items-center justify-between border-b px-3 py-2">
      <span class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ __('Inspector') }}</span>
      <button class="text-gray-400 hover:text-gray-700" @click="selectedProject = null">
        <FeatherIcon name="x" class="h-4 w-4" />
      </button>
    </div>
    <ProjectInspector :project="selectedProject" class="flex-1 overflow-hidden" @open="navigateToProject" />
  </div>

  <!-- Admin-only: import existing BSM construction sites -->
  <BacklogImportDialog
    v-if="canManageImport"
    v-model:open="showImportDialog"
    @imported="reloadProjects()"
  />

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
import { useUserPreferences } from '@/composables/useUserPreferences'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import BacklogImportDialog from '@/components/lcs/BacklogImportDialog.vue'
import ColumnPicker from '@/components/lcs/ColumnPicker.vue'
import ProjectInspector from '@/components/lcs/ProjectInspector.vue'
import ProjectDashboard from '@/components/lcs/ProjectDashboard.vue'
import ProjectMap from '@/components/lcs/ProjectMap.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconFolder from '~icons/lucide/folder'
import IconSearchX from '~icons/lucide/search-x'
import IconAlertCircle from '~icons/lucide/alert-circle'

const session = sessionStore()
const userPrefs = useUserPreferences()
const { pilandaMode } = usePilandaMode()
const { inspectPanel } = usePilandaInspect()

function openPreferences() {
  window.dispatchEvent(new CustomEvent('lcs-open-preferences'))
}

// Admin-only: show the BSM-import button to sysadmin + sales managers
const showImportDialog = ref(false)
const canManageImport = computed(() => {
  const roles = session.user_roles || session.roles || []
  return userPrefs.state.isSystemManager
    || (Array.isArray(roles) && (roles.includes('System Manager') || roles.includes('Sales Manager')))
})

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
// Inspector selection: single click selects, double click opens.
// In Pilanda mode the details load into the docked shell inspector
// (ProjectInspector as a dynamic panel); in CRM-only mode there is no shell
// inspector, so the local fixed overlay below is used instead.
const selectedProject = ref(null)
function selectProject(p) {
  selectedProject.value = p
  if (pilandaMode.value) {
    inspectPanel({
      component: ProjectInspector,
      props: { project: p },
      on: { open: navigateToProject },
      title: __('Project'),
    })
  }
}

// KPI overview strip over the list
const overview = computed(() => {
  const list = projectList.value || []
  const by = (ph) => list.filter((p) => p.phase === ph).length
  const total = list.reduce((s, p) => s + (Number(p.estimated_value) || 0), 0)
  return { execution: by('Execution'), won: by('Won'), completed: by('Completed'), total }
})
const overviewMoney = computed(() => {
  const n = overview.value.total
  if (n >= 1_000_000) return '€' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return '€' + Math.round(n / 1_000) + 'k'
  return '€' + n
})
const sortField = ref('modified')
const sortDirection = ref('desc')

// View mode: list | map | dashboard — persisted per browser
const viewMode = useStorage('lcs-projects-view-mode', 'list')
const VIEW_MODES = [
  { key: 'list', icon: 'list', label: __('List') },
  { key: 'map', icon: 'map', label: __('Map') },
  { key: 'dashboard', icon: 'bar-chart-2', label: __('Dashboard') },
]

// Map/dashboard data: full portfolio with country centroid coordinates
const mapData = createResource({
  url: 'lcs_integrations.projects.api.get_project_map_data',
})
watch(
  viewMode,
  (mode) => {
    if (mode !== 'list' && !mapData.data && !mapData.loading) mapData.fetch()
  },
  { immediate: true },
)
const mapProjects = computed(() => mapData.data || [])

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
  { label: __('Qualified'), value: 'Qualified' },
  { label: __('Budget'), value: 'Budget' },
  { label: __('Richtpreis'), value: 'Richtpreis' },
  { label: __('Offer'), value: 'Offer' },
  { label: __('Negotiation'), value: 'Negotiation' },
  { label: __('Won'), value: 'Won' },
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

// ---- Per-user configurable columns ---------------------------------
// Catalog = every field the list API provides. Cells with bespoke
// renderers keep them (v-if by key in the template); anything else
// falls back to the generic text/date cell.
const COLUMN_CATALOG = [
  { key: 'project_number', label: __('Project #'), sortable: true },
  { key: 'project_name', label: __('Name'), sortable: true },
  { key: 'project_type', label: __('Type') },
  { key: 'country', label: __('Country') },
  { key: 'phase', label: __('Phase') },
  { key: 'status', label: __('Status') },
  { key: 'salesperson', label: __('Salesperson') },
  { key: 'organization', label: __('Organization') },
  { key: 'expected_close_date', label: __('Expected Close'), date: true },
  { key: 'modified', label: __('Last Modified'), date: true },
  { key: 'probability', label: __('Prob.'), sortable: true, align: 'right' },
  { key: 'estimated_value', label: __('Value'), sortable: true, align: 'right' },
]
const DEFAULT_COLUMNS = [
  'project_number', 'project_name', 'project_type', 'country',
  'phase', 'status', 'salesperson', 'probability', 'estimated_value',
]
const selectedColumns = ref([...DEFAULT_COLUMNS])
// Hydrate from the user's saved preference once prefs are loaded
watch(
  () => userPrefs.state.prefs.list_columns,
  () => {
    const saved = userPrefs.getListColumns('lcs_projects')
    if (saved && saved.length) {
      const valid = COLUMN_CATALOG.map((c) => c.key)
      selectedColumns.value = saved.filter((k) => valid.includes(k))
    }
  },
  { immediate: true },
)
const visibleColumns = computed(() =>
  COLUMN_CATALOG.filter((c) => selectedColumns.value.includes(c.key)),
)
function formatDateCell(v) {
  if (!v) return ''
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleDateString('de-DE')
}

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
    'expected_close_date', 'is_important',
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
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyboard)
  // Don't leave a project panel in the shell inspector on other pages.
  if (pilandaMode.value) inspectPanel(null)
})

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

// Badge tone maps — token-based pills (data-tone → scoped CSS).
// Tones: brand | info | success | warning | danger | neutral.
function typeTone(type) {
  return { SB: 'info', WI: 'brand', LL: 'success', SK: 'warning' }[type] || 'neutral'
}
function phaseTone(phase) {
  return {
    Qualified: 'info', Budget: 'success', Richtpreis: 'brand', Offer: 'warning',
    Negotiation: 'warning', Won: 'success', Execution: 'brand',
    Completed: 'neutral', Lost: 'danger',
  }[phase] || 'neutral'
}
function statusTone(status) {
  return {
    Open: 'info', Active: 'success', 'On Hold': 'warning',
    Completed: 'neutral', Cancelled: 'danger',
  }[status] || 'neutral'
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

<style scoped>
/* Pilanda design system — token-only chrome (matches LCSLeads/LCSNetwork). */
.lcsp-canvas { background: var(--pp-bg-base); }
.lcsp-head { padding: var(--pp-space-5) var(--pp-space-5) var(--pp-space-3); }
.lcsp-filterbar { background: var(--pp-bg-surface); border-color: var(--pp-border-subtle); }
.lcsp-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--pp-space-3); padding: var(--pp-space-4) var(--pp-space-5) 0; }
.lcsp-state { padding: var(--pp-space-10, 40px) var(--pp-space-5); }

/* Table chrome */
.lcsp-thead { background: var(--pp-bg-sunken); color: var(--pp-text-tertiary); }
.lcsp-row { border-color: var(--pp-border-subtle); }
.lcsp-row:hover { background: var(--pp-bg-hover); }
.lcsp-row--sel { background: var(--pp-accent-soft); }

/* Token pills (phase / status / type) */
.lcsp-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px;
  font-weight: var(--pp-weight-semibold); padding: 2px var(--pp-space-2);
  border-radius: var(--pp-radius-full); white-space: nowrap; }
.lcsp-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.lcsp-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent);    color: var(--pp-state-info); }
.lcsp-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.lcsp-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.lcsp-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.lcsp-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
.lcsp-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

@media (max-width: 900px) {
  .lcsp-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
