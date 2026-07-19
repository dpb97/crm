<!-- PP_REV: PpPageHead@1 -->
<!--
  PpPageHead.vue — A-Liga-Seitenkopf (SSOT-Baustein).

  Eyebrow (klein, uppercase, Brand-Farbe) · großer Titel (Heading-Font) ·
  dezente Sub-Zeile (tertiär). Rechts optionaler #actions-Slot (Buttons,
  Filter, Segmented). Idiom aus ThemePreviewPls (pls-head) verallgemeinert.

  Reine Anzeige, keine Events. Struktur als scoped style mit --pp-*-Tokens
  (Copy-Modell: reist mit). Hell/dunkel-fest.
-->
<script setup>
defineProps({
  eyebrow:  { type: String, default: "" },
  title:    { type: String, required: true },
  subtitle: { type: String, default: "" },
});
</script>

<template>
  <header class="pp-pagehead">
    <div class="pp-pagehead__main">
      <span v-if="eyebrow" class="pp-pagehead__eyebrow">{{ eyebrow }}</span>
      <h1 class="pp-pagehead__title">{{ title }}</h1>
      <p v-if="subtitle" class="pp-pagehead__sub">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="pp-pagehead__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.pp-pagehead {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--pp-space-4);
  flex-wrap: wrap;
}
.pp-pagehead__main { min-width: 0; }
.pp-pagehead__eyebrow {
  display: block;
  font-size: var(--pp-fs-12);
  font-weight: var(--pp-weight-bold);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--pp-brand-primary);
}
.pp-pagehead__title {
  margin: 2px 0 0;
  font-family: var(--pp-font-heading);
  font-size: var(--pp-fs-32);
  font-weight: var(--pp-weight-semibold);
  letter-spacing: -0.02em;
  color: var(--pp-text-primary);
}
.pp-pagehead__sub {
  margin: var(--pp-space-1) 0 0;
  font-size: var(--pp-fs-14);
  color: var(--pp-text-tertiary);
  font-variant-numeric: tabular-nums;
}
.pp-pagehead__actions {
  display: flex;
  align-items: center;
  gap: var(--pp-space-2);
  flex-wrap: wrap;
}
</style>
