<!--
  QuickContactActions
  ===================
  Call / Mail / WhatsApp App / WhatsApp Web quick links for a contact. Each action is
  disabled (greyed, non-clickable) when its underlying field is empty.
  Shared by the contact page and the project inspector.
-->

<template>
  <!-- Only actionable links are rendered (no greyed-out empty boxes). -->
  <div class="flex flex-wrap gap-2">
    <!-- Plain callto: link — hands the number to the OS' registered dialer
         (Teams / Skype / softphone). No Call Log / Teams deep-link flow. -->
    <a v-if="phone" :href="'callto:' + telNumber(phone)" :class="actionCls">
      <FeatherIcon name="phone" class="h-4 w-4" /> {{ __('Call') }}
    </a>
    <a v-if="email" :href="`mailto:${email}`" :class="actionCls">
      <FeatherIcon name="mail" class="h-4 w-4" /> {{ __('Mail') }}
    </a>
    <!-- wa.me opens the installed WhatsApp app (mobile app / desktop client). -->
    <a v-if="phone" :href="`https://wa.me/${waNumber(phone)}`" target="_blank" rel="noopener" :class="actionCls">
      <FeatherIcon name="message-circle" class="h-4 w-4" /> WhatsApp
    </a>
    <!-- web.whatsapp.com opens WhatsApp Web in the browser. -->
    <a v-if="phone" :href="waWebLink(phone)" target="_blank" rel="noopener" :class="actionCls">
      <FeatherIcon name="message-circle" class="h-4 w-4" /> WhatsApp Web
    </a>
    <span v-if="!phone && !email" class="px-1 py-2 text-xs text-gray-400">{{ __('No contact details yet') }}</span>
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  email: { type: String, default: '' },
  phone: { type: String, default: '' },
  // 4 = two-up on mobile, four-up on >=sm; otherwise always two-up.
  cols: { type: Number, default: 2 },
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
const actionCls =
  'flex min-h-[40px] flex-1 basis-[calc(50%-0.25rem)] min-w-[110px] items-center justify-center gap-1.5 rounded-md border border-gray-200 px-2.5 py-2 text-xs font-medium text-gray-700 transition hover:border-lcs-secondary hover:text-lcs-secondary'
</script>
