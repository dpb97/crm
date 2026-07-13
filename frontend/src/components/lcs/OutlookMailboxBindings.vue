<!--
  OutlookMailboxBindings
  ======================
  Manage the user ↔ Outlook-mailbox mapping (Outlook Mailbox Binding) right
  in the CRM UI: one binding per salesperson. Each binding controls which
  Graph mailbox is synced for which CRM user, whether it is active, and
  whether only mails from a known contact/company are imported. Add, edit,
  toggle, test and remove — no Desk trip needed.
-->

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Mailbox mapping') }}</h3>
        <p class="text-xs text-ink-gray-5">
          {{ __('One mailbox per salesperson. Import stays filtered to known contacts/companies when enabled.') }}
        </p>
      </div>
      <Button :loading="list.loading" variant="ghost" icon="refresh-cw" @click="list.reload()" />
    </div>

    <!-- Existing bindings -->
    <div class="overflow-x-auto rounded-lg border">
      <table class="w-full min-w-[46rem] text-sm">
        <thead class="bg-gray-50 text-left text-[11px] font-medium uppercase text-gray-500">
          <tr class="border-b">
            <th class="px-3 py-2">{{ __('CRM User') }}</th>
            <th class="px-3 py-2">{{ __('Graph Mailbox (UPN)') }}</th>
            <th class="px-3 py-2 text-center">{{ __('Active') }}</th>
            <th class="px-3 py-2 text-center">{{ __('Only known') }}</th>
            <th class="px-3 py-2">{{ __('Last sync') }}</th>
            <th class="px-3 py-2 text-right">{{ __('Actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in bindings" :key="b.name" class="border-b align-middle hover:bg-gray-50">
            <td class="px-3 py-2">
              <Link
                doctype="User"
                :filters="{ user_type: 'System User', enabled: 1 }"
                :modelValue="b.user"
                @update:modelValue="(v) => saveField(b, 'user', v)"
              />
            </td>
            <td class="px-3 py-2">
              <FormControl
                type="text"
                size="sm"
                :modelValue="b.graph_mailbox"
                :debounce="600"
                @update:modelValue="(v) => saveField(b, 'graph_mailbox', v)"
              />
            </td>
            <td class="px-3 py-2 text-center">
              <input type="checkbox" :checked="b.is_active" @change="saveField(b, 'is_active', $event.target.checked ? 1 : 0)" />
            </td>
            <td class="px-3 py-2 text-center">
              <input type="checkbox" :checked="b.import_only_known_domains" @change="saveField(b, 'import_only_known_domains', $event.target.checked ? 1 : 0)" />
            </td>
            <td class="px-3 py-2 text-xs text-gray-500">
              <span v-if="b.last_error" class="text-red-500" :title="b.last_error">⚠ {{ __('error') }}</span>
              <span v-else>{{ b.last_sync ? shortTime(b.last_sync) : '—' }}</span>
            </td>
            <td class="px-3 py-2">
              <div class="flex items-center justify-end gap-1">
                <Button size="sm" variant="ghost" iconLeft="zap" :label="__('Test')" :loading="testing === b.name" @click="test(b)" />
                <Button size="sm" variant="ghost" iconLeft="download-cloud" :label="__('History')" @click="openBackfill(b)" />
                <Button size="sm" variant="ghost" theme="red" icon="trash-2" @click="remove(b)" />
              </div>
            </td>
          </tr>
          <tr v-if="!bindings.length && !list.loading">
            <td colspan="6" class="px-3 py-8 text-center text-sm text-gray-400">{{ __('No mailboxes mapped yet.') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add binding -->
    <div class="flex flex-wrap items-end gap-2 rounded-lg border border-dashed p-3">
      <div class="min-w-[14rem] flex-1">
        <div class="mb-1 text-xs text-gray-400">{{ __('CRM User') }}</div>
        <Link
          doctype="User"
          :filters="{ user_type: 'System User', enabled: 1 }"
          :modelValue="draft.user"
          @update:modelValue="onPickUser"
        />
      </div>
      <div class="min-w-[16rem] flex-1">
        <div class="mb-1 text-xs text-gray-400">{{ __('Graph Mailbox (UPN)') }}</div>
        <FormControl type="text" size="sm" v-model="draft.graph_mailbox" :placeholder="__('e.g. vertrieb@lcs-group.com')" />
      </div>
      <Button variant="solid" iconLeft="plus" :label="__('Add mailbox')" :loading="adding" @click="add" />
    </div>

    <p v-if="testResult" class="text-sm" :class="testResult.ok ? 'text-green-600' : 'text-red-600'">
      {{ testResult.text }}
    </p>

    <!-- Historical backfill -->
    <Dialog v-model="showBackfill" :options="{ title: __('Load mail history'), size: 'sm' }">
      <template #body-content>
        <div class="space-y-3">
          <p class="text-sm text-ink-gray-6">
            {{ __('Imports historical mail from known contacts/companies for') }}
            <span class="font-medium text-ink-gray-9">{{ backfillTarget?.graph_mailbox }}</span>.
            {{ __('Runs in the background; new emails appear on the linked companies.') }}
          </p>
          <FormControl type="date" :label="__('Since (optional)')" v-model="backfillSince" />
          <p class="text-xs text-ink-gray-4">{{ __('Leave empty to load the full mailbox history.') }}</p>
          <div class="flex justify-end gap-2 pt-1">
            <Button :label="__('Cancel')" @click="showBackfill = false" />
            <Button variant="solid" iconLeft="download-cloud" :label="__('Start')" :loading="backfilling" @click="startBackfill" />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { createListResource, call, toast, Button, FormControl, Dialog } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const DOCTYPE = 'Outlook Mailbox Binding'
const testing = ref('')
const adding = ref(false)
const testResult = ref(null)
const draft = reactive({ user: '', graph_mailbox: '' })

const showBackfill = ref(false)
const backfillTarget = ref(null)
const backfillSince = ref('')
const backfilling = ref(false)

const list = createListResource({
  doctype: DOCTYPE,
  fields: ['name', 'user', 'graph_mailbox', 'is_active', 'import_only_known_domains', 'last_sync', 'last_error'],
  orderBy: 'user asc',
  pageLength: 200,
  auto: true,
})
const bindings = computed(() => list.data || [])

async function saveField(binding, fieldname, value) {
  if (binding[fieldname] === value) return
  const prev = binding[fieldname]
  binding[fieldname] = value
  try {
    await call('frappe.client.set_value', { doctype: DOCTYPE, name: binding.name, fieldname, value })
  } catch (e) {
    binding[fieldname] = prev
    toast.error(e?.messages?.[0] || __('Could not save'))
  }
}

function onPickUser(v) {
  draft.user = v
  // default the mailbox to the user's own email if empty
  if (!draft.graph_mailbox && v && v.includes('@')) draft.graph_mailbox = v
}

async function add() {
  if (!draft.user || !draft.graph_mailbox) {
    toast.error(__('Pick a user and a mailbox.'))
    return
  }
  adding.value = true
  try {
    await call('frappe.client.insert', {
      doc: {
        doctype: DOCTYPE,
        user: draft.user,
        graph_mailbox: draft.graph_mailbox,
        is_active: 1,
        import_only_known_domains: 1,
      },
    })
    draft.user = ''
    draft.graph_mailbox = ''
    toast.success(__('Mailbox mapped.'))
    list.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not add the mailbox.'))
  } finally {
    adding.value = false
  }
}

async function remove(binding) {
  try {
    await call('frappe.client.delete', { doctype: DOCTYPE, name: binding.name })
    toast.success(__('Mailbox removed.'))
    list.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not remove the mailbox.'))
  }
}

async function test(binding) {
  testing.value = binding.name
  testResult.value = null
  try {
    const res = await call('lcs_integrations.outlook_sync.api.test_connection', { mailbox: binding.graph_mailbox })
    if (res.ok) {
      const mb = res.mailbox ? ` · ${res.mailbox}` : ''
      testResult.value = { ok: res.mailbox_ok !== false, text: `${binding.graph_mailbox}: ${__('connection OK')}${mb}` }
    } else {
      testResult.value = { ok: false, text: `${binding.graph_mailbox}: ${res.error}` }
    }
  } catch (e) {
    testResult.value = { ok: false, text: e?.messages?.[0] || __('Test failed') }
  } finally {
    testing.value = ''
  }
}

function openBackfill(binding) {
  backfillTarget.value = binding
  backfillSince.value = ''
  showBackfill.value = true
}

async function startBackfill() {
  backfilling.value = true
  try {
    await call('lcs_integrations.outlook_sync.backfill_service.enqueue_backfill', {
      user: backfillTarget.value.user,
      since: backfillSince.value || null,
    })
    toast.success(__('History backfill started — running in the background.'))
    showBackfill.value = false
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not start the backfill.'))
  } finally {
    backfilling.value = false
  }
}

function shortTime(dt) {
  return String(dt).replace('T', ' ').slice(0, 16)
}
</script>
