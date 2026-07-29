<!--
  PpMobileNav — bottom tab bar for the Pilanda shell on phones.
  1:1 port of the klickdummy design master's `.mnav` (58px bar at the bottom,
  icon + 10.5px label per tab, brand "Pi" pill for the assistant), retokenised
  to --pp-*. The master shows this only at container width <=600px; here the
  host renders it conditionally for isMobile. Purely presentational — the host
  wires each tab's target via @select.
-->
<template>
  <nav class="pp-mnav" role="navigation" aria-label="Navigation">
    <button
      v-for="it in items"
      :key="it.key"
      type="button"
      class="pp-mnav__btn"
      :class="{ 'is-active': it.key === activeKey }"
      @click="emit('select', it.key)"
    >
      <span v-if="it.pi" class="pp-mnav__pi">Pi</span>
      <component v-else :is="it.icon" class="pp-mnav__ic" />
      <span class="pp-mnav__lbl">{{ it.label }}</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  items:     { type: Array, default: () => [] },   // [{ key, label, icon (component) | pi:true }]
  activeKey: { type: String, default: '' },
})
const emit = defineEmits(['select'])
</script>

<style scoped>
.pp-mnav {
  flex: none;
  height: 58px;
  display: flex;
  align-items: stretch;
  justify-content: space-around;
  background: var(--pp-bg-surface);
  border-top: 1px solid var(--pp-border-subtle);
}
.pp-mnav__btn {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--pp-text-secondary);
  font-family: inherit;
  font-size: 10.5px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  cursor: pointer;
  min-width: 0;
}
.pp-mnav__btn:hover,
.pp-mnav__btn.is-active { color: var(--pp-brand-primary); }
.pp-mnav__ic { width: 22px; height: 22px; }
.pp-mnav__lbl { line-height: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
/* Brand "Pi" pill — assistant tab (master signature). */
.pp-mnav__pi {
  font-weight: var(--pp-weight-semibold, 600);
  font-size: 14px;
  line-height: 1.3;
  color: #fff;
  background: linear-gradient(135deg, var(--pp-brand-primary), var(--pp-brand-primary-d));
  border-radius: var(--pp-radius-ui);
  padding: 2px 8px;
}
</style>
