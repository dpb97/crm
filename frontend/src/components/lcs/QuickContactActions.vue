<!--
  QuickContactActions
  ===================
  Call / Mail / WhatsApp App / WhatsApp Web quick links for a contact. Each action is
  disabled (greyed, non-clickable) when its underlying field is empty.
  Shared by the contact page and the project inspector.
-->

<template>
  <!-- Only actionable links are rendered (no greyed-out empty boxes).
       Order = the primary quick actions first: Call · SMS · WhatsApp · Teams.
       With both a mobile and a landline the call action splits in two; the
       mobile-only channels (SMS, WhatsApp) always use the mobile number. -->
  <div class="flex flex-wrap gap-2">
    <!-- Call: mobile. Labelled "Mobile" only when a landline is also present. -->
    <a v-if="mobileNo" :href="'callto:' + telNumber(mobileNo)" :class="actionCls">
      <FeatherIcon name="smartphone" class="h-4 w-4" /> {{ landlineNo ? __('Mobile') : __('Call') }}
    </a>
    <!-- Call: landline. Labelled "Landline" only when a mobile is also present. -->
    <a v-if="landlineNo" :href="'callto:' + telNumber(landlineNo)" :class="actionCls">
      <FeatherIcon name="phone" class="h-4 w-4" /> {{ mobileNo ? __('Landline') : __('Call') }}
    </a>
    <a v-if="mobileNo" :href="'sms:' + telNumber(mobileNo)" :class="actionCls">
      <FeatherIcon name="message-square" class="h-4 w-4" /> SMS
    </a>
    <!-- wa.me opens the installed WhatsApp app — mobile number only. -->
    <a v-if="mobileNo" :href="`https://wa.me/${waNumber(mobileNo)}`" target="_blank" rel="noopener" :class="actionCls">
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
    <a v-if="mobileNo && !isMobile" :href="waWebLink(mobileNo)" target="_blank" rel="noopener" :class="actionCls">
      <FeatherIcon name="message-circle" class="h-4 w-4" /> WhatsApp Web
    </a>
    <span v-if="!mobileNo && !landlineNo && !email" class="px-1 py-2 text-xs text-gray-400">{{ __('No contact details yet') }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
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
