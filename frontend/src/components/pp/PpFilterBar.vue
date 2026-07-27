<!-- PP_REV: PpFilterBar@1 -->
<!--
  PpFilterBar.vue — the filter strip that sits above a CRM table: a "FILTER"
  caption, one or more pill segment groups, a search field and room for extra
  controls.

  Extracted from LCSCallLogs.vue (`.crmc-filter`), the design master for the
  CRM tables, so every list page gets the identical strip instead of its own
  near-copy.

  Props:
    segments   Array<{ key, label }> — the segment pills
    modelValue String  — active segment key (v-model)
    search     String  — search text (v-model:search)
    placeholder String — search placeholder; empty hides the search field
    caption    String  — leading caption (default "Filter")

  Slots:
    #segments  replaces the segment group entirely (for multi-group filters)
    #actions   trailing controls, right of the search field

  STRICT --pp-* tokens, light + dark. Scoped, prefix `pp-filterbar`.
-->
<script setup>
defineProps({
  segments: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
  search: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  caption: { type: String, default: '' },
})
defineEmits(['update:modelValue', 'update:search'])
</script>

<template>
  <section class="pp-filterbar">
    <span class="pp-filterbar__cap">{{ caption || __('Filter') }}</span>

    <slot name="segments">
      <div v-if="segments.length" class="pp-filterbar__seg" role="tablist">
        <button
          v-for="s in segments"
          :key="s.key"
          type="button"
          class="pp-filterbar__seg-btn"
          :class="{ 'is-active': modelValue === s.key }"
          :aria-pressed="modelValue === s.key"
          @click="$emit('update:modelValue', s.key)"
        >{{ s.label }}</button>
      </div>
    </slot>

    <div v-if="placeholder" class="pp-filterbar__search">
      <input
        :value="search"
        type="search"
        class="pp-filterbar__input"
        :placeholder="placeholder"
        @input="$emit('update:search', $event.target.value)"
      />
    </div>

    <slot name="actions" />
  </section>
</template>

<style scoped>
.pp-filterbar {
  display: flex; align-items: center; gap: var(--pp-space-3); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-4);
  background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-xs);
}
.pp-filterbar__cap {
  font-size: 10px; font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase;
  color: var(--pp-text-tertiary);
}

.pp-filterbar__seg {
  display: inline-flex; gap: 2px; padding: 2px;
  border-radius: var(--pp-radius-full);
  background: var(--pp-bg-base);
  border: 1px solid var(--pp-border-default);
  overflow: hidden;   /* keeps the active pill inside the rounded track */
}
.pp-filterbar__seg-btn {
  appearance: none; cursor: pointer; font-family: inherit;
  font-size: var(--pp-fs-13, 13px);
  padding: 4px 14px; border: none;
  background: transparent; color: var(--pp-text-secondary);
  /* !important: pp-tokens.css caps EVERY <button> at --pp-radius-ui (3px) and
     only exempts the Tailwind class .rounded-full — a plain border-radius
     declaration loses to it, which squared these segments off. */
  border-radius: var(--pp-radius-full) !important;
}
.pp-filterbar__seg-btn:hover { color: var(--pp-brand-primary, #008b8b); }
/* Explicit Pilanda cyan fallback: the Tailwind lcs-primary utilities fall back
   to the legacy LCS navy (11 58 111) when the brand var does not resolve, and
   the active segment then renders dark blue instead of the master's teal. */
.pp-filterbar__seg-btn.is-active {
  background: var(--pp-brand-primary, #008b8b); color: var(--pp-text-on-accent, #fff);
  font-weight: var(--pp-weight-semibold);
}

.pp-filterbar__search { flex: 1; min-width: 200px; }
.pp-filterbar__input {
  appearance: none; width: 100%; font-family: inherit;
  font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3);
  border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base);
}
.pp-filterbar__input:focus {
  outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15);
}
</style>
