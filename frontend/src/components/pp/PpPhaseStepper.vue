<!-- PP_REV: PpPhaseStepper@3 -->
<!--
  PpPhaseStepper.vue — nummerierter Phasen-Stepper über Oberstufen (SSOT-Baustein).

  Zeigt eine Folge nummerierter Knoten mit Verbindungslinien und darüber die
  Oberstufen-Köpfe (group), die ihre Schritte überspannen. Knoten-Status relativ
  zu `current` (1-basiert): done (<current, Häkchen), active (===current),
  todo (>current).

  @2 (Klickdummy-Revision Marco 24.07.2026, Etappe 2 — `phaseStepperHtml`/
  `.pps-step.is-link`): Schritte sind OPTIONAL klickbar. Trägt ein steps-Eintrag
  ein Feld `go` (String), wird der Schritt zum Link: `cursor:pointer`, Hover
  (Label akzentuiert + unterstrichen, Knoten-Rand akzentuiert), Klick/Enter/Space
  emittiert `go` mit dem `go`-Wert (a11y: role=button + tabindex). Schritte OHNE
  `go` bleiben reine Anzeige (Default, rückwärtskompatibel zu @1).

  @3 (Klickdummy-Revision Marco 24.07.2026, Nachtprogramm — `phaseStepperHtml`
  `steps.some(s => s.group)`): die Oberstufen-Zeile ist OPTIONAL. Trägt KEIN
  Schritt ein `group`, entfällt die `pp-phase-stepper__groups`-Zeile komplett
  (nur die Stepper-Zeile rendert). Sobald mindestens ein Schritt eine Gruppe
  hat, verhält sich der Baustein wie @2 (rückwärtskompatibel — bestehende
  Konsumenten mit durchgehend gesetzten Gruppen ändern sich nicht).

  Eigener Klassenstamm .pp-phase-stepper__* (kollisionsfrei zur Legacy-.pp-stepper-
  Wizard). Struktur-CSS in pilanda_theme_components.css (unlayered SSOT).
  STRIKT --pp-*-Tokens, hell/dunkel.

  Props:  steps [{ idx, label, group, go? }] · current (Number, 1-basiert)
  Emits:  go (go-Wert des geklickten Schritts)
-->
<script setup>
import { computed } from "vue";

const props = defineProps({
  steps:   { type: Array, required: true }, // [{ idx, label, group, go? }]
  current: { type: Number, default: 1 },
});
const emit = defineEmits(["go"]);

function stepState(idx) {
  if (idx < props.current) return "done";
  if (idx === props.current) return "active";
  return "todo";
}
function activate(s) { if (s.go) emit("go", s.go); }

// Gruppenzeile nur zeigen, wenn mindestens ein Schritt eine Oberstufe trägt (@3).
const hasGroups = computed(() => props.steps.some((s) => !!s.group));

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
    <div v-if="hasGroups" class="pp-phase-stepper__groups">
      <span v-for="g in superGroups" :key="g.group" class="pp-phase-stepper__supergroup" :style="{ flex: g.span }">{{ g.group }}</span>
    </div>
    <ol class="pp-phase-stepper__steps">
      <li v-for="(s, i) in steps" :key="s.idx"
          :class="['pp-phase-stepper__step', 'is-' + stepState(s.idx), { 'is-link': !!s.go }]"
          :role="s.go ? 'button' : null" :tabindex="s.go ? 0 : null"
          @click="activate(s)" @keydown.enter.prevent="activate(s)" @keydown.space.prevent="activate(s)">
        <span v-if="i > 0" class="pp-phase-stepper__line" aria-hidden="true"></span>
        <span class="pp-phase-stepper__node" :title="s.go ? s.label + ' — öffnen' : s.label">
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
