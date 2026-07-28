<!--
  TaskCreateModal — shell-mounted "create task" dialog opened from the inspector
  burger / function bar. Prefilled with the currently selected object (linked via
  the CRM Task reference), so a task is one click away from any list.
-->
<template>
  <PpModal v-model:open="state.open" :title="__('New task')" :width="520">
    <div class="tcm">
      <p v-if="state.ref?.title" class="tcm-ctx">
        {{ __('For') }}: <b>{{ state.ref.title }}</b>
        <span v-if="state.ref.doctype" class="tcm-ctx-dt">· {{ state.ref.doctype }}</span>
      </p>

      <label class="tcm-field">
        <span class="tcm-cap">{{ __('Title') }}</span>
        <input v-model="form.title" type="text" class="tcm-input" :placeholder="__('e.g. Prepare offer, call back …')" />
      </label>

      <div class="tcm-row">
        <label class="tcm-field">
          <span class="tcm-cap">{{ __('Priority') }}</span>
          <select v-model="form.priority" class="tcm-input">
            <option value="Low">{{ __('Low') }}</option>
            <option value="Medium">{{ __('Medium') }}</option>
            <option value="High">{{ __('High') }}</option>
          </select>
        </label>
        <label class="tcm-field">
          <span class="tcm-cap">{{ __('Due date') }}</span>
          <input v-model="form.due_date" type="date" class="tcm-input" />
        </label>
      </div>

      <label class="tcm-field">
        <span class="tcm-cap">{{ __('Description') }}</span>
        <textarea v-model="form.description" rows="3" class="tcm-input" :placeholder="__('Details …')" />
      </label>

      <div class="tcm-foot">
        <Button variant="subtle" :label="__('Cancel')" @click="closeTask" />
        <Button variant="solid" :label="__('Create task')" :loading="saving" :disabled="!form.title.trim() || saving" @click="save" />
      </div>
    </div>
  </PpModal>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { call, toast, Button } from 'frappe-ui'
import PpModal from '@/components/pp/PpModal.vue'
import { useCreateTask } from '@/composables/useCreateTask'

const { state, closeTask } = useCreateTask()

const saving = ref(false)
const form = reactive({ title: '', priority: 'Medium', due_date: '', description: '' })

// Prefill the title from the selected object each time the modal opens.
watch(() => state.open, (open) => {
  if (open) {
    form.title = state.ref?.title ? `${state.ref.title}: ` : ''
    form.priority = 'Medium'
    form.due_date = ''
    form.description = ''
  }
})

async function save() {
  const title = form.title.trim()
  if (!title) return
  saving.value = true
  try {
    const doc = {
      doctype: 'CRM Task',
      title,
      priority: form.priority,
      status: 'Todo',
      description: form.description || '',
    }
    if (form.due_date) doc.due_date = form.due_date
    if (state.ref?.doctype && state.ref?.name) {
      doc.reference_doctype = state.ref.doctype
      doc.reference_docname = state.ref.name
    }
    await call('frappe.client.insert', { doc })
    toast.success(__('Task created'))
    closeTask()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not create task'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.tcm { display: flex; flex-direction: column; gap: var(--pp-space-3); }
.tcm-ctx { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary);
  background: var(--pp-bg-sunken); padding: var(--pp-space-2) var(--pp-space-3); border-radius: var(--pp-radius-ui); }
.tcm-ctx b { color: var(--pp-text-primary); }
.tcm-ctx-dt { color: var(--pp-text-tertiary); }
.tcm-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-3); }
.tcm-field { display: flex; flex-direction: column; gap: 4px; }
.tcm-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.05em; text-transform: uppercase; color: var(--pp-text-tertiary); }
.tcm-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.tcm-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.tcm-foot { display: flex; justify-content: flex-end; gap: var(--pp-space-2); margin-top: var(--pp-space-1); }
</style>
