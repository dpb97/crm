<!-- PP_REV: PpWorkflowStepper@2 -->
<!--
  PpWorkflowStepper.vue — GENERISCHER linearer Status-Workflow (SSOT-Baustein).

  Für beliebige Freigabe-/Bearbeitungsketten (z. B. Entwurf → Prüfung →
  Freigabe → Übergabe) über EXPLIZITE, von der App gelieferte Zustände. Jeder
  Schritt trägt seinen Status selbst (done | active | open | blocked) — die
  Komponente rechnet nichts aus, sie zeigt an. Darunter die aktuell möglichen
  Aktionen als Buttons; ein Klick meldet nur das Event zurück.

  ABGRENZUNG zu PpPhaseStepper: PpPhaseStepper ist der CRM-/Methodik-spezifische
  Stepper mit Oberstufen-Köpfen und Status RELATIV zu einem `current`-Index
  (reine Anzeige). PpWorkflowStepper ist domänenneutral, führt je Schritt einen
  EXPLIZITEN Status (inkl. `blocked`) und emittiert Aktionen — gedacht für
  Statusmaschinen (Tickets, Dokumentenfreigaben, Prüfläufe).

  ECHTE props-in / events-out Komponente — kein Store, kein Backend.

  Props:
    steps           Array<{ key, label, state, hint? }>
                    · state 'done' | 'active' | 'open' | 'blocked'
    currentActions  Array<{ label, event, kind?, disabled? }>
                    · kind  'primary' | 'default' | 'danger' (Button-Optik)

  Emits:
    action  (event)   der `event`-String der geklickten Aktion

  Scoped, Prefix `pp-wfs`. STRIKT --pp-*-Tokens, hell + dunkel.
-->
<script setup>
import IconCheck from "~icons/lucide/check";
import IconBan   from "~icons/lucide/ban";

const props = defineProps({
  steps:          { type: Array, default: () => [] }, // [{ key, label, state, hint? }]
  currentActions: { type: Array, default: () => [] }, // [{ label, event, kind?, disabled? }]
});
const emit = defineEmits(["action"]);

const KINDS = new Set(["primary", "default", "danger"]);
function btnKind(a) {
  return KINDS.has(a.kind) ? a.kind : "default";
}
</script>

<template>
  <div class="pp-wfs">
    <ol class="pp-wfs__steps">
      <li
        v-for="(s, i) in steps"
        :key="s.key"
        class="pp-wfs__step"
        :class="'is-' + s.state"
      >
        <span v-if="i > 0" class="pp-wfs__line" aria-hidden="true"></span>
        <span class="pp-wfs__node" :title="s.hint || s.label">
          <IconCheck v-if="s.state === 'done'" class="pp-wfs__ico" />
          <IconBan v-else-if="s.state === 'blocked'" class="pp-wfs__ico" />
          <span v-else class="pp-wfs__num">{{ i + 1 }}</span>
        </span>
        <span class="pp-wfs__label">
          <span class="pp-wfs__label-text">{{ s.label }}</span>
          <span v-if="s.hint" class="pp-wfs__hint">{{ s.hint }}</span>
        </span>
      </li>
    </ol>

    <div v-if="currentActions.length" class="pp-wfs__actions">
      <button
        v-for="a in currentActions"
        :key="a.event"
        type="button"
        class="pp-wfs__btn"
        :class="'pp-wfs__btn--' + btnKind(a)"
        :disabled="a.disabled"
        @click="emit('action', a.event)"
      >{{ a.label }}</button>
    </div>
  </div>
</template>

<style scoped>
.pp-wfs {
  display: flex; flex-direction: column; gap: var(--pp-space-4);
  font-family: var(--pp-font-body); color: var(--pp-text-primary);
}

/* ---- Schrittkette ---------------------------------------------- */
.pp-wfs__steps {
  list-style: none; margin: 0; padding: 0;
  display: flex; align-items: flex-start;
}
.pp-wfs__step {
  position: relative; flex: 1 1 0; min-width: 0;
  display: flex; flex-direction: column; align-items: center; gap: var(--pp-space-2);
  text-align: center;
}
.pp-wfs__line {
  position: absolute; top: 13px; right: 50%; left: -50%;
  height: 2px; background: var(--pp-border-default); z-index: 0;
}
.pp-wfs__node {
  position: relative; z-index: 1;
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: var(--pp-radius-full);
  border: 2px solid var(--pp-border-default);
  background: var(--pp-bg-surface); color: var(--pp-text-tertiary);
  font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
}
.pp-wfs__ico { width: 15px; height: 15px; }
.pp-wfs__num { line-height: 1; }
.pp-wfs__label { display: flex; flex-direction: column; gap: 1px; max-width: 100%; }
.pp-wfs__label-text {
  font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium, 500);
  color: var(--pp-text-secondary);
  overflow: hidden; text-overflow: ellipsis;
}
.pp-wfs__hint { font-size: 11px; color: var(--pp-text-tertiary); }

/* Zustände */
.pp-wfs__step.is-done .pp-wfs__node {
  border-color: var(--pp-state-success); background: var(--pp-state-success);
  color: var(--pp-text-on-accent);
}
.pp-wfs__step.is-done .pp-wfs__line { background: var(--pp-state-success); }
.pp-wfs__step.is-active .pp-wfs__node {
  border-color: var(--pp-brand-primary); color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.18);
}
.pp-wfs__step.is-active .pp-wfs__label-text { color: var(--pp-text-primary); font-weight: var(--pp-weight-semibold); }
.pp-wfs__step.is-blocked .pp-wfs__node {
  border-color: var(--pp-state-danger); background: color-mix(in oklab, var(--pp-state-danger) 14%, transparent);
  color: var(--pp-state-danger);
}
.pp-wfs__step.is-blocked .pp-wfs__label-text { color: var(--pp-state-danger); }
/* is-open = Standard (offen), keine Zusatzfarbe */

/* ---- Aktionsleiste --------------------------------------------- */
.pp-wfs__actions {
  display: flex; flex-wrap: wrap; gap: var(--pp-space-2);
  justify-content: flex-end;
  border-top: 1px solid var(--pp-border-subtle);
  padding-top: var(--pp-space-3);
}
.pp-wfs__btn {
  appearance: none; cursor: pointer; font-family: inherit;
  font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium, 500);
  padding: var(--pp-space-2) var(--pp-space-4);
  border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-border-default);
  background: var(--pp-bg-surface); color: var(--pp-text-primary);
  line-height: 1.3;
}
.pp-wfs__btn:hover:not(:disabled) { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.pp-wfs__btn:disabled { opacity: 0.5; cursor: not-allowed; }
.pp-wfs__btn--primary {
  background: var(--pp-brand-primary); border-color: var(--pp-brand-primary);
  color: var(--pp-text-on-accent);
}
.pp-wfs__btn--primary:hover:not(:disabled) {
  background: var(--pp-brand-primary-d, var(--pp-brand-primary)); border-color: var(--pp-brand-primary-d, var(--pp-brand-primary));
  color: var(--pp-text-on-accent);
}
.pp-wfs__btn--danger { border-color: var(--pp-state-danger); color: var(--pp-state-danger); }
.pp-wfs__btn--danger:hover:not(:disabled) {
  background: color-mix(in oklab, var(--pp-state-danger) 12%, transparent);
  border-color: var(--pp-state-danger); color: var(--pp-state-danger);
}
</style>
