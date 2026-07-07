<!--
  GlobalSearchDialog — Ctrl/Cmd+K search across leads, deals, contacts,
  organizations and LCS projects. One backend round trip returns grouped
  hits (permission-checked per doctype); arrow keys navigate, Enter opens.
-->

<template>
  <Dialog v-model="show" :options="{ size: 'lg' }">
    <template #body>
      <div class="flex items-center gap-2 border-b px-4 py-3">
        <FeatherIcon name="search" class="h-4 w-4 shrink-0 text-gray-400" />
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          class="w-full border-0 bg-transparent p-0 text-base focus:ring-0"
          :placeholder="__('Search leads, deals, contacts, projects...')"
          @keydown.down.prevent="move(1)"
          @keydown.up.prevent="move(-1)"
          @keydown.enter.prevent="openActive()"
        />
        <span class="shrink-0 rounded border px-1.5 py-0.5 text-[10px] text-gray-400">ESC</span>
      </div>

      <div class="max-h-[24rem] overflow-y-auto p-2">
        <div v-if="loading" class="px-3 py-6 text-center text-sm text-gray-400">{{ __('Searching...') }}</div>
        <div v-else-if="query.length >= 2 && !flat.length" class="px-3 py-6 text-center text-sm text-gray-400">
          {{ __('No results for') }} „{{ query }}"
        </div>
        <div v-else-if="query.length < 2" class="px-3 py-6 text-center text-sm text-gray-400">
          {{ __('Type at least 2 characters') }}
        </div>

        <template v-for="group in groups" :key="group.doctype">
          <div class="px-3 pb-1 pt-3 text-[10px] font-bold uppercase tracking-wider text-gray-400">
            {{ __(GROUP_LABELS[group.doctype] || group.doctype) }}
          </div>
          <button
            v-for="r in group.results"
            :key="group.doctype + r.name"
            type="button"
            class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left transition"
            :class="isActive(group.doctype, r.name) ? 'bg-lcs-primary/10' : 'hover:bg-gray-50'"
            @mouseenter="setActive(group.doctype, r.name)"
            @click="open(group.doctype, r)"
          >
            <FeatherIcon :name="GROUP_ICONS[group.doctype] || 'file'" class="h-3.5 w-3.5 shrink-0 text-gray-400" />
            <span class="min-w-0">
              <span class="block truncate text-sm text-ink-gray-9">{{ r.label }}</span>
              <span v-if="r.sub" class="block truncate text-xs text-gray-400">{{ r.sub }}</span>
            </span>
          </button>
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Dialog, FeatherIcon, call } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'

const show = defineModel({ type: Boolean, default: false })
const router = useRouter()

const GROUP_LABELS = {
  'CRM Lead': 'Leads',
  'CRM Deal': 'Deals',
  Contact: 'Contacts',
  'CRM Organization': 'Organizations',
  'LCS Project': 'Projects',
}
const GROUP_ICONS = {
  'CRM Lead': 'user-plus',
  'CRM Deal': 'briefcase',
  Contact: 'user',
  'CRM Organization': 'home',
  'LCS Project': 'folder',
}
const ROUTES = {
  'CRM Lead': (n) => ({ name: 'Lead', params: { leadId: n } }),
  'CRM Deal': (n) => ({ name: 'Deal', params: { dealId: n } }),
  Contact: (n) => ({ name: 'Contact', params: { contactId: n } }),
  'CRM Organization': (n) => ({ name: 'Organization', params: { organizationId: n } }),
  'LCS Project': (n) => ({ name: 'LCS Project', params: { id: n } }),
}

const query = ref('')
const groups = ref([])
const loading = ref(false)
const active = ref(null) // `${doctype}::${name}`
const inputRef = ref(null)

watch(show, async (v) => {
  if (v) {
    query.value = ''
    groups.value = []
    active.value = null
    await nextTick()
    inputRef.value?.focus()
  }
})

watchDebounced(
  query,
  async (q) => {
    if ((q || '').trim().length < 2) {
      groups.value = []
      return
    }
    loading.value = true
    try {
      groups.value = (await call('lcs_integrations.global_search.api.global_search', { txt: q })) || []
      active.value = flat.value[0]?.key || null
    } catch (e) {
      groups.value = []
    } finally {
      loading.value = false
    }
  },
  { debounce: 250 },
)

const flat = computed(() =>
  groups.value.flatMap((g) =>
    g.results.map((r) => ({ key: `${g.doctype}::${r.name}`, doctype: g.doctype, ...r })),
  ),
)

function isActive(dt, name) {
  return active.value === `${dt}::${name}`
}
function setActive(dt, name) {
  active.value = `${dt}::${name}`
}
function move(dir) {
  if (!flat.value.length) return
  const idx = flat.value.findIndex((r) => r.key === active.value)
  const next = (idx + dir + flat.value.length) % flat.value.length
  active.value = flat.value[next].key
}
function openActive() {
  const hit = flat.value.find((r) => r.key === active.value)
  if (hit) open(hit.doctype, hit)
}
function open(doctype, r) {
  const to = ROUTES[doctype]?.(r.name)
  if (!to) return
  show.value = false
  router.push(to)
}
</script>
