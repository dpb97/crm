<!--
  DisplayPreferencesDialog — lets each user configure what they see.
  Everything in here is cosmetic. Security-relevant restrictions live in
  the Access Profile which is admin-controlled.
-->

<template>
  <Dialog
    v-model="openLocal"
    :options="{ title: __('Display Preferences'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-6">
        <!-- Access profile — read-only for normal users -->
        <section v-if="loaded && accessProfile" class="rounded-lg border bg-blue-50 border-blue-200 p-3">
          <div class="flex items-start gap-2">
            <FeatherIcon name="shield" class="mt-0.5 h-4 w-4 text-blue-700" />
            <div class="flex-1 text-sm">
              <div class="font-semibold text-blue-900">
                {{ __('Access Profile') }}: {{ accessProfile.profile_name }}
              </div>
              <div class="mt-1 text-xs text-blue-700">
                {{ __('Your admin has granted you access to:') }}
                <span v-if="accessProfile.countries?.length">
                  {{ accessProfile.countries.join(', ') }}
                </span>
                <span v-else>{{ __('all countries') }}</span>
                ·
                <span v-if="accessProfile.project_types?.length">
                  {{ accessProfile.project_types.join(', ') }}
                </span>
                <span v-else>{{ __('all project types') }}</span>
                <span v-if="accessProfile.own_only"> · {{ __('own projects only') }}</span>
              </div>
              <div v-if="accessProfile.hide_pricing || accessProfile.hide_fusion || accessProfile.hide_bsm" class="mt-1 text-xs text-blue-700">
                <FeatherIcon name="lock" class="inline h-3 w-3" />
                {{ __('Some sections are hidden by your profile and cannot be enabled here.') }}
              </div>
            </div>
          </div>
        </section>

        <!-- Display sections -->
        <section>
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
            {{ __('Show / Hide Sections') }}
          </h3>
          <div class="grid grid-cols-2 gap-x-6 gap-y-2">
            <PrefToggle
              v-model="form.show_integration_panel"
              :label="__('Integration Status Panel')"
              :description="__('6-system overview on project detail pages')"
            />
            <PrefToggle
              v-model="form.show_forecasting"
              :label="__('Forecasting Page')"
              :description="__('Monthly / Quarterly / Yearly revenue forecast')"
              :locked="accessProfile?.hide_forecasting"
            />
            <PrefToggle
              v-model="form.show_team_section"
              :label="__('Team / HRMS Section')"
              :description="__('Project manager and team members')"
              :locked="accessProfile?.hide_team"
            />
            <PrefToggle
              v-model="form.show_training_section"
              :label="__('LMS Training Requirements')"
              :description="__('Required courses and compliance status')"
              :locked="accessProfile?.hide_team"
            />
            <PrefToggle
              v-model="form.show_fusion_section"
              :label="__('Fusion Manage (PLM)')"
              :description="__('Item number, state, BOM link')"
              :locked="accessProfile?.hide_fusion"
            />
            <PrefToggle
              v-model="form.show_bsm_section"
              :label="__('BSM (Construction)')"
              :description="__('Baustellen-Management-Link, Defekte')"
              :locked="accessProfile?.hide_bsm"
            />
            <PrefToggle
              v-model="form.show_opportunity_matrix"
              :label="__('Opportunity Matrix Tab')"
              :description="__('5-dimension scoring radar chart')"
              :locked="accessProfile?.hide_opportunity_matrix"
            />
            <PrefToggle
              v-model="form.show_pricing_details"
              :label="__('Pricing Stages')"
              :description="__('Budget → Richtpreis → Angebot cards')"
              :locked="accessProfile?.hide_pricing"
            />
          </div>
        </section>

        <!-- Navigation defaults -->
        <section>
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
            {{ __('Navigation Defaults') }}
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              :label="__('Default List View')"
              type="select"
              v-model="form.default_list_view"
              :options="[
                { label: __('Table'), value: 'Table' },
                { label: __('Cards'), value: 'Cards' },
                { label: __('Kanban'), value: 'Kanban' }
              ]"
            />
            <FormControl
              :label="__('Forecasting Default Period')"
              type="select"
              v-model="form.default_period_forecasting"
              :options="[
                { label: __('Month'), value: 'month' },
                { label: __('Quarter'), value: 'quarter' },
                { label: __('Year'), value: 'year' }
              ]"
            />
            <FormControl
              :label="__('Voice Input Language')"
              type="select"
              v-model="form.voice_input_language"
              :options="[
                { label: 'Deutsch (DE)', value: 'de-DE' },
                { label: 'English (US)', value: 'en-US' },
                { label: 'Italiano (IT)', value: 'it-IT' },
                { label: 'Français (FR)', value: 'fr-FR' }
              ]"
            />
            <div class="flex items-end gap-2 pb-1">
              <input type="checkbox" v-model="form.default_show_only_mine" id="def-mine" class="rounded border-gray-300" />
              <label for="def-mine" class="text-sm text-gray-700">
                {{ __('Start with "My Projects" filter enabled') }}
              </label>
            </div>
          </div>
        </section>

        <!-- Behavior -->
        <section>
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
            {{ __('Behavior') }}
          </h3>
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="form.compact_mode" class="rounded border-gray-300" />
              {{ __('Compact mode — denser layouts, smaller fonts') }}
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="form.confirm_phase_changes" class="rounded border-gray-300" />
              {{ __('Confirm before moving a project backwards in the pipeline') }}
            </label>
          </div>
        </section>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="openLocal = false" :label="__('Cancel')" />
        <Button
          variant="solid"
          @click="save"
          :loading="saving"
          :disabled="saving"
          :label="__('Save Preferences')"
          iconLeft="check"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Dialog, Button, FormControl, FeatherIcon, call, toast } from 'frappe-ui'

// Inline toggle with description and lock indicator
const PrefToggle = {
  props: ['modelValue', 'label', 'description', 'locked'],
  emits: ['update:modelValue'],
  template: `
    <label class="flex items-start gap-2 py-1 cursor-pointer" :class="{ 'opacity-50 cursor-not-allowed': locked }">
      <input
        type="checkbox"
        :checked="!!modelValue && !locked"
        :disabled="locked"
        @change="$emit('update:modelValue', $event.target.checked ? 1 : 0)"
        class="mt-0.5 rounded border-gray-300"
      />
      <div class="flex-1">
        <div class="flex items-center gap-1 text-sm font-medium text-gray-900">
          {{ label }}
          <svg v-if="locked" class="inline h-3 w-3 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
        </div>
        <div v-if="description" class="text-xs text-gray-500">{{ description }}</div>
      </div>
    </label>
  `,
}

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'saved'])

const openLocal = computed({
  get: () => props.open,
  set: v => emit('update:open', v),
})

const loaded = ref(false)
const saving = ref(false)
const accessProfile = ref(null)
const form = ref({})

watch(openLocal, async (v) => {
  if (v && !loaded.value) await load()
})

async function load() {
  try {
    const res = await call('lcs_integrations.visibility.service.get_user_preferences')
    const payload = res.message || res
    form.value = { ...payload.preferences }
    accessProfile.value = payload.access_profile
    loaded.value = true
  } catch (err) {
    toast({ title: __('Failed to load preferences'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}

async function save() {
  saving.value = true
  try {
    // Strip access_profile — users can't change their own
    const payload = { ...form.value }
    delete payload.access_profile
    delete payload.user
    delete payload.name
    delete payload.doctype
    await call('lcs_integrations.visibility.service.save_user_preferences', { preferences: payload })
    toast({ title: __('Preferences saved'), icon: 'check-circle', iconClasses: 'text-green-500' })
    emit('saved', form.value)
    openLocal.value = false
  } catch (err) {
    toast({ title: __('Save failed'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    saving.value = false
  }
}
</script>
