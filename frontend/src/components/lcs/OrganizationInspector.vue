<!--
  OrganizationInspector — docked-inspector content for a company (Firma).
  ==================================================================
  Mounted into the Pilanda shell inspector via usePilandaInspect().inspectPanel
  when a row in the Firmen list is single-clicked. Read-only summary + "Open".
  Sibling of ContactInspector / ProjectInspector. Fetches by name so it does
  not depend on the (transformed) list row shape.
-->
<template>
  <div class="oi">
    <div v-if="loading" class="oi-muted">{{ __('Loading...') }}</div>

    <template v-else-if="o">
      <div class="oi-head">
        <Avatar :image="o.organization_logo" :label="o.organization_name || organizationId" size="lg" />
        <div class="min-w-0">
          <div class="oi-name">{{ o.organization_name || organizationId }}</div>
          <div v-if="o.industry" class="oi-role">{{ o.industry }}</div>
        </div>
      </div>

      <dl class="oi-meta">
        <div>
          <dt>{{ __('Website') }}</dt>
          <dd>
            <a v-if="o.website" :href="o.website" target="_blank" rel="noopener" class="oi-link">{{ prettyUrl(o.website) }}</a>
            <span v-else class="oi-muted">—</span>
          </dd>
        </div>
        <div><dt>{{ __('Territory') }}</dt><dd>{{ o.territory || '—' }}</dd></div>
        <div><dt>{{ __('Employees') }}</dt><dd>{{ o.no_of_employees || '—' }}</dd></div>
        <div><dt>{{ __('Annual Revenue') }}</dt><dd>{{ o.annual_revenue ? fmtMoney(o.annual_revenue) : '—' }}</dd></div>
      </dl>

      <div class="oi-foot">
        <Button variant="solid" iconLeft="external-link" :label="__('Open')" @click="$emit('open', organizationId)" />
      </div>
    </template>

    <div v-else class="oi-muted">{{ __('No organization selected') }}</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { call, Avatar, Button } from 'frappe-ui'

const props = defineProps({
  organizationId: { type: String, default: '' },
})
defineEmits(['open'])

const o = ref(null)
const loading = ref(false)

async function load() {
  if (!props.organizationId) {
    o.value = null
    return
  }
  loading.value = true
  try {
    const data = await call('frappe.client.get_value', {
      doctype: 'CRM Organization',
      filters: { name: props.organizationId },
      fieldname: ['organization_name', 'website', 'industry', 'no_of_employees', 'annual_revenue', 'territory', 'organization_logo'],
    })
    o.value = data || null
  } catch (e) {
    o.value = null
  } finally {
    loading.value = false
  }
}
watch(() => props.organizationId, load, { immediate: true })

function prettyUrl(u) {
  return String(u || '').replace(/^https?:\/\//, '').replace(/\/$/, '')
}
function fmtMoney(v) {
  const n = Number(v) || 0
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 }).format(n)
}
</script>

<style scoped>
.oi { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.oi-muted { color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); }

.oi-head { display: flex; align-items: center; gap: var(--pp-space-3); }
.oi-name { font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.oi-role { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }

.oi-meta { display: flex; flex-direction: column; gap: var(--pp-space-3); margin: 0; }
.oi-meta dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.oi-meta dd { margin: 2px 0 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.oi-link { color: var(--pp-brand-primary); text-decoration: none; }
.oi-link:hover { text-decoration: underline; }

.oi-foot { margin-top: var(--pp-space-1); }
</style>
