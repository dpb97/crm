<!--
  ConflictResolver — three-way merge dialog for offline sync conflicts.

  Shown when a queued mutation cannot be replayed because the server
  value of a field has changed since the mutation was queued. User
  picks per field: Keep Mine (local), Use Server, or type Custom.
-->

<template>
  <Dialog
    :model-value="!!mutation"
    @update:model-value="v => !v && $emit('close')"
    :options="{ title: __('Sync Conflict'), size: 'lg' }"
  >
    <template #body-content>
      <div v-if="mutation" class="space-y-4">
        <!-- Header explanation -->
        <div class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <div class="flex items-start gap-2">
            <FeatherIcon name="alert-triangle" class="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div class="font-semibold">{{ __('This record was changed by someone else while you were offline.') }}</div>
              <div class="mt-1 text-xs text-amber-700">
                {{ __('Pick how to resolve each conflicting field. "Mine" keeps your offline change. "Theirs" discards yours.') }}
              </div>
            </div>
          </div>
          <div class="mt-2 flex items-center gap-3 text-xs">
            <span class="font-mono text-amber-800">{{ mutation.doctype }} · {{ mutation.name }}</span>
            <span class="text-amber-600">{{ mutation.description }}</span>
          </div>
        </div>

        <!-- Per-field conflict rows -->
        <div class="space-y-3">
          <div
            v-for="(conflict, field) in mutation.conflicts"
            :key="field"
            class="rounded-xl border bg-white p-4"
          >
            <div class="mb-3 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="font-mono text-xs text-gray-500">{{ field }}</span>
                <span v-if="choices[field]" :class="choiceBadgeClass(choices[field])" class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase">
                  {{ __(choices[field]) }}
                </span>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <!-- Mine (local) -->
              <ConflictOption
                :label="__('Mine (offline)')"
                :value="conflict.local"
                :selected="choices[field] === 'local'"
                color="blue"
                icon="edit-3"
                @click="choices[field] = 'local'; customValues[field] = ''"
              />

              <!-- Theirs (server) -->
              <ConflictOption
                :label="__('Theirs (server)')"
                :value="conflict.server"
                :selected="choices[field] === 'server'"
                color="amber"
                icon="cloud"
                @click="choices[field] = 'server'; customValues[field] = ''"
              />

              <!-- Custom merge -->
              <div
                class="rounded-lg border-2 p-3 transition cursor-pointer"
                :class="choices[field] === 'custom' ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-purple-300 bg-gray-50'"
                @click="choices[field] = 'custom'"
              >
                <div class="mb-1.5 flex items-center gap-1 text-xs font-semibold text-purple-700">
                  <FeatherIcon name="git-merge" class="h-3 w-3" />
                  {{ __('Custom') }}
                </div>
                <input
                  v-if="choices[field] === 'custom'"
                  v-model="customValues[field]"
                  type="text"
                  class="w-full rounded-md border border-purple-300 bg-white px-2 py-1 text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                  :placeholder="__('Type custom value...')"
                  @click.stop
                />
                <div v-else class="text-xs italic text-gray-400">{{ __('Click to enter custom value') }}</div>
              </div>
            </div>

            <!-- Base value reference -->
            <div class="mt-2 rounded-md bg-gray-50 px-3 py-1.5 text-[11px] text-gray-500">
              <span class="font-semibold">{{ __('Was') }}:</span>
              <span class="ml-1 font-mono">{{ formatValue(conflict.base) }}</span>
              <span class="ml-2 text-gray-400">({{ __('value when you started editing') }})</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-between">
        <div class="flex gap-2">
          <Button variant="ghost" size="sm" @click="keepAllMine" :label="__('Keep all mine')" iconLeft="edit-3" />
          <Button variant="ghost" size="sm" @click="useAllServer" :label="__('Use all server')" iconLeft="cloud" />
        </div>
        <div class="flex gap-2">
          <Button variant="ghost" @click="$emit('close')" :label="__('Cancel')" />
          <Button
            variant="solid"
            @click="resolve"
            :disabled="!allResolved"
            :label="__('Apply Resolution')"
            iconLeft="check"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Dialog, Button, FeatherIcon, toast } from 'frappe-ui'
import { resolveConflict, discardMutation } from '@/utils/syncEngine'

// Inline "option" card component for DRY visual language
const ConflictOption = {
  props: ['label', 'value', 'selected', 'color', 'icon'],
  components: { FeatherIcon },
  template: `
    <div
      class="rounded-lg border-2 p-3 transition cursor-pointer"
      :class="wrapperClass"
      @click="$emit('click')"
    >
      <div class="mb-1.5 flex items-center gap-1 text-xs font-semibold" :class="labelClass">
        <FeatherIcon :name="icon" class="h-3 w-3" />
        {{ label }}
      </div>
      <div class="break-words text-sm font-medium" :class="valueClass">{{ formatted }}</div>
    </div>
  `,
  computed: {
    wrapperClass() {
      const selectedMap = { blue: 'border-blue-400 bg-blue-50', amber: 'border-amber-400 bg-amber-50' }
      const idleMap = { blue: 'border-gray-200 hover:border-blue-300 bg-white', amber: 'border-gray-200 hover:border-amber-300 bg-white' }
      return this.selected ? selectedMap[this.color] : idleMap[this.color]
    },
    labelClass() {
      const m = { blue: 'text-blue-700', amber: 'text-amber-700' }
      return m[this.color] || 'text-gray-600'
    },
    valueClass() {
      return this.value == null || this.value === '' ? 'italic text-gray-400' : 'text-gray-900'
    },
    formatted() {
      if (this.value == null || this.value === '') return __('(empty)')
      if (typeof this.value === 'boolean') return this.value ? '✓' : '✗'
      if (typeof this.value === 'object') return JSON.stringify(this.value)
      return String(this.value)
    },
  },
  emits: ['click'],
}

const props = defineProps({
  mutation: { type: Object, default: null },
})
const emit = defineEmits(['close'])

// Per-field choice: 'local' | 'server' | 'custom'
const choices = ref({})
const customValues = ref({})

// Reset when mutation changes
watch(() => props.mutation?.id, () => {
  choices.value = {}
  customValues.value = {}
  if (props.mutation?.conflicts) {
    // Default every field to 'local' (keep mine) — safe default
    for (const field of Object.keys(props.mutation.conflicts)) {
      choices.value[field] = 'local'
    }
  }
}, { immediate: true })

const allResolved = computed(() => {
  if (!props.mutation?.conflicts) return false
  for (const [field, choice] of Object.entries(choices.value)) {
    if (!choice) return false
    if (choice === 'custom' && !customValues.value[field]) return false
  }
  return Object.keys(props.mutation.conflicts).every(f => !!choices.value[f])
})

function choiceBadgeClass(choice) {
  const m = { local: 'bg-blue-100 text-blue-800', server: 'bg-amber-100 text-amber-800', custom: 'bg-purple-100 text-purple-800' }
  return m[choice] || 'bg-gray-100 text-gray-700'
}

function keepAllMine() {
  for (const field of Object.keys(props.mutation.conflicts)) {
    choices.value[field] = 'local'
  }
}

function useAllServer() {
  for (const field of Object.keys(props.mutation.conflicts)) {
    choices.value[field] = 'server'
  }
}

function formatValue(v) {
  if (v == null || v === '') return __('(empty)')
  if (typeof v === 'boolean') return v ? '✓' : '✗'
  return String(v)
}

async function resolve() {
  if (!allResolved.value) return
  const resolutions = {}
  for (const [field, choice] of Object.entries(choices.value)) {
    const conflict = props.mutation.conflicts[field]
    if (choice === 'local') resolutions[field] = conflict.local
    else if (choice === 'server') resolutions[field] = conflict.server
    else if (choice === 'custom') resolutions[field] = customValues.value[field]
  }
  try {
    await resolveConflict(props.mutation.id, resolutions)
    toast({ title: __('Conflict resolved'), icon: 'check-circle', iconClasses: 'text-green-500' })
    emit('close')
  } catch (err) {
    toast({ title: __('Resolution failed'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}
</script>
