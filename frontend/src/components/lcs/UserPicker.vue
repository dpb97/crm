<!--
  UserPicker — inline-editable Link→User field.

  Click the value to open a debounced search popover. Clear via the X.
  Emits `save` with the selected user id (or "" to clear).
-->

<template>
  <div class="relative inline-block">
    <button
      type="button"
      class="group inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-sm text-gray-800 transition hover:bg-gray-100"
      :class="value ? '' : 'text-gray-400 italic'"
      @click="open = !open"
    >
      <FeatherIcon v-if="value" name="user" class="h-3 w-3 text-gray-400" />
      <span>{{ displayName }}</span>
      <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-3 w-3 text-gray-300 group-hover:text-gray-500" />
    </button>

    <!-- Popover -->
    <Teleport to="body">
      <div
        v-if="open"
        class="fixed inset-0 z-40"
        @click="close"
      >
        <div
          class="absolute z-50 w-72 rounded-lg border bg-white shadow-xl"
          :style="popoverStyle"
          @click.stop
        >
          <div class="border-b p-2">
            <input
              ref="search"
              v-model="query"
              type="search"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
              :placeholder="__('Search user by name or email')"
              @input="onSearch"
            />
          </div>
          <div class="max-h-64 overflow-y-auto">
            <button
              v-if="value"
              class="flex w-full items-center gap-2 border-b px-3 py-2 text-left text-xs text-red-600 hover:bg-red-50"
              @click="pick('')"
            >
              <FeatherIcon name="x" class="h-3 w-3" />
              {{ __('Clear assignment') }}
            </button>
            <button
              v-for="u in results"
              :key="u.name"
              class="flex w-full items-center gap-2 border-b px-3 py-2 text-left hover:bg-gray-50"
              :class="{ 'bg-blue-50': u.name === value }"
              @click="pick(u.name)"
            >
              <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-lcs-primary/10 text-[10px] font-bold text-lcs-primary">
                {{ initials(u.full_name || u.name) }}
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium text-gray-900">{{ u.full_name || u.name }}</span>
                <span class="block truncate text-xs text-gray-500">{{ u.name }}</span>
              </span>
            </button>
            <div v-if="!results.length && query.length >= 2 && !searching" class="py-6 text-center text-xs text-gray-400">
              {{ __('No users match.') }}
            </div>
            <div v-if="searching" class="py-6 text-center">
              <div class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { FeatherIcon, call } from 'frappe-ui'

const props = defineProps({
  value: { type: String, default: '' },
  placeholder: { type: String, default: '—' },
})
const emit = defineEmits(['save'])

const open = ref(false)
const query = ref('')
const results = ref([])
const searching = ref(false)
const search = ref(null)
const popoverStyle = ref({ top: '0px', left: '0px' })

const displayName = computed(() => {
  if (props.value) {
    // If we have a cached full_name in results for this value, prefer it
    const match = results.value.find(u => u.name === props.value)
    return match?.full_name || props.value
  }
  return props.placeholder
})

function initials(name) {
  if (!name) return '?'
  return name.split(/\s+/).slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('')
}

watch(open, async (v) => {
  if (v) {
    await nextTick()
    _positionPopover()
    search.value?.focus()
    if (!results.value.length) await loadRecent()
  }
})

function _positionPopover() {
  // Position below the trigger button
  const btn = search.value?.closest('.relative') || document.activeElement
  // Fallback: center on viewport
  popoverStyle.value = {
    top: '120px',
    left: '50%',
    transform: 'translateX(-50%)',
  }
}

function close() {
  open.value = false
  query.value = ''
}

function pick(name) {
  emit('save', name)
  open.value = false
  query.value = ''
}

async function loadRecent() {
  searching.value = true
  try {
    const res = await call('frappe.client.get_list', {
      doctype: 'User',
      filters: { enabled: 1, user_type: 'System User' },
      fields: ['name', 'full_name'],
      order_by: 'modified desc',
      limit_page_length: 10,
    })
    results.value = res.message || res || []
  } catch (err) {
    console.warn('User loadRecent failed:', err)
    results.value = []
  } finally {
    searching.value = false
  }
}

let timer = null
function onSearch() {
  clearTimeout(timer)
  if (query.value.length < 2) {
    loadRecent()
    return
  }
  searching.value = true
  timer = setTimeout(async () => {
    try {
      const like = `%${query.value}%`
      const res = await call('frappe.client.get_list', {
        doctype: 'User',
        or_filters: { name: ['like', like], full_name: ['like', like] },
        filters: { enabled: 1, user_type: 'System User' },
        fields: ['name', 'full_name'],
        order_by: 'full_name asc',
        limit_page_length: 20,
      })
      results.value = res.message || res || []
    } catch (err) {
      console.warn('User search failed:', err)
      results.value = []
    } finally {
      searching.value = false
    }
  }, 250)
}
</script>
