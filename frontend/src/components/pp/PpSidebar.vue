<!-- PP_REV: PpSidebar@8 -->
<!--
  PpSidebar.vue — vollständige App-Navigations-Sidebar (SSOT-Baustein).

  @3 (Nav-Umbau 2.0 / N3, Klickdummy-Handoff 13.07.2026): Aus dem reinen
  Collapse-Rahmen (@2) wird die KOMPLETTE Nav-Sidebar — Kopf = Modul-Dropdown,
  Körper = Modulmenü, darunter der getönte „Allgemein"-Teil + „Wissen"-Block.
  Das verbindliche Collapse-Muster [[collapse-pattern]] bleibt erhalten, ab @4
  im Klickdummy-Griff (Marco 14.07.2026 — löst den runden Kanten-Knopf
  `.pp-collapse-btn--edge` der Spez 04.07. ab):
    · GRIFF = schmale 7-px-Zieh-Leiste (col-resize) an der rechten Innenkante
      mit 1-px-Linie; mittig ein 16×34-Toggle-Knopf (Chevron je Zustand,
      opacity .5 → 1 bei Hover von Leiste/Knopf, Hover-Farbe Akzent).
    · BREITE EINSTELLBAR — Ziehen an der Leiste (min/max geklammert; unter das
      Minimum → klappt zu).
    · COLLAPSE AUF ICON-RAIL — Klick auf den Knopf; im Collapsed-Zustand bleibt
      der Knopf erreichbar (schmale Rail, nur Icons, Tooltips via title).

  @5 (Marco 15.07.2026): KEINE Status-Badges in der Navigation — das
  „bald"-Badge im Modul-Dropdown ist entfernt. Zustand/Status gehört
  ausschließlich in die Canvas (Status-Pille in der Überschrift) bzw. den
  Inspektor; SSOT dafür ist die Klickdummy-README §7 („Pille im Canvas").

  Aufbau (Spez Marco 13.07.2026):
    KOPF   Dropdown-Trigger: aktives Modul mit Icon; Panel = Hauptmodule der
           Zonen a + c, Trennlinie dazwischen, aktives Modul markiert (nie
           ausgeblendet), NIE Sub-Punkte.
    KÖRPER Bei Zone-a/c-Modulen fix „Dashboard" oben (aktiv beim Öffnen);
           dann die Modul-Items in Gruppen — Gruppen NUR per Trennlinie
           (nie Überschriften), Chevron-Collapse für sub:1/sub:2 (Standard
           eingeklappt, der Parent bleibt ein Link/klickbar).
    GETÖNT „Allgemein"-Block (Reihenfolge liefert der Host über `allgemein`);
           Trennlinie; „Wissen"-Block (`wissen`).
  Einfach-Selektion: genau EIN aktiver Punkt (v-model:activeKey).

  @7 (Klickdummy-Revision Marco 24.07.2026 — Regel 5):
    · CHEVRON-GRUPPE ÖFFNET, WENN PARENT ODER KIND AKTIV IST. Standard bleibt
      eingeklappt; sobald der Parent selbst oder ein (Enkel-)Kind der aktive
      Punkt ist, klappt die Gruppe automatisch auf (zusätzlich zum manuellen
      Chevron-Toggle). Umgesetzt über `groupOpen()` (manuell ODER enthält den
      aktiven Schlüssel) — greift für Modulmenü, Allgemein und Wissen.
    · SUB-EINRÜCKUNG NIE LINKS DES PARENT-TEXTS: Unterpunkte (Ebene 2/3) rücken
      auf die PARENT-TEXTKANTE (41 px = 16 px Padding + 16 px Icon + 9 px Gap)
      ein — sie sind ikonlos, sonst stünde der Text links des Parents. Dezente
      Führungslinie auf der Icon-Achse (~23 px) und leicht kleinere/gedämpfte
      Schrift.

  @6 (21.07.2026 — Klickdummy-Sync):
    · ZURÜCK-Zeile (Regel 3): schlichter Pfeil als eigene Zeile GANZ OBEN über dem
      Modul-Dropdown; Label = vorherige Station, ellipsiert (title=Volltext), darf
      NIE in den Canvas überlaufen (min-width:0/max-width:100%). Prop `back`, Emit `back`.
    · ICON-REGEL (Regel 10): Icons NUR auf Ebene 1. Chevron-Kinder (sub/sub2) haben
      KEIN Icon.
    · EINFACH-SELEKTION (Regel 10): jede hervorhebbare Zeile leitet „aktiv" aus dem
      EINEN Skalar `activeKey` ab — auch Modul-Verweise (News/Wissen) über den
      Sentinel `mod:<id>`. Damit nimmt ein Klick auf einen Allgemein-/Wissen-Punkt
      der Modul-/News-Zeile die Markierung ab (genau EIN aktiver Punkt).
    · LABEL-OVERRIDE: Prop `labelOverrides` ({ Original: Ersatz }) — z. B.
      „Terminpläne" → „Projektplan", wenn ein Projekt gewählt ist.

  ECHTE props-in / events-out — KEINE Attrappen, kein Store, kein Backend.
  Datenmodell = nav-v2 (zonen/module/allgemein/wissen); der Host reicht die
  Struktur durch und navigiert auf die Events.

  Props:
    modules   Array  nav-v2-Module: { id, name, icon, zone, status, target,
                      g:[{ sec, items:[{ n,t,k,x,sub,icon,d,q,app }] }] }
    zones     Array  [{ code, label }] — nur a + c erscheinen im Dropdown
    activeId  String (v-model)  aktives Modul (id)
    activeKey String (v-model)  aktiver Menüpunkt-Schlüssel; "dash" = Dashboard,
                      null = keiner
    allgemein Array  ANZEIGE-geordnete „Allgemein"-Einträge, jeder:
                      { label, icon?, target?, external?, planned?, app?, d?,
                        key?, children?:[ …gleiche Form ] }
    wissen    Array  ANZEIGE-geordneter „Wissen"-Block (gleiche Form)
    generalTitle  String  Getönter-Block-Titel (default "Allgemein")
    iconResolver  Function (nameOrKeyword) => Icon-Komponente | null
    collapsed, width, minWidth, maxWidth, railWidth, resizable  (Collapse-Muster)
    drawer     Boolean  Mobile-Off-Canvas-Modus (Drawer + Scrim)
    mobileOpen Boolean (v-model)  Drawer offen (nur bei drawer=true)

  Emits:
    update:collapsed, update:width, update:activeId, update:activeKey,
    update:mobileOpen
    navigate  { type:'module'|'item'|'dashboard', id?, key?, item? }
    inspect   item | null   (füttert PpInspector; Modulwechsel → null)
-->
<script setup>
import { ref, computed, reactive, watch, onBeforeUnmount } from "vue";
import ChevronLeft from "~icons/lucide/chevron-left";
import ChevronRight from "~icons/lucide/chevron-right";
import ChevronDown from "~icons/lucide/chevron-down";
import CircleDot from "~icons/lucide/circle-dot";

const props = defineProps({
  modules:   { type: Array, default: () => [] },
  zones:     { type: Array, default: () => [] },
  activeId:  { type: String, default: "" },
  activeKey: { type: [String, null], default: null },
  allgemein: { type: Array, default: () => [] },
  wissen:    { type: Array, default: () => [] },
  generalTitle: { type: String, default: "Allgemein" },
  iconResolver: { type: Function, default: null },
  back:          { type: [Object, null], default: null },   // { label, full? } | null
  labelOverrides:{ type: Object, default: () => ({}) },      // { Original: Ersatz }

  collapsed: { type: Boolean, default: false },
  width:     { type: Number, default: 256 },
  minWidth:  { type: Number, default: 170 },
  maxWidth:  { type: Number, default: 440 },
  railWidth: { type: Number, default: 56 },
  resizable: { type: Boolean, default: true },

  drawer:     { type: Boolean, default: false },
  mobileOpen: { type: Boolean, default: false },
});
const emit = defineEmits([
  "update:collapsed", "update:width", "update:activeId", "update:activeKey",
  "update:mobileOpen", "navigate", "inspect", "back",
]);

/* Label-Kürzung „… letzte Worte" (wie crumbCut im Klickdummy) — für die
   Zurück-Zeile; der Volltext bleibt im title. */
function crumbCut(t, n) {
  t = String(t || ""); n = n || 34;
  if (t.length <= n) return t;
  const tail = t.slice(t.length - (n - 2));
  const sp = tail.indexOf(" ");
  return "… " + (sp > 0 && sp < 14 ? tail.slice(sp + 1) : tail);
}

/* ---------- Icons ---------- */
function resolveIcon(item) {
  if (item && item.icon && typeof item.icon !== "string") return item.icon; // schon Komponente
  const name = (item && (item.icon || item.n || item.label)) || "";
  const r = props.iconResolver ? props.iconResolver(name) : null;
  return r || CircleDot;
}

/* ---------- Breite / Collapse (bestehendes Pattern) ---------- */
const w = ref(props.width);
watch(() => props.width, (v) => (w.value = v));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const dragging = ref(false);
let sx = 0, sw = 0;
function startResize(e) {
  if (!props.resizable || props.collapsed || props.drawer) return;   // nur ziehbar wenn ausgeklappt
  dragging.value = true; sx = e.clientX; sw = w.value;
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", endResize);
  e.preventDefault();
}
function onMove(e) {
  const nw = sw + (e.clientX - sx);
  if (nw < props.minWidth - 28) { endResize(); emit("update:collapsed", true); return; }
  w.value = clamp(nw, props.minWidth, props.maxWidth);
  emit("update:width", w.value);
}
function endResize() {
  window.removeEventListener("pointermove", onMove);
  window.removeEventListener("pointerup", endResize);
  dragging.value = false;
}
onBeforeUnmount(endResize);

/* ---------- Dropdown ---------- */
const ddOpen = ref(false);
const activeModule = computed(() => props.modules.find((m) => m.id === props.activeId) || props.modules[0] || null);
const dropdownZones = computed(() =>
  props.zones
    .filter((z) => z.code === "a" || z.code === "c")
    .map((z) => ({ ...z, items: props.modules.filter((m) => m.zone === z.code) }))
    .filter((z) => z.items.length)
);
function toggleDD() { ddOpen.value = !ddOpen.value; }
function pickModule(m) {
  ddOpen.value = false;
  if (m.id === props.activeId) return;
  emit("update:activeId", m.id);
  const key = (m.zone === "a" || m.zone === "c") ? "dash" : null;
  emit("update:activeKey", key);
  emit("inspect", null);           // Modulwechsel → Spezifikation einklappen
  emit("navigate", { type: "module", id: m.id });
}

/* ---------- Modulmenü: Baum aus sub-Ebenen (portiert aus dem Klickdummy) ---------- */
const hasDashboard = computed(() => {
  const z = activeModule.value && activeModule.value.zone;
  return z === "a" || z === "c";
});

/* Baut je Gruppe die verschachtelte Struktur nach sub-Level:
   sub:1 = Kind des vorangehenden Level-0, sub:2 = Kind des vorangehenden Level-1.
   Parent bleibt eigenständiger Link. Rückgabe: [{ key, item, children:[…] }]. */
function buildTree(items, gi) {
  const rows = items.map((it, ii) => ({ it, key: gi + "-" + ii }));
  const out = [];
  for (let j = 0; j < rows.length; j++) {
    const x = rows[j];
    if (x.it.sub) continue;                       // Kind — beim Parent eingesammelt
    const kids = [];
    let kk = j + 1;
    while (kk < rows.length && rows[kk].it.sub) { kids.push(rows[kk]); kk++; }
    const children = [];
    for (let a = 0; a < kids.length; a++) {
      const k1 = kids[a];
      if ((k1.it.sub || 0) >= 2) continue;        // Level-2 beim Level-1 eingesammelt
      const g2 = [];
      let b = a + 1;
      while (b < kids.length && (kids[b].it.sub || 0) >= 2) { g2.push(kids[b]); b++; }
      children.push({ key: k1.key, item: k1.it, children: g2.map((c) => ({ key: c.key, item: c.it, children: [] })) });
    }
    out.push({ key: x.key, item: x.it, children });
  }
  return out;
}
const menuGroups = computed(() => {
  const m = activeModule.value;
  if (!m || !Array.isArray(m.g)) return [];
  return m.g
    .map((g, gi) => ({ sec: g.sec, tree: buildTree(g.items || [], gi) }))
    .filter((g) => g.tree.length);
});

/* ---------- Allgemein / Wissen: Host liefert ANZEIGE-Struktur mit children ---------- */
let _auto = 0;
function normGeneral(list, prefix) {
  return (list || []).map((it) => {
    const key = it.key || (prefix + "-" + (_auto++));
    return {
      key, item: it,
      children: (it.children || []).map((c) => ({ key: c.key || (prefix + "-" + (_auto++)), item: c, children: [] })),
    };
  });
}
const allgemeinTree = computed(() => { _auto = 0; return normGeneral(props.allgemein, "a"); });
const wissenTree    = computed(() => normGeneral(props.wissen, "w"));

/* ---------- Chevron-Collapse (Standard eingeklappt) ---------- */
const expanded = reactive({});
function toggleGroup(key) { expanded[key] = !expanded[key]; }
const isExpanded = (key) => !!expanded[key];

/* @7 (Regel 5): Gruppe ist offen, wenn sie manuell aufgeklappt wurde ODER der
   Parent bzw. ein (Enkel-)Kind der aktive Punkt ist. `keyActive` (weiter unten,
   Funktionsdeklaration → hoisted) deckt Item-Keys und Modul-Verweise ab. */
function containsActive(node) {
  if (keyActive(node)) return true;
  return (node.children || []).some((c) => containsActive(c));
}
function groupOpen(node) { return isExpanded(node.key) || containsActive(node); }

/* ---------- Auswahl / Navigation ---------- */
function selectDashboard() {
  emit("update:activeKey", "dash");
  emit("inspect", null);
  emit("navigate", { type: "dashboard", id: props.activeId });
}
function selectItem(node) {
  emit("update:activeKey", node.key);
  emit("inspect", node.item);                    // Spezifikation füllen
  emit("navigate", { type: "item", key: node.key, item: node.item });
  if (props.drawer) emit("update:mobileOpen", false);
}
function selectModuleItem(id) {                   // Modul-Verweis im Allgemein/Wissen (z.B. „News")
  emit("update:activeId", id);
  // Einfach-Selektion: der Verweis ist selbst der EINE aktive Punkt (Sentinel).
  emit("update:activeKey", "mod:" + id);
  emit("inspect", null);
  emit("navigate", { type: "module", id });
  if (props.drawer) emit("update:mobileOpen", false);
}

/* Aktiv-Zustand IMMER aus dem einen Skalar activeKey (Einfach-Selektion): ein
   Modul-Verweis (moduleId) über den Sentinel, sonst über den Zeilen-Key. */
function keyActive(node) {
  return node.item && node.item.moduleId
    ? props.activeKey === "mod:" + node.item.moduleId
    : props.activeKey === node.key;
}

/* Label + optionaler Override (z. B. „Terminpläne" → „Projektplan"). */
const itemTitle = (it) => {
  const base = it.n || it.label || "";
  return props.labelOverrides[base] || base;
};
</script>

<template>
  <div v-if="drawer && mobileOpen" class="pp-sidebar__scrim" @click="emit('update:mobileOpen', false)"></div>
  <aside class="pp-sidebar" :class="{ 'is-collapsed': collapsed && !drawer, 'is-resizing': dragging,
           'is-drawer': drawer, 'is-open': drawer && mobileOpen }"
         :style="{ width: drawer ? null : ((collapsed ? railWidth : w) + 'px') }"
         aria-label="Navigation">

    <!-- ZURÜCK-Zeile (Regel 3): schlichter Pfeil, Label = vorherige Station,
         ellipsiert; läuft NIE in den Canvas über. -->
    <div v-if="back && !collapsed" class="pp-sidebar__back">
      <button type="button" class="pp-back" @click="emit('back')" :title="back.full || back.label">
        <ChevronLeft class="pp-back__ic" />
        <span class="pp-back__lbl">{{ crumbCut(back.label, 28) }}</span>
      </button>
    </div>

    <!-- KOPF: Modul-Dropdown (nur im nav-v2-Modus) -->
    <div v-if="modules.length" class="pp-sidebar__head">
      <div class="pp-nav-dd" :class="{ 'is-open': ddOpen }">
        <button class="pp-nav-dd__trigger" type="button" :aria-expanded="ddOpen"
                :title="collapsed ? (activeModule && activeModule.name) : null"
                @click="toggleDD">
          <span class="pp-nav-dd__icon"><component :is="resolveIcon(activeModule || {})" /></span>
          <span v-if="!collapsed" class="pp-nav-dd__name">{{ activeModule ? activeModule.name : "…" }}</span>
          <span v-if="!collapsed" class="pp-nav-dd__caret" aria-hidden="true"><ChevronDown /></span>
        </button>
        <template v-if="ddOpen">
          <div class="pp-nav-dd__backdrop" @click="ddOpen = false"></div>
          <div class="pp-nav-dd__panel" role="listbox" aria-label="Modul wählen">
            <template v-for="(z, zi) in dropdownZones" :key="z.code">
              <div v-if="zi > 0" class="pp-nav__sep"></div>
              <button v-for="m in z.items" :key="m.id" type="button" role="option"
                      class="pp-nav-dd__item" :class="{ 'is-active': m.id === activeId }"
                      :aria-selected="m.id === activeId" @click="pickModule(m)">
                <span class="pp-nav__ic"><component :is="resolveIcon(m)" /></span>
                <span class="pp-nav-dd__item-name">{{ m.name }}</span>
              </button>
            </template>
          </div>
        </template>
      </div>
    </div>

    <!-- KÖRPER: Modulmenü + Allgemein + Wissen; ohne nav-v2-Daten = Host-Slot (Legacy) -->
    <div class="pp-sidebar__body">
      <slot v-if="!modules.length" :collapsed="collapsed" />
      <template v-else>
      <!-- fixes Dashboard je a/c-Modul -->
      <template v-if="hasDashboard">
        <button type="button" class="pp-nav__item" :class="{ 'is-active': activeKey === 'dash' }"
                title="Dashboard" @click="selectDashboard">
          <span class="pp-nav__ic"><component :is="resolveIcon({ icon: 'layout-dashboard' })" /></span>
          <span class="pp-nav__label">Dashboard</span>
        </button>
        <div class="pp-nav__sep"></div>
      </template>

      <!-- Modul-Gruppen: nur Trennlinien (keine Überschriften) -->
      <template v-for="(g, gi) in menuGroups" :key="gi">
        <div v-if="gi > 0" class="pp-nav__sep"></div>
        <template v-for="node in g.tree" :key="node.key">
          <!-- Parent mit Kindern: Zeile bleibt Link + Chevron-Toggle daneben -->
          <div v-if="node.children.length" class="pp-nav__group" :class="{ 'is-open': groupOpen(node) }">
            <div class="pp-nav__item pp-nav__item--parent" :class="{ 'is-active': activeKey === node.key }">
              <button type="button" class="pp-nav__row" :title="itemTitle(node.item)" @click="selectItem(node)">
                <span class="pp-nav__ic"><component :is="resolveIcon(node.item)" /></span>
                <span class="pp-nav__label">{{ itemTitle(node.item) }}</span>
              </button>
              <button type="button" class="pp-nav__chev" :aria-expanded="groupOpen(node)"
                      :aria-label="groupOpen(node) ? 'einklappen' : 'ausklappen'"
                      @click.stop="toggleGroup(node.key)"><ChevronDown /></button>
            </div>
            <div v-show="groupOpen(node)" class="pp-nav__children">
              <template v-for="c in node.children" :key="c.key">
                <div v-if="c.children.length" class="pp-nav__group" :class="{ 'is-open': groupOpen(c) }">
                  <div class="pp-nav__item pp-nav__item--parent pp-nav__item--sub" :class="{ 'is-active': activeKey === c.key }">
                    <button type="button" class="pp-nav__row" :title="itemTitle(c.item)" @click="selectItem(c)">
                      <!-- Icon-Regel: Chevron-Kinder (sub) tragen KEIN Icon -->
                      <span class="pp-nav__label">{{ itemTitle(c.item) }}</span>
                    </button>
                    <button type="button" class="pp-nav__chev" :aria-expanded="groupOpen(c)"
                            :aria-label="groupOpen(c) ? 'einklappen' : 'ausklappen'"
                            @click.stop="toggleGroup(c.key)"><ChevronDown /></button>
                  </div>
                  <div v-show="groupOpen(c)" class="pp-nav__children">
                    <button v-for="d in c.children" :key="d.key" type="button"
                            class="pp-nav__item pp-nav__item--sub2" :class="{ 'is-active': activeKey === d.key }"
                            :title="itemTitle(d.item)" @click="selectItem(d)">
                      <span class="pp-nav__label">{{ itemTitle(d.item) }}</span>
                    </button>
                  </div>
                </div>
                <button v-else type="button" class="pp-nav__item pp-nav__item--sub"
                        :class="{ 'is-active': activeKey === c.key }" :title="itemTitle(c.item)" @click="selectItem(c)">
                  <span class="pp-nav__label">{{ itemTitle(c.item) }}</span>
                </button>
              </template>
            </div>
          </div>
          <!-- Blatt ohne Kinder -->
          <button v-else type="button" class="pp-nav__item" :class="{ 'is-active': activeKey === node.key }"
                  :title="itemTitle(node.item)" @click="selectItem(node)">
            <span class="pp-nav__ic"><component :is="resolveIcon(node.item)" /></span>
            <span class="pp-nav__label">{{ itemTitle(node.item) }}</span>
          </button>
        </template>
      </template>

      <!-- Getönter Allgemein-Teil -->
      <div v-if="allgemeinTree.length || wissenTree.length" class="pp-nav__sep"></div>
      <div v-if="allgemeinTree.length || wissenTree.length" class="pp-sidebar__general">
        <template v-for="node in allgemeinTree" :key="node.key">
          <div v-if="node.children.length" class="pp-nav__group" :class="{ 'is-open': groupOpen(node) }">
            <div class="pp-nav__item pp-nav__item--parent">
              <button type="button" class="pp-nav__row" :title="itemTitle(node.item)"
                      @click="node.item.moduleId ? selectModuleItem(node.item.moduleId) : selectItem(node)">
                <span class="pp-nav__ic"><component :is="resolveIcon(node.item)" /></span>
                <span class="pp-nav__label">{{ itemTitle(node.item) }}</span>
                <span v-if="node.children.length" class="pp-nav__count">{{ node.children.length }}</span>
              </button>
              <button type="button" class="pp-nav__chev" :aria-expanded="groupOpen(node)"
                      :aria-label="groupOpen(node) ? 'einklappen' : 'ausklappen'"
                      @click.stop="toggleGroup(node.key)"><ChevronDown /></button>
            </div>
            <div v-show="groupOpen(node)" class="pp-nav__children">
              <button v-for="c in node.children" :key="c.key" type="button"
                      class="pp-nav__item pp-nav__item--sub" :class="{ 'is-active': keyActive(c) }"
                      :title="itemTitle(c.item)" @click="c.item.moduleId ? selectModuleItem(c.item.moduleId) : selectItem(c)">
                <span class="pp-nav__label">{{ itemTitle(c.item) }}</span>
              </button>
            </div>
          </div>
          <button v-else type="button" class="pp-nav__item"
                  :class="{ 'is-active': keyActive(node) }"
                  :title="itemTitle(node.item)" @click="node.item.moduleId ? selectModuleItem(node.item.moduleId) : selectItem(node)">
            <span class="pp-nav__ic"><component :is="resolveIcon(node.item)" /></span>
            <span class="pp-nav__label">{{ itemTitle(node.item) }}</span>
          </button>
        </template>

        <template v-if="wissenTree.length">
          <div class="pp-nav__sep"></div>
          <template v-for="node in wissenTree" :key="node.key">
            <div v-if="node.children.length" class="pp-nav__group" :class="{ 'is-open': groupOpen(node) }">
              <div class="pp-nav__item pp-nav__item--parent">
                <button type="button" class="pp-nav__row" :title="itemTitle(node.item)"
                        @click="node.item.moduleId ? selectModuleItem(node.item.moduleId) : selectItem(node)">
                  <span class="pp-nav__ic"><component :is="resolveIcon(node.item)" /></span>
                  <span class="pp-nav__label">{{ itemTitle(node.item) }}</span>
                </button>
                <button type="button" class="pp-nav__chev" :aria-expanded="groupOpen(node)"
                        :aria-label="groupOpen(node) ? 'einklappen' : 'ausklappen'"
                        @click.stop="toggleGroup(node.key)"><ChevronDown /></button>
              </div>
              <div v-show="groupOpen(node)" class="pp-nav__children">
                <button v-for="c in node.children" :key="c.key" type="button"
                        class="pp-nav__item pp-nav__item--sub"
                        :class="{ 'is-active': keyActive(c) }"
                        :title="itemTitle(c.item)" @click="c.item.moduleId ? selectModuleItem(c.item.moduleId) : selectItem(c)">
                  <span class="pp-nav__label">{{ itemTitle(c.item) }}</span>
                </button>
              </div>
            </div>
            <button v-else type="button" class="pp-nav__item"
                    :class="{ 'is-active': keyActive(node) }" :title="itemTitle(node.item)"
                    @click="node.item.moduleId ? selectModuleItem(node.item.moduleId) : selectItem(node)">
              <span class="pp-nav__ic"><component :is="resolveIcon(node.item)" /></span>
              <span class="pp-nav__label">{{ itemTitle(node.item) }}</span>
            </button>
          </template>
        </template>
      </div>
      </template>
    </div>

    <!-- Griff: Zieh-Leiste (Breite) + mittiger Toggle (Collapse) — [[collapse-pattern]] -->
    <div v-if="!drawer" class="pp-rez pp-rez--right" :class="{ 'is-collapsed': collapsed }"
         :title="resizable && !collapsed ? 'Breite ziehen' : null" @pointerdown="startResize">
      <button class="pp-rez__tog" type="button"
              @pointerdown.stop @click="emit('update:collapsed', !collapsed)"
              :title="collapsed ? 'Navigation ausklappen' : 'Navigation einklappen'"
              :aria-label="collapsed ? 'Navigation ausklappen' : 'Navigation einklappen'"
              :aria-expanded="!collapsed">
        <ChevronRight v-if="collapsed" /><ChevronLeft v-else />
      </button>
    </div>
  </aside>
</template>

<style scoped>
.pp-sidebar { position: relative; flex: 0 0 auto; box-sizing: border-box; height: 100%;
  display: flex; flex-direction: column; min-height: 0; overflow: visible;
  background: var(--pp-bg-surface); border-right: 1px solid var(--pp-border-default);
  transition: width var(--pp-duration-base) var(--pp-ease-standard); }
.pp-sidebar.is-resizing { transition: none; }

/* ---- Zurück-Zeile (@6) — läuft NIE über: min-width:0 + Ellipsis ---- */
.pp-sidebar__back { flex: 0 0 auto; display: flex; align-items: center;
  padding: var(--pp-space-2) var(--pp-space-2) 0; min-width: 0; max-width: 100%; overflow: hidden; }
.pp-back { flex: 1 1 auto; min-width: 0; max-width: 100%; overflow: hidden;
  appearance: none; cursor: pointer; font-family: inherit; height: 30px;
  display: flex; align-items: center; gap: 7px; padding: 0 var(--pp-space-2);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); color: var(--pp-text-secondary); text-align: left; }
.pp-back:hover { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.pp-back__ic { width: 15px; height: 15px; flex: 0 0 auto; }
.pp-back__lbl { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-semibold); }

.pp-sidebar__head { flex: 0 0 auto; padding: var(--pp-space-2); border-bottom: 1px solid var(--pp-border-subtle); }
.pp-sidebar__body { flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden;
  padding: var(--pp-space-1) var(--pp-space-2) var(--pp-space-3);
  scrollbar-width: none; -ms-overflow-style: none; }
.pp-sidebar__body::-webkit-scrollbar { width: 0; height: 0; display: none; }

/* ---- Dropdown ---- */
.pp-nav-dd { position: relative; }
.pp-nav-dd__trigger { appearance: none; cursor: pointer; font-family: inherit;
  display: flex; align-items: center; gap: var(--pp-space-2); width: 100%;
  padding: var(--pp-space-2) var(--pp-space-3);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface);
  color: var(--pp-text-primary); font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold);
  border-radius: var(--pp-radius-ui);
  transition: border-color var(--pp-duration-fast) var(--pp-ease-standard), box-shadow var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-nav-dd__trigger:hover { border-color: var(--pp-border-strong); }
.pp-nav-dd.is-open .pp-nav-dd__trigger { border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px var(--pp-accent-soft); }
.pp-nav-dd__icon { display: inline-flex; flex: 0 0 auto; }
.pp-nav-dd__icon :deep(svg) { width: 18px; height: 18px; color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.pp-nav-dd__name { flex: 1 1 auto; text-align: left; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-nav-dd__caret { flex: 0 0 auto; color: var(--pp-text-secondary); display: inline-flex;
  transition: transform var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-nav-dd__caret :deep(svg) { width: 15px; height: 15px; }
.pp-nav-dd.is-open .pp-nav-dd__caret { transform: rotate(180deg); }
.pp-nav-dd__backdrop { position: fixed; inset: 0; z-index: var(--pp-z-overlay); }
.pp-nav-dd__panel { position: absolute; top: calc(100% + var(--pp-space-1)); left: 0; right: 0;
  z-index: calc(var(--pp-z-overlay) + 1); max-height: 62vh; overflow-y: auto; padding: var(--pp-space-1);
  background: var(--pp-bg-elevated); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-lg);
  scrollbar-width: none; }
.pp-nav-dd__panel::-webkit-scrollbar { width: 0; display: none; }
.pp-nav-dd__item { appearance: none; cursor: pointer; font-family: inherit; text-align: left; width: 100%;
  display: flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-1) var(--pp-space-2); border: 0; background: transparent;
  color: var(--pp-text-primary); font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium);
  border-radius: var(--pp-radius-xs); }
.pp-nav-dd__item:hover { background: var(--pp-bg-hover); }
.pp-nav-dd__item.is-active { background: var(--pp-accent-soft); color: var(--pp-brand-primary-d, var(--pp-brand-primary)); cursor: default; }
.pp-nav-dd__item-name { flex: 1 1 auto; }

/* ---- Menü-Items ---- */
.pp-nav__item { appearance: none; cursor: pointer; font-family: inherit; text-align: left; width: 100%;
  display: flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-2) var(--pp-space-2) var(--pp-space-2) var(--pp-space-3);
  border: 0; background: transparent; color: var(--pp-text-primary);
  font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-medium);
  border-radius: var(--pp-radius-ui); position: relative;
  transition: background var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-nav__item:hover { background: var(--pp-bg-hover); }
.pp-nav__item.is-active { background: var(--pp-accent-soft); color: var(--pp-brand-primary-d, var(--pp-brand-primary)); font-weight: var(--pp-weight-semibold); }
.pp-nav__item.is-active::before { content: ""; position: absolute; left: -2px; top: 5px; bottom: 5px; width: 3px;
  background: var(--pp-brand-primary); border-radius: 0 3px 3px 0; }
.pp-nav__ic { display: inline-flex; flex: 0 0 auto; }
.pp-nav__ic :deep(svg) { width: 18px; height: 18px; color: currentColor; opacity: .9; }
.pp-nav__item.is-active .pp-nav__ic :deep(svg) { opacity: 1; }
.pp-nav__label { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-nav__count { flex: 0 0 auto; font-size: 10px; font-weight: var(--pp-weight-bold);
  color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }

/* Parent-Zeile mit Chevron */
.pp-nav__item--parent { padding-right: var(--pp-space-1); gap: 0; }
.pp-nav__row { appearance: none; cursor: pointer; font: inherit; text-align: left; color: inherit;
  flex: 1 1 auto; min-width: 0; display: flex; align-items: center; gap: var(--pp-space-2);
  border: 0; background: transparent; padding: 0; }
.pp-nav__chev { appearance: none; cursor: pointer; flex: 0 0 auto; display: inline-flex; align-items: center;
  border: 0; background: transparent; padding: 2px; border-radius: var(--pp-radius-xs); color: var(--pp-text-tertiary); }
.pp-nav__chev:hover { color: var(--pp-brand-primary-d, var(--pp-brand-primary)); background: var(--pp-bg-hover); }
.pp-nav__chev :deep(svg) { width: 13px; height: 13px; transition: transform var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-nav__group.is-open > .pp-nav__item--parent .pp-nav__chev :deep(svg) { transform: rotate(180deg); }
/* @7 Regel 5: Unterpunkte rücken auf die PARENT-TEXTKANTE ein (Padding + Icon +
   Gap) — nie weiter links als der Parent-Text. Führungslinie auf der Icon-Achse. */
.pp-nav__children { display: block; position: relative; }
.pp-nav__children::before { content: ""; position: absolute; top: 2px; bottom: 2px;
  left: calc(var(--pp-space-3) + 7px); width: 1px; background: var(--pp-border-subtle); }

.pp-nav__item--sub,
.pp-nav__item--sub2 { font-size: var(--pp-fs-13, 13px); }
.pp-nav__item--sub  .pp-nav__label,
.pp-nav__item--sub2 .pp-nav__label { color: var(--pp-text-secondary); }
.pp-nav__item--sub.is-active  .pp-nav__label,
.pp-nav__item--sub2.is-active .pp-nav__label { color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
/* Textkante des Parents = Padding-links (space-3) + Icon (16px) + Gap (space-2). */
.pp-nav__item--sub  { padding-left: calc(var(--pp-space-3) + 16px + var(--pp-space-2)); }
.pp-nav__item--sub2 { padding-left: calc(var(--pp-space-3) + 16px + var(--pp-space-2) + var(--pp-space-4)); }
.pp-nav__item--parent.pp-nav__item--sub { padding-left: calc(var(--pp-space-3) + 16px + var(--pp-space-2)); }

/* Trennlinie statt Überschrift */
.pp-nav__sep { height: 1px; margin: var(--pp-space-2) var(--pp-space-2); background: var(--pp-border-subtle); }

/* Getönter Allgemein-Teil */
.pp-sidebar__general { margin-top: var(--pp-space-1); padding: var(--pp-space-2) var(--pp-space-1) var(--pp-space-2);
  border-radius: var(--pp-radius-ui); background: color-mix(in oklab, var(--pp-text-primary) 5%, transparent); }
.pp-sidebar__general .pp-nav__sep { background: color-mix(in oklab, var(--pp-text-primary) 9%, transparent); }

/* ---- Icon-Rail (collapsed) ---- */
.pp-sidebar.is-collapsed .pp-nav-dd__trigger { justify-content: center; padding: var(--pp-space-2) 0; }
.pp-sidebar.is-collapsed .pp-nav__item,
.pp-sidebar.is-collapsed .pp-nav__item--parent { justify-content: center; padding-left: 0; padding-right: 0; gap: 0; }
.pp-sidebar.is-collapsed .pp-nav__label,
.pp-sidebar.is-collapsed .pp-nav__count,
.pp-sidebar.is-collapsed .pp-nav__chev { display: none; }
.pp-sidebar.is-collapsed .pp-nav__row { justify-content: center; }
.pp-sidebar.is-collapsed .pp-nav__children { display: none; }        /* Rail zeigt nur Ebene 1 */
.pp-sidebar.is-collapsed .pp-nav__item.is-active::before { left: 0; }
.pp-sidebar.is-collapsed .pp-sidebar__general { background: transparent; }

/* ---- Mobile-Drawer ---- */
.pp-sidebar.is-drawer { position: fixed; top: 0; bottom: 0; left: 0; z-index: var(--pp-z-modal);
  width: min(86%, 330px); transform: translateX(-100%);
  transition: transform var(--pp-duration-base) var(--pp-ease-decelerate);
  box-shadow: var(--pp-shadow-xl); }
.pp-sidebar.is-drawer.is-open { transform: none; }
.pp-sidebar__scrim { position: fixed; inset: 0; z-index: calc(var(--pp-z-modal) - 1);
  background: rgb(var(--pp-shadow-deep-rgb) / .4);
  -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); }

/* ---- Griff: Zieh-Leiste + mittiger Toggle (Klickdummy-Muster, Marco 14.07.) ---- */
.pp-rez { position: absolute; top: 0; bottom: 0; width: 7px; z-index: 5; cursor: col-resize; background: transparent; }
.pp-rez--right { right: -3.5px; }
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
