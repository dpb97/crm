<!-- PP_REV: PpFilterBar@2 -->
<!--
  PpFilterBar.vue — the filter strip that sits above a CRM table: a "FILTER"
  caption, one or more pill segment groups, a search field and room for extra
  controls.

  Extracted from LCSCallLogs.vue (`.crmc-filter`), the design master for the
  CRM tables, so every list page gets the identical strip instead of its own
  near-copy.

  @2 (Smartphone): on mobile (< 768) the strip collapses to a single "Filter"
  trigger that shows the active segment; tapping opens a modal holding the
  segments, the search field and the #actions slot. Desktop is unchanged.
  Rule (Marco, Pilanda-weit): on the phone filters are collapsed by default and
  only expand as a central modal — never inline where they eat the list.

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
import { ref, computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { useViewport } from '@/composables/useViewport'
import PpModal from '@/components/pp/PpModal.vue'

const props = defineProps({
  segments: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
  search: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  caption: { type: String, default: '' },
})
defineEmits(['update:modelValue', 'update:search'])

const { isMobile } = useViewport()
const modalOpen = ref(false)

// Label of the currently active segment — shown on the collapsed mobile trigger.
const activeSegLabel = computed(() => props.segments.find((s) => s.key === props.modelValue)?.label || '')
</script>

<template>
  <!-- Desktop: the full inline strip -->
  <section v-if="!isMobile" class="pp-filterbar">
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

  <!-- Mobile: collapsed trigger + modal (filters are closed by default here) -->
  <template v-else>
    <div class="pp-filterbar pp-filterbar--mobile">
      <button type="button" class="pp-filterbar__trigger" @click="modalOpen = true">
        <FeatherIcon name="filter" class="pp-filterbar__trigger-ic" />
        <span class="pp-filterbar__trigger-lbl">{{ activeSegLabel || caption || __('Filter') }}</span>
        <span v-if="search" class="pp-filterbar__trigger-dot" aria-hidden="true" />
        <FeatherIcon name="chevron-down" class="pp-filterbar__trigger-ch" />
      </button>
    </div>

    <PpModal v-model:open="modalOpen" :title="caption || __('Filter')" :width="520">
      <div class="pp-filterbar__sheet">
        <slot name="segments">
          <div v-if="segments.length" class="pp-filterbar__seg pp-filterbar__seg--stack" role="tablist">
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

        <div v-if="placeholder" class="pp-filterbar__search pp-filterbar__search--full">
          <input
            :value="search"
            type="search"
            class="pp-filterbar__input"
            :placeholder="placeholder"
            @input="$emit('update:search', $event.target.value)"
          />
        </div>

        <div class="pp-filterbar__sheet-actions"><slot name="actions" /></div>
      </div>

      <template #footer>
        <button type="button" class="pp-filterbar__done" @click="modalOpen = false">{{ __('Done') }}</button>
      </template>
    </PpModal>
  </template>
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

/* --- Mobile: collapsed trigger + modal sheet -------------------------------- */
.pp-filterbar--mobile { padding: var(--pp-space-2) var(--pp-space-2); }
.pp-filterbar__trigger {
  appearance: none; cursor: pointer; font-family: inherit; width: 100%;
  display: flex; align-items: center; gap: var(--pp-space-2);
  padding: 9px var(--pp-space-3);
  font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui);
}
.pp-filterbar__trigger-ic { width: 15px; height: 15px; color: var(--pp-text-tertiary); flex: 0 0 auto; }
.pp-filterbar__trigger-lbl { flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: var(--pp-weight-medium); }
.pp-filterbar__trigger-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--pp-brand-primary); flex: 0 0 auto; }
.pp-filterbar__trigger-ch { width: 15px; height: 15px; color: var(--pp-text-tertiary); flex: 0 0 auto; }

.pp-filterbar__sheet { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.pp-filterbar__seg--stack { display: flex; flex-wrap: wrap; gap: 4px; overflow: visible; }
.pp-filterbar__seg--stack .pp-filterbar__seg-btn { flex: 1 1 auto; padding: 8px 14px; }
.pp-filterbar__search--full { flex: none; min-width: 0; }
.pp-filterbar__sheet-actions { display: flex; flex-wrap: wrap; gap: var(--pp-space-2); }
.pp-filterbar__sheet-actions:empty { display: none; }
.pp-filterbar__done {
  appearance: none; cursor: pointer; font-family: inherit; font-size: 13px; font-weight: var(--pp-weight-medium);
  padding: 8px 18px; border: 1px solid var(--pp-brand-primary); border-radius: var(--pp-radius-ui);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent);
}
</style>
