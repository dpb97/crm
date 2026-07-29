<!--
  ProjectPhaseInspector — docked-inspector content for a clicked BPF phase.
  Shows the phase, its status, the editable requirement for that phase (fill it
  right here) and a gate-checked "move to this phase" action. Loads/saves the
  LCS Project itself so it works standalone in the shell inspector.
-->
<template>
  <div class="ppi">
    <div v-if="!doc" class="ppi-muted">{{ __('Loading …') }}</div>
    <template v-else>
      <div class="ppi-head">
        <span class="ppi-title">{{ __(phase) }}</span>
        <span class="ppi-badge" :class="statusTone">{{ statusText }}</span>
      </div>
      <p class="ppi-desc">{{ phaseDesc }}</p>

      <!-- Editable requirement for this phase -->
      <div v-if="phase === 'Qualified'" class="ppi-req">
        <label class="ppi-cap">{{ __('Questionaire') }}</label>
        <div class="ppi-row">
          <a v-if="doc.questionaire" :href="doc.questionaire" target="_blank" rel="noopener" class="ppi-link">{{ __('View') }}</a>
          <button class="ppi-btn" :disabled="uploading" @click="triggerUpload">
            <FeatherIcon name="upload" class="h-3.5 w-3.5" />{{ uploading ? __('Uploading …') : (doc.questionaire ? __('Replace') : __('Upload')) }}
          </button>
          <input ref="fileInput" type="file" class="hidden" @change="onFile" />
        </div>
      </div>

      <div v-else-if="phase === 'Budget'" class="ppi-req">
        <label class="ppi-cap">{{ __('Customer budget') }} (EUR)</label>
        <input type="number" class="ppi-input" :value="doc.budget_customer" @change="setField('budget_customer', numOrNull($event))" :disabled="!!doc.budget_unknown" />
        <label class="ppi-chk"><input type="checkbox" :checked="!!doc.budget_unknown" @change="setField('budget_unknown', $event.target.checked ? 1 : 0)" />{{ __('Budget unknown') }}</label>
      </div>

      <div v-else-if="phase === 'Richtpreis'" class="ppi-req">
        <label class="ppi-cap">{{ __('Richtpreis') }} (EUR)</label>
        <input type="number" class="ppi-input" :value="doc.richtpreis" @change="setField('richtpreis', numOrNull($event))" :disabled="!!doc.richtpreis_impossible" />
        <label class="ppi-chk"><input type="checkbox" :checked="!!doc.richtpreis_impossible" @change="setField('richtpreis_impossible', $event.target.checked ? 1 : 0)" />{{ __('Richtpreis not possible') }}</label>
      </div>

      <div v-else-if="phase === 'Offer'" class="ppi-req">
        <label class="ppi-cap">{{ __('Offer amount (EUR)') }}</label>
        <input type="number" class="ppi-input" :value="doc.angebot_total" @change="setField('angebot_total', numOrNull($event))" />
        <p class="ppi-hint">{{ __('Create the binding offer in the Offers tab.') }}</p>
      </div>

      <p v-else class="ppi-hint">{{ __('No data to fill for this phase.') }}</p>

      <button class="ppi-move" :disabled="phase === doc.phase || moving" @click="moveHere">
        {{ phase === doc.phase ? __('Current phase') : (moving ? __('Moving …') : __('Move to this phase')) }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { call, toast, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  projectId: { type: String, required: true },
  phase: { type: String, required: true },
})
const emit = defineEmits(['changed'])

const doc = ref(null)
const moving = ref(false)
const uploading = ref(false)
const fileInput = ref(null)

const FIELDS = ['phase', 'budget_customer', 'budget_unknown', 'richtpreis', 'richtpreis_impossible', 'questionaire', 'angebot_total']
async function load() {
  doc.value = null
  if (!props.projectId) return
  try {
    const res = await call('frappe.client.get_value', { doctype: 'LCS Project', filters: { name: props.projectId }, fieldname: FIELDS })
    doc.value = res?.message || res || {}
  } catch { doc.value = {} }
}
watch(() => props.projectId, load, { immediate: true })

const PHASE_DESC = {
  Qualified: 'Interessent qualifiziert — Questionaire erfassen, dann Budget.',
  Budget: 'Kundenbudget erfassen oder als nicht bekannt markieren.',
  Richtpreis: 'Internen Richtpreis erfassen oder als nicht möglich markieren.',
  Offer: 'Verbindliches Angebot erstellen und einreichen.',
  Negotiation: 'Angebot in Verhandlung mit dem Kunden.',
  Won: 'Auftrag gewonnen.',
  Execution: 'Projekt in Ausführung.',
  Completed: 'Projekt abgeschlossen.',
}
const phaseDesc = computed(() => __(PHASE_DESC[props.phase] || ''))

const PHASES = ['Qualified', 'Budget', 'Richtpreis', 'Offer', 'Negotiation', 'Won', 'Execution', 'Completed']
const statusTone = computed(() => {
  if (!doc.value) return 'neutral'
  if (props.phase === doc.value.phase) return 'brand'
  return PHASES.indexOf(props.phase) < PHASES.indexOf(doc.value.phase) ? 'success' : 'neutral'
})
const statusText = computed(() => (
  props.phase === doc.value?.phase ? __('Current') : (statusTone.value === 'success' ? __('Done') : __('Open'))
))

function numOrNull(ev) { const v = parseFloat(ev.target.value); return isNaN(v) ? null : v }

async function setField(fieldname, value) {
  try {
    await call('frappe.client.set_value', { doctype: 'LCS Project', name: props.projectId, fieldname, value })
    if (doc.value) doc.value[fieldname] = value
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Save failed'))
  }
}

async function moveHere() {
  if (props.phase === doc.value?.phase) return
  moving.value = true
  try {
    await call('frappe.client.set_value', { doctype: 'LCS Project', name: props.projectId, fieldname: 'phase', value: props.phase })
    if (doc.value) doc.value.phase = props.phase
    toast.success(__('Phase updated'))
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not change phase'))
  } finally {
    moving.value = false
  }
}

function triggerUpload() { fileInput.value?.click() }
async function onFile(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file) return
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file, file.name)
    form.append('is_private', '1')
    form.append('folder', 'Home/Attachments')
    form.append('doctype', 'LCS Project')
    form.append('docname', props.projectId)
    const csrf = window.csrf_token || ''
    const res = await window.fetch('/api/method/upload_file', {
      method: 'POST', credentials: 'include', headers: csrf ? { 'X-Frappe-CSRF-Token': csrf } : {}, body: form,
    })
    if (!res.ok) throw new Error(String(res.status))
    const payload = await res.json()
    const url = payload?.message?.file_url
    if (url) await setField('questionaire', url)
    toast.success(__('Questionaire uploaded'))
  } catch (e) {
    toast.error(__('Could not attach PDF'))
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.ppi { display: flex; flex-direction: column; gap: var(--pp-space-3); }
.ppi-muted { color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); }
.ppi-head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-2); }
.ppi-title { font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.ppi-badge { font-size: 10px; font-weight: var(--pp-weight-bold); text-transform: uppercase; letter-spacing: 0.05em;
  padding: 2px 8px; border-radius: var(--pp-radius-full); }
.ppi-badge.brand { color: var(--pp-text-on-accent); background: var(--pp-brand-primary); }
.ppi-badge.success { color: var(--pp-state-success); background: color-mix(in oklab, var(--pp-state-success) 15%, transparent); }
.ppi-badge.neutral { color: var(--pp-text-secondary); background: var(--pp-bg-sunken); }
.ppi-desc { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); line-height: 1.5; }
.ppi-req { display: flex; flex-direction: column; gap: var(--pp-space-2); padding: var(--pp-space-3);
  background: var(--pp-bg-sunken); border-radius: var(--pp-radius-ui); }
.ppi-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.05em; text-transform: uppercase; color: var(--pp-text-tertiary); }
.ppi-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-14, 14px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.ppi-input:disabled { opacity: 0.5; }
.ppi-row { display: flex; align-items: center; gap: var(--pp-space-2); }
.ppi-chk { display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.ppi-link { font-size: var(--pp-fs-12, 12px); color: var(--pp-brand-primary); }
.ppi-hint { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.ppi-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: 12px; font-weight: var(--pp-weight-medium);
  display: inline-flex; align-items: center; gap: 5px; padding: 6px 11px; border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-brand-primary); background: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.ppi-btn:disabled { opacity: 0.6; cursor: default; }
.ppi-move { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold);
  padding: 8px var(--pp-space-4); border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-brand-primary);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent); margin-top: var(--pp-space-1); }
.ppi-move:disabled { opacity: 0.5; cursor: default; background: var(--pp-bg-sunken); color: var(--pp-text-tertiary); border-color: var(--pp-border-subtle); }
</style>
