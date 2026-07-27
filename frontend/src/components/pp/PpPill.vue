<!-- PP_REV: PpPill@1 -->
<!--
  PpPill.vue — status pill (coloured dot + label), the one badge shape used
  across every CRM table.

  Extracted from LCSCallLogs.vue (`.crmc-pill`), the design master for the CRM
  tables. Before this, every page carried its own copy of the same rule set
  under a different prefix, so the pills drifted apart page by page.

  Props:
    tone   'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'brand'
    dot    Boolean (default true) — leading state dot

  Content comes from the default slot, so callers keep their own labels and
  translations.

  STRICT --pp-* tokens, light + dark. Scoped, prefix `pp-pill`.
-->
<script setup>
defineProps({
  tone: { type: String, default: 'neutral' },
  dot: { type: Boolean, default: true },
})
</script>

<template>
  <span class="pp-pill" :data-tone="tone">
    <i v-if="dot" class="pp-pill__dot" />
    <slot />
  </span>
</template>

<style scoped>
.pp-pill {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2);
  border-radius: var(--pp-radius-full);
  white-space: nowrap;
}
.pp-pill__dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }

.pp-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent);    color: var(--pp-state-info); }
.pp-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.pp-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.pp-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
.pp-pill[data-tone="brand"]   { background: rgb(var(--pp-brand-primary-rgb) / 0.14);                       color: var(--pp-brand-primary); }
.pp-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }
</style>
