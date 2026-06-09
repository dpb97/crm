<!--
  ContactShareDialog
  ==================
  Share a Contact with other users via the LCS DocShare wrapper
  (lcs_integrations.contacts.sharing). Lists current shares and lets the
  user grant read/write access or revoke it.

  Backend enforces `share` permission on the Contact, so this dialog only
  succeeds for users actually allowed to share the record.

  The user search is rendered inline (not teleported) so clicking a result
  does not register as an outside-click that would close the Dialog.
-->

<template>
  <Dialog v-model="show" :options="{ title: __('Share contact') }">
    <template #body-content>
      <div class="space-y-4">
        <!-- Add a user -->
        <div>
          <label class="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
            {{ __('Share with') }}
          </label>
          <div class="relative">
            <input
              v-model="query"
              type="search"
              class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
              :placeholder="__('Search user by name or email')"
              @input="search"
            />
            <ul
              v-if="results.length"
              class="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-md border bg-white shadow-lg"
            >
              <li v-for="u in results" :key="u.name">
                <button
                  type="button"
                  class="block w-full px-3 py-1.5 text-left text-sm hover:bg-gray-50"
                  @click="onPickUser(u.name)"
                >
                  <span class="font-medium text-gray-900">{{ u.full_name || u.name }}</span>
                  <span class="ml-1 text-xs text-gray-400">{{ u.name }}</span>
                </button>
              </li>
            </ul>
          </div>
          <label class="mt-2 flex items-center gap-1.5 text-xs text-gray-600">
            <input type="checkbox" v-model="grantWrite" class="rounded border-gray-300" />
            {{ __('Allow editing') }}
          </label>
        </div>

        <!-- Current shares -->
        <div>
          <h4 class="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
            {{ __('Shared with') }}
          </h4>
          <div v-if="loading" class="py-3 text-center text-xs text-gray-400">{{ __('Loading…') }}</div>
          <ul v-else-if="shares.length" class="divide-y divide-gray-50">
            <li v-for="s in shares" :key="s.user" class="flex items-center justify-between py-2">
              <div class="min-w-0">
                <p class="truncate text-sm text-gray-900">{{ s.user }}</p>
                <p class="text-[11px] text-gray-400">
                  {{ s.write ? __('Can edit') : __('Can view') }}
                </p>
              </div>
              <button
                type="button"
                class="text-gray-400 transition hover:text-red-600"
                :aria-label="__('Revoke access')"
                @click="revoke(s.user)"
              >
                <FeatherIcon name="x" class="h-4 w-4" />
              </button>
            </li>
          </ul>
          <p v-else class="py-3 text-center text-xs text-gray-400">
            {{ __('Not shared with anyone yet.') }}
          </p>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Dialog, FeatherIcon, call, toast } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  contact: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])

const show = ref(props.modelValue)
const shares = ref([])
const loading = ref(false)
const grantWrite = ref(false)
const query = ref('')
const results = ref([])
let searchTimer = null

watch(() => props.modelValue, (v) => {
  show.value = v
  if (v) {
    query.value = ''
    results.value = []
    loadShares()
  }
})
watch(show, (v) => emit('update:modelValue', v))

async function loadShares() {
  if (!props.contact) return
  loading.value = true
  try {
    shares.value =
      (await call('lcs_integrations.contacts.sharing.list_contact_shares', {
        contact: props.contact,
      })) || []
  } catch (err) {
    toast.error(err.message || __('Could not load shares'))
  } finally {
    loading.value = false
  }
}

function search() {
  clearTimeout(searchTimer)
  const q = query.value.trim()
  if (!q) {
    results.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      results.value =
        (await call('frappe.client.get_list', {
          doctype: 'User',
          filters: [['enabled', '=', 1]],
          or_filters: [
            ['full_name', 'like', `%${q}%`],
            ['name', 'like', `%${q}%`],
          ],
          fields: ['name', 'full_name'],
          limit_page_length: 10,
        })) || []
    } catch {
      results.value = []
    }
  }, 250)
}

async function onPickUser(user) {
  if (!user) return
  try {
    await call('lcs_integrations.contacts.sharing.share_contact', {
      contact: props.contact,
      user,
      read: 1,
      write: grantWrite.value ? 1 : 0,
    })
    toast.success(__('Contact shared'))
    query.value = ''
    results.value = []
    await loadShares()
  } catch (err) {
    toast.error(err.message || __('Could not share contact'))
  }
}

async function revoke(user) {
  try {
    await call('lcs_integrations.contacts.sharing.unshare_contact', {
      contact: props.contact,
      user,
    })
    await loadShares()
  } catch (err) {
    toast.error(err.message || __('Could not revoke access'))
  }
}
</script>
