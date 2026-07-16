<!--
  LCSThemeToggle — three-way segmented control for Light / Dark / System.

  Persists the choice in localStorage (key 'theme') and updates the
  <html data-theme="..."> attribute, which:
    - drives Tailwind's [data-theme="dark"] dark variants
    - swaps every CSS variable defined under html[data-theme="dark"]
      in index.css so all `lcs-*` colour tokens flip in lockstep

  Reuses the same storage key frappe-ui's useTheme() composable
  already manages, so the LCS toggle and Frappe's built-in theme
  picker stay synchronised.
-->

<template>
  <div class="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white p-0.5 text-xs">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="inline-flex items-center gap-1 rounded-full px-2 py-1 transition"
      :class="active === opt.value
        ? 'bg-lcs-primary text-white shadow-sm'
        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'"
      :aria-pressed="active === opt.value"
      :title="opt.tooltip"
      @click="setTheme(opt.value)"
    >
      <FeatherIcon :name="opt.icon" class="h-3 w-3" />
      <span class="hidden sm:inline">{{ opt.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const STORAGE_KEY = 'theme'

const options = [
  { value: 'light',  label: __('Light'),  icon: 'sun',     tooltip: __('Always light') },
  { value: 'dark',   label: __('Dark'),   icon: 'moon',    tooltip: __('Always dark') },
  { value: 'system', label: __('System'), icon: 'monitor', tooltip: __('Follow OS preference') },
]

const stored = ref(localStorage.getItem(STORAGE_KEY) || 'system')
const systemPrefersDark = ref(false)

const active = computed(() => stored.value)

const effective = computed(() => {
  if (stored.value === 'system') {
    return systemPrefersDark.value ? 'dark' : 'light'
  }
  return stored.value
})

function apply() {
  document.documentElement.setAttribute('data-theme', effective.value)
}

function setTheme(value) {
  stored.value = value
  localStorage.setItem(STORAGE_KEY, value)
  apply()
}

let mq = null
function onSystemChange(e) {
  systemPrefersDark.value = e.matches
  if (stored.value === 'system') apply()
}

onMounted(() => {
  mq = window.matchMedia('(prefers-color-scheme: dark)')
  systemPrefersDark.value = mq.matches
  mq.addEventListener('change', onSystemChange)
  apply()
})

onUnmounted(() => {
  if (mq) mq.removeEventListener('change', onSystemChange)
})
</script>
