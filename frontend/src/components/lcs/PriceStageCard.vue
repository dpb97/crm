<!--
  PriceStageCard — editable currency card for a pricing stage.
  Shows the value prominently, allows click-to-edit with save/cancel.
-->

<template>
  <div
    class="relative rounded-xl border p-4 transition"
    :class="cardClasses"
  >
    <div class="flex items-start justify-between">
      <div class="flex items-center gap-1.5">
        <FeatherIcon v-if="icon" :name="icon" class="h-3.5 w-3.5" :class="iconClass" />
        <div>
          <div class="text-[10px] font-bold uppercase tracking-wider" :class="labelClass">{{ label }}</div>
          <div v-if="sublabel" class="text-[10px] font-normal normal-case" :class="sublabelClass">{{ sublabel }}</div>
        </div>
      </div>
      <button
        v-if="editable && !editing"
        class="opacity-0 transition group-hover:opacity-100"
        :class="iconClass"
        @click="startEdit"
        :aria-label="__('Edit')"
      >
        <FeatherIcon name="edit-2" class="h-3.5 w-3.5" />
      </button>
    </div>

    <!-- Display mode -->
    <div v-if="!editing" @click="editable && startEdit()" :class="{ 'cursor-pointer': editable }" class="group">
      <div class="mt-2 text-xl font-bold tabular-nums" :class="valueClass">
        {{ value ? formatCurrency(value) : '—' }}
      </div>
    </div>

    <!-- Edit mode -->
    <div v-else class="mt-2 space-y-2">
      <div class="flex items-center gap-1">
        <span class="text-sm text-gray-400">{{ currency }}</span>
        <input
          ref="inputEl"
          v-model.number="editValue"
          type="number"
          min="0"
          step="1000"
          class="w-full rounded-md border border-gray-300 px-2 py-1 text-base font-bold tabular-nums focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
          :placeholder="__('e.g. 450000')"
          @keydown.enter="save"
          @keydown.escape="cancel"
        />
      </div>
      <div class="flex gap-1">
        <button
          class="flex-1 rounded-md bg-lcs-primary px-2 py-1 text-xs font-semibold text-white hover:bg-lcs-secondary"
          @click="save"
        >
          {{ __('Save') }}
        </button>
        <button
          class="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
          @click="cancel"
        >
          {{ __('Cancel') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  label: { type: String, required: true },
  sublabel: { type: String, default: '' },
  value: { type: Number, default: null },
  color: { type: String, default: 'gray' },
  icon: { type: String, default: '' },
  editable: { type: Boolean, default: false },
  currency: { type: String, default: 'EUR' },
})

const emit = defineEmits(['save'])

const editing = ref(false)
const editValue = ref(null)
const inputEl = ref(null)

// Color variants — aligned with hero bar
const cardClasses = computed(() => {
  const variants = {
    gray: 'border-gray-200 bg-white hover:border-gray-300',
    blue: 'border-blue-200 bg-blue-50/60 hover:border-blue-300',
    green: props.value ? 'border-green-300 bg-green-50/60 hover:border-green-400' : 'border-gray-200 bg-white hover:border-gray-300',
  }
  return (variants[props.color] || variants.gray) + ' group'
})

const labelClass = computed(() => {
  const variants = { gray: 'text-gray-500', blue: 'text-blue-700', green: props.value ? 'text-green-700' : 'text-gray-500' }
  return variants[props.color] || variants.gray
})

const sublabelClass = computed(() => {
  const variants = { gray: 'text-gray-400', blue: 'text-blue-500/70', green: props.value ? 'text-green-600' : 'text-gray-400' }
  return variants[props.color] || variants.gray
})

const valueClass = computed(() => {
  if (!props.value) return 'text-gray-300'
  const variants = { gray: 'text-gray-900', blue: 'text-blue-900', green: 'text-green-800' }
  return variants[props.color] || variants.gray
})

const iconClass = computed(() => {
  const variants = { gray: 'text-gray-400', blue: 'text-blue-500', green: props.value ? 'text-green-600' : 'text-gray-400' }
  return variants[props.color] || variants.gray
})

function startEdit() {
  editValue.value = props.value || null
  editing.value = true
  nextTick(() => inputEl.value?.focus())
}

function save() {
  const val = editValue.value === '' || editValue.value == null ? null : Number(editValue.value)
  emit('save', val)
  editing.value = false
}

function cancel() {
  editing.value = false
}

function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: props.currency || 'EUR', maximumFractionDigits: 0 }).format(val)
}
</script>
