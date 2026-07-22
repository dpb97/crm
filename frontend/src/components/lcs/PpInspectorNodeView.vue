<!--
  PpInspectorNodeView — generic rich content for the docked Pilanda inspector.
  ==========================================================================
  Rendered into PpInspector's default slot (via DesktopLayout) whenever a page
  pushes a `view` through usePilandaInspect().inspectNode(view). Keeps the SSOT
  PpInspector untouched — it stays a dumb shell (header + collapse + body slot).

  view = {
    badge:    { label, tone: 'brand' | 'info' },
    rows:     [ { label, value } ],
    sections: [ { title, items: [{ text, muted? }], empty } ],
    action:   { label, onClick }            // optional footer button
  }
  (title is rendered by the inspector head via its #title slot.)
-->
<template>
  <div v-if="view" class="inv">
    <div v-if="view.badge" class="inv-head">
      <span class="inv-role" :class="view.badge.tone === 'brand' ? 'is-brand' : 'is-info'">
        <i class="inv-dot" :class="view.badge.tone === 'brand' ? 'is-brand' : 'is-info'" />
        {{ view.badge.label }}
      </span>
    </div>

    <dl v-if="view.rows && view.rows.length" class="inv-meta">
      <div v-for="(r, i) in view.rows" :key="i">
        <dt>{{ r.label }}</dt>
        <dd>{{ r.value }}</dd>
      </div>
    </dl>

    <section v-for="(s, i) in view.sections || []" :key="'s' + i" class="inv-sec">
      <h4 class="inv-sec-title">{{ s.title }}</h4>
      <ul v-if="s.items && s.items.length" class="inv-list">
        <li v-for="(it, j) in s.items" :key="j">
          {{ it.text }}<span v-if="it.muted" class="inv-muted"> · {{ it.muted }}</span>
        </li>
      </ul>
      <p v-else class="inv-desc">{{ s.empty }}</p>
    </section>

    <div v-if="view.action" class="inv-foot">
      <Button
        variant="solid"
        :label="view.action.label"
        iconLeft="external-link"
        @click="view.action.onClick && view.action.onClick()"
      />
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'

defineProps({
  view: { type: Object, default: null },
})
</script>

<style scoped>
.inv { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.inv-head { display: flex; }
.inv-role { display: inline-flex; align-items: center; gap: 6px; font-size: 11px;
  font-weight: var(--pp-weight-semibold); padding: 2px var(--pp-space-2);
  border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }
.inv-dot { width: 9px; height: 9px; border-radius: var(--pp-radius-full); flex-shrink: 0; }
.inv-dot.is-brand { background: var(--pp-brand-primary); }
.inv-dot.is-info { background: var(--pp-state-info); }

.inv-meta { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-2) var(--pp-space-4); margin: 0; }
.inv-meta dt { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.inv-meta dd { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }

.inv-sec { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.inv-sec-title { margin: 0; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-text-tertiary); }
.inv-list { margin: 0; padding-left: var(--pp-space-4); font-size: var(--pp-fs-14);
  color: var(--pp-text-secondary); display: flex; flex-direction: column; gap: 2px; }
.inv-muted { color: var(--pp-text-tertiary); }
.inv-desc { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-secondary); line-height: var(--pp-lh-relaxed, 1.6); }

.inv-foot { margin-top: var(--pp-space-2); }
</style>
