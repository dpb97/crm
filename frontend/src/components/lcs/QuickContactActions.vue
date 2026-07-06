<!--
  QuickContactActions
  ===================
  Call / Mail / WhatsApp / Teams quick links for a contact. Each action is
  disabled (greyed, non-clickable) when its underlying field is empty.
  Shared by the contact page and the project inspector.
-->

<template>
  <div class="grid grid-cols-2 gap-2" :class="cols === 4 ? 'sm:grid-cols-4' : ''">
    <a :href="phone ? `tel:${phone}` : null" :class="actionCls(phone)">
      <FeatherIcon name="phone" class="h-4 w-4" /> {{ __('Call') }}
    </a>
    <a :href="email ? `mailto:${email}` : null" :class="actionCls(email)">
      <FeatherIcon name="mail" class="h-4 w-4" /> {{ __('Mail') }}
    </a>
    <a :href="phone ? `https://wa.me/${waNumber(phone)}` : null" target="_blank" rel="noopener" :class="actionCls(phone)">
      <FeatherIcon name="message-circle" class="h-4 w-4" /> WhatsApp
    </a>
    <a :href="email ? teamsLink(email) : null" target="_blank" rel="noopener" :class="actionCls(email)">
      <FeatherIcon name="users" class="h-4 w-4" /> Teams
    </a>
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

// wa.me wants the country code without '+' and without leading zeros. Strip the
// '+' and a leading international '00' prefix. A purely national number (single
// leading 0, no country code) cannot be resolved reliably and is passed through.
function waNumber(p) {
  let n = String(p).replace(/[^\d+]/g, '')
  if (n.startsWith('+')) n = n.slice(1)
  else if (n.startsWith('00')) n = n.slice(2)
  return n.replace(/\D/g, '')
}
function teamsLink(email) {
  return `https://teams.microsoft.com/l/chat/0/0?users=${encodeURIComponent(email)}`
}
function actionCls(enabled) {
  return [
    'flex items-center justify-center gap-1.5 rounded-md border px-2 py-1.5 text-xs font-medium transition',
    enabled
      ? 'border-gray-200 text-gray-700 hover:border-lcs-secondary hover:text-lcs-secondary'
      : 'pointer-events-none border-gray-100 text-gray-300',
  ]
}
</script>
