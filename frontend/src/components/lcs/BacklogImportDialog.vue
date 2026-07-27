<!--
  BacklogImportDialog — one-click import of existing BSM construction
  sites into the CRM as LCS Projects.

  Flow:
    1. User opens dialog → default state (dry-run + only-active checked)
    2. Clicks "Preview" → calls api_backfill with dry_run=true → shows
       a summary table so user can verify before touching the DB
    3. Clicks "Import now" → runs for real → shows success toast + emits
       'imported' so the caller can reload the list

  Admin-only (System Manager or Sales Manager). Backend enforces the
  role check via frappe.only_for.
-->

<template>
  <Dialog
    v-model="openLocal"
    :options="{ title: __('Import from BSM (Construction Sites)'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <!-- Explanation -->
        <div class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
          <div class="flex items-start gap-2">
            <FeatherIcon name="info" class="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div class="font-semibold">{{ __('What this does') }}</div>
              <p class="mt-1 text-xs text-blue-700">
                {{ __('Creates an LCS Project in the CRM for every BSM construction-site project that doesn\'t already have one. Uses name prefixes (SB-, WI-, LL-, AS_) to classify the project type. Skips any BSM project that is already linked.') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Options -->
        <div class="space-y-2">
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" v-model="onlyActive" class="rounded border-gray-300" />
            {{ __('Only import active BSM projects (skip Completed / Cancelled)') }}
          </label>
        </div>

        <!-- Preview results -->
        <div v-if="preview" class="rounded-lg border bg-gray-50 p-3">
          <div class="mb-2 flex items-center justify-between">
            <div class="text-xs font-semibold uppercase tracking-wide text-gray-500">
              <FeatherIcon name="eye" class="mr-1 inline h-3 w-3" />
              {{ __('Preview') }}
            </div>
            <div class="flex gap-3 text-xs">
              <span><span class="font-semibold text-green-600">{{ preview.created }}</span> {{ __('new') }}</span>
              <span><span class="font-semibold text-gray-500">{{ preview.already_linked }}</span> {{ __('already linked') }}</span>
              <span v-if="preview.errors"><span class="font-semibold text-red-600">{{ preview.errors }}</span> {{ __('errors') }}</span>
            </div>
          </div>

          <div class="max-h-64 overflow-y-auto rounded border bg-white">
            <table class="pp-table">
              <thead class="sticky top-0">
                <tr class="border-b text-left text-gray-500">
                  <th class="font-medium">{{ __('BSM Project') }}</th>
                  <th class="font-medium">{{ __('Type') }}</th>
                  <th class="font-medium">{{ __('Organization') }}</th>
                  <th class="font-medium">{{ __('Country') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(p, i) in preview.projects"
                  :key="i"
                  class="border-b last:border-0"
                >
                  <td class="px-3 py-1.5 font-medium text-gray-800">{{ p.bsm_name }}</td>
                  <td class="px-3 py-1.5">
                    <span :class="typeClass(p.project_type)" class="inline-block rounded px-1.5 py-0.5 text-[10px] font-bold">
                      {{ p.project_type }}
                    </span>
                  </td>
                  <td class="px-3 py-1.5 text-gray-600">{{ p.organization || '—' }}</td>
                  <td class="px-3 py-1.5 text-gray-600">{{ p.country || '—' }}</td>
                </tr>
                <tr v-if="!preview.projects.length">
                  <td colspan="4" class="py-4 text-center text-gray-400">
                    {{ __('No BSM projects to import. Everything is already linked.') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Import result -->
        <div v-if="result && !preview" class="rounded-lg border border-green-200 bg-green-50 p-3 text-sm">
          <div class="flex items-center gap-2 font-semibold text-green-800">
            <FeatherIcon name="check-circle" class="h-4 w-4" />
            {{ __('Import complete') }}
          </div>
          <div class="mt-1 text-xs text-green-700">
            {{ __('Created') }} <strong>{{ result.created }}</strong> {{ __('new LCS Projects') }}.
            <span v-if="result.errors > 0"> {{ result.errors }} {{ __('errors — check the Error Log') }}.</span>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-between w-full">
        <Button variant="ghost" @click="openLocal = false" :label="__('Close')" />
        <div class="flex gap-2">
          <Button
            variant="outline"
            @click="runPreview"
            :loading="running && mode === 'preview'"
            :disabled="running"
            :label="__('Preview')"
            iconLeft="eye"
          />
          <Button
            variant="solid"
            @click="runImport"
            :loading="running && mode === 'import'"
            :disabled="running || !preview || preview.projects.length === 0"
            :label="__('Import now')"
            iconLeft="download"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Dialog, Button, FeatherIcon, call, toast } from 'frappe-ui'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'imported'])

const openLocal = computed({
  get: () => props.open,
  set: v => emit('update:open', v),
})

const onlyActive = ref(true)
const running = ref(false)
const mode = ref('')  // 'preview' | 'import'
const preview = ref(null)
const result = ref(null)

async function runPreview() {
  running.value = true
  mode.value = 'preview'
  result.value = null
  try {
    const res = await call('lcs_integrations.cross_module.backfill_projects.api_backfill', {
      dry_run: 1,
      only_active: onlyActive.value ? 1 : 0,
    })
    preview.value = res.message || res
  } catch (err) {
    toast({ title: __('Preview failed'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    running.value = false
  }
}

async function runImport() {
  running.value = true
  mode.value = 'import'
  try {
    const res = await call('lcs_integrations.cross_module.backfill_projects.api_backfill', {
      dry_run: 0,
      only_active: onlyActive.value ? 1 : 0,
    })
    result.value = res.message || res
    preview.value = null  // hide preview table so the success banner shows
    toast({
      title: __('Imported'),
      text: `${result.value.created} ${__('projects created')}`,
      icon: 'check-circle',
      iconClasses: 'text-green-500',
    })
    emit('imported', result.value)
  } catch (err) {
    toast({ title: __('Import failed'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    running.value = false
    mode.value = ''
  }
}

function typeClass(type) {
  const m = {
    SB: 'bg-blue-100 text-blue-800',
    WI: 'bg-purple-100 text-purple-800',
    LL: 'bg-emerald-100 text-emerald-800',
    SK: 'bg-amber-100 text-amber-800',
    Other: 'bg-gray-100 text-gray-700',
  }
  return m[type] || 'bg-gray-100 text-gray-700'
}
</script>
