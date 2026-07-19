<!-- PP_REV: PpPhaseStepper@1 -->
<!--
  PpPhaseStepper.vue — nummerierter Phasen-Stepper über Oberstufen (SSOT-Baustein).

  Zeigt eine Folge nummerierter Knoten mit Verbindungslinien und darüber die
  Oberstufen-Köpfe (group), die ihre Schritte überspannen. Knoten-Status relativ
  zu `current` (1-basiert): done (<current, Häkchen), active (===current),
  todo (>current). Reine Anzeige, keine Events.

  Eigener Klassenstamm .pp-phase-stepper__* (kollisionsfrei zur Legacy-.pp-stepper-
  Wizard). Struktur-CSS in pilanda_theme_components.css (unlayered SSOT).
  STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
import { computed } from "vue";

const props = defineProps({
  steps:   { type: Array, required: true }, // [{ idx, label, group }]
  current: { type: Number, default: 1 },
});

function stepState(idx) {
  if (idx < props.current) return "done";
  if (idx === props.current) return "active";
  return "todo";
}

// Oberstufen-Köpfe aus den Schritten ableiten (Reihenfolge des ersten Auftretens).
const superGroups = computed(() => {
  const seen = [];
  for (const s of props.steps) if (!seen.includes(s.group)) seen.push(s.group);
  return seen.map((g) => ({
    group: g,
    span: props.steps.filter((s) => s.group === g).length,
  }));
});
</script>

<template>
  <div class="pp-phase-stepper">
    <div class="pp-phase-stepper__groups">
      <span v-for="g in superGroups" :key="g.group" class="pp-phase-stepper__supergroup" :style="{ flex: g.span }">{{ g.group }}</span>
    </div>
    <ol class="pp-phase-stepper__steps">
      <li v-for="(s, i) in steps" :key="s.idx" :class="['pp-phase-stepper__step', 'is-' + stepState(s.idx)]">
        <span v-if="i > 0" class="pp-phase-stepper__line" aria-hidden="true"></span>
        <span class="pp-phase-stepper__node" :title="s.label">
          <svg v-if="stepState(s.idx) === 'done'" class="pp-phase-stepper__check" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M3.5 8.5l3 3 6-6.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-else class="pp-phase-stepper__num">{{ s.idx }}</span>
        </span>
        <span class="pp-phase-stepper__label">{{ s.label }}</span>
      </li>
    </ol>
  </div>
</template>
