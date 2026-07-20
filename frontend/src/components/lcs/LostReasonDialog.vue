<!--
  LostReasonDialog — Pflicht-Verlustgrund für „Lost"-Statuswechsel (LCS-Baustein).
  =============================================================================
  Aus LCSDeals.vue extrahiert (20.07.2026), damit sowohl das Deal-Kanban
  (LCSDeals) als auch die Deal-Detailseite (LCSDeal) DIESELBE Dialog-Logik
  teilen — statt sie zu duplizieren (keine Schatten-Kopie).

  Der Ziel-Status vom Typ „Lost" verlangt serverseitig ein Pflicht-lost_reason
  (crm_deal.py::validate_lost_reason). Dieser Dialog lädt die CRM Lost Reason
  LIVE, erzwingt die Auswahl (bei „Other" zusätzlich eine Notiz) und meldet den
  gewählten Grund über `confirm` zurück. Er selbst persistiert NICHTS und setzt
  KEINEN Status zurück — Optimistik, Persistenz und Rollback bleiben beim Eltern
  (der weiß, WELCHE Verkaufschance in WELCHE Ausgangsspalte zurückspringt).

  v-model = offen/zu (Boolean). Emits: confirm({ reason, notes }).
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Mark opportunity as lost') }">
    <template #body-content>
      <div class="space-y-4">
        <FormControl
          type="select"
          :label="__('Reason for loss')"
          v-model="reason"
          :options="reasonOptions"
          required
        />
        <FormControl
          v-if="reason === 'Other'"
          type="textarea"
          :label="__('Additional notes')"
          v-model="notes"
          rows="3"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button variant="ghost" :label="__('Cancel')" @click="show = false" />
        <Button variant="solid" theme="red" :label="__('Save')" :loading="saving" @click="onSave" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createListResource, toast, Dialog, FormControl, Button } from 'frappe-ui'

const show = defineModel({ type: Boolean, default: false })
defineProps({
  // Persistenz läuft im Eltern; das Save-Button-Spinner spiegelt dessen Zustand.
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm'])

const reason = ref('')
const notes = ref('')

const reasonsRes = createListResource({
  doctype: 'CRM Lost Reason',
  fields: ['name'],
  pageLength: 100,
  cache: 'lcs-lost-reasons',
  auto: true,
})
const reasonOptions = computed(() =>
  (reasonsRes.data || []).map((r) => ({ label: __(r.name), value: r.name })),
)

// Formular bei jedem Öffnen zurücksetzen.
watch(show, (open) => {
  if (open) {
    reason.value = ''
    notes.value = ''
  }
})

function onSave() {
  if (!reason.value) {
    toast({ title: __('Please select a reason for the loss.'), icon: 'alert-circle', iconClasses: 'text-red-500' })
    return
  }
  if (reason.value === 'Other' && !notes.value) {
    toast({ title: __('Please add a note for the selected reason.'), icon: 'alert-circle', iconClasses: 'text-red-500' })
    return
  }
  emit('confirm', { reason: reason.value, notes: notes.value })
}
</script>
