<template>
  <div class="relative" ref="rootEl">
    <Tooltip :text="__('Choose columns — saved to your user profile')">
      <Button variant="ghost" iconLeft="columns" :label="__('Columns')" @click="open = !open" />
    </Tooltip>

    <div
      v-if="open"
      class="absolute right-0 z-30 mt-1 w-64 rounded-md border border-gray-200 bg-white p-2 shadow-lg"
    >
      <div class="mb-1 px-2 pt-1 text-xs font-semibold uppercase tracking-wide text-gray-400">
        {{ __('Visible columns') }}
      </div>
      <div
        v-for="col in catalog"
        :key="col.key"
        class="group flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-gray-50"
        :class="{ 'opacity-50': dragKey === col.key, 'bg-lcs-primary/5 ring-1 ring-lcs-primary/30': dragOverKey === col.key }"
        draggable="true"
        @dragstart="onDragStart(col.key)"
        @dragover.prevent="dragOverKey = col.key"
        @drop.prevent="onDrop(col.key)"
        @dragend="dragKey = null; dragOverKey = null"
      >
        <span class="cursor-grab select-none text-gray-300 group-hover:text-gray-400" :title="__('Drag to reorder')" aria-hidden="true">⋮⋮</span>
        <label class="flex flex-1 cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            class="rounded border-gray-300 text-lcs-primary focus:ring-lcs-primary"
            :checked="modelValue.includes(col.key)"
            :disabled="modelValue.length === 1 && modelValue.includes(col.key)"
            @change="toggle(col.key)"
          />
          <span class="text-gray-700">{{ col.label }}</span>
        </label>
      </div>
      <div class="mt-2 flex items-center justify-between border-t pt-2">
        <Button variant="ghost" :label="__('Reset')" @click="reset" class="text-gray-500" />
        <span v-if="saving" class="px-2 text-xs text-gray-400">{{ __('Saving…') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ColumnPicker — reusable per-user column selection for LCS list pages.
 *
 * Selection is persisted server-side in `LCS User Preferences.list_columns`
 * (JSON keyed by tableKey), so it follows the user across devices — the
 * same guarantee the core CRM lists get from CRM View Settings.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { Button, Tooltip } from 'frappe-ui'
import { useUserPreferences } from '@/composables/useUserPreferences'

const props = defineProps({
  tableKey: { type: String, required: true },
  catalog: { type: Array, required: true }, // [{ key, label }]
  modelValue: { type: Array, required: true }, // selected keys
  defaults: { type: Array, required: true },
})
const emit = defineEmits(['update:modelValue', 'reorder'])

const open = ref(false)
const saving = ref(false)
const rootEl = ref(null)
const userPrefs = useUserPreferences()

// Drag-and-drop reordering of the column list. Emits the new full key order
// (all catalog keys); the page persists it and derives the on-screen order.
const dragKey = ref(null)
const dragOverKey = ref(null)
function onDragStart(key) { dragKey.value = key }
function onDrop(targetKey) {
  const from = dragKey.value
  dragKey.value = null
  dragOverKey.value = null
  if (!from || from === targetKey) return
  const keys = props.catalog.map((c) => c.key)
  const fi = keys.indexOf(from)
  const ti = keys.indexOf(targetKey)
  if (fi >= 0 && ti >= 0) {
    keys.splice(ti, 0, keys.splice(fi, 1)[0])
    emit('reorder', keys)
  }
}

function toggle(key) {
  const next = props.modelValue.includes(key)
    ? props.modelValue.filter((k) => k !== key)
    : // keep catalog order when re-adding
      props.catalog.map((c) => c.key).filter(
        (k) => props.modelValue.includes(k) || k === key,
      )
  apply(next)
}

function reset() {
  apply([...props.defaults])
}

async function apply(next) {
  emit('update:modelValue', next)
  saving.value = true
  try {
    await userPrefs.saveListColumns(props.tableKey, next)
  } finally {
    saving.value = false
  }
}

function onClickOutside(e) {
  if (open.value && rootEl.value && !rootEl.value.contains(e.target)) {
    open.value = false
  }
}
onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>
