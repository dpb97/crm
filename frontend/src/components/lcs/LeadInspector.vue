<!--
  LeadInspector — docked-inspector content for a lead.
  ==================================================================
  A lead is the PRE-STAGE of a project (Chance → Lead → Projekt), so this panel
  is framed like a proto-project, not a contact card: the opportunity title, the
  path-to-project stepper (Lead → Angebot → Projekt), the deal facts (value,
  country, deadline) and the Opportunity Matrix come first; the contact details
  are demoted to a small secondary line. Primary action = convert to project.
-->
<template>
  <div class="li">
    <template v-if="lead">
      <div class="li-head">
        <div class="li-name">{{ displayName }}</div>
        <span v-if="lead.status" class="li-pill">{{ __(lead.status) }}</span>
      </div>

      <!-- Path to project — this lead is a project precursor. -->
      <section class="li-path">
        <div v-for="(g, i) in pathGroups" :key="g.key" class="li-path-step" :class="{ 'is-done': i < activeGroup, 'is-active': i === activeGroup }">
          <span class="li-path-dot" />
          <span class="li-path-label">{{ g.label }}</span>
          <IconChevron v-if="i < pathGroups.length - 1" class="li-path-arr" />
        </div>
      </section>
      <p class="li-stage">{{ __('Current stage') }}: <b>{{ __(lead.status || 'New') }}</b></p>

      <!-- Deal facts (project precursor), from the originating chance. -->
      <dl class="li-facts">
        <div><dt>{{ __('Value') }}</dt><dd>{{ chanceValue }}</dd></div>
        <div><dt>{{ __('Country') }}</dt><dd>{{ chance.country || '—' }}</dd></div>
        <div><dt>{{ __('Deadline') }}</dt><dd>{{ fmtDate(chance.deadline) }}</dd></div>
        <div><dt>{{ __('Salesperson') }}</dt><dd>{{ lead.lead_owner || '—' }}</dd></div>
        <div><dt>{{ __('Company') }}</dt><dd>{{ lead.organization || '—' }}</dd></div>
      </dl>

      <!-- Opportunity Matrix — SSOT on the originating LCS Chance (chance.crm_lead). -->
      <section class="li-sec">
        <h4 class="li-sec-title">{{ __('Opportunity Matrix') }}</h4>
        <OpportunityMatrix
          v-if="chance.name"
          :technical-fit="chance.technical_fit || 0"
          :commercial-fit="chance.commercial_fit || 0"
          :relationship="chance.relationship_strength || 0"
          :competition="chance.competition_level || 0"
          :strategic-importance="chance.strategic_importance || 0"
          @update="onMatrixUpdate"
        />
        <p v-else class="li-muted">
          {{ __('No linked opportunity — the matrix is maintained on the opportunity (Chance → Lead).') }}
        </p>
      </section>

      <!-- Contact — demoted to a small secondary line. -->
      <section class="li-sec">
        <h4 class="li-sec-title">{{ __('Contact') }}</h4>
        <div class="li-contact">
          <a v-if="lead.email" class="li-line" :href="`mailto:${lead.email}`"><IconMail class="li-ico" />{{ lead.email }}</a>
          <a v-if="lead.mobile_no" class="li-line li-line--muted" :href="`tel:${lead.mobile_no}`"><IconPhone class="li-ico" />{{ lead.mobile_no }}</a>
          <span v-if="!lead.email && !lead.mobile_no" class="li-muted">—</span>
        </div>
        <QuickContactActions :email="lead.email" :phone="lead.mobile_no" class="li-actions" />
      </section>

      <div class="li-foot">
        <Button variant="solid" iconLeft="git-branch" :label="__('Convert to project')" :loading="converting" @click="convertToProject" />
        <Button variant="subtle" iconLeft="external-link" :label="__('Open in CRM')" @click="$emit('open', lead.name)" />
      </div>
    </template>

    <div v-else class="li-muted">{{ __('No lead selected') }}</div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, call, toast } from 'frappe-ui'
import IconMail from '~icons/lucide/mail'
import IconPhone from '~icons/lucide/phone'
import IconChevron from '~icons/lucide/chevron-right'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'

const props = defineProps({
  lead: { type: Object, default: null },
})
defineEmits(['open'])

const router = useRouter()

// Path to project: a lead sits in the "Lead" band of Lead → Angebot → Projekt.
const pathGroups = computed(() => [
  { key: 'lead', label: __('Lead') },
  { key: 'offer', label: __('Offer') },
  { key: 'project', label: __('Project') },
])
const LEAD_IDX = { New: 0, Contacted: 1, Nurture: 1, Qualified: 2, Converted: 3 }
const activeGroup = computed(() => {
  const idx = LEAD_IDX[props.lead?.status] ?? 0
  return idx <= 2 ? 0 : idx <= 6 ? 1 : 2
})

function eur(v) {
  const n = Number(v) || 0
  if (!n) return '—'
  if (n >= 1_000_000) return (n / 1_000_000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' M€'
  if (n >= 1_000) return Math.round(n / 1_000).toLocaleString('de-DE') + ' k€'
  return Math.round(n).toLocaleString('de-DE') + ' €'
}
const chanceValue = computed(() => eur(chance.value?.order_value))
function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(String(v).replace(' ', 'T'))
  return isNaN(d) ? String(v) : new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}

// Opportunity Matrix lives on the LCS Chance that originated this lead; load it
// on lead change and persist slider edits back to that chance (single SSOT).
const chance = ref({})
watch(() => props.lead?.name, async (name) => {
  chance.value = {}
  if (!name) return
  try {
    const res = await call('lcs_integrations.projects.api.get_chance_by_lead', { lead: name })
    chance.value = res || {}
  } catch { chance.value = {} }
}, { immediate: true })

function onMatrixUpdate({ field, value }) {
  if (!chance.value?.name) return
  chance.value[field] = value
  call('frappe.client.set_value', { doctype: 'LCS Chance', name: chance.value.name, fieldname: field, value })
    .catch((e) => toast.error(e?.messages?.[0] || e?.message || __('Could not save.')))
}
const converting = ref(false)
function convertToProject() {
  if (!props.lead) return
  converting.value = true
  call('lcs_integrations.projects.api.create_project_from_lead', { lead_name: props.lead.name })
    .then((name) => {
      const id = name?.message || name
      toast.success(__('Project created') + ': ' + id)
      if (id) router.push({ name: 'LCS Project', params: { id } })
    })
    .catch((e) => toast.error(e?.messages?.[0] || e?.message || __('Could not create project')))
    .finally(() => { converting.value = false })
}

const displayName = computed(() => {
  const l = props.lead
  if (!l) return ''
  return l.lead_name || [l.first_name, l.last_name].filter(Boolean).join(' ') || l.organization || l.name
})
</script>

<style scoped>
.li { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.li-muted { color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); }

.li-head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3); }
.li-name { font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.li-pill { flex-shrink: 0; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full);
  background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

/* Path-to-project stepper (Lead → Angebot → Projekt) */
.li-path { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.li-path-step { display: inline-flex; align-items: center; gap: 4px; color: var(--pp-text-tertiary); }
.li-path-dot { width: 8px; height: 8px; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-sunken); border: 1px solid var(--pp-border-default); flex-shrink: 0; }
.li-path-label { font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-medium); }
.li-path-arr { width: 13px; height: 13px; color: var(--pp-text-tertiary); margin: 0 2px; }
.li-path-step.is-done .li-path-dot { background: var(--pp-state-success); border-color: var(--pp-state-success); }
.li-path-step.is-active .li-path-dot { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); }
.li-path-step.is-active .li-path-label { color: var(--pp-brand-primary); font-weight: var(--pp-weight-semibold); }
.li-stage { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-secondary); }
.li-stage b { color: var(--pp-text-primary); }

.li-facts { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-3); margin: 0;
  padding: var(--pp-space-3); background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); }
.li-facts dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.li-facts dd { margin: 2px 0 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary);
  font-variant-numeric: tabular-nums; }
.li-contact { display: flex; flex-direction: column; gap: 2px; }

.li-sec { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.li-sec-title { margin: 0; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.li-line { display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px);
  color: var(--pp-text-secondary); text-decoration: none; }
.li-line--muted { color: var(--pp-text-tertiary); }
.li-line:hover { color: var(--pp-brand-primary); }
.li-ico { width: 14px; height: 14px; flex-shrink: 0; }

.li-actions { margin-top: var(--pp-space-2); }
.li-foot { margin-top: var(--pp-space-1); display: flex; flex-direction: column; gap: var(--pp-space-2); align-items: flex-start; }
</style>
