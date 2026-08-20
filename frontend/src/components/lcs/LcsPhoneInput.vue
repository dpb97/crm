<!--
  LcsPhoneInput — a simple phone field for a Contact: a searchable country
  dial-code picker (flag + name + dial) plus a plain number input. Stores the
  combined value (e.g. +43664123456).

  IMPORTANT: `Contact.mobile_no` is read-only and derived from the `phone_nos`
  child table on validate, so it cannot be written directly (a direct save is
  silently discarded → "number gone after saving"). This control therefore
  persists via lcs_integrations.contacts.api.set_primary_phone (upserts the
  primary Contact Phone) and asks the page to reload with `saved`. If no
  `contact` is given it falls back to plain v-model/change emits.
-->
<template>
  <div ref="root" class="lcs-phone">
    <button
      type="button"
      class="lcs-phone-code"
      :disabled="saving"
      @click="toggle"
    >
      <span class="lcs-phone-flag">{{ current.flag }}</span>
      <span class="lcs-phone-dial">{{ code }}</span>
      <FeatherIcon name="chevron-down" class="lcs-phone-caret" />
    </button>

    <input
      v-model="num"
      type="tel"
      class="lcs-phone-num"
      :placeholder="__('Number')"
      :disabled="saving"
      @input="emitInput"
      @blur="commit"
    />

    <!-- Searchable country menu -->
    <div v-if="open" class="lcs-phone-menu">
      <input
        ref="searchEl"
        v-model="search"
        type="search"
        class="lcs-phone-search"
        :placeholder="__('Search country') + ' …'"
        @keydown.enter.prevent="filtered[0] && pick(filtered[0])"
      />
      <ul class="lcs-phone-list">
        <li
          v-for="c in filtered"
          :key="c.iso"
          class="lcs-phone-item"
          :class="{ 'is-active': c.dial === code }"
          @click="pick(c)"
        >
          <span class="lcs-phone-flag">{{ c.flag }}</span>
          <span class="lcs-phone-name">{{ c.name }}</span>
          <span class="lcs-phone-item-dial">{{ c.dial }}</span>
        </li>
        <li v-if="!filtered.length" class="lcs-phone-empty">{{ __('No match') }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { FeatherIcon, call, toast } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: String, default: '' },
  // Contact name — when set, the control saves itself into phone_nos.
  contact: { type: String, default: '' },
  // Which primary number this field edits: "mobile" (mobile_no) or "phone" (landline).
  kind: { type: String, default: 'mobile' },
})
const emit = defineEmits(['update:modelValue', 'change', 'saved'])

// name is used for the search; dial + flag for display. Austria first (home market).
const CODES = [
  { iso: 'AT', dial: '+43', flag: '🇦🇹', name: 'Österreich' },
  { iso: 'DE', dial: '+49', flag: '🇩🇪', name: 'Deutschland' },
  { iso: 'CH', dial: '+41', flag: '🇨🇭', name: 'Schweiz' },
  { iso: 'IT', dial: '+39', flag: '🇮🇹', name: 'Italien' },
  { iso: 'FR', dial: '+33', flag: '🇫🇷', name: 'Frankreich' },
  { iso: 'GB', dial: '+44', flag: '🇬🇧', name: 'Vereinigtes Königreich' },
  { iso: 'IE', dial: '+353', flag: '🇮🇪', name: 'Irland' },
  { iso: 'US', dial: '+1', flag: '🇺🇸', name: 'USA' },
  { iso: 'CA', dial: '+1', flag: '🇨🇦', name: 'Kanada' },
  { iso: 'ES', dial: '+34', flag: '🇪🇸', name: 'Spanien' },
  { iso: 'PT', dial: '+351', flag: '🇵🇹', name: 'Portugal' },
  { iso: 'NL', dial: '+31', flag: '🇳🇱', name: 'Niederlande' },
  { iso: 'BE', dial: '+32', flag: '🇧🇪', name: 'Belgien' },
  { iso: 'LU', dial: '+352', flag: '🇱🇺', name: 'Luxemburg' },
  { iso: 'DK', dial: '+45', flag: '🇩🇰', name: 'Dänemark' },
  { iso: 'SE', dial: '+46', flag: '🇸🇪', name: 'Schweden' },
  { iso: 'NO', dial: '+47', flag: '🇳🇴', name: 'Norwegen' },
  { iso: 'FI', dial: '+358', flag: '🇫🇮', name: 'Finnland' },
  { iso: 'PL', dial: '+48', flag: '🇵🇱', name: 'Polen' },
  { iso: 'CZ', dial: '+420', flag: '🇨🇿', name: 'Tschechien' },
  { iso: 'SK', dial: '+421', flag: '🇸🇰', name: 'Slowakei' },
  { iso: 'HU', dial: '+36', flag: '🇭🇺', name: 'Ungarn' },
  { iso: 'SI', dial: '+386', flag: '🇸🇮', name: 'Slowenien' },
  { iso: 'HR', dial: '+385', flag: '🇭🇷', name: 'Kroatien' },
  { iso: 'RS', dial: '+381', flag: '🇷🇸', name: 'Serbien' },
  { iso: 'RO', dial: '+40', flag: '🇷🇴', name: 'Rumänien' },
  { iso: 'BG', dial: '+359', flag: '🇧🇬', name: 'Bulgarien' },
  { iso: 'GR', dial: '+30', flag: '🇬🇷', name: 'Griechenland' },
  { iso: 'TR', dial: '+90', flag: '🇹🇷', name: 'Türkei' },
  { iso: 'RU', dial: '+7', flag: '🇷🇺', name: 'Russland' },
  { iso: 'UA', dial: '+380', flag: '🇺🇦', name: 'Ukraine' },
  { iso: 'QA', dial: '+974', flag: '🇶🇦', name: 'Katar' },
  { iso: 'SA', dial: '+966', flag: '🇸🇦', name: 'Saudi-Arabien' },
  { iso: 'AE', dial: '+971', flag: '🇦🇪', name: 'VAE' },
  { iso: 'IL', dial: '+972', flag: '🇮🇱', name: 'Israel' },
  { iso: 'IN', dial: '+91', flag: '🇮🇳', name: 'Indien' },
  { iso: 'NP', dial: '+977', flag: '🇳🇵', name: 'Nepal' },
  { iso: 'CN', dial: '+86', flag: '🇨🇳', name: 'China' },
  { iso: 'JP', dial: '+81', flag: '🇯🇵', name: 'Japan' },
  { iso: 'AU', dial: '+61', flag: '🇦🇺', name: 'Australien' },
  { iso: 'NZ', dial: '+64', flag: '🇳🇿', name: 'Neuseeland' },
  { iso: 'PG', dial: '+675', flag: '🇵🇬', name: 'Papua-Neuguinea' },
  { iso: 'BR', dial: '+55', flag: '🇧🇷', name: 'Brasilien' },
  { iso: 'AR', dial: '+54', flag: '🇦🇷', name: 'Argentinien' },
  { iso: 'CL', dial: '+56', flag: '🇨🇱', name: 'Chile' },
  { iso: 'CO', dial: '+57', flag: '🇨🇴', name: 'Kolumbien' },
  { iso: 'ZA', dial: '+27', flag: '🇿🇦', name: 'Südafrika' },
]

const root = ref(null)
const searchEl = ref(null)
const code = ref('+43')
const num = ref('')
const open = ref(false)
const search = ref('')
const saving = ref(false)

// The value we last read from / wrote to the doc — so we never fire a redundant
// save when nothing actually changed (blur after no edit, external reload, …).
let committed = ''

const current = computed(() => CODES.find((c) => c.dial === code.value) || { flag: '🏳️', dial: code.value })

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return CODES
  return CODES.filter((c) => c.name.toLowerCase().includes(q) || c.dial.includes(q) || c.iso.toLowerCase() === q)
})

function currentVal() {
  const digits = String(num.value || '').replace(/[^\d]/g, '')
  return digits ? code.value + digits : ''
}

function parse(v) {
  v = String(v || '').trim()
  committed = ''
  if (!v) { num.value = ''; committed = ''; return }
  // longest dial code first so +43 doesn't shadow +420 etc.
  const hit = [...CODES].sort((a, b) => b.dial.length - a.dial.length).find((c) => v.startsWith(c.dial))
  if (hit) { code.value = hit.dial; num.value = v.slice(hit.dial.length).replace(/^[\s-]+/, '') }
  else { num.value = v }
  committed = currentVal()
}
parse(props.modelValue)
watch(() => props.modelValue, (v) => parse(v))

// Keystrokes only update the live model — no save (avoids one save per digit).
function emitInput() { emit('update:modelValue', currentVal()) }

// Commit = persist. On a Contact this writes into phone_nos (mobile_no is
// read-only/derived) and asks the page to reload; otherwise plain emits.
async function commit() {
  const val = currentVal()
  if (val === committed) return
  committed = val
  if (!props.contact) {
    emit('update:modelValue', val)
    emit('change', val)
    return
  }
  saving.value = true
  try {
    await call('lcs_integrations.contacts.api.set_primary_phone', { contact: props.contact, value: val, kind: props.kind })
    emit('saved')
  } catch (err) {
    committed = '' // let the next blur retry
    toast.error(err?.messages?.[0] || err?.message || __('Could not save the number.'))
  } finally {
    saving.value = false
  }
}

function toggle() {
  open.value = !open.value
  if (open.value) { search.value = ''; nextTick(() => searchEl.value?.focus()) }
}
function pick(c) {
  code.value = c.dial
  open.value = false
  if (num.value.trim()) commit() // a dial change with a number entered commits
}

function onDocPointer(e) { if (open.value && root.value && !root.value.contains(e.target)) open.value = false }
onMounted(() => document.addEventListener('mousedown', onDocPointer))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocPointer))
</script>

<style scoped>
.lcs-phone { position: relative; display: flex; align-items: center; gap: 6px; }
.lcs-phone-code {
  appearance: none; cursor: pointer; font-family: inherit; font-size: 14px;
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 6px; border-radius: var(--pp-radius-ui, 6px);
  border: 1px solid var(--pp-border-subtle, #e5e7eb);
  background: var(--pp-bg-base, #f3f4f6); color: var(--pp-text-primary, #111827);
}
.lcs-phone-code:disabled { opacity: 0.6; cursor: wait; }
.lcs-phone-flag { font-size: 16px; line-height: 1; }
.lcs-phone-dial { font-variant-numeric: tabular-nums; }
.lcs-phone-caret { width: 13px; height: 13px; color: var(--pp-text-tertiary, #6b7280); }
.lcs-phone-num {
  flex: 1; min-width: 0; appearance: none; font-family: inherit; font-size: 14px;
  padding: 4px 8px; border-radius: var(--pp-radius-ui, 6px);
  border: 1px solid var(--pp-border-subtle, #e5e7eb);
  background: var(--pp-bg-base, #f3f4f6); color: var(--pp-text-primary, #111827); outline: none;
}
.lcs-phone-num:focus, .lcs-phone-code:focus { border-color: var(--pp-brand-primary, #008b8b); }

/* Searchable country menu */
.lcs-phone-menu {
  position: absolute; top: calc(100% + 4px); left: 0; z-index: 50;
  width: 260px; max-width: 80vw; display: flex; flex-direction: column;
  background: var(--pp-bg-surface, #fff); border: 1px solid var(--pp-border-default, #d1d5db);
  border-radius: var(--pp-radius-ui, 6px); box-shadow: var(--pp-shadow-xl, 0 12px 32px rgb(0 0 0 / 0.18));
  overflow: hidden;
}
.lcs-phone-search {
  appearance: none; font-family: inherit; font-size: 13px; margin: 6px;
  padding: 6px 8px; border: 1px solid var(--pp-border-default, #d1d5db);
  border-radius: var(--pp-radius-ui, 6px); background: var(--pp-bg-base, #f3f4f6);
  color: var(--pp-text-primary, #111827); outline: none;
}
.lcs-phone-search:focus { border-color: var(--pp-brand-primary, #008b8b); }
.lcs-phone-list { list-style: none; margin: 0; padding: 0 0 4px; max-height: 240px; overflow-y: auto; }
.lcs-phone-item {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  padding: 7px 10px; font-size: 13px; color: var(--pp-text-primary, #111827);
}
.lcs-phone-item:hover { background: var(--pp-bg-hover, #f3f4f6); }
.lcs-phone-item.is-active { background: var(--pp-accent-soft, #e6f6f6); font-weight: var(--pp-weight-semibold, 600); }
.lcs-phone-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lcs-phone-item-dial { color: var(--pp-text-tertiary, #6b7280); font-variant-numeric: tabular-nums; }
.lcs-phone-empty { padding: 10px; font-size: 13px; color: var(--pp-text-tertiary, #6b7280); text-align: center; }
</style>
