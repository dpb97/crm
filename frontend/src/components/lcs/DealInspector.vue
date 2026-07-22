<!--
  DealInspector — docked-inspector content for a deal / opportunity.
  ==================================================================
  Mounted into the Pilanda shell inspector via usePilandaInspect().inspectPanel
  when a Kanban card in the Verkaufschancen board (LCSDeals) is single-clicked,
  replacing the page's own PpDrawer overlay in Pilanda mode. Dumb presenter —
  the page resolves all display strings and passes them in.
-->
<template>
  <div class="di2">
    <h3 class="di2-title">{{ org || dealName }}</h3>

    <div class="di2-figures">
      <div class="di2-figure">
        <span class="di2-cap">{{ __('Value') }}</span>
        <span class="di2-val">{{ value || '—' }}</span>
      </div>
      <div class="di2-figure">
        <span class="di2-cap">{{ __('Phase') }}</span>
        <span class="di2-val di2-val--phase">{{ phase || '—' }}</span>
      </div>
      <div class="di2-figure">
        <span class="di2-cap">{{ __('Close Probability') }}</span>
        <span class="di2-val">{{ probability != null ? probability + ' %' : '—' }}</span>
      </div>
    </div>

    <dl class="di2-meta">
      <div><dt>{{ __('Owner') }}</dt><dd>{{ owner || '—' }}</dd></div>
      <div><dt>{{ __('Currency') }}</dt><dd>{{ currency || '—' }}</dd></div>
      <div><dt>{{ __('Last update') }}</dt><dd>{{ updated || '—' }}</dd></div>
    </dl>

    <div class="di2-foot">
      <Button variant="solid" iconLeft="external-link" :label="__('Open in CRM')" @click="$emit('open', dealName)" />
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'

defineProps({
  dealName: { type: String, default: '' },
  org: { type: String, default: '' },
  value: { type: String, default: '' },
  phase: { type: String, default: '' },
  probability: { type: [Number, String], default: null },
  owner: { type: String, default: '' },
  currency: { type: String, default: '' },
  updated: { type: String, default: '' },
})
defineEmits(['open'])
</script>

<style scoped>
.di2 { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.di2-title { margin: 0; font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); }

.di2-figures { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-3); }
.di2-figure { display: flex; flex-direction: column; gap: 2px; padding: var(--pp-space-2) var(--pp-space-3);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-sunken); }
.di2-cap { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.di2-val { font-size: var(--pp-fs-14); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); font-variant-numeric: tabular-nums; }
.di2-val--phase { color: var(--pp-brand-primary); }

.di2-meta { display: flex; flex-direction: column; gap: var(--pp-space-3); margin: 0; }
.di2-meta dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.di2-meta dd { margin: 2px 0 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }

.di2-foot { margin-top: var(--pp-space-1); }
</style>
