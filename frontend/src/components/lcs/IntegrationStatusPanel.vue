<!--
  IntegrationStatusPanel
  ======================
  360° view of the integrated stack state for a single LCS Project:
  CRM · ERPNext · BSM · HRMS · LMS · Fusion Manage.

  Each system shows a colored card with: state, key identifier,
  drill-down deep link. Clicking a card in "expanded" mode shows
  the full detail; in the default compact layout it only surfaces
  the headline so the hero area stays scannable.
-->

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        <FeatherIcon name="git-branch" class="h-3.5 w-3.5" />
        {{ __('Integrated Systems') }}
      </h3>
      <button
        class="flex items-center gap-1 text-xs text-gray-400 transition hover:text-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
        @click="refresh"
        :disabled="loading"
        :aria-label="__('Refresh integration status')"
        :aria-busy="loading"
      >
        <FeatherIcon name="refresh-cw" class="h-3 w-3" :class="loading ? 'animate-spin' : ''" />
        {{ loading ? __('Refreshing...') : __('Refresh') }}
      </button>
    </div>

    <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6 lg:gap-3">
      <SystemCard
        label="CRM"
        icon="users"
        :tone="status.crm?.linked ? 'green' : 'gray'"
        :primary="status.crm?.organization || __('Not linked')"
        :secondary="status.crm?.deal ? 'Deal: ' + status.crm.deal : ''"
      />

      <SystemCard
        label="ERPNext"
        icon="package"
        :tone="erpTone"
        :primary="status.erpnext?.status || __('—')"
        :secondary="erpSecondary"
      >
        <template #actions>
          <ErpNextDeepLink
            v-if="status.erpnext?.sales_order"
            doctype="Sales Order"
            :name="status.erpnext.sales_order"
            :label="__('SO')"
          />
          <ErpNextDeepLink
            v-else-if="status.erpnext?.quotation"
            doctype="Quotation"
            :name="status.erpnext.quotation"
            :label="__('Quote')"
          />
          <ErpNextDeepLink
            v-else-if="status.erpnext?.customer"
            doctype="Customer"
            :name="status.erpnext.customer"
            :label="__('Customer')"
          />
        </template>
      </SystemCard>

      <SystemCard
        label="BSM"
        icon="hard-hat"
        :tone="status.bsm?.project ? 'green' : 'gray'"
        :primary="status.bsm?.project || __('Not started')"
        :secondary="bsmSecondary"
      >
        <template #actions>
          <a
            v-if="status.bsm?.project"
            :href="`/app/bsm-project/${encodeURIComponent(status.bsm.project)}`"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:border-lcs-secondary hover:text-lcs-primary"
          >
            <FeatherIcon name="external-link" class="h-3 w-3" /> {{ __('Open') }}
          </a>
        </template>
      </SystemCard>

      <SystemCard
        label="HRMS"
        icon="user-check"
        :tone="hrmsTone"
        :primary="status.hrms?.project_manager || __('No PM')"
        :secondary="`${status.hrms?.team_size || 0} ${__('team members')}`"
      />

      <SystemCard
        label="LMS"
        icon="award"
        :tone="lmsTone"
        :primary="`${status.lms?.team_compliant || 0} / ${status.hrms?.team_size || 0} ${__('compliant')}`"
        :secondary="lmsSecondary"
      />

      <SystemCard
        label="Fusion Manage"
        icon="box"
        :tone="status.fusion?.item_id ? 'purple' : 'gray'"
        :primary="status.fusion?.number || status.fusion?.item_id || __('Unlinked')"
        :secondary="status.fusion?.state || ''"
      >
        <template #actions>
          <FusionManageDeepLink
            v-if="status.fusion?.item_id && status.fusion?.workspace"
            :workspace="status.fusion.workspace"
            :item-id="status.fusion.item_id"
            :label="__('PLM')"
          />
        </template>
      </SystemCard>
    </div>

    <!-- Training drill-down when compliance is not 100% -->
    <div
      v-if="status.hrms?.training && hasTrainingIssues"
      class="rounded-lg border border-amber-200 bg-amber-50 p-3"
    >
      <div class="flex items-start gap-2">
        <FeatherIcon name="alert-triangle" class="h-4 w-4 shrink-0 text-amber-600" />
        <div class="flex-1 text-xs text-amber-900">
          <div class="font-semibold">{{ __('Training compliance issue') }}</div>
          <div class="mt-1">
            <span v-if="status.hrms.training['Missing Certifications']">
              {{ status.hrms.training['Missing Certifications'] }} {{ __('team members missing required certifications') }}.
            </span>
            <span v-if="status.hrms.training['Expiring Soon']" class="ml-1">
              {{ status.hrms.training['Expiring Soon'] }} {{ __('certifications expiring soon') }}.
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'
import ErpNextDeepLink from '@/components/lcs/ErpNextDeepLink.vue'
import FusionManageDeepLink from '@/components/lcs/FusionManageDeepLink.vue'

// Small presentation card inline — trivial and tightly coupled to the panel
const SystemCard = {
  props: ['label', 'icon', 'tone', 'primary', 'secondary'],
  components: { FeatherIcon },
  computed: {
    toneClasses() {
      const m = {
        green: 'border-green-200 bg-green-50/50',
        amber: 'border-amber-200 bg-amber-50/50',
        red:   'border-red-200 bg-red-50/50',
        blue:  'border-blue-200 bg-blue-50/50',
        purple: 'border-purple-200 bg-purple-50/50',
        gray:  'border-gray-200 bg-gray-50/30',
      }
      return m[this.tone] || m.gray
    },
    iconColor() {
      const m = { green: 'text-green-600', amber: 'text-amber-600', red: 'text-red-600', blue: 'text-blue-600', purple: 'text-purple-600', gray: 'text-gray-400' }
      return m[this.tone] || m.gray
    },
  },
  template: `
    <div class="rounded-xl border p-3 transition hover:shadow-sm" :class="toneClasses">
      <div class="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider" :class="iconColor">
        <FeatherIcon :name="icon" class="h-3 w-3" />
        {{ label }}
      </div>
      <div class="mt-1 truncate text-sm font-semibold text-gray-900">{{ primary }}</div>
      <div v-if="secondary" class="mt-0.5 truncate text-xs text-gray-500">{{ secondary }}</div>
      <div v-if="$slots.actions" class="mt-2">
        <slot name="actions" />
      </div>
    </div>
  `,
}

const props = defineProps({
  project: { type: String, required: true },
})

const status = ref({})
const loading = ref(false)

async function refresh() {
  if (!props.project) return
  loading.value = true
  try {
    status.value = await call('lcs_integrations.cross_module.integration_status.get_integration_status', {
      project: props.project,
    })
  } catch (err) {
    console.warn('Integration status fetch failed:', err)
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
watch(() => props.project, refresh)

// Tone derivation for each system — green if healthy, amber on attention, red on failure, gray if unlinked
const erpTone = computed(() => {
  const s = status.value.erpnext
  if (!s) return 'gray'
  if (s.sales_order) return 'green'
  if (s.quotation) return 'blue'
  if (s.customer) return 'amber'
  return 'gray'
})

const erpSecondary = computed(() => {
  const s = status.value.erpnext
  if (!s) return ''
  if (s.sales_order_count > 1) return `${s.sales_order_count} SOs · ${s.quotation_count} Quotes`
  if (s.quotation_count > 1) return `${s.quotation_count} Quotes`
  return s.customer ? `Customer: ${s.customer}` : ''
})

const bsmSecondary = computed(() => {
  const s = status.value.bsm
  if (!s?.project) return ''
  const parts = []
  if (s.status) parts.push(s.status)
  if (s.defects_open) parts.push(`${s.defects_open} ${__('open defects')}`)
  return parts.join(' · ')
})

const hrmsTone = computed(() => {
  const s = status.value.hrms
  if (!s) return 'gray'
  if (!s.team_size) return 'amber'
  const t = s.training || {}
  if ((t['Missing Certifications'] || 0) > 0) return 'red'
  if ((t['Expiring Soon'] || 0) > 0) return 'amber'
  return 'green'
})

const lmsTone = computed(() => {
  const s = status.value.lms
  const hrms = status.value.hrms
  if (!s?.required_courses) return 'gray'
  const teamSize = hrms?.team_size || 0
  if (!teamSize) return 'amber'
  if (s.team_missing > 0) return 'red'
  if (s.team_compliant === teamSize) return 'green'
  return 'amber'
})

const lmsSecondary = computed(() => {
  const s = status.value.lms
  if (!s) return ''
  return `${s.required_courses || 0} ${__('required courses')}`
})

const hasTrainingIssues = computed(() => {
  const t = status.value.hrms?.training
  if (!t) return false
  return (t['Missing Certifications'] || 0) > 0 || (t['Expiring Soon'] || 0) > 0
})
</script>
