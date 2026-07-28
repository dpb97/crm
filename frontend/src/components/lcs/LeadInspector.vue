<!--
  LeadInspector — docked-inspector content for a lead (Interessent).
  ==================================================================
  Mounted into the Pilanda shell inspector via usePilandaInspect().inspectPanel
  when a row in the Interessenten list (LCSLeads) is single-clicked, replacing
  the page's own PpDrawer overlay in Pilanda mode. Read-only summary + comms +
  "Open in CRM". Receives the lead object straight from the list (no fetch).
-->
<template>
  <div class="li">
    <template v-if="lead">
      <div class="li-head">
        <div class="li-name">{{ displayName }}</div>
        <span v-if="lead.status" class="li-pill">{{ __(lead.status) }}</span>
      </div>

      <dl class="li-meta">
        <div><dt>{{ __('Company') }}</dt><dd>{{ lead.organization || '—' }}</dd></div>
        <div><dt>{{ __('Lead owner') }}</dt><dd>{{ lead.lead_owner || '—' }}</dd></div>
      </dl>

      <section class="li-sec">
        <h4 class="li-sec-title">{{ __('Contacts') }}</h4>
        <a v-if="lead.email" class="li-line" :href="`mailto:${lead.email}`">
          <IconMail class="li-ico" />{{ lead.email }}
        </a>
        <a v-if="lead.mobile_no" class="li-line li-line--muted" :href="`tel:${lead.mobile_no}`">
          <IconPhone class="li-ico" />{{ lead.mobile_no }}
        </a>
        <p v-if="!lead.email && !lead.mobile_no" class="li-muted">—</p>
        <QuickContactActions :email="lead.email" :phone="lead.mobile_no" class="li-actions" />
      </section>

      <div class="li-foot">
        <Button variant="solid" iconLeft="external-link" :label="__('Open in CRM')" @click="$emit('open', lead.name)" />
      </div>
    </template>

    <div v-else class="li-muted">{{ __('No lead selected') }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'
import IconMail from '~icons/lucide/mail'
import IconPhone from '~icons/lucide/phone'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'

const props = defineProps({
  lead: { type: Object, default: null },
})
defineEmits(['open'])

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

.li-meta { display: flex; flex-direction: column; gap: var(--pp-space-3); margin: 0; }
.li-meta dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.li-meta dd { margin: 2px 0 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }

.li-sec { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.li-sec-title { margin: 0; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.li-line { display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px);
  color: var(--pp-text-secondary); text-decoration: none; }
.li-line--muted { color: var(--pp-text-tertiary); }
.li-line:hover { color: var(--pp-brand-primary); }
.li-ico { width: 14px; height: 14px; flex-shrink: 0; }

.li-actions { margin-top: var(--pp-space-2); }
.li-foot { margin-top: var(--pp-space-1); }
</style>
