<!-- PP_REV: PpEmptyState@1 -->
<!--
  PpEmptyState.vue — Leerzustand für leere Listen/Tabellen (SSOT-Baustein).

  ECHTE props-in / slots-out Komponente: kein Store, keine Daten.
    props:  icon (lucide-Komponente, optional), title, hint (erklärender Text)
    slots:  #action = Call-to-Action (z. B. Button); default überschreibt hint

  Struktur-CSS global in components.css (.pp-empty / .pp-empty__*).
  STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
import Inbox from "~icons/lucide/inbox";

defineProps({
  icon:  { type: [Object, Function], default: null },
  title: { type: String, required: true },
  hint:  { type: String, default: "" },
});
</script>

<template>
  <div class="pp-empty">
    <span class="pp-empty__icon"><component :is="icon || Inbox" /></span>
    <span class="pp-empty__title">{{ title }}</span>
    <span v-if="$slots.default || hint" class="pp-empty__text">
      <slot>{{ hint }}</slot>
    </span>
    <div v-if="$slots.action" class="pp-empty__action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.pp-empty__action { margin-top: var(--pp-space-3); }
</style>
