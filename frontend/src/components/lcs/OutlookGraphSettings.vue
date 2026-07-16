<!--
  OutlookGraphSettings
  ====================
  Surfaces the LCS Outlook/Graph sync settings (LCS Outlook Sync Settings
  single) inside the CRM settings UI, next to the standard Email Accounts —
  so the Graph-based sync can be used instead of / alongside an IMAP/Outlook
  account. Includes a live "Test connection" against Microsoft Graph and a
  link to manage which mailboxes are tracked (Outlook Mailbox Binding).
-->

<template>
  <div class="flex h-full flex-col">
    <SettingsPage doctype="LCS Outlook Sync Settings" class="flex-1 p-8" />

    <!-- Connection test + tracked-mailbox hint -->
    <div class="border-t px-8 py-4">
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            {{ __('Test connection') }}
          </label>
          <input
            v-model="probeMailbox"
            type="text"
            class="w-72 border border-gray-300 px-2 py-1.5 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
            :placeholder="__('Optional: mailbox UPN to probe, e.g. vertrieb@lcs-group.com')"
          />
        </div>
        <Button
          :loading="testing"
          :label="__('Test Microsoft Graph connection')"
          iconLeft="zap"
          @click="testConnection"
        />
      </div>
      <p
        v-if="testResult"
        class="mt-2 text-sm"
        :class="testResult.ok ? 'text-ink-green-3' : 'text-ink-red-3'"
      >
        {{ testResult.message }}
      </p>
    </div>

    <!-- Mailbox mapping (user ↔ Graph mailbox), editable inline -->
    <div class="border-t px-8 py-6">
      <OutlookMailboxBindings />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Button, call, toast } from 'frappe-ui'
import SettingsPage from '@/components/Settings/SettingsPage.vue'
import OutlookMailboxBindings from '@/components/lcs/OutlookMailboxBindings.vue'

const probeMailbox = ref('')
const testing = ref(false)
const testResult = ref(null)

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const res = await call('lcs_integrations.outlook_sync.api.test_connection', {
      mailbox: probeMailbox.value || undefined,
    })
    if (res.ok) {
      let msg = __('Connection OK — Graph token acquired.')
      if (res.mailbox) msg += ' ' + res.mailbox
      testResult.value = { ok: true, message: msg }
      toast.success(__('Microsoft Graph connection OK'))
    } else {
      testResult.value = { ok: false, message: res.error || __('Connection failed') }
      toast.error(res.error || __('Connection failed'))
    }
  } catch (err) {
    testResult.value = { ok: false, message: err.message || __('Connection failed') }
    toast.error(err.message || __('Connection failed'))
  } finally {
    testing.value = false
  }
}
</script>
