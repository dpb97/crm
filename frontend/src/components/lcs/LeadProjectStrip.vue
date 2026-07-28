<!--
  LeadProjectStrip — full-width "project precursor" band on the Lead detail page.
  ============================================================================
  A lead is the pre-stage of a project (Chance → Lead → Projekt), so the top of
  the lead page reads like a proto-project rather than a contact: the opportunity
  title, the path-to-project stepper (Lead → Angebot → Projekt), the deal facts
  (value / country / deadline from the originating chance) and the primary action
  "Convert to project". Compact single band; the Activities + field sidebar below
  stay untouched. Facts come from the LCS Chance linked via chance.crm_lead.
-->
<template>
  <div class="lps">
    <div class="lps-main">
      <div class="lps-title">
        <IconTarget class="lps-title-ico" />
        <span class="lps-vorhaben">{{ vorhaben }}</span>
        <span v-if="lead?.status" class="lps-pill">{{ __(lead.status) }}</span>
      </div>
      <div class="lps-path">
        <template v-for="(g, i) in pathGroups" :key="g.key">
          <span class="lps-step" :class="{ 'is-done': i < activeGroup, 'is-active': i === activeGroup }">
            <span class="lps-dot" />{{ g.label }}
          </span>
          <IconChevron v-if="i < pathGroups.length - 1" class="lps-arr" />
        </template>
      </div>
    </div>

    <dl class="lps-facts">
      <div><dt>{{ __('Value') }}</dt><dd>{{ chanceValue }}</dd></div>
      <div><dt>{{ __('Country') }}</dt><dd>{{ chance.country || '—' }}</dd></div>
      <div><dt>{{ __('Deadline') }}</dt><dd>{{ fmtDate(chance.deadline) }}</dd></div>
    </dl>

    <div class="lps-act">
      <Button variant="solid" iconLeft="git-branch" :label="__('Convert to project')" :loading="converting" @click="convertToProject" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, call, toast } from 'frappe-ui'
import IconTarget from '~icons/lucide/target'
import IconChevron from '~icons/lucide/chevron-right'

const props = defineProps({
  lead: { type: Object, default: null },
})

const router = useRouter()

const vorhaben = computed(() => {
  const l = props.lead
  if (!l) return ''
  return l.lead_name || [l.first_name, l.last_name].filter(Boolean).join(' ') || l.organization || l.name
})

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

// Deal facts live on the LCS Chance that originated this lead.
const chance = ref({})
watch(() => props.lead?.name, async (name) => {
  chance.value = {}
  if (!name) return
  try {
    const res = await call('lcs_integrations.projects.api.get_chance_by_lead', { lead: name })
    chance.value = res || {}
  } catch { chance.value = {} }
}, { immediate: true })

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

const converting = ref(false)
function convertToProject() {
  if (!props.lead?.name) return
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
</script>

<style scoped>
.lps { display: flex; align-items: center; gap: var(--pp-space-5); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-5); border-bottom: 1px solid var(--pp-border-subtle);
  background: var(--pp-bg-surface); }
.lps-main { display: flex; flex-direction: column; gap: 6px; min-width: 220px; flex: 1; }
.lps-title { display: flex; align-items: center; gap: var(--pp-space-2); }
.lps-title-ico { width: 16px; height: 16px; color: var(--pp-brand-primary); flex-shrink: 0; }
.lps-vorhaben { font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.lps-pill { font-size: 11px; font-weight: var(--pp-weight-semibold); padding: 2px var(--pp-space-2);
  border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

.lps-path { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.lps-step { display: inline-flex; align-items: center; gap: 5px; font-size: var(--pp-fs-12, 12px);
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-medium); }
.lps-dot { width: 8px; height: 8px; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-sunken); border: 1px solid var(--pp-border-default); }
.lps-step.is-done .lps-dot { background: var(--pp-state-success); border-color: var(--pp-state-success); }
.lps-step.is-active .lps-dot { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); }
.lps-step.is-active { color: var(--pp-brand-primary); font-weight: var(--pp-weight-semibold); }
.lps-arr { width: 13px; height: 13px; color: var(--pp-text-tertiary); }

.lps-facts { display: flex; gap: var(--pp-space-5); margin: 0; }
.lps-facts dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.lps-facts dd { margin: 2px 0 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary);
  font-variant-numeric: tabular-nums; }

.lps-act { flex-shrink: 0; }
</style>
