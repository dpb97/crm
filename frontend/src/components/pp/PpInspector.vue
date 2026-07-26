<!-- PP_REV: PpInspector@9 -->
<!--
  PpInspector.vue — rechter Inspektor / „Spezifikation" (SSOT).

  Verbindliches Collapse-Muster [[collapse-pattern]] — ab @4 im Klickdummy-Griff
  (Marco 14.07.2026 — löst den runden Kanten-Knopf `.pp-collapse-btn--edge` der
  Spez 04.07. ab):
    · GRIFF = schmale 7-px-Zieh-Leiste (col-resize) an der linken Innenkante mit
      1-px-Linie; mittig ein 16×34-Toggle-Knopf (Chevron je Zustand, opacity
      .5 → 1 bei Hover von Leiste/Knopf, Hover-Farbe Akzent).
    · BREITE EINSTELLBAR — Ziehen an der Leiste (min/max geklammert; unter das
      Minimum → klappt zu).
    · COLLAPSE AUF ICON-RAIL — Klick auf den Knopf; im Collapsed-Zustand bleibt
      der Knopf erreichbar (schmale Rail + optionaler #rail-Slot für Icons).

  @3 (Nav-Umbau 2.0 / N3, 13.07.2026): eingebautes „Spezifikation"-Verhalten.
  Reicht der Host über `spec` einen Menüpunkt herein (Vertrag `pilanda:inspect`
  UNVERÄNDERT — die Sidebar emittiert genau dieses Item), rendert der Inspektor
  von sich aus die Eckdaten (Bedeutung/Herkunft/App/Ziel) + Herkunfts-/Status-
  Badges. Beim Modulwechsel setzt der Host `spec=null` und klappt ein (die
  Sidebar emittiert dann `inspect(null)`). Ein eigener Slot bleibt möglich.

  @5 (E11, Marco 15.07.2026): Der Canvas sagt IMMER ehrlich, ob der Inhalt
  GEBAUT oder IN ENTWICKLUNG ist und welches Repo/System verdrahtet wird.
  Liefert der Host `spec.herkunft` (String) und `spec.built` (Boolean —
  z. B. aus pilanda nav-v2 item_meta), rendert der Inspektor diese statt
  der k-/x-Fallbacks: Pille „gebaut"/„in Entwicklung", Herkunft z. B.
  „Frappe-/ERPNext-Standard", „Eigene Entwicklung — Repo <name>",
  „Eigene Entwicklung — Repo noch zu erstellen", „Externe Applikation".

  @6 (Overlay-Drawer, Marco 19.07.2026): Neue OPT-IN-Variante `overlay` — der
  Inspektor fährt als Drawer VON RECHTS über den Inhalt (Scrim + Blur), statt
  eine feste Spalte zu belegen. Gedacht für schmale Viewports (Portal ≤768px),
  analog zur PpSidebar-Drawer-Mechanik:
    · Auf/Zu über das bestehende `collapsed`-v-model — offen = NICHT eingeklappt
      (der Host setzt collapsed=false → Drawer fährt ein).
    · Scrim-Klick, ESC und ein Schließen-Knopf im Kopf setzen collapsed=true.
    · a11y: role=dialog + aria-modal; beim Öffnen wandert der Fokus auf den
      Schließen-Knopf; im geschlossenen Zustand aria-hidden (off-canvas).
    · Im Overlay-Modus entfällt der Zieh-Griff/Rail (nicht sinnvoll als Sheet).
  RÜCKWÄRTSKOMPATIBEL: ohne `overlay` (default false) rendert der Baustein
  exakt wie @5 (feste Spalte + Zieh-Griff + Icon-Rail).

  @8 (Befund 16, Marco 26.07.2026 — „im Inspektor bleiben nur der Burger, Hilfe
  und Academy … das gilt für ALLE Pages"): Der Inspektor-Body zeigt jetzt NUR
  die Spezifikation (reine Anzeige). ALLE Aktionen wandern in die zentrale
  Vollbreiten-Funktionsbar `PpFunctionBar@3`, geöffnet über den Burger (☰) im
  Inspektor-Kopf. Vue-Nachzug der Klickdummy-Mechanik (`inspburger`/`inspacts`
  entleert/`insphelp`, Commit 9acf524):
    · KOPF = Burger (☰, links) · Titel „Spezifikation" · Status-Pille (rechts).
      Der Burger toggelt die Funktionsbar über `v-model:funcbarOpen`; ist keine
      Funktion verdrahtet (`funcbarAvailable=false`), erscheint er gedimmt
      (`ibx-off`) und ist inert. Der Burger bleibt im collapsed Icon-Rail
      erreichbar.
    · BODY = ausschließlich die Spezifikation: Name des gewählten Elements +
      Herkunfts-/Status-Badges + Eckdaten (Bedeutung/Herkunft/App/Ziel). KEINE
      Aktions-Buttons mehr.
    · FUSS = Hilfe (?-Knopf, Overlay klappt nach OBEN; nur wenn `helpText`) +
      Academy (emittiert `academy`, immer sichtbar — Lernplattform).
  BREAKING ggü. @7: die Aktions-Zone (`actions`-Prop, Slot `#actions`) ist
  entfernt — Aktionen gehören in eine `PpFunctionBar`. `status`/`statusTone`
  (jetzt im Kopf) und `helpText` (Fuß) bleiben. Ohne die neuen Funcbar-Props
  rendert der Baustein wie @7 minus Aktions-Zone.

  @9 (Zentral-Etappe, 26.07.2026): Die Status-Pille kennt jetzt auch die von
  mehreren ThemePreview-Seiten genutzten Ton-Werte `ok`/`warn`/`neutral` (bisher
  ohne Token-Klasse → Pille ungetönt). Nur CSS ergänzt (hell + dunkel, --pp-*),
  bestehendes Muster fortgeführt; keine Logik-/API-Änderung.

  Props:
    spec       Object|null  Menüpunkt: { n|label, k, x, app, t|target, q, d,
                             herkunft?, built? }
    catLabels  Object       Herkunfts-Label je k (default std/cust/ext)
    title      String       Kopf-Titel (default „Spezifikation")
    header     Boolean (default true)
    overlay    Boolean (default false)  Overlay-Drawer von rechts statt Spalte
    status     String       Status-Pille rechts im Kopf (@8)
    statusTone String       Pille-Ton: brand|info|success|warning|danger sowie die
                             Alias-Töne ok|warn|neutral (@9). Leer → Auto-Ableitung
                             aus dem Text (derivePillTone).
    helpText   String       Hilfetext → ?-Knopf im Fuß, Overlay nach oben (@8)
    funcbarOpen      Boolean (v-model)  Ist die Funktionsbar offen (Burger-Toggle)
    funcbarAvailable Boolean (default true)  false → Burger gedimmt/inert (ibx-off)
    collapsed, width, minWidth, maxWidth, railWidth, resizable
  Slots: (default) eigener Inhalt statt Spec · #title · #rail ·
         #default-content (Seiten-Standardinhalt, wenn kein `spec` gewählt)
  Emits: update:collapsed, update:width, update:funcbarOpen, academy
-->
<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount, useSlots } from "vue";
import ChevronLeft from "~icons/lucide/chevron-left";
import ChevronRight from "~icons/lucide/chevron-right";
import Menu from "~icons/lucide/menu";
import GraduationCap from "~icons/lucide/graduation-cap";
import FileText from "~icons/lucide/file-text";
import X from "~icons/lucide/x";

const props = defineProps({
  spec:      { type: [Object, null], default: null },
  catLabels: { type: Object, default: () => ({ std: "Frappe-Standard", cust: "Custom (Pilanda)", ext: "Extern" }) },
  collapsed: { type: Boolean, default: false },
  width:     { type: Number, default: 320 },
  minWidth:  { type: Number, default: 230 },
  maxWidth:  { type: Number, default: 520 },
  railWidth: { type: Number, default: 48 },
  title:     { type: String, default: "Spezifikation" },
  header:    { type: Boolean, default: true },
  resizable: { type: Boolean, default: true },
  overlay:   { type: Boolean, default: false },
  // @8 — Kopf-Status + Funcbar-Burger + Fuß-Hilfe
  status:           { type: String, default: "" },
  statusTone:       { type: String, default: "" },
  helpText:         { type: String, default: "" },
  funcbarOpen:      { type: Boolean, default: false },
  funcbarAvailable: { type: Boolean, default: true },
});
const emit = defineEmits(["update:collapsed", "update:width", "update:funcbarOpen", "academy"]);

/* @6: Overlay-Drawer — Zustände + ESC/Fokus (analog PpSidebar-Drawer). */
const isRail   = computed(() => props.collapsed && !props.overlay);   // Icon-Rail nur ohne Overlay
const isOpen   = computed(() => props.overlay && !props.collapsed);   // Drawer sichtbar
const closeBtn = ref(null);
function requestClose() { emit("update:collapsed", true); }
function onKeydown(e) { if (e.key === "Escape" && isOpen.value) requestClose(); }
watch(isOpen, (open) => {
  if (open) {
    window.addEventListener("keydown", onKeydown);
    nextTick(() => closeBtn.value && closeBtn.value.focus());
  } else {
    window.removeEventListener("keydown", onKeydown);
  }
});

const w = ref(props.width);
watch(() => props.width, (v) => (w.value = v));

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const dragging = ref(false);
let sx = 0, sw = 0;
function startResize(e) {
  if (!props.resizable || props.collapsed || props.overlay) return;   // nur ziehbar wenn ausgeklappt (nie im Overlay)
  dragging.value = true; sx = e.clientX; sw = w.value;
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", endResize);
  e.preventDefault();
}
function onMove(e) {
  const nw = sw - (e.clientX - sx);
  if (nw < props.minWidth - 28) { endResize(); emit("update:collapsed", true); return; }
  w.value = clamp(nw, props.minWidth, props.maxWidth);
  emit("update:width", w.value);
}
function endResize() {
  window.removeEventListener("pointermove", onMove);
  window.removeEventListener("pointerup", endResize);
  dragging.value = false;
}
onBeforeUnmount(() => { endResize(); window.removeEventListener("keydown", onKeydown); window.removeEventListener("keydown", onHelpKey); });

/* ---------- Spezifikation ---------- */
const specName = computed(() => (props.spec ? (props.spec.n || props.spec.label || "") : ""));
const specCat  = computed(() => (props.spec ? (props.spec.k || "") : ""));
const catLabel = computed(() => props.catLabels[specCat.value] || specCat.value || "—");
const specTarget = computed(() => {
  if (!props.spec) return "";
  const t = props.spec.t || props.spec.target || "";
  return t + (props.spec.q ? "?" + props.spec.q : "");
});
const isPresent = computed(() => !!(props.spec && props.spec.x));
// @5: Bau-Status/Herkunft vom Host (nav-v2 item_meta); Fallback x/k-Label.
const builtKnown = computed(() => !!props.spec && props.spec.built !== undefined);
const statusOn = computed(() => (builtKnown.value ? !!props.spec.built : isPresent.value));
const statusLabel = computed(() =>
  builtKnown.value ? (props.spec.built ? "gebaut" : "in Entwicklung")
                   : (isPresent.value ? "vorhanden" : "geplant"));
const herkunft = computed(() => (props.spec && props.spec.herkunft) || catLabel.value);

/* ---------- @8 Kopf-Status + Fuß-Hilfe ---------- */
const slots = useSlots();
const hasDefaultContent = computed(() => !!slots["default-content"]);

/* Status-Pille: Ton explizit oder aus dem Text abgeleitet (wie pillTone im
   Klickdummy — token-basiert, kein neues Farbwerk). */
function derivePillTone(s) {
  const t = String(s || "").toLowerCase();
  if (/gewonnen|aktiv|live|fertig|abgeschlossen|freigegeben|bestanden|auftrag|bezahlt|verfügbar|erledigt|grün|ok\b/.test(t)) return "success";
  if (/neu|geplant|entwurf|info|angelegt|eingang/.test(t)) return "info";
  if (/prüfung|wartet|offen|in arbeit|in bearbeitung|teilweise|mahnung|knapp|gelb|angebot|verhandlung/.test(t)) return "warning";
  if (/kritisch|verloren|überfällig|gesperrt|fehler|storniert|keine chance|rot|eskaliert/.test(t)) return "danger";
  return "brand";
}
const statusToneClass = computed(() =>
  "is-" + (props.statusTone || derivePillTone(props.status)));

/* @8 Burger → Funktionsbar toggeln (nur wenn eine Funcbar verdrahtet ist). */
function toggleFuncbar() {
  if (!props.funcbarAvailable) return;
  emit("update:funcbarOpen", !props.funcbarOpen);
}

/* Hilfe-Overlay (klappt nach OBEN; ESC / Klick außerhalb schließt). */
const helpOpen = ref(false);
function toggleHelp() { helpOpen.value = !helpOpen.value; }
function closeHelp() { helpOpen.value = false; }
function onHelpKey(e) { if (e.key === "Escape" && helpOpen.value) { e.stopPropagation(); closeHelp(); } }
watch(helpOpen, (open) => {
  if (open) window.addEventListener("keydown", onHelpKey);
  else window.removeEventListener("keydown", onHelpKey);
});
</script>

<template>
  <!-- Overlay-Scrim (nur @6-Overlay, wenn offen) -->
  <div v-if="isOpen" class="pp-inspector__scrim" @click="requestClose"></div>

  <aside class="pp-inspector"
         :class="{ 'is-collapsed': isRail, 'is-resizing': dragging, 'is-overlay': overlay, 'is-open': isOpen }"
         :style="overlay ? null : { width: (collapsed ? railWidth : w) + 'px' }"
         :role="overlay ? 'dialog' : null" :aria-modal="overlay ? 'true' : null"
         :aria-label="overlay ? title : null" :aria-hidden="overlay && collapsed ? 'true' : null"
         :inert="overlay && collapsed ? true : null">
    <!-- Griff: Zieh-Leiste (Breite) + mittiger Toggle (Collapse) — [[collapse-pattern]]; im Overlay entfällt er -->
    <div v-if="!overlay" class="pp-rez pp-rez--left" :class="{ 'is-collapsed': collapsed }"
         :title="resizable && !collapsed ? 'Breite ziehen' : null" @pointerdown="startResize">
      <button class="pp-rez__tog" type="button"
              @pointerdown.stop @click="emit('update:collapsed', !collapsed)"
              :title="collapsed ? 'Spezifikation ausklappen' : 'Spezifikation einklappen'"
              :aria-label="collapsed ? 'Spezifikation ausklappen' : 'Spezifikation einklappen'"
              :aria-expanded="!collapsed">
        <ChevronLeft v-if="collapsed" /><ChevronRight v-else />
      </button>
    </div>

    <template v-if="isRail">
      <!-- Icon-Rail: Burger bleibt erreichbar (Befund 16), darunter der Kontext-Icon-Slot -->
      <div class="pp-inspector__rail">
        <button type="button" class="pp-funcbar__burger" :class="{ 'ibx-off': !funcbarAvailable }"
                title="Funktionen" aria-label="Funktionen" aria-haspopup="true"
                :aria-expanded="String(funcbarOpen)" @click.stop="toggleFuncbar">
          <Menu />
        </button>
        <slot name="rail"><FileText class="pp-inspector__rail-ic" /></slot>
      </div>
    </template>

    <template v-else>
      <div v-if="header" class="pp-inspector__head">
        <button type="button" class="pp-funcbar__burger" :class="{ 'ibx-off': !funcbarAvailable }"
                title="Funktionen" aria-label="Funktionen" aria-haspopup="true"
                :aria-expanded="String(funcbarOpen)" @click.stop="toggleFuncbar">
          <Menu />
        </button>
        <span class="pp-inspector__title"><slot name="title">{{ title }}</slot></span>
        <span v-if="status" class="pp-inspector__status" :class="statusToneClass">{{ status }}</span>
        <button v-if="overlay" ref="closeBtn" type="button" class="pp-inspector__close"
                @click="requestClose" title="Spezifikation schließen" aria-label="Spezifikation schließen">
          <X />
        </button>
      </div>

      <div class="pp-inspector__body">
        <slot>
          <!-- eingebautes Spezifikations-Panel (reine Anzeige, Befund 16) -->
          <template v-if="spec">
            <div class="pp-spec__name">{{ specName }}</div>
            <div class="pp-spec__badges">
              <span class="pp-spec__tag" :class="'pp-spec__tag--' + specCat">{{ catLabel }}</span>
              <span class="pp-spec__pill" :class="statusOn ? 'is-present' : 'is-planned'">
                {{ statusLabel }}
              </span>
            </div>
            <dl class="pp-spec__kv">
              <div class="pp-spec__row"><dt>Bedeutung</dt><dd>{{ spec.d || "—" }}</dd></div>
              <div class="pp-spec__row"><dt>Herkunft</dt><dd>{{ herkunft }}</dd></div>
              <div class="pp-spec__row"><dt>App</dt><dd>{{ spec.app || "—" }}</dd></div>
              <div class="pp-spec__row"><dt>Ziel (Klick)</dt><dd><code class="pp-spec__code">{{ specTarget || "—" }}</code></dd></div>
            </dl>
          </template>
          <!-- Seiten-Standardinhalt (kein Detail gewählt) -->
          <slot v-else-if="hasDefaultContent" name="default-content" />
          <div v-else class="pp-inspector__empty">Kein Element ausgewählt.</div>
        </slot>
      </div>

      <!-- @8 Fuß: Hilfe (nur bei helpText) + Academy (immer) -->
      <div class="pp-inspector__foot" :class="{ 'is-help-open': helpOpen }">
        <div v-if="helpOpen" class="pp-inspector__help-backdrop" @click="closeHelp"></div>
        <div v-if="helpOpen && helpText" class="pp-inspector__help-pop" role="note">{{ helpText }}</div>
        <button v-if="helpText" type="button" class="pp-inspector__foot-btn" :aria-expanded="helpOpen"
                title="Hilfe zu dieser Seite" aria-label="Hilfe zu dieser Seite" @click="toggleHelp">
          <span class="pp-inspector__qm">?</span>Hilfe
        </button>
        <button type="button" class="pp-inspector__foot-btn"
                title="Academy — Lernplattform öffnen" aria-label="Academy öffnen" @click="emit('academy')">
          <GraduationCap class="pp-inspector__foot-ic" />Academy
        </button>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.pp-inspector { position: relative; flex: 0 0 auto; box-sizing: border-box; height: 100%;
  display: flex; flex-direction: column; min-height: 0; overflow: visible;
  background: var(--pp-bg-surface); border-left: 1px solid var(--pp-border-default);
  transition: width var(--pp-duration-base) var(--pp-ease-standard); }
.pp-inspector.is-resizing { transition: none; }

/* ---- @6 Overlay-Drawer (von rechts) ---- */
.pp-inspector.is-overlay { position: fixed; top: 0; right: 0; bottom: 0; z-index: var(--pp-z-modal);
  width: min(92%, 400px); height: auto;
  transform: translateX(100%);
  transition: transform var(--pp-duration-base) var(--pp-ease-decelerate);
  box-shadow: var(--pp-shadow-xl); }
.pp-inspector.is-overlay.is-open { transform: none; }
.pp-inspector__scrim { position: fixed; inset: 0; z-index: calc(var(--pp-z-modal) - 1);
  background: rgb(var(--pp-shadow-deep-rgb) / .4);
  -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); }
.pp-inspector__close { appearance: none; cursor: pointer; flex: 0 0 auto; display: inline-flex;
  align-items: center; justify-content: center; width: 26px; height: 26px; padding: 0;
  border: 1px solid transparent; border-radius: var(--pp-radius-ui); background: transparent;
  color: var(--pp-brand-primary-d, var(--pp-brand-primary));
  transition: background var(--pp-duration-fast) var(--pp-ease-standard),
    border-color var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-inspector__close:hover { background: var(--pp-bg-hover); border-color: var(--pp-border-default); }
.pp-inspector__close:focus-visible { outline: none; box-shadow: var(--pp-shadow-focus-ring); }
.pp-inspector__close :deep(svg) { width: 15px; height: 15px; display: block; }

.pp-inspector__head { display: flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-2) var(--pp-space-3); flex-shrink: 0;
  border-bottom: 1px solid var(--pp-border-subtle);
  background: var(--pp-accent-soft); color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.pp-inspector__title { flex: 1 1 auto; font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  text-transform: uppercase; letter-spacing: .06em; }
.pp-inspector__body { flex: 1 1 auto; min-height: 0; overflow: auto; padding: var(--pp-space-4); }
.pp-inspector__empty { color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); }

/* @8 Burger im Kopf: nutzt die zentrale .pp-funcbar__burger-Struktur (components.css).
   ibx-off = gedimmt/inert, wenn keine Funcbar verdrahtet ist. */
.pp-inspector__head .pp-funcbar__burger { flex: 0 0 auto; }
.pp-funcbar__burger.ibx-off { opacity: .38; pointer-events: none; }

/* ---- @8 Kopf-Status-Pille (rechts) ---- */
.pp-inspector__status { flex: 0 0 auto; font-size: 9.5px; font-weight: var(--pp-weight-bold);
  letter-spacing: .03em; padding: 3px 9px; border-radius: var(--pp-radius-ui); text-transform: uppercase;
  white-space: nowrap; }
.pp-inspector__status.is-brand   { background: var(--pp-bg-surface); color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.pp-inspector__status.is-info    { background: color-mix(in oklab, var(--pp-state-info) 16%, transparent);    color: var(--pp-state-info); }
.pp-inspector__status.is-success { background: color-mix(in oklab, var(--pp-state-success) 18%, transparent); color: var(--pp-state-success); }
.pp-inspector__status.is-warning { background: color-mix(in oklab, var(--pp-state-warning) 20%, transparent); color: var(--pp-state-warning); }
.pp-inspector__status.is-danger  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
/* @9 Alias-Töne mehrerer ThemePreview-Seiten (ok/warn/neutral) — gleiches Muster. */
.pp-inspector__status.is-ok      { background: color-mix(in oklab, var(--pp-state-success) 18%, transparent); color: var(--pp-state-success); }
.pp-inspector__status.is-warn    { background: color-mix(in oklab, var(--pp-state-warning) 20%, transparent); color: var(--pp-state-warning); }
.pp-inspector__status.is-neutral { background: var(--pp-bg-hover); color: var(--pp-text-secondary); }

/* ---- @8 Fuß: Hilfe + Academy (Overlay klappt nach oben) ---- */
.pp-inspector__foot { position: relative; flex: 0 0 auto; display: flex; gap: var(--pp-space-2);
  padding: var(--pp-space-2) var(--pp-space-3); border-top: 1px solid var(--pp-border-subtle); }
.pp-inspector__foot-btn { appearance: none; cursor: pointer; display: inline-flex; align-items: center;
  justify-content: center; gap: 6px; padding: 6px 8px; min-width: 0;
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-tertiary);
  font-family: inherit; font-size: 11.5px; font-weight: var(--pp-weight-semibold); white-space: nowrap;
  transition: color var(--pp-duration-fast) var(--pp-ease-standard),
    border-color var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-inspector__foot-btn:hover, .pp-inspector__foot.is-help-open .pp-inspector__foot-btn[aria-expanded="true"] {
  color: var(--pp-brand-primary-d, var(--pp-brand-primary)); border-color: var(--pp-brand-primary); }
.pp-inspector__foot-btn:focus-visible { outline: none; box-shadow: var(--pp-shadow-focus-ring); }
.pp-inspector__qm { width: 15px; height: 15px; flex: 0 0 15px; border-radius: var(--pp-radius-full);
  border: 1px solid currentColor; display: inline-flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: var(--pp-weight-bold); }
.pp-inspector__foot-ic { width: 14px; height: 14px; flex: 0 0 14px; }
.pp-inspector__help-backdrop { position: fixed; inset: 0; z-index: var(--pp-z-overlay); }
.pp-inspector__help-pop { position: absolute; bottom: calc(100% + 4px); left: var(--pp-space-3); right: var(--pp-space-3);
  z-index: calc(var(--pp-z-overlay) + 1); padding: var(--pp-space-3);
  background: var(--pp-bg-elevated); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-lg);
  font-size: var(--pp-fs-12, 12px); line-height: 1.5; color: var(--pp-text-primary); }

.pp-inspector__rail { display: flex; flex-direction: column; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-3) 0 var(--pp-space-2); height: 100%; }
.pp-inspector__rail-ic { width: 18px; height: 18px; color: var(--pp-text-tertiary); }

/* ---- Spezifikations-Panel ---- */
.pp-spec__name { font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); margin-bottom: var(--pp-space-2); line-height: 1.3; }
.pp-spec__badges { display: flex; align-items: center; gap: var(--pp-space-2); margin-bottom: var(--pp-space-3); flex-wrap: wrap; }
.pp-spec__tag { font-size: 9.5px; font-weight: var(--pp-weight-bold); letter-spacing: .03em;
  padding: 3px 9px; border-radius: var(--pp-radius-ui); color: var(--pp-text-on-accent); }
.pp-spec__tag--std  { background: var(--pp-cat-std); }
.pp-spec__tag--cust { background: var(--pp-cat-cust); }
.pp-spec__tag--ext  { background: var(--pp-cat-ext); }
.pp-spec__pill { font-size: 9.5px; font-weight: var(--pp-weight-bold); letter-spacing: .03em;
  padding: 3px 9px; border-radius: var(--pp-radius-ui); }
.pp-spec__pill.is-present { background: color-mix(in oklab, var(--pp-state-success) 20%, transparent); color: var(--pp-state-success); }
.pp-spec__pill.is-planned { background: var(--pp-bg-hover); color: var(--pp-text-secondary); }

.pp-spec__kv { margin: 0; }
.pp-spec__row { display: flex; flex-direction: column; gap: 2px; margin-bottom: var(--pp-space-3); }
.pp-spec__row dt { font-size: 9.5px; text-transform: uppercase; letter-spacing: .06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); margin: 0; }
.pp-spec__row dd { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.pp-spec__code { display: inline-block; background: var(--pp-bg-hover); padding: 2px 7px;
  border-radius: var(--pp-radius-xs); font-size: var(--pp-fs-12); font-family: inherit;
  color: var(--pp-text-primary); word-break: break-all; }

/* ---- Griff: Zieh-Leiste + mittiger Toggle (Klickdummy-Muster, Marco 14.07.) ---- */
.pp-rez { position: absolute; top: 0; bottom: 0; width: 7px; z-index: 5; cursor: col-resize; background: transparent; }
.pp-rez--left { left: -3.5px; }
.pp-rez.is-collapsed { cursor: default; }
.pp-rez::before { content: ""; position: absolute; top: 0; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 1px; background: var(--pp-border-default);
  transition: background-color var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-rez:hover::before { background: var(--pp-brand-primary); }
.pp-rez.is-collapsed:hover::before { background: var(--pp-border-default); }
.pp-rez__tog { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 16px; height: 34px; padding: 0; display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-secondary);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-sm); cursor: pointer; z-index: 6; opacity: .5;
  transition: opacity var(--pp-duration-fast) var(--pp-ease-standard),
    color var(--pp-duration-fast) var(--pp-ease-standard),
    border-color var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-rez:hover .pp-rez__tog, .pp-rez__tog:hover { opacity: 1; }
.pp-rez__tog:hover { color: var(--pp-brand-primary); border-color: var(--pp-brand-primary); }
.pp-rez__tog:focus-visible { opacity: 1; outline: none; box-shadow: var(--pp-shadow-focus-ring); }
.pp-rez__tog :deep(svg) { width: 12px; height: 12px; display: block; }
</style>
