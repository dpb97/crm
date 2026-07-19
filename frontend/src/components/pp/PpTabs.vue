<!-- PP_REV: PpTabs@1 -->
<!--
  PpTabs.vue — Tab-Leiste (SSOT-Baustein).

  Tab-Buttons (role=tab) entlang einer Unterstrich-Leiste. `tabs` listet alle
  Reiter; `enabled` (optional) schaltet die umschaltbaren frei — alle übrigen
  werden deaktiviert (sichtbar, aber nicht klickbar). `modelValue` ist der
  aktive Reiter; Klick auf einen freigeschalteten Reiter emittiert
  `update:modelValue` (v-model). Beschriftung = sichtbarer Text (per Text/Rolle
  klickbar). Zugängliche Semantik: role=tablist/tab + aria-selected + disabled.

  Struktur-CSS in pilanda_theme_components.css (.pp-tabs__*, unlayered SSOT).
  STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
const props = defineProps({
  tabs:       { type: Array,  required: true },   // [String]
  enabled:    { type: Array,  default: null },    // [String] | null → alle frei
  modelValue: { type: String, required: true },
});
const emit = defineEmits(["update:modelValue"]);

const isEnabled = (t) => props.enabled == null || props.enabled.includes(t);
function select(t) { if (isEnabled(t)) emit("update:modelValue", t); }
</script>

<template>
  <nav class="pp-tabs" role="tablist">
    <button v-for="t in tabs" :key="t" role="tab" type="button"
            :class="['pp-tabs__tab', { 'is-active': modelValue === t, 'is-disabled': !isEnabled(t) }]"
            :aria-selected="modelValue === t" :disabled="!isEnabled(t)"
            :title="isEnabled(t) ? t : t + ' — noch nicht gebaut'"
            @click="select(t)">{{ t }}</button>
  </nav>
</template>
