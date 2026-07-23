<!--
  PhoneInput — international phone field with a country flag selector.
  ===================================================================
  Drop-in control for Data/Phone fields (wired in FieldLayout/Field.vue). Shows
  a real flag (flag-icons SVGs — emoji flags don't render on Windows) derived
  from the number's dialing prefix, plus a searchable country dropdown that
  prepends the dial code. The stored value stays a plain string incl. "+<dial>".

  props:  value, placeholder, disabled
  emits:  change (the full phone string)
-->
<template>
  <div ref="root" class="pi" :class="{ 'pi--disabled': disabled }">
    <!-- Country selector -->
    <button
      type="button"
      class="pi-country"
      :disabled="disabled"
      :title="current ? current.name + ' (+' + current.dial + ')' : __('Select country')"
      @click="toggle"
    >
      <span v-if="current" :class="['fi', 'fi-' + current.iso2.toLowerCase()]" class="pi-flag" />
      <IconGlobe v-else class="pi-globe" />
      <IconChevron class="pi-caret" />
    </button>

    <!-- Number -->
    <input
      ref="field"
      class="pi-input"
      type="tel"
      inputmode="tel"
      autocomplete="tel"
      :value="local"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="onInput"
      @blur="emitChange"
    />

    <!-- Dropdown -->
    <div v-if="open" class="pi-menu">
      <input
        ref="search"
        v-model="q"
        class="pi-search"
        :placeholder="__('Search country') + ' …'"
        @keydown.esc="close"
      />
      <ul class="pi-list">
        <li
          v-for="c in filtered"
          :key="c.iso2"
          class="pi-item"
          :class="{ 'is-active': current && current.iso2 === c.iso2 }"
          @click="pick(c)"
        >
          <span :class="['fi', 'fi-' + c.iso2.toLowerCase()]" class="pi-flag" />
          <span class="pi-name">{{ c.name }}</span>
          <span class="pi-dial">+{{ c.dial }}</span>
        </li>
        <li v-if="!filtered.length" class="pi-empty">{{ __('No match') }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import IconGlobe from '~icons/lucide/globe'
import IconChevron from '~icons/lucide/chevron-down'
import { COUNTRIES, detectCountry } from '@/utils/phoneCountry'
import 'flag-icons/css/flag-icons.min.css'

const props = defineProps({
  value: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

const local = ref(props.value || '')
const forcedIso = ref(null) // set when the user picks a country explicitly
watch(() => props.value, (v) => { if (v !== local.value) local.value = v || '' })

const current = computed(() => {
  const d = detectCountry(local.value)
  if (d) return d
  if (forcedIso.value) return COUNTRIES.find((c) => c.iso2 === forcedIso.value) || null
  return null
})

function onInput(e) {
  local.value = e.target.value
  forcedIso.value = null
  emit('change', local.value)
}
function emitChange() {
  emit('change', local.value)
}

// --- Dropdown ---
const open = ref(false)
const q = ref('')
const root = ref(null)
const field = ref(null)
const search = ref(null)
const filtered = computed(() => {
  const n = q.value.trim().toLowerCase()
  if (!n) return COUNTRIES
  return COUNTRIES.filter(
    (c) => c.name.toLowerCase().includes(n) || String(c.dial).includes(n) || c.iso2.toLowerCase().includes(n),
  )
})
function toggle() {
  if (props.disabled) return
  open.value = !open.value
  if (open.value) {
    q.value = ''
    nextTick(() => search.value && search.value.focus())
    document.addEventListener('mousedown', onDocClick)
  } else {
    document.removeEventListener('mousedown', onDocClick)
  }
}
function close() {
  open.value = false
  document.removeEventListener('mousedown', onDocClick)
}
function onDocClick(e) {
  if (root.value && !root.value.contains(e.target)) close()
}
function pick(c) {
  // Strip an existing "+<dial>" prefix, keep the national part, prepend the new dial.
  const cur = detectCountry(local.value)
  let national = local.value.trim()
  if (cur) national = national.replace(/^\+\s*/, '').replace(new RegExp('^' + cur.dial + '\\s*'), '')
  else national = national.replace(/^\+?\s*/, '')
  local.value = ('+' + c.dial + ' ' + national).trimEnd()
  forcedIso.value = c.iso2
  emit('change', local.value)
  close()
  nextTick(() => field.value && field.value.focus())
}
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick))
</script>

<style scoped>
.pi { position: relative; display: flex; align-items: stretch; width: 100%;
  border: 1px solid var(--pp-border-default, #d1d5db); border-radius: var(--pp-radius-ui, 6px);
  background: var(--pp-bg-surface, #fff); min-height: 28px; overflow: visible; }
.pi:focus-within { border-color: var(--pp-brand-primary, #008B8B);
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--pp-brand-primary, #008B8B) 20%, transparent); }
.pi--disabled { opacity: 0.6; }

.pi-country { display: inline-flex; align-items: center; gap: 4px; padding: 0 8px;
  border: none; border-right: 1px solid var(--pp-border-subtle, #e5e7eb); background: transparent;
  cursor: pointer; border-radius: var(--pp-radius-ui, 6px) 0 0 var(--pp-radius-ui, 6px); }
.pi-country:hover:not(:disabled) { background: var(--pp-bg-hover, #f3f4f6); }
.pi-flag { width: 20px; height: 15px; border-radius: 2px; box-shadow: 0 0 0 1px rgb(0 0 0 / 0.06); background-size: cover; }
.pi-globe { width: 16px; height: 16px; color: var(--pp-text-tertiary, #9ca3af); }
.pi-caret { width: 12px; height: 12px; color: var(--pp-text-tertiary, #9ca3af); }

.pi-input { flex: 1 1 auto; min-width: 0; border: none; outline: none; background: transparent;
  padding: 0 10px; font-family: inherit; font-size: var(--pp-fs-14, 14px); color: var(--pp-text-primary, #111827); }

.pi-menu { position: absolute; top: calc(100% + 4px); left: 0; z-index: 50; width: 280px; max-width: 90vw;
  background: var(--pp-bg-surface, #fff); border: 1px solid var(--pp-border-default, #d1d5db);
  border-radius: var(--pp-radius-ui, 6px); box-shadow: var(--pp-shadow-lg, 0 10px 30px rgb(0 0 0 / 0.15));
  padding: 6px; }
.pi-search { width: 100%; box-sizing: border-box; padding: 6px 8px; margin-bottom: 6px;
  border: 1px solid var(--pp-border-default, #d1d5db); border-radius: var(--pp-radius-ui, 6px);
  font-size: var(--pp-fs-13, 13px); outline: none; background: var(--pp-bg-base, #f9fafb); }
.pi-search:focus { border-color: var(--pp-brand-primary, #008B8B); }
.pi-list { list-style: none; margin: 0; padding: 0; max-height: 260px; overflow-y: auto; }
.pi-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; cursor: pointer;
  border-radius: var(--pp-radius-ui, 6px); font-size: var(--pp-fs-13, 13px); }
.pi-item:hover { background: var(--pp-bg-hover, #f3f4f6); }
.pi-item.is-active { background: color-mix(in oklab, var(--pp-brand-primary, #008B8B) 12%, transparent); }
.pi-name { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--pp-text-primary, #111827); }
.pi-dial { color: var(--pp-text-tertiary, #6b7280); font-variant-numeric: tabular-nums; }
.pi-empty { padding: 8px; color: var(--pp-text-tertiary, #9ca3af); font-size: var(--pp-fs-13, 13px); text-align: center; }
</style>
