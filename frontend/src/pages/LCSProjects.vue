<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Sales Projects'), route: { name: 'LCS Projects' } }]" />
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
        :title="__('Sales Projects')"
        :subtitle="viewMode === 'list' && !projectsLoading ? `${projectList.length} ${__('of')} ${totalCount} ${__('Projects')}` : ''"
      />
    </div>
    <!-- H1: Visibility of system status — result count + active filters indicator -->
    <div class="lcsp-filterbar flex flex-wrap items-center justify-between gap-y-2 border-b px-5 py-3">
      <div class="flex flex-wrap items-center gap-2 sm:gap-4">
        <!-- ANSICHT: Liste ⇄ Phasenboard (design master) -->
        <div class="flex items-center gap-2">
          <span class="lcsp-cap">{{ __('View') }}</span>
          <div class="flex items-center rounded-lg border bg-gray-50 p-0.5">
            <button
              v-for="view in VIEW_MODES"
              :key="view.key"
              type="button"
              class="rounded-md px-3 py-1 text-xs font-medium transition"
              :class="viewMode === view.key ? 'bg-white text-lcs-primary shadow-sm' : 'text-gray-500 hover:text-gray-700'"
              :aria-pressed="viewMode === view.key"
              @click="viewMode = view.key"
            >{{ view.label }}</button>
          </div>
        </div>
        <!-- Spalten (per-user column selection) -->
        <ColumnPicker
          v-if="viewMode === 'list'"
          table-key="lcs_projects"
          :catalog="COLUMN_CATALOG"
          :defaults="DEFAULT_COLUMNS"
          v-model="selectedColumns"
        />
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
        <span v-if="viewMode === 'list' && !projectsLoading" class="lcsp-stats">
          {{ projectList.length }} {{ __('of') }} {{ totalCount }} {{ __('Projects') }}
          <template v-if="lostQuarter.count">
            · {{ __('Lost (quarter)') }}: <b>{{ lostQuarter.count }}</b> ({{ moneyShort(lostQuarter.value) }})
          </template>
        </span>
        <Tooltip :text="__('Refresh list (Ctrl+R)')">
          <Button
            variant="ghost"
            icon="refresh-cw"
            @click="reloadProjects()"
            :class="{ 'animate-spin': projectsLoading }"
          />
        </Tooltip>
      </div>
    </div>

    <!-- Main content area -->
    <div class="flex-1 overflow-y-auto overflow-x-auto">
      <!-- Map view — fills the full available height -->
      <div v-if="viewMode === 'map'" class="h-full p-5">
        <div v-if="mapData.loading && !mapProjects.length" class="flex h-full items-center justify-center">
          <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-primary" />
        </div>
        <ProjectMap v-else :projects="mapProjects" height-class="h-full" />
      </div>

      <!-- Dashboard view (portfolio, independent of list filters) -->
      <div v-else-if="viewMode === 'dashboard'" class="p-5">
        <div v-if="mapData.loading && !mapProjects.length" class="flex items-center justify-center py-16">
          <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-primary" />
        </div>
        <ProjectDashboard v-else :projects="mapProjects" :loading="mapData.loading" />
      </div>

      <!-- Kanban view — projects grouped by phase; drag persists the phase.
           Same descent contract as the table (click → inspector, dbl → open). -->
      <div v-else-if="viewMode === 'kanban'" class="h-full overflow-auto p-5">
        <PpKanban
          v-if="projectList.length"
          :columns="kanbanColumns"
          :cards="kanbanCards"
          @card-click="selectProjectById"
          @card-dblclick="navigateToProjectById"
          @move="onProjectMove"
        />
        <div v-else-if="projectsLoading" class="flex items-center justify-center py-16">
          <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-primary" />
        </div>
        <PpEmptyState v-else :icon="IconFolder" :title="__('No projects yet')" :hint="__('Projects appear here grouped by phase.')" />
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

      <!-- Data table — card "Vertriebsprojekte" per the design master -->
      <div v-else class="lcsp-tablecard">
        <div class="lcsp-cardhead">
          <div class="lcsp-cardhead-l">
            <h3 class="lcsp-cardtitle">{{ __('Sales Projects') }}</h3>
            <span class="lcsp-cardcount">{{ projectList.length }} / {{ totalCount }}</span>
          </div>
          <span class="lcsp-cardsub">{{ __('Row = details in the inspector · double-click opens the sales project') }}</span>
        </div>
        <table class="pp-table">
        <thead class="lcsp-thead sticky top-0 z-10">
          <tr>
            <th class="lcsp-th-sel">
              <input
                type="checkbox"
                class="lcsp-check"
                :checked="allSelected"
                :indeterminate.prop="someSelected"
                :aria-label="__('Select all')"
                @change="toggleSelectAll"
              />
              <span v-if="selectedRows.size" class="lcsp-selcount">{{ selectedRows.size }}</span>
            </th>
            <th
              v-for="col in visibleColumns"
              :key="col.key"
              class="select-none"
              :class="[
                col.align === 'right' ? 'text-right' : '',
                col.sortable ? 'lcsp-th--sortable' : '',
                'lcsp-th--drag',
                { 'is-dragover': dragOverCol === col.key },
              ]"
              :title="__('Drag to reorder · click to sort')"
              :aria-sort="col.sortable && sortField === col.key ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'"
              draggable="true"
              @click="col.sortable && toggleSort(col.key)"
              @dragstart="onColDragStart(col.key)"
              @dragover.prevent="dragOverCol = col.key"
              @drop.prevent="onColDrop(col.key)"
              @dragend="dragCol = null; dragOverCol = null"
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
            class="lcsp-row group cursor-pointer transition-colors"
            :class="{ 'lcsp-row--sel': selectedIndex === index || selectedProject?.name === p.name }"
            @click="selectProject(p)"
            @dblclick="navigateToProject(p)"
            @keydown.enter="navigateToProject(p)"
            tabindex="0"
            :aria-label="`${p.project_name} — ${p.phase}`"
          >
            <td class="lcsp-td-sel" @click.stop>
              <input
                type="checkbox"
                class="lcsp-check"
                :checked="selectedRows.has(p.name)"
                :aria-label="__('Select row')"
                @change="toggleSelectRow(p.name)"
              />
            </td>
            <template v-for="col in visibleColumns" :key="col.key">
              <!-- Bespoke cells keep their original renderers -->
              <td v-if="col.key === 'project_number'">
                <span class="lcsp-num">{{ p.project_number }}</span>
                <span v-if="isCreatedToday(p)" class="lcsp-badge-today">{{ __('Resolved today') }}</span>
              </td>

              <td v-else-if="col.key === 'project_name'">
                <div class="flex items-center gap-2">
                  <span class="pp-cell-strong">{{ p.project_name }}</span>
                  <Tooltip v-if="p.notes" :text="notesPreview(p.notes)">
                    <span class="lcsp-noteflag" @click.stop>
                      <FeatherIcon name="edit-3" class="h-2.5 w-2.5" />
                    </span>
                  </Tooltip>
                </div>
                <span class="pp-cell-sub">{{ __('Double-click opens the sales project') }}</span>
              </td>

              <td v-else-if="col.key === 'project_type'">
                <Tooltip :text="typeFullName(p.project_type)">
                  <PpPill :tone="typeTone(p.project_type)" :dot="false">{{ p.project_type }}</PpPill>
                </Tooltip>
              </td>

              <td v-else-if="col.key === 'phase'">
                <PpPill :tone="phaseTone(p.phase)">{{ __(p.phase) }}</PpPill>
              </td>

              <td v-else-if="col.key === 'status'">
                <PpPill :tone="statusTone(p.status)">{{ __(p.status || 'Open') }}</PpPill>
              </td>

              <td v-else-if="col.key === 'probability'" class="text-right">
                <span v-if="p.probability" :class="probabilityClass(p.probability)" class="font-medium tabular-nums">
                  {{ Math.round(p.probability) }}%
                </span>
                <span v-else class="pp-cell-muted">—</span>
              </td>

              <td v-else-if="col.key === 'estimated_value'" class="lcsp-td-money text-right">
                <span v-if="p.estimated_value">{{ moneyShort(p.estimated_value) }}</span>
                <span v-else class="pp-cell-muted">—</span>
              </td>

              <td v-else-if="col.key === 'weighted'" class="lcsp-td-money text-right">
                <span v-if="p.estimated_value && p.probability">{{ moneyShort(weightedValue(p)) }}</span>
                <span v-else class="pp-cell-muted">—</span>
              </td>

              <td v-else-if="col.key === 'expected_close_date'" class="pp-cell-soft text-right">
                {{ formatClosing(p) }}
              </td>

              <!-- Generic cell: dates formatted, everything else as text -->
              <td v-else class="pp-cell-soft" :class="col.align === 'right' ? 'text-right' : ''">
                {{ col.date ? formatDateCell(p[col.key]) : (p[col.key] || '—') }}
              </td>
            </template>
          </tr>
        </tbody>
        </table>
      </div>
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
import { createResource, call, Breadcrumbs, Button, FormControl, Dialog, Tooltip, FeatherIcon, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { sessionStore } from '@/stores/session'
import { useOfflineList } from '@/composables/useOfflineList'
import { useUserPreferences } from '@/composables/useUserPreferences'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { useListFuncbar } from '@/composables/useListFuncbar'
import BacklogImportDialog from '@/components/lcs/BacklogImportDialog.vue'
import ColumnPicker from '@/components/lcs/ColumnPicker.vue'
import ProjectInspector from '@/components/lcs/ProjectInspector.vue'
import ProjectDashboard from '@/components/lcs/ProjectDashboard.vue'
import ProjectMap from '@/components/lcs/ProjectMap.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpPill from '@/components/pp/PpPill.vue'
import PpKanban from '@/components/pp/PpKanban.vue'
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

// --- Kanban view (Befund 18: same SSOT list, same descent contract) --------
// Single card click → inspector (selectProject), double click → open, drag →
// persist the phase. PpKanban holds the moved card optimistically; the reload
// after persisting confirms it (or reverts it on error).
function selectProjectById(id) {
  const p = projectList.value.find((x) => x.name === id)
  if (p) selectProject(p)
}
function navigateToProjectById(id) {
  const p = projectList.value.find((x) => x.name === id)
  if (p) navigateToProject(p)
}
const kanbanColumns = computed(() =>
  phaseOptions.filter((o) => o.value).map((o) => ({ key: o.value, label: o.label })),
)
const kanbanCards = computed(() =>
  projectList.value.map((p) => ({
    id: p.name,
    col: p.phase,
    title: p.project_name || p.name,
    badges: [
      ...(p.project_type ? [{ label: p.project_type, tone: typeTone(p.project_type) }] : []),
      ...(p.estimated_value ? [{ label: formatCurrency(p.estimated_value), tone: 'neutral' }] : []),
    ],
    assignee: p.salesperson || null,
  })),
)
async function onProjectMove({ cardId, fromCol, toCol }) {
  if (fromCol === toCol) return
  try {
    await call('frappe.client.set_value', { doctype: 'LCS Project', name: cardId, fieldname: { phase: toCol } })
    toast({ title: __('Phase updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
    reloadProjects()
  } catch (e) {
    toast({ title: __('Could not save. Please try again.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' })
    reloadProjects()
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
// Lost this quarter — count + summed value (design master header stat).
const lostQuarter = computed(() => {
  const q = new Date(); q.setMonth(q.getMonth() - 3)
  const lost = (projectList.value || []).filter((p) => {
    if (p.phase !== 'Lost') return false
    const d = new Date(String(p.modified || '').replace(' ', 'T'))
    return isNaN(d) ? true : d >= q
  })
  return { count: lost.length, value: lost.reduce((s, p) => s + (Number(p.estimated_value) || 0), 0) }
})
const sortField = ref('modified')
const sortDirection = ref('desc')

// View mode: Liste ⇄ Phasenboard (design master). The territory/portfolio maps
// live on their own nav page (Projektlandkarte), so the in-list toggle is just
// the two views the master shows.
const viewMode = useStorage('lcs-projects-view-mode', 'list')
if (!['list', 'kanban'].includes(viewMode.value)) viewMode.value = 'list'
const VIEW_MODES = [
  { key: 'list', label: __('List') },
  { key: 'kanban', label: __('Phase board') },
]

// Map/dashboard data: full portfolio with country centroid coordinates
const mapData = createResource({
  url: 'lcs_integrations.projects.api.get_project_map_data',
})
watch(
  viewMode,
  (mode) => {
    if (['map', 'dashboard'].includes(mode) && !mapData.data && !mapData.loading) mapData.fetch()
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
// Order follows the klickdummy design master: Projektnummer · Vertriebsprojekt ·
// Firma · Phase · Wert · Wahrsch. · Gewichtet · Abschluss · Verkäufer.
// visibleColumns filters this list preserving THIS order, so the catalog order
// is the on-screen order. Extra fields below are opt-in via the column picker.
const COLUMN_CATALOG = [
  { key: 'project_number', label: __('Project number'), sortable: true },
  { key: 'project_name', label: __('Sales project'), sortable: true },
  { key: 'organization', label: __('Company') },
  { key: 'phase', label: __('Phase') },
  { key: 'estimated_value', label: __('Value'), sortable: true, align: 'right' },
  { key: 'probability', label: __('Prob.'), sortable: true, align: 'right' },
  { key: 'weighted', label: __('Weighted'), align: 'right' },
  { key: 'expected_close_date', label: __('Closing'), align: 'right' },
  { key: 'salesperson', label: __('Seller') },
  { key: 'project_type', label: __('Type') },
  { key: 'country', label: __('Country') },
  { key: 'status', label: __('Status') },
  { key: 'modified', label: __('Last Modified'), date: true },
]
const DEFAULT_COLUMNS = [
  'project_number', 'project_name', 'organization', 'phase',
  'estimated_value', 'probability', 'weighted', 'expected_close_date', 'salesperson',
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
// Per-user column order (drag headers to reorder), reconciled with the catalog
// so new/removed columns are handled. Persisted in the browser.
const columnOrder = useStorage('lcs-projects-col-order', COLUMN_CATALOG.map((c) => c.key))
const orderedCatalog = computed(() => {
  const ord = columnOrder.value
  const known = COLUMN_CATALOG.map((c) => c.key)
  const kept = ord.filter((k) => known.includes(k))
  const rest = known.filter((k) => !kept.includes(k))
  return [...kept, ...rest].map((k) => COLUMN_CATALOG.find((c) => c.key === k)).filter(Boolean)
})
const visibleColumns = computed(() =>
  orderedCatalog.value.filter((c) => selectedColumns.value.includes(c.key)),
)

// Drag-and-drop column reordering.
const dragCol = ref(null)
const dragOverCol = ref(null)
function onColDragStart(key) { dragCol.value = key }
function onColDrop(targetKey) {
  const from = dragCol.value
  dragOverCol.value = null
  if (!from || from === targetKey) { dragCol.value = null; return }
  const keys = orderedCatalog.value.map((c) => c.key)
  const fi = keys.indexOf(from)
  const ti = keys.indexOf(targetKey)
  if (fi >= 0 && ti >= 0) { keys.splice(ti, 0, keys.splice(fi, 1)[0]); columnOrder.value = keys }
  dragCol.value = null
}

// Row selection (checkbox column; independent of the inspector row-click).
const selectedRows = ref(new Set())
const allSelected = computed(() =>
  projectList.value.length > 0 && projectList.value.every((p) => selectedRows.value.has(p.name)),
)
const someSelected = computed(() =>
  projectList.value.some((p) => selectedRows.value.has(p.name)) && !allSelected.value,
)
function toggleSelectRow(id) {
  const next = new Set(selectedRows.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedRows.value = next
}
function toggleSelectAll() {
  selectedRows.value = allSelected.value ? new Set() : new Set(projectList.value.map((p) => p.name))
}
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
    'probability', 'estimated_value', 'notes', 'modified', 'creation',
    'expected_close_date', 'is_important',
  ],
  filters: activeFilters,
  orderBy: orderBy,
  pageLength: 100,
})

const totalCount = computed(() => projectsData.value?.length || 0)
const projectList = computed(() => projectsData.value || [])

useListFuncbar({ title: __('Projects'), meaning: __('Sales projects (Deal = Project).'), count: () => projectList.value.length, reload: reloadProjects,
  taskRef: () => selectedProject.value ? { doctype: 'LCS Project', name: selectedProject.value.name, title: selectedProject.value.project_name || selectedProject.value.name } : null })

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

// Compact money (design master: "2,6 M€" / "820 k€").
function moneyShort(val) {
  const n = Number(val) || 0
  if (!n) return '—'
  if (n >= 1_000_000) return (n / 1_000_000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' M€'
  if (n >= 1_000) return Math.round(n / 1_000).toLocaleString('de-DE') + ' k€'
  return Math.round(n).toLocaleString('de-DE') + ' €'
}
// Weighted value = estimated value × win probability.
function weightedValue(p) {
  return (Number(p.estimated_value) || 0) * (Number(p.probability) || 0) / 100
}
// Closing date as "Dez 2026"; Won/Completed show "gewonnen MM/YYYY".
function formatClosing(p) {
  const v = p.expected_close_date
  if (['Won', 'Completed'].includes(p.phase) && v) {
    const d = new Date(v)
    if (!isNaN(d)) return __('won') + ' ' + String(d.getMonth() + 1).padStart(2, '0') + '/' + d.getFullYear()
  }
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : new Intl.DateTimeFormat('de-DE', { month: 'short', year: 'numeric' }).format(d)
}
// "Resolved today" badge — project created today (freshly converted from a lead).
function isCreatedToday(p) {
  if (!p.creation) return false
  const d = new Date(String(p.creation).replace(' ', 'T'))
  const now = new Date()
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
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

/* Chrome comes from the global .pp-table utility. This list keeps its own
   <table> (instead of PpDataGrid) because it sorts and paginates SERVER-side
   via order_by — the grid would only sort the page it happens to hold. */
.lcsp-th--sortable { cursor: pointer; }
.lcsp-th--sortable:hover { color: var(--pp-text-secondary); background: var(--pp-bg-hover); }
.lcsp-row--sel td { background: rgb(var(--pp-brand-primary-rgb) / 0.10); }

/* Spalten per Drag umsortieren */
.lcsp-th--drag { cursor: grab; }
.lcsp-th--drag.is-dragover { box-shadow: inset 3px 0 0 var(--pp-brand-primary); }

/* Auswahl-Spalte (Checkboxen) */
.lcsp-th-sel, .lcsp-td-sel { width: 40px; text-align: center; white-space: nowrap; }
.lcsp-check { width: 15px; height: 15px; accent-color: var(--pp-brand-primary); cursor: pointer; vertical-align: middle; }
.lcsp-selcount { display: inline-block; margin-left: 4px; vertical-align: middle; font-size: 10px;
  font-weight: var(--pp-weight-bold); color: var(--pp-text-on-accent); background: var(--pp-brand-primary);
  padding: 1px 6px; border-radius: var(--pp-radius-full); letter-spacing: 0; }

/* Project number — brand-teal, bold (design master) + "heute gelöst" badge. */
.lcsp-num { font-family: var(--pp-font-mono, monospace); font-size: var(--pp-fs-13, 13px);
  font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary); }
.lcsp-badge-today { margin-left: var(--pp-space-2); display: inline-flex; align-items: center;
  font-size: 10px; font-weight: var(--pp-weight-semibold); padding: 1px var(--pp-space-2);
  border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.lcsp-td-money { font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); font-variant-numeric: tabular-nums; }
.lcsp-noteflag { display: inline-flex; align-items: center; padding: 2px 4px;
  border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-accent-amber) 18%, transparent);
  color: var(--pp-accent-amber); }

/* Toolbar caption ("ANSICHT") + result stats. */
.lcsp-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.lcsp-stats { color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; }
.lcsp-stats b { color: var(--pp-text-primary); font-weight: var(--pp-weight-semibold); }

/* "Vertriebsprojekte" card wrapping the table. */
.lcsp-tablecard { margin: var(--pp-space-4) var(--pp-space-5) var(--pp-space-6);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); overflow: hidden; }
.lcsp-cardhead { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3);
  flex-wrap: wrap; padding: var(--pp-space-3) var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle); background: var(--pp-bg-sunken); }
.lcsp-cardhead-l { display: flex; align-items: baseline; gap: var(--pp-space-2); }
.lcsp-cardtitle { margin: 0; font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.lcsp-cardcount { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.lcsp-cardsub { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }

@media (max-width: 900px) {
  .lcsp-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
