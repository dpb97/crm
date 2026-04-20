<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Projects'), route: { name: 'LCS Projects' } }]" />
    </template>
    <template #right-header>
      <Button variant="solid" @click="showNewDialog = true" :label="__('New Project')" iconLeft="plus" />
    </template>
  </LayoutHeader>
  <div class="p-4">
    <!-- Filter bar -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <FormControl
        type="select"
        :options="typeOptions"
        v-model="filters.project_type"
        :placeholder="__('All Types')"
        class="w-32"
      />
      <FormControl
        type="select"
        :options="phaseOptions"
        v-model="filters.phase"
        :placeholder="__('All Phases')"
        class="w-36"
      />
      <FormControl
        type="text"
        v-model="filters.country"
        :placeholder="__('Country')"
        class="w-32"
      />
      <Button variant="ghost" @click="clearFilters" :label="__('Clear')" />
    </div>
    <!-- Projects table -->
    <div class="rounded-lg border bg-white">
      <div v-if="projects.loading" class="p-8 text-center text-gray-500">
        {{ __('Loading...') }}
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
            <th class="px-4 py-3">{{ __('Project #') }}</th>
            <th class="px-4 py-3">{{ __('Name') }}</th>
            <th class="px-4 py-3">{{ __('Type') }}</th>
            <th class="px-4 py-3">{{ __('Country') }}</th>
            <th class="px-4 py-3">{{ __('Phase') }}</th>
            <th class="px-4 py-3">{{ __('Salesperson') }}</th>
            <th class="px-4 py-3 text-right">{{ __('Probability') }}</th>
            <th class="px-4 py-3 text-right">{{ __('Value') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in projectList"
            :key="p.name"
            class="cursor-pointer border-b transition hover:bg-gray-50"
            @click="$router.push({ name: 'LCS Project', params: { id: p.name } })"
          >
            <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ p.project_number }}</td>
            <td class="px-4 py-3 font-medium text-gray-900">{{ p.project_name }}</td>
            <td class="px-4 py-3">
              <span
                :class="typeClass(p.project_type)"
                class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
              >
                {{ p.project_type }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ p.country }}</td>
            <td class="px-4 py-3">
              <span
                :class="phaseClass(p.phase)"
                class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
              >
                {{ __(p.phase) }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ p.salesperson }}</td>
            <td class="px-4 py-3 text-right">
              <span v-if="p.probability" class="text-gray-700">{{ Math.round(p.probability) }}%</span>
            </td>
            <td class="px-4 py-3 text-right font-medium text-gray-900">
              <span v-if="p.estimated_value">{{ formatCurrency(p.estimated_value) }}</span>
            </td>
          </tr>
          <tr v-if="!projectList.length">
            <td colspan="8" class="px-4 py-8 text-center text-gray-400">
              {{ __('No projects found') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <!-- New Project Dialog -->
  <Dialog v-model="showNewDialog" :options="{ title: __('New Project'), size: 'lg' }">
    <template #body-content>
      <div class="grid grid-cols-2 gap-4">
        <FormControl :label="__('Project Name')" v-model="newProject.project_name" type="text" required />
        <FormControl :label="__('Project Type')" v-model="newProject.project_type" type="select" :options="typeOptionsRaw" />
        <FormControl :label="__('Project Abbreviation')" v-model="newProject.project_abbr" type="text" />
        <FormControl :label="__('Country')" v-model="newProject.country" type="text" />
        <FormControl :label="__('Salesperson')" v-model="newProject.salesperson" type="text" />
        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="newProject.is_gu" id="gu-check" class="rounded border-gray-300" />
          <label for="gu-check" class="text-sm">{{ __('General Contractor (GU)') }}</label>
        </div>
        <div class="col-span-2">
          <FormControl :label="__('Description')" v-model="newProject.project_description" type="textarea" />
        </div>
      </div>
    </template>
    <template #actions>
      <Button variant="solid" @click="createProject" :loading="creating" :label="__('Create Project')" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import { createListResource, createResource, Breadcrumbs, Button, FormControl, Dialog, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'

const router = useRouter()

const filters = reactive({ project_type: '', phase: '', country: '' })
const showNewDialog = ref(false)
const creating = ref(false)
const newProject = reactive({
  project_name: '',
  project_type: 'SB',
  project_abbr: '',
  country: '',
  salesperson: '',
  is_gu: false,
  project_description: '',
})

const typeOptionsRaw = [
  { label: 'SB — Seilbahn', value: 'SB' },
  { label: 'WI — Winde', value: 'WI' },
  { label: 'LL — Liftanlage', value: 'LL' },
  { label: 'SK — Sonderkonstruktion', value: 'SK' },
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

const activeFilters = computed(() => {
  const f = {}
  if (filters.project_type) f.project_type = filters.project_type
  if (filters.phase) f.phase = filters.phase
  if (filters.country) f.country = ['like', `%${filters.country}%`]
  return f
})

const projects = createListResource({
  doctype: 'LCS Project',
  fields: [
    'name', 'project_name', 'project_number', 'project_type',
    'country', 'phase', 'status', 'salesperson', 'probability',
    'estimated_value', 'modified',
  ],
  filters: activeFilters,
  orderBy: 'modified desc',
  pageLength: 50,
  auto: true,
})

watch(activeFilters, () => { projects.reload() }, { deep: true })

const projectList = computed(() => projects.data || [])

function clearFilters() {
  filters.project_type = ''
  filters.phase = ''
  filters.country = ''
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

function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(val)
}

async function createProject() {
  creating.value = true
  try {
    const res = createResource({
      url: 'frappe.client.insert',
      params: { doc: { doctype: 'LCS Project', ...newProject } },
    })
    await res.submit()
    showNewDialog.value = false
    Object.assign(newProject, {
      project_name: '', project_type: 'SB', project_abbr: '',
      country: '', salesperson: '', is_gu: false, project_description: '',
    })
    projects.reload()
    toast.success(__('Project created'))
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error creating project'))
  } finally {
    creating.value = false
  }
}
</script>
