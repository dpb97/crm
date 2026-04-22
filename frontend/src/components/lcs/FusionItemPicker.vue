<!--
  FusionItemPicker — autocomplete-style widget for linking an LCS Project
  to a Fusion Manage item.

  Shows:
  - current linked item (if any) with unlink button
  - workspace dropdown (populated from tenant)
  - type-ahead search with debounced calls to search_items
  - item cards that the user can click to link

  Emits `linked` with the new link info after the backend confirms.
-->

<template>
  <div class="space-y-3">
    <!-- Currently linked state -->
    <div
      v-if="linked"
      class="rounded-lg border border-purple-200 bg-purple-50 p-3"
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2 text-xs font-semibold text-purple-700">
            <FeatherIcon name="box" class="h-3 w-3" />
            {{ __('Linked to Fusion Manage') }}
          </div>
          <div class="mt-1 font-mono text-sm text-purple-900">{{ fusionNumber || fusionItemId }}</div>
          <div v-if="fusionDescription" class="mt-0.5 truncate text-xs text-purple-700">
            {{ fusionDescription }}
          </div>
          <div v-if="fusionState" class="mt-1 inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-medium text-purple-800">
            <span class="h-1.5 w-1.5 rounded-full bg-purple-500" />
            {{ fusionState }}
          </div>
        </div>
        <div class="flex flex-col items-end gap-1">
          <a
            v-if="deepLinkUrl"
            :href="deepLinkUrl"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 rounded-md border border-purple-300 bg-white px-2 py-1 text-xs font-medium text-purple-700 hover:bg-purple-100"
          >
            <FeatherIcon name="external-link" class="h-3 w-3" /> {{ __('Open') }}
          </a>
          <button
            class="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-500 hover:border-red-300 hover:text-red-600"
            @click="unlink"
            :disabled="busy"
          >
            <FeatherIcon name="x" class="h-3 w-3" /> {{ __('Unlink') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Not linked — show picker -->
    <div v-else class="rounded-lg border border-dashed border-gray-200 p-3">
      <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        <FeatherIcon name="link" class="mr-1 inline h-3 w-3" />
        {{ __('Link a Fusion Manage item') }}
      </div>

      <!-- Workspace selector -->
      <div class="mb-2 flex items-center gap-2">
        <label class="text-xs text-gray-500">{{ __('Workspace') }}:</label>
        <select
          v-model="selectedWorkspace"
          class="flex-1 rounded-md border border-gray-300 bg-white px-2 py-1 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
          :disabled="workspacesLoading || !workspaces.length"
        >
          <option v-if="workspacesLoading" value="">{{ __('Loading workspaces...') }}</option>
          <option v-else-if="!workspaces.length" value="">{{ __('No workspaces available') }}</option>
          <option v-for="w in workspaces" :key="w.id" :value="w.id">
            {{ w.name }} ({{ w.id }})
          </option>
        </select>
      </div>

      <!-- Search input -->
      <div class="relative">
        <input
          v-model="searchQuery"
          type="search"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 pr-8 text-sm placeholder:text-gray-400 focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
          :placeholder="__('Search by item number or description...')"
          :disabled="!selectedWorkspace"
          @input="onSearch"
        />
        <div v-if="searching" class="absolute right-2 top-1.5">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
        </div>
      </div>

      <!-- Results -->
      <div v-if="searchResults.length" class="mt-2 max-h-60 overflow-y-auto rounded-md border bg-white">
        <button
          v-for="item in searchResults"
          :key="item.id"
          class="flex w-full items-start justify-between gap-2 border-b px-3 py-2 text-left hover:bg-purple-50"
          @click="linkItem(item)"
          :disabled="busy"
        >
          <div class="min-w-0 flex-1">
            <div class="font-mono text-xs font-semibold text-gray-800">{{ item.number || item.id }}</div>
            <div v-if="item.description" class="mt-0.5 truncate text-xs text-gray-600">{{ item.description }}</div>
          </div>
          <span v-if="item.state" class="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-700">
            {{ item.state }}
          </span>
        </button>
      </div>

      <div v-else-if="searchQuery.length >= 2 && !searching" class="mt-2 rounded-md bg-gray-50 p-3 text-center text-xs text-gray-500">
        {{ __('No items match your search.') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { call, FeatherIcon, toast } from 'frappe-ui'

const props = defineProps({
  projectName: { type: String, required: true },
  fusionWorkspace: { type: String, default: '' },
  fusionItemId: { type: String, default: '' },
  fusionNumber: { type: String, default: '' },
  fusionDescription: { type: String, default: '' },
  fusionState: { type: String, default: '' },
})

const emit = defineEmits(['linked', 'unlinked'])

const linked = ref(!!props.fusionItemId)
watch(() => props.fusionItemId, (v) => { linked.value = !!v })

const workspaces = ref([])
const workspacesLoading = ref(false)
const selectedWorkspace = ref(props.fusionWorkspace)

const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref([])
const busy = ref(false)

const deepLinkUrl = ref('')

async function loadWorkspaces() {
  workspacesLoading.value = true
  try {
    const res = await call('lcs_integrations.fusion_manage.service.list_workspaces')
    workspaces.value = res.message || res || []
    if (!selectedWorkspace.value && workspaces.value.length) {
      selectedWorkspace.value = workspaces.value[0].id
    }
  } catch (err) {
    console.warn('Fusion workspaces load failed:', err)
  } finally {
    workspacesLoading.value = false
  }
}

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  searching.value = true
  searchTimer = setTimeout(async () => {
    try {
      const res = await call('lcs_integrations.fusion_manage.service.search_items', {
        query: searchQuery.value,
        workspace: selectedWorkspace.value,
      })
      searchResults.value = res.message || res || []
    } catch (err) {
      console.warn('search_items failed:', err)
      searchResults.value = []
    } finally {
      searching.value = false
    }
  }, 300)
}

async function linkItem(item) {
  if (busy.value) return
  busy.value = true
  try {
    const res = await call('lcs_integrations.fusion_manage.service.link_project_to_item', {
      project: props.projectName,
      workspace: selectedWorkspace.value,
      item_id: item.id,
    })
    toast({ title: __('Linked'), text: item.number || item.id, icon: 'check-circle', iconClasses: 'text-green-500' })
    emit('linked', { workspace: selectedWorkspace.value, item_id: item.id, item: res.message?.item || res.item })
  } catch (err) {
    toast({ title: __('Link failed'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = false
  }
}

async function unlink() {
  if (!confirm(__('Remove the Fusion Manage link from this project?'))) return
  busy.value = true
  try {
    await call('lcs_integrations.fusion_manage.service.unlink_project', { project: props.projectName })
    toast({ title: __('Unlinked'), icon: 'check-circle', iconClasses: 'text-green-500' })
    emit('unlinked')
  } catch (err) {
    toast({ title: __('Unlink failed'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    busy.value = false
  }
}

async function resolveDeepLink() {
  if (!props.fusionWorkspace || !props.fusionItemId) {
    deepLinkUrl.value = ''
    return
  }
  try {
    const res = await call('lcs_integrations.fusion_manage.service.get_deep_link', {
      workspace: props.fusionWorkspace,
      item_id: props.fusionItemId,
    })
    deepLinkUrl.value = res.message || res || ''
  } catch {
    deepLinkUrl.value = ''
  }
}

onMounted(() => {
  if (!linked.value) loadWorkspaces()
  resolveDeepLink()
})

watch(() => props.fusionItemId, () => resolveDeepLink())
</script>
