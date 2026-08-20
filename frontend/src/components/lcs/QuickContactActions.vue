<!--
  QuickContactActions
  ===================
  Call / Mail / WhatsApp App / WhatsApp Web quick links for a contact. Each action is
  disabled (greyed, non-clickable) when its underlying field is empty.
  Shared by the contact page and the project inspector.
-->

<template>
  <div class="flex flex-col gap-2">
    <!-- With both a mobile and a landline, a tab picks which number ALL the
         phone actions (Call · SMS · WhatsApp) target. Only shown when both exist. -->
    <div v-if="mobileNo && landlineNo" class="inline-flex self-start rounded-md border border-gray-200 p-0.5 text-xs">
      <button
        type="button"
        class="flex items-center gap-1 rounded px-2.5 py-1 font-medium transition"
        :class="activeNum === 'mobile' ? 'bg-lcs-secondary text-white' : 'text-gray-600 hover:text-lcs-secondary'"
        @click="activeNum = 'mobile'"
      >
        <FeatherIcon name="smartphone" class="h-3.5 w-3.5" /> {{ __('Mobile') }}
      </button>
      <button
        type="button"
        class="flex items-center gap-1 rounded px-2.5 py-1 font-medium transition"
        :class="activeNum === 'landline' ? 'bg-lcs-secondary text-white' : 'text-gray-600 hover:text-lcs-secondary'"
        @click="activeNum = 'landline'"
      >
        <FeatherIcon name="phone" class="h-3.5 w-3.5" /> {{ __('Landline') }}
      </button>
    </div>

    <!-- Only actionable links are rendered (no greyed-out empty boxes).
         Order = Call · SMS · WhatsApp · Teams · Mail. Phone actions use the
         number selected by the tab above (mobile when there is only one). -->
    <div class="flex flex-wrap gap-2">
      <a v-if="activePhone" :href="'callto:' + telNumber(activePhone)" :class="actionCls">
        <FeatherIcon name="phone" class="h-4 w-4" /> {{ __('Call') }}
      </a>
      <a v-if="activePhone" :href="'sms:' + telNumber(activePhone)" :class="actionCls">
        <FeatherIcon name="message-square" class="h-4 w-4" /> SMS
      </a>
      <!-- wa.me opens the installed WhatsApp app (mobile app / desktop client). -->
      <a v-if="activePhone" :href="`https://wa.me/${waNumber(activePhone)}`" target="_blank" rel="noopener" :class="actionCls">
        <FeatherIcon name="message-circle" class="h-4 w-4" /> WhatsApp
      </a>
      <!-- Teams chat deep link by e-mail (opens a Teams chat, not a call). -->
      <a v-if="email" :href="teamsLink(email)" target="_blank" rel="noopener" :class="actionCls">
        <FeatherIcon name="message-square" class="h-4 w-4" /> Teams
      </a>
      <a v-if="email" :href="`mailto:${email}`" :class="actionCls">
        <FeatherIcon name="mail" class="h-4 w-4" /> {{ __('Mail') }}
      </a>
      <!-- web.whatsapp.com opens WhatsApp Web in the browser — desktop only; on the
           phone the native WhatsApp app link above already covers it. -->
      <a v-if="activePhone && !isMobile" :href="waWebLink(activePhone)" target="_blank" rel="noopener" :class="actionCls">
        <FeatherIcon name="message-circle" class="h-4 w-4" /> WhatsApp Web
      </a>
      <span v-if="!activePhone && !email" class="px-1 py-2 text-xs text-gray-400">{{ __('No contact details yet') }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { useViewport } from '@/composables/useViewport'

const { isMobile } = useViewport()

const props = defineProps({
  email: { type: String, default: '' },
  // Mobile number → Call/SMS/WhatsApp. `phone` is a backwards-compatible alias.
  mobile: { type: String, default: '' },
  phone: { type: String, default: '' },
  // Landline → its own Call button (no SMS/WhatsApp).
  landline: { type: String, default: '' },
  // 4 = two-up on mobile, four-up on >=sm; otherwise always two-up.
  cols: { type: Number, default: 2 },
})

const mobileNo = computed(() => props.mobile || props.phone || '')
const landlineNo = computed(() => props.landline || '')

// The number the phone actions target. Follows the tab when both exist; falls
// back to whichever single number is present.
const activeNum = ref('mobile')
const activePhone = computed(() => {
  if (activeNum.value === 'landline' && landlineNo.value) return landlineNo.value
  if (activeNum.value === 'mobile' && mobileNo.value) return mobileNo.value
  return mobileNo.value || landlineNo.value
})

// callto: wants a clean number — keep digits and a single leading '+'.
function telNumber(p) {
  const n = String(p).replace(/[^\d+]/g, '')
  return n.startsWith('+') ? '+' + n.slice(1).replace(/\+/g, '') : n
}

// wa.me wants the country code without '+' and without leading zeros. Strip the
// '+' and a leading international '00' prefix. A purely national number (single
// leading 0, no country code) cannot be resolved reliably and is passed through.
function waNumber(p) {
  let n = String(p).replace(/[^\d+]/g, '')
  if (n.startsWith('+')) n = n.slice(1)
  else if (n.startsWith('00')) n = n.slice(2)
  return n.replace(/\D/g, '')
}
// WhatsApp Web deep link — opens web.whatsapp.com with the number prefilled.
function waWebLink(p) {
  return `https://web.whatsapp.com/send/?phone=${waNumber(p)}&text&type=phone_number&app_absent=0`
}
// Teams deep link — opens a Teams CHAT with the person by e-mail address
// (was l/call → started a call; l/chat opens the chat window instead).
function teamsLink(mail) {
  return `https://teams.microsoft.com/l/chat/0/0?users=${encodeURIComponent(mail)}`
}
const actionCls =
  'flex min-h-[40px] flex-1 basis-[calc(50%-0.25rem)] min-w-[110px] items-center justify-center gap-1.5 rounded-md border border-gray-200 px-2.5 py-2 text-xs font-medium text-gray-700 transition hover:border-lcs-secondary hover:text-lcs-secondary'
</script>
