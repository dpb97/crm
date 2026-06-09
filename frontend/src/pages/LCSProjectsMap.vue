<!--
  LCSProjectsMap — full-bleed world map of all LCS Projects.
  Wraps the existing ProjectMap component with page chrome, filters,
  and a fetch against lcs_integrations.projects.map_api.get_projects_for_map.
-->

<template>
  <div class="flex h-full flex-col">
    <!-- Page header with filters -->
    <header
      class="flex flex-wrap items-center gap-3 border-b border-gray-200 bg-white px-4 py-3"
    >
      <h1 class="text-lg font-semibold text-gray-900">
        {{ __('Projects Map') }}
      </h1>

      <div class="ml-auto flex flex-wrap items-center gap-2">
        <FormControl
          v-model="phaseFilter"
          type="select"
          :placeholder="__('Phase')"
          :options="phaseOptions"
          class="min-w-[140px]"
        />
        <FormControl
          v-model="salesManagerFilter"
          type="autocomplete"
          :placeholder="__('Sales Manager')"
          :options="salesManagerOptions"
          class="min-w-[180px]"
        />
        <Button
          v-if="phaseFilter || salesManagerFilter"
          variant="ghost"
          @click="clearFilters"
        >
          {{ __('Clear') }}
        </Button>
        <Button :loading="loading" @click="fetchData">
          <template #prefix>
            <LucideRefreshCw class="h-4 w-4" />
          </template>
          {{ __('Refresh') }}
        </Button>
      </div>
    </header>

    <!-- Banner: countries without coordinates -->
    <div
      v-if="unmappedCountries.length"
      class="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800"
    >
      <span class="font-medium">{{ __('Missing map coordinates:') }}</span>
      {{ unmappedCountries.join(', ') }}
      <span class="ml-1 text-amber-700">
        ({{ __('add them in map_api.py') }})
      </span>
    </div>

    <!-- Map body -->
    <div class="flex-1 overflow-hidden bg-gray-50 p-3">
      <ProjectMap
        :projects="filteredProjects"
        height-class="h-[calc(100vh-13rem)]"
      />
    </div>

    <!-- Stats footer -->
    <footer
      class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-2 text-xs text-gray-500"
    >
      <span>
        {{ filteredProjects.length }} {{ __('shown') }} ·
        {{ mappedProjects.length }} {{ __('mapped') }} ·
        {{ allProjects.length }} {{ __('total') }}
      </span>
      <span v-if="lastFetchedAt" class="text-gray-400">
        {{ __('Updated') }}: {{ lastFetchedAt }}
      </span>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, FormControl, createResource } from 'frappe-ui'
import LucideRefreshCw from '~icons/lucide/refresh-cw'
import ProjectMap from '@/components/lcs/ProjectMap.vue'

const allProjects = ref([])
const unmappedCountries = ref([])
const lastFetchedAt = ref('')
const loading = ref(false)

const phaseFilter = ref('')
const salesManagerFilter = ref('')

const phaseOptions = [
  '',
  'Qualified',
  'Budget',
  'Richtpreis',
  'Offer',
  'Negotiation',
  'Won',
  'Execution',
  'Completed',
  'Lost',
]

const usersResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'User',
    filters: { enabled: 1, user_type: 'System User' },
    fields: ['name', 'full_name'],
    limit_page_length: 200,
  },
  auto: true,
})

const salesManagerOptions = computed(() =>
  (usersResource.data || []).map((u) => ({
    label: u.full_name || u.name,
    value: u.name,
  })),
)

const mappedProjects = computed(() =>
  allProjects.value.filter((p) => p.latitude != null && p.longitude != null),
)

const filteredProjects = computed(() =>
  mappedProjects.value.filter((p) => {
    if (phaseFilter.value && p.phase !== phaseFilter.value) return false
    if (
      salesManagerFilter.value &&
      p.sales_manager !== salesManagerFilter.value
    )
      return false
    return true
  }),
)

function clearFilters() {
  phaseFilter.value = ''
  salesManagerFilter.value = ''
}

async function fetchData() {
  loading.value = true
  try {
    const r = await fetch(
      '/api/method/lcs_integrations.projects.map_api.get_projects_for_map',
      {
        credentials: 'include',
        headers: { 'X-Frappe-CSRF-Token': window.csrf_token || 'token' },
      },
    )
    const json = await r.json()
    const msg = json.message || {}
    allProjects.value = msg.projects || []
    unmappedCountries.value = msg.unmapped_countries || []
    lastFetchedAt.value = new Date().toLocaleTimeString()
  } catch (e) {
    console.error('Failed to load projects map data', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
