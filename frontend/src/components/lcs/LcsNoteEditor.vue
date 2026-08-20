<!--
  LcsNoteEditor — open a note to read/edit its text, replay a voice recording,
  and manage its links to several CRM entities at once (Projekt, Lead, Chance,
  Kontakt, Firma). Backed by lcs_integrations.notes.api (get/update/delete_note,
  add/remove_note_link). Emits `changed` after any write, `closed` on close.
-->
<template>
  <PpModal :open="open" :title="__('Note')" :width="640" :fullscreen="isMobile" @update:open="$emit('update:open', $event)">
    <div v-if="loading" class="py-12 text-center text-sm text-ink-gray-4">{{ __('Loading …') }}</div>
    <div v-else class="flex flex-col gap-4">
      <!-- Voice: replay the recording -->
      <div v-if="note.note_type === 'voice' && note.audio_file" class="rounded-lg border border-ink-gray-2 bg-surface-gray-1 p-2">
        <div class="mb-1 flex items-center gap-1.5 text-xs font-medium text-ink-gray-6">
          <FeatherIcon name="mic" class="h-3.5 w-3.5" /> {{ __('Voice note') }}
        </div>
        <audio :src="note.audio_file" controls preload="none" class="w-full" />
      </div>

      <!-- Transcript / text — editable -->
      <div>
        <label class="mb-1 block text-xs font-medium text-ink-gray-6">
          {{ note.note_type === 'voice' ? __('Transcript') : __('Note') }}
        </label>
        <textarea
          v-model="content"
          rows="6"
          class="w-full rounded-md border border-ink-gray-3 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 outline-none focus:border-lcs-secondary"
          :placeholder="__('Note text …')"
        />
      </div>

      <!-- Links to entities -->
      <div>
        <label class="mb-1 block text-xs font-medium text-ink-gray-6">{{ __('Linked to') }}</label>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="l in note.links"
            :key="l.link_doctype + l.link_name"
            class="inline-flex items-center gap-1 rounded-full border border-ink-gray-2 bg-surface-gray-1 px-2 py-1 text-xs text-ink-gray-8"
          >
            <FeatherIcon :name="iconFor(l.link_doctype)" class="h-3 w-3 text-ink-gray-5" />
            {{ l.title }}
            <button type="button" class="ml-0.5 text-ink-gray-4 hover:text-red-600" @click="removeLink(l)"><FeatherIcon name="x" class="h-3 w-3" /></button>
          </span>
          <span v-if="!note.links?.length" class="text-xs text-ink-gray-4">{{ __('Not linked yet') }}</span>
        </div>

        <!-- Add a link -->
        <div class="mt-2 flex flex-wrap items-center gap-2">
          <select v-model="pickDt" class="rounded-md border border-ink-gray-3 bg-surface-white px-2 py-1.5 text-sm outline-none">
            <option v-for="e in ENTITIES" :key="e.dt" :value="e.dt">{{ __(e.label) }}</option>
          </select>
          <div class="relative flex-1 min-w-[180px]">
            <input
              v-model="q"
              type="text"
              class="w-full rounded-md border border-ink-gray-3 bg-surface-white px-3 py-1.5 text-sm outline-none focus:border-lcs-secondary"
              :placeholder="__('Search to link') + ' …'"
              @input="search"
            />
            <div v-if="results.length" class="absolute z-10 mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-ink-gray-2 bg-surface-white shadow-lg">
              <button
                v-for="r in results"
                :key="r.name"
                type="button"
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-surface-gray-2"
                @click="addLink(r)"
              >
                <FeatherIcon :name="iconFor(pickDt)" class="h-3.5 w-3.5 text-ink-gray-5" />
                <span class="truncate">{{ r.label }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <button type="button" class="mr-auto inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm text-red-600 hover:bg-red-50" @click="onDelete">
        <FeatherIcon name="trash-2" class="h-4 w-4" /> {{ __('Delete') }}
      </button>
      <button type="button" class="rounded-md px-3 py-1.5 text-sm text-ink-gray-6 hover:bg-surface-gray-2" @click="$emit('update:open', false)">{{ __('Cancel') }}</button>
      <button
        type="button"
        class="rounded-md bg-lcs-secondary px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        :disabled="saving || !content.trim()"
        @click="onSave"
      >{{ saving ? __('Saving …') : __('Save') }}</button>
    </template>
  </PpModal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { FeatherIcon, call, toast } from 'frappe-ui'
import PpModal from '@/components/pp/PpModal.vue'
import { useViewport } from '@/composables/useViewport'

const props = defineProps({
  open: { type: Boolean, default: false },
  noteId: { type: String, default: '' },
})
const emit = defineEmits(['update:open', 'changed'])
const { isMobile } = useViewport()

const ENTITIES = [
  { dt: 'LCS Project', label: 'Project', title: 'project_name' },
  { dt: 'CRM Lead', label: 'Lead', title: 'lead_name' },
  { dt: 'LCS Chance', label: 'Chance', title: 'title' },
  { dt: 'Contact', label: 'Contact', title: 'full_name' },
  { dt: 'CRM Organization', label: 'Organization', title: 'organization_name' },
]
function iconFor(dt) {
  return { 'LCS Project': 'briefcase', 'CRM Lead': 'user-plus', 'LCS Chance': 'target', 'Contact': 'user', 'CRM Organization': 'home' }[dt] || 'link'
}

const loading = ref(false)
const saving = ref(false)
const note = ref({ links: [] })
const content = ref('')
const pickDt = ref('LCS Project')
const q = ref('')
const results = ref([])

watch(() => props.open, (v) => { if (v && props.noteId) load() })

async function load() {
  loading.value = true
  results.value = []
  q.value = ''
  try {
    note.value = await call('lcs_integrations.notes.api.get_note', { name: props.noteId })
    content.value = note.value.content || ''
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the note.'))
    emit('update:open', false)
  } finally {
    loading.value = false
  }
}

let t = null
function search() {
  clearTimeout(t)
  const needle = q.value.trim()
  if (needle.length < 2) { results.value = []; return }
  const ent = ENTITIES.find((e) => e.dt === pickDt.value)
  t = setTimeout(async () => {
    try {
      const rows = await call('frappe.client.get_list', {
        doctype: pickDt.value,
        filters: [[ent.title, 'like', `%${needle}%`]],
        fields: ['name', ent.title],
        limit_page_length: 10,
      })
      results.value = (rows || []).map((r) => ({ name: r.name, label: r[ent.title] || r.name }))
    } catch { results.value = [] }
  }, 250)
}

async function addLink(r) {
  results.value = []
  q.value = ''
  try {
    note.value = await call('lcs_integrations.notes.api.add_note_link', {
      name: props.noteId, link_doctype: pickDt.value, link_name: r.name,
    })
    emit('changed')
  } catch (e) { toast.error(e?.messages?.[0] || __('Could not add the link.')) }
}

async function removeLink(l) {
  try {
    note.value = await call('lcs_integrations.notes.api.remove_note_link', {
      name: props.noteId, link_doctype: l.link_doctype, link_name: l.link_name,
    })
    emit('changed')
  } catch (e) { toast.error(e?.messages?.[0] || __('Could not remove the link.')) }
}

async function onSave() {
  saving.value = true
  try {
    note.value = await call('lcs_integrations.notes.api.update_note', { name: props.noteId, text: content.value })
    content.value = note.value.content || ''
    toast.success(__('Note saved'))
    emit('changed')
    emit('update:open', false)
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the note.'))
  } finally { saving.value = false }
}

async function onDelete() {
  if (!window.confirm(__('Delete this note?'))) return
  try {
    await call('lcs_integrations.notes.api.delete_note', { name: props.noteId })
    toast.success(__('Note deleted'))
    emit('changed')
    emit('update:open', false)
  } catch (e) { toast.error(e?.messages?.[0] || __('Could not delete the note.')) }
}
</script>
