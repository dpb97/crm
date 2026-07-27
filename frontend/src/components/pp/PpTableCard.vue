<!-- PP_REV: PpTableCard@1 -->
<!--
  PpTableCard.vue — the card a CRM table lives in: header with the table title
  on the left and the count note ("5 of 5 · row = details in the inspector") on
  the right, table body below, optional footer.

  Extracted from LCSCallLogs.vue (`.crmc-card`), the design master for the CRM
  tables. The card owns the internal scroll so a table inside a fixed-viewport
  layout scrolls in its own body rather than pushing the page.

  Props:
    title    String
    shown    Number|null — rows after filtering; omit to hide the count note
    total    Number|null — rows before filtering
    note     String — replaces the generated count note entirely
    hint     String — trailing half of the note (default "row = details in the
             inspector"); pass '' to print the bare count
    grow     Boolean (default true) — fill the remaining height and scroll
             internally. Pass false when several cards share one scrolling
             page, so each keeps its natural height instead of stretching.

  Slots:
    default  the table (usually PpDataGrid) or an empty state
    #actions controls in the header, between title and note
    #footer  optional footer strip

  STRICT --pp-* tokens, light + dark. Scoped, prefix `pp-tablecard`.
-->
<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  shown: { type: Number, default: null },
  total: { type: Number, default: null },
  note: { type: String, default: '' },
  hint: { type: String, default: null },
  grow: { type: Boolean, default: true },
})

const countNote = computed(() => {
  if (props.note) return props.note
  if (props.shown === null || props.total === null) return ''
  const count = `${props.shown} ${__('of')} ${props.total}`
  const hint = props.hint === null ? __('row = details in the inspector') : props.hint
  return hint ? `${count} · ${hint}` : count
})
</script>

<template>
  <section class="pp-tablecard" :class="{ 'pp-tablecard--fit': !grow }">
    <header v-if="title || countNote || $slots.actions" class="pp-tablecard__head">
      <span class="pp-tablecard__title">{{ title }}</span>
      <slot name="actions" />
      <span v-if="countNote" class="pp-tablecard__note">{{ countNote }}</span>
    </header>

    <slot />

    <footer v-if="$slots.footer" class="pp-tablecard__foot">
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped>
.pp-tablecard {
  flex: 1; min-height: 0;
  display: flex; flex-direction: column;
  background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-xs);
  overflow: hidden;
}
/* Several cards on one scrolling page: natural height, no stretching. */
.pp-tablecard--fit { flex: 0 0 auto; min-height: auto; }
.pp-tablecard__head {
  flex: 0 0 auto;
  display: flex; align-items: baseline; gap: var(--pp-space-3);
  padding: var(--pp-space-3) var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle);
}
.pp-tablecard__title {
  font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-bold);
  color: var(--pp-text-primary);
}
.pp-tablecard__note { margin-left: auto; font-size: 11px; color: var(--pp-text-tertiary); }
.pp-tablecard__foot {
  flex: 0 0 auto;
  padding: var(--pp-space-2) var(--pp-space-4);
  border-top: 1px solid var(--pp-border-subtle);
  font-size: var(--pp-fs-12); color: var(--pp-text-tertiary);
}

/* The grid inside takes the remaining height and scrolls internally; its own
   frame would double the card border. */
.pp-tablecard :deep(.pp-datagrid) {
  flex: 1; min-height: 0;
  border: 0; border-radius: 0; background: transparent;
}
</style>
