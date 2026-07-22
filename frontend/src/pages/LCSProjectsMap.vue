<!--
  LCSProjectsMap — full-bleed world map of all LCS Projects.
  Wraps the existing ProjectMap component with page chrome, filters,
  and a fetch against lcs_integrations.projects.map_api.get_projects_for_map.
-->

<template>
  <div class="lcspm flex h-full flex-col">
    <!-- Page header with filters -->
    <header class="lcspm-head">
      <PpPageHead
        :eyebrow="__('Sales / CRM')"
        :title="__('Projects Map')"
        :subtitle="__('Live world map of all LCS projects — filter by phase or sales manager')"
      >
        <template #actions>
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
        </template>
      </PpPageHead>
    </header>

    <!-- Banner: countries without coordinates -->
    <div v-if="unmappedCountries.length" class="lcspm-banner">
      <span class="lcspm-banner-strong">{{ __('Missing map coordinates:') }}</span>
      {{ unmappedCountries.join(', ') }}
      <span class="lcspm-banner-note">({{ __('add them in country_coords.py') }})</span>
    </div>

    <!-- Map body — OSM detail map -->
    <div class="lcspm-body flex-1 overflow-auto p-3">
      <ProjectMap
        :projects="filteredProjects"
        height-class="h-[calc(100vh-16rem)]"
      />
    </div>

    <!-- Stats footer -->
    <footer class="lcspm-foot">
      <span>
        {{ filteredProjects.length }} {{ __('shown') }} ·
        {{ mappedProjects.length }} {{ __('mapped') }} ·
        {{ allProjects.length }} {{ __('total') }}
      </span>
      <span v-if="lastFetchedAt" class="lcspm-foot-muted">
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
import PpPageHead from '@/components/pp/PpPageHead.vue'

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

<style scoped>
.lcspm { background: var(--pp-bg-base); }
.lcspm-head { padding: var(--pp-space-5) var(--pp-space-5) var(--pp-space-4);
  background: var(--pp-bg-surface); border-bottom: 1px solid var(--pp-border-subtle); }
.lcspm-banner { padding: var(--pp-space-2) var(--pp-space-4); font-size: var(--pp-fs-12);
  border-bottom: 1px solid color-mix(in oklab, var(--pp-state-warning) 30%, transparent);
  background: color-mix(in oklab, var(--pp-state-warning) 12%, transparent);
  color: var(--pp-state-warning); }
.lcspm-banner-strong { font-weight: var(--pp-weight-semibold); }
.lcspm-banner-note { margin-left: var(--pp-space-1); opacity: 0.8; }
.lcspm-body { background: var(--pp-bg-base); }
.lcspm-foot { display: flex; align-items: center; justify-content: space-between;
  padding: var(--pp-space-2) var(--pp-space-4); font-size: var(--pp-fs-12);
  color: var(--pp-text-tertiary); background: var(--pp-bg-surface);
  border-top: 1px solid var(--pp-border-subtle); }
.lcspm-foot-muted { color: var(--pp-text-tertiary); opacity: 0.75; }
</style>
