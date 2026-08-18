<!--
  LcsPhoneInput — a simple phone field: a country dial-code dropdown + a plain
  number input. Replaces the CRM multi-value phone control for mobile_no in the
  contact side panel. Stores the combined E.164 value (e.g. +43664123456).
-->
<template>
  <div class="flex items-center gap-1.5">
    <select v-model="code" class="lcs-phone-code" @change="emitVal">
      <option v-for="c in CODES" :key="c.iso" :value="c.dial">{{ c.flag }} {{ c.dial }}</option>
    </select>
    <input
      v-model="num"
      type="tel"
      class="lcs-phone-num"
      :placeholder="__('Number')"
      @input="emitVal"
      @blur="emitVal"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue', 'change'])

// A pragmatic set of dial codes (Austria first as the default market).
const CODES = [
  { iso: 'AT', dial: '+43', flag: '🇦🇹' },
  { iso: 'DE', dial: '+49', flag: '🇩🇪' },
  { iso: 'CH', dial: '+41', flag: '🇨🇭' },
  { iso: 'IT', dial: '+39', flag: '🇮🇹' },
  { iso: 'FR', dial: '+33', flag: '🇫🇷' },
  { iso: 'GB', dial: '+44', flag: '🇬🇧' },
  { iso: 'US', dial: '+1', flag: '🇺🇸' },
  { iso: 'ES', dial: '+34', flag: '🇪🇸' },
  { iso: 'NL', dial: '+31', flag: '🇳🇱' },
  { iso: 'BE', dial: '+32', flag: '🇧🇪' },
  { iso: 'PL', dial: '+48', flag: '🇵🇱' },
  { iso: 'CZ', dial: '+420', flag: '🇨🇿' },
  { iso: 'SI', dial: '+386', flag: '🇸🇮' },
  { iso: 'HR', dial: '+385', flag: '🇭🇷' },
  { iso: 'AU', dial: '+61', flag: '🇦🇺' },
  { iso: 'QA', dial: '+974', flag: '🇶🇦' },
  { iso: 'SA', dial: '+966', flag: '🇸🇦' },
  { iso: 'BR', dial: '+55', flag: '🇧🇷' },
  { iso: 'AR', dial: '+54', flag: '🇦🇷' },
  { iso: 'CL', dial: '+56', flag: '🇨🇱' },
  { iso: 'CO', dial: '+57', flag: '🇨🇴' },
  { iso: 'IN', dial: '+91', flag: '🇮🇳' },
  { iso: 'NP', dial: '+977', flag: '🇳🇵' },
  { iso: 'JP', dial: '+81', flag: '🇯🇵' },
  { iso: 'NZ', dial: '+64', flag: '🇳🇿' },
  { iso: 'PG', dial: '+675', flag: '🇵🇬' },
  { iso: 'CA', dial: '+1', flag: '🇨🇦' },
]

const code = ref('+43')
const num = ref('')

function parse(v) {
  v = String(v || '').trim()
  if (!v) { num.value = ''; return }
  // longest dial code first, so +43 doesn't shadow +420 etc.
  const hit = [...CODES].sort((a, b) => b.dial.length - a.dial.length).find((c) => v.startsWith(c.dial))
  if (hit) { code.value = hit.dial; num.value = v.slice(hit.dial.length).replace(/^[\s-]+/, '') }
  else { num.value = v }  // unknown/no prefix — keep as typed
}
parse(props.modelValue)
watch(() => props.modelValue, (v) => parse(v))

function emitVal() {
  const digits = String(num.value || '').replace(/[^\d]/g, '')
  const val = digits ? code.value + digits : ''
  emit('update:modelValue', val)
  emit('change', val)
}
</script>

<style scoped>
.lcs-phone-code {
  appearance: none; font-family: inherit; font-size: 14px;
  padding: 4px 6px; border-radius: var(--pp-radius-ui, 6px);
  border: 1px solid var(--pp-border-subtle, #e5e7eb);
  background: var(--pp-bg-base, #f3f4f6); color: var(--pp-text-primary, #111827);
}
.lcs-phone-num {
  flex: 1; min-width: 0; appearance: none; font-family: inherit; font-size: 14px;
  padding: 4px 8px; border-radius: var(--pp-radius-ui, 6px);
  border: 1px solid var(--pp-border-subtle, #e5e7eb);
  background: var(--pp-bg-base, #f3f4f6); color: var(--pp-text-primary, #111827);
  outline: none;
}
.lcs-phone-num:focus, .lcs-phone-code:focus { border-color: var(--pp-brand-primary, #008b8b); }
</style>
