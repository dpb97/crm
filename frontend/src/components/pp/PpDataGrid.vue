<!-- PP_REV: PpDataGrid@6 -->
<!--
  PpDataGrid.vue — erweiterte, wiederverwendbare Datentabelle (List-Ansichten/
  Reports). Ersetzt spaeter statische Tabellen.

  ECHTE props-in / events-out Komponente — kein Store, kein Backend.

  @6 (26.07.2026, Konsistenz-Sweep F24 — „gleiche Dinge immer gleich" + neuer
  Picker-Vertrag Marco):
    (a) COLCHOOSER-KONSUM: der frühere EIGENE Spalten-Wähler
      (`pp-datagrid__colmenu`) ist ersetzt durch Konsum des gemeinsamen
      Bausteins PpColChooser (EIN Spalten-Wähler stack-weit). `columnTools`
      rendert jetzt die PpColChooser-Pille „Spalten"; Sichtbarkeit + DnD-
      Reihenfolge laufen über dessen Events. Optik/Bedienung identisch zu Gantt.
    (b) PICKER-VERTRAG: die Picker-Spalte ist DEFAULT AUS. `pickable` schaltet
      die FÄHIGKEIT frei; die Aktivierung steuert der Verbraucher über die neue
      v-model-Prop `pickMode` (Toggle „Auswählen" gehört in die Funktionsbar-
      Werkzeuge des Verbrauchers). Im Picker-Modus ist die GANZE Zeile
      Auswahlfläche (Klick auf Zeile ODER Checkbox wählt); der `row-click`-Emit
      (Inspektor-Selektion) PAUSIERT im Picker-Modus, `row-dblclick` bleibt.
      `picked` v-model + Zähler unverändert. Voll rückwärtskompatibel:
      Verbraucher ohne `pickMode` verhalten sich wie bisher (Picker bleibt aus).

  @5 (26.07.2026, Marco A2 — Klickdummy Listen-Picker `wireListPick`/
  `enhancePickTable`): ADDITIV, voll rueckwaertskompatibel (alle Verbraucher
  unveraendert — neue Props optional, default aus).
    · `pickable` + v-model `picked` (Array<id>): KONTROLLIERTE Picker-Spalte GANZ
      LINKS (Checkboxen). Kopf-Checkbox = alle an/aus (indeterminate bei Teil-
      auswahl), dezenter Zaehler im Kopf, ausgewaehlte Zeilen dezent markiert
      (`.pp-datagrid__row--picked`). Abgrenzung zu `selectable`: `selectable` ist
      die LEGACY-Variante mit INTERNEM Auswahlzustand + Bulk-Leiste (emit
      update:selection); `pickable` ist die kontrollierte Klickdummy-Parity, deren
      Auswahl der Host per v-model haelt (z. B. um kontextabhaengige Aktionen in
      die Funktionsbar zu injizieren). Nur EINE der beiden je Tabelle nutzen.
    · Emit `row-dblclick`(id): Doppelklick auf eine Datenzeile (Doppelklick-Detail-
      regel). Ohne Listener wirkungslos.

  @4 (23.07.2026): Spalten koennen mit `hidden: true` STANDARDMAESSIG
  ausgeblendet starten und werden ueber den Spalten-Chooser (`columnTools`)
  eingeblendet — nachgezogen aus dem Klickdummy-Artikelstamm (Batch V:
  Beschreibung/Zolltarifnummer/Preis/Lieferant/Bestand). „Zuruecksetzen" stellt
  den initialen Sichtbarkeitszustand wieder her. RUECKWAERTSKOMPATIBEL: ohne
  `hidden` starten alle Spalten sichtbar wie @3.

  Props:
    columns     Array<{ key, label, align?, group?, agg?, width?, pin?, hidden? }>
                · align 'left'|'right'|'center' (default 'left')
                · group  optionaler Spaltengruppen-Name → gemeinsame Uebergruppen-Kopfzeile
                · agg    'sum'|'avg' → Summen-/Schnitt-Fusszeile fuer diese Spalte
                · width  px-Zahl (feste Spaltenbreite)
                · pin    true → Spalte links fixiert (sticky)
                · hidden true → Spalte initial ausgeblendet (per Chooser einblendbar)
    rows        Array<{ id, [key]: value, _children?: Array<row> }>
    groupBy     String (optional column.key) — Zeilen werden gruppiert (Gruppenkopf)
    selectable  Boolean (default false) — Auswahl-Checkboxen + Select-all + Bulk-Leiste
    expandable  Boolean (default false) — Zeilen mit _children bekommen Aufklapp-Chevron

  Emits:
    row-click          (id)
    update:selection   (Array<id>)
    toggle-expand      (id)

  Slots (@3):
    #cell-<colKey>   Zell-Renderer je Spalte (benannt nach column.key).
                     Slot-Props { row, value, col }. Gilt fuer Datenzeilen
                     UND Detail-Unterzeilen (dort row = das Kind).
                     OHNE Slot exakt bisheriges Text-Rendering (fmt()) —
                     voll rueckwaertskompatibel. Fuer Ampel-Punkte,
                     Fortschrittsbalken, Links etc.

  STRIKT --pp-*-Tokens, hell + dunkel. Scoped, Prefix `pp-datagrid`.
-->
<script setup>
import { ref, computed, onBeforeUnmount } from "vue";
import ChevronUp    from "~icons/lucide/chevron-up";
import ChevronDown  from "~icons/lucide/chevron-down";
import ChevronsUpDown from "~icons/lucide/chevrons-up-down";
import ChevronRight from "~icons/lucide/chevron-right";
import X            from "~icons/lucide/x";
import PpColChooser from "./PpColChooser.vue";

const props = defineProps({
  columns:    { type: Array,   default: () => [] },
  rows:       { type: Array,   default: () => [] },
  groupBy:    { type: String,  default: "" },
  selectable: { type: Boolean, default: false },
  expandable: { type: Boolean, default: false },
  columnTools:{ type: Boolean, default: true },  // @7: Spaltenauswahl-Toolbar (Sichtbarkeit) — jetzt STANDARD AN
  chooserKeys:{ type: Array,   default: null },  // @4: Chooser auf diese keys begrenzen (null = alle Spalten)
  reorderable:{ type: Boolean, default: true },  // @7: Spaltenreihenfolge per Drag and Drop — jetzt STANDARD AN
  resizable:  { type: Boolean, default: false }, // Spaltenbreite per Ziehen am Rand
  filterable: { type: Boolean, default: true },  // @7: Spaltenfilter je Spalte (Filterzeile) — STANDARD AN
  pickable:   { type: Boolean, default: false }, // @5: kontrollierte Picker-Spalte links (v-model:picked)
  picked:     { type: Array,   default: () => [] }, // @5: ausgewaehlte ids (kontrolliert)
  pickMode:   { type: Boolean, default: false }, // @6: Picker-Modus an/aus (v-model, DEFAULT AUS)
});
const emit = defineEmits(["row-click", "update:selection", "toggle-expand", "update:picked", "update:pickMode", "row-dblclick"]);

/* ---- Spalten-Normalisierung ------------------------------------ */
const baseCols = computed(() =>
  props.columns.map((c) => ({
    key:   c.key,
    label: c.label ?? c.key,
    align: c.align || "left",
    group: c.group || "",
    agg:   c.agg || "",
    width: typeof c.width === "number" ? c.width : null,
    minWidth: typeof c.minWidth === "number" ? c.minWidth : 60,
    pin:   !!c.pin,
    hidden: !!c.hidden,
  })),
);

/* Initial ausgeblendete Spalten (column.hidden) — Basis für Chooser + Reset. */
const initialHidden = computed(() => new Set(baseCols.value.filter((c) => c.hidden).map((c) => c.key)));

/* Spalten, die der Chooser anbietet (chooserKeys begrenzt, sonst alle). */
const chooserCols = computed(() =>
  props.chooserKeys ? baseCols.value.filter((c) => props.chooserKeys.includes(c.key)) : baseCols.value,
);

/* ---- Spalten-Verwaltung: Reihenfolge / Sichtbarkeit / Breite ---- */
const colOrder  = ref(null);          // Array<key> | null = natürliche Reihenfolge
const colHidden = ref(new Set(props.columns.filter((c) => c.hidden).map((c) => c.key))); // ausgeblendete keys (initial aus column.hidden)
const colWidths = ref({});            // key -> px (Resize-Override)
const chooserOpen = ref(false);       // PpColChooser-Panel offen

const orderedKeys = computed(() => colOrder.value ?? baseCols.value.map((c) => c.key));

/* Wirksame Spalten (Reihenfolge + Sichtbarkeit + Breite angewandt). */
const cols = computed(() =>
  orderedKeys.value
    .map((k) => baseCols.value.find((c) => c.key === k))
    .filter(Boolean)
    .filter((c) => !colHidden.value.has(c.key))
    .map((c) => ({ ...c, width: colWidths.value[c.key] ?? c.width })),
);

function toggleColVis(key) {
  const next = new Set(colHidden.value);
  if (next.has(key)) next.delete(key);
  else if (cols.value.length > 1) next.add(key);   // mindestens eine Spalte sichtbar lassen
  colHidden.value = next;
}
function resetCols() {
  colOrder.value = null;
  colHidden.value = new Set(initialHidden.value); // initialen Sichtbarkeitszustand wiederherstellen
  colWidths.value = {};
  colFilters.value = {};                           // Spaltenfilter zurücksetzen
  chooserOpen.value = false;
}

/* ---- PpColChooser-Anbindung (@6, EIN Spalten-Wähler) ----------- */
/* Items in AKTUELLER Reihenfolge (chooserCols folgt orderedKeys über baseCols). */
const chooserItems = computed(() =>
  orderedKeys.value
    .map((k) => chooserCols.value.find((c) => c.key === k))
    .filter(Boolean)
    .map((c) => ({ k: c.key, l: c.label, checked: !colHidden.value.has(c.key) })),
);
/* DnD-Reihenfolge aus dem Chooser: bei Teil-Auswahl (chooserKeys) nur die
   betroffenen Slots im vollen colOrder ersetzen, Rest bleibt an Ort. */
function onChooserReorder(newKeys) {
  if (!props.chooserKeys) { colOrder.value = newKeys.slice(); return; }
  const full = orderedKeys.value.slice();
  const slots = full.map((k, i) => (props.chooserKeys.includes(k) ? i : -1)).filter((i) => i >= 0);
  slots.forEach((slot, idx) => { if (newKeys[idx] != null) full[slot] = newKeys[idx]; });
  colOrder.value = full;
}

/* Drag-and-Drop Spaltenreihenfolge */
const dragKey = ref(null);
const dragOverKey = ref(null);
function onColDragStart(key) { if (props.reorderable) dragKey.value = key; }
function onColDragOver(key) { if (dragKey.value) dragOverKey.value = key; }
function onColDrop(targetKey) {
  if (dragKey.value && dragKey.value !== targetKey) {
    const keys = orderedKeys.value.slice();
    const from = keys.indexOf(dragKey.value);
    const to = keys.indexOf(targetKey);
    if (from >= 0 && to >= 0) { keys.splice(to, 0, keys.splice(from, 1)[0]); colOrder.value = keys; }
  }
  dragKey.value = null; dragOverKey.value = null;
}
function onColDragEnd() { dragKey.value = null; dragOverKey.value = null; }

/* Spaltenbreite ziehen (Resize) — window-Listener, kein setPointerCapture */
let resizeKey = null, resizeStartX = 0, resizeStartW = 0;
function startResize(ev, key) {
  resizeKey = key;
  resizeStartX = ev.clientX;
  const th = ev.target && ev.target.closest && ev.target.closest("th");
  resizeStartW = th ? th.offsetWidth : (colWidths.value[key] || 120);
  window.addEventListener("mousemove", onResizeMove);
  window.addEventListener("mouseup", endResize);
}
function onResizeMove(ev) {
  if (!resizeKey) return;
  const base = baseCols.value.find((c) => c.key === resizeKey);
  const min = base ? base.minWidth : 60;
  const w = Math.max(min, resizeStartW + (ev.clientX - resizeStartX));
  colWidths.value = { ...colWidths.value, [resizeKey]: Math.round(w) };
}
function endResize() {
  resizeKey = null;
  window.removeEventListener("mousemove", onResizeMove);
  window.removeEventListener("mouseup", endResize);
}
onBeforeUnmount(endResize);

/* Zweizeiliger Kopf nur wenn mindestens eine Spalte einer Gruppe angehoert. */
const hasGroups = computed(() => cols.value.some((c) => c.group));

/* Uebergruppen-Segmente fuer die obere Kopfzeile (colspan ueber gleiche group). */
const groupSegments = computed(() => {
  const segs = [];
  for (const c of cols.value) {
    const last = segs[segs.length - 1];
    if (c.group && last && last.group === c.group) last.span += 1;
    else segs.push({ group: c.group, span: 1 });
  }
  return segs;
});

/* Picker sichtbar nur wenn Fähigkeit frei UND Modus an (@6, Default aus). */
const showPick = computed(() => props.pickable && props.pickMode);

/* Wieviele fuehrende Steuer-Spalten (Picker / Auswahl / Aufklappen) gibt es? */
const leadCols = computed(() => (showPick.value ? 1 : 0) + (props.selectable ? 1 : 0) + (props.expandable ? 1 : 0));

/* Zeilen-Klick: im Picker-Modus wählt die ganze Zeile; sonst Inspektor-Selektion. */
function onRowClick(id) {
  if (showPick.value) togglePick(id);
  else emit("row-click", id);
}

/* ---- Sortierung (clientseitig) --------------------------------- */
const sortKey = ref("");
const sortDir = ref("asc"); // 'asc' | 'desc'

function onSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = key;
    sortDir.value = "asc";
  }
}

function cmp(a, b) {
  if (a == null && b == null) return 0;
  if (a == null) return -1;
  if (b == null) return 1;
  const na = typeof a === "number" ? a : Number(a);
  const nb = typeof b === "number" ? b : Number(b);
  if (!Number.isNaN(na) && !Number.isNaN(nb) && a !== "" && b !== "") return na - nb;
  return String(a).localeCompare(String(b), "de", { numeric: true });
}

/* ---- Spaltenfilter (clientseitig, je Spalte) ------------------- */
const filterRowOpen = ref(false);
const colFilters = ref({}); // key -> Filtertext
function setFilter(key, val) { colFilters.value = { ...colFilters.value, [key]: val }; }
const activeFilters = computed(() =>
  Object.entries(colFilters.value).filter(([, v]) => String(v ?? "").trim() !== ""),
);
const filteredRows = computed(() => {
  if (!activeFilters.value.length) return props.rows;
  return props.rows.filter((r) =>
    activeFilters.value.every(([k, v]) =>
      String(r[k] ?? "").toLowerCase().includes(String(v).toLowerCase()),
    ),
  );
});

const sortedRows = computed(() => {
  const list = filteredRows.value.slice();
  if (!sortKey.value) return list;
  const k = sortKey.value;
  const f = sortDir.value === "asc" ? 1 : -1;
  return list.sort((r1, r2) => cmp(r1[k], r2[k]) * f);
});

/* ---- Gruppierung der Zeilen ------------------------------------ */
const sectioned = computed(() => {
  if (!props.groupBy) return [{ label: null, rows: sortedRows.value }];
  const map = new Map();
  for (const r of sortedRows.value) {
    const key = r[props.groupBy] ?? "—";
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(r);
  }
  return [...map.entries()].map(([label, rows]) => ({ label, rows }));
});

/* Gesamtzahl Datenspalten (fuer colspan in Gruppen-/Detailzeilen). */
const totalColspan = computed(() => leadCols.value + cols.value.length);

/* ---- Auswahl --------------------------------------------------- */
const selected = ref(new Set());

const allIds = computed(() => props.rows.map((r) => r.id));
const allSelected = computed(
  () => allIds.value.length > 0 && allIds.value.every((id) => selected.value.has(id)),
);
const someSelected = computed(
  () => allIds.value.some((id) => selected.value.has(id)) && !allSelected.value,
);
const selectedCount = computed(() => selected.value.size);

function emitSelection() {
  emit("update:selection", [...selected.value]);
}
function toggleRowSel(id) {
  if (selected.value.has(id)) selected.value.delete(id);
  else selected.value.add(id);
  selected.value = new Set(selected.value);
  emitSelection();
}
function toggleAll() {
  if (allSelected.value) selected.value = new Set();
  else selected.value = new Set(allIds.value);
  emitSelection();
}
function clearSel() {
  selected.value = new Set();
  emitSelection();
}

/* ---- Kontrollierter Picker (@5) -------------------------------- */
const pickedSet = computed(() => new Set(props.picked));
const allPicked = computed(
  () => allIds.value.length > 0 && allIds.value.every((id) => pickedSet.value.has(id)),
);
const somePicked = computed(
  () => allIds.value.some((id) => pickedSet.value.has(id)) && !allPicked.value,
);
const pickedCount = computed(() => props.picked.length);
function togglePick(id) {
  const next = props.picked.slice();
  const i = next.indexOf(id);
  if (i >= 0) next.splice(i, 1);
  else next.push(id);
  emit("update:picked", next);
}
function togglePickAll() {
  emit("update:picked", allPicked.value ? [] : allIds.value.slice());
}

/* ---- Aufklappen ------------------------------------------------ */
const expanded = ref(new Set());
function hasChildren(row) {
  return props.expandable && Array.isArray(row._children) && row._children.length > 0;
}
function toggleExpand(row) {
  if (!hasChildren(row)) return;
  if (expanded.value.has(row.id)) expanded.value.delete(row.id);
  else expanded.value.add(row.id);
  expanded.value = new Set(expanded.value);
  emit("toggle-expand", row.id);
}

/* ---- Summen-Fusszeile ------------------------------------------ */
const hasFooter = computed(() => cols.value.some((c) => c.agg));

const footerValues = computed(() => {
  const out = {};
  for (const c of cols.value) {
    if (!c.agg) continue;
    const nums = sortedRows.value
      .map((r) => (typeof r[c.key] === "number" ? r[c.key] : Number(r[c.key])))
      .filter((n) => !Number.isNaN(n));
    if (!nums.length) { out[c.key] = null; continue; }
    const sum = nums.reduce((a, n) => a + n, 0);
    out[c.key] = c.agg === "avg" ? sum / nums.length : sum;
  }
  return out;
});

function fmt(v) {
  if (v == null) return "";
  if (typeof v === "number") {
    return v.toLocaleString("de-DE", { maximumFractionDigits: 2 });
  }
  return v;
}

function sortState(key) {
  if (sortKey.value !== key) return "none";
  return sortDir.value === "asc" ? "ascending" : "descending";
}
</script>

<template>
  <div class="pp-datagrid">
    <!-- Spalten-Toolbar: Sichtbarkeit (PpColChooser, EIN Baustein) / Hinweis Reorder+Resize -->
    <div v-if="columnTools || reorderable || resizable || filterable" class="pp-datagrid__toolbar">
      <PpColChooser
        v-if="columnTools"
        v-model:open="chooserOpen"
        :items="chooserItems"
        :reorderable="reorderable"
        head="Spalten anzeigen"
        label="Spalten"
        @toggle="toggleColVis($event.k)"
        @reorder="onChooserReorder"
      />
      <button
        v-if="filterable"
        type="button"
        class="pp-datagrid__filterbtn"
        :class="{ 'is-active': filterRowOpen || activeFilters.length }"
        @click="filterRowOpen = !filterRowOpen"
      >Filter<span v-if="activeFilters.length" class="pp-datagrid__filterbadge">{{ activeFilters.length }}</span></button>
      <button v-if="columnTools" type="button" class="pp-datagrid__colreset" @click="resetCols">Zurücksetzen</button>
      <span v-if="reorderable || resizable" class="pp-datagrid__toolbar-hint">
        {{ reorderable && resizable ? 'Spaltenkopf ziehen = umsortieren · Rand ziehen = Breite'
          : reorderable ? 'Spaltenkopf ziehen zum Umsortieren' : 'Spaltenrand ziehen für Breite' }}
      </span>
    </div>

    <!-- Bulk-Leiste (nur bei Auswahl > 0) -->
    <div v-if="selectable && selectedCount > 0" class="pp-datagrid__bulk">
      <span class="pp-datagrid__bulk-count">{{ selectedCount }} ausgewählt</span>
      <button type="button" class="pp-datagrid__bulk-action">Aktion</button>
      <button type="button" class="pp-datagrid__bulk-clear" @click="clearSel" aria-label="Auswahl aufheben">
        <X /> Aufheben
      </button>
    </div>

    <div class="pp-datagrid__scroll">
      <table class="pp-datagrid__table" :class="{ 'is-fixed': cols.some((c) => c.width) }">
        <thead class="pp-datagrid__head">
          <!-- Uebergruppen-Kopf (zweizeilig) -->
          <tr v-if="hasGroups" class="pp-datagrid__group">
            <th
              v-if="leadCols"
              class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__th-group"
              :colspan="leadCols"
              :class="{ 'pp-datagrid__pin': cols.some((c) => c.pin) }"
            ></th>
            <th
              v-for="(seg, i) in groupSegments"
              :key="'g' + i"
              class="pp-datagrid__cell pp-datagrid__th-group"
              :class="{ 'pp-datagrid__th-group--named': seg.group }"
              :colspan="seg.span"
            >
              {{ seg.group }}
            </th>
          </tr>

          <!-- Spalten-Kopf -->
          <tr>
            <th
              v-if="showPick"
              class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__cell--ctrl pp-datagrid__cell--pick"
            >
              <input
                type="checkbox"
                class="pp-datagrid__check"
                :checked="allPicked"
                :indeterminate.prop="somePicked"
                @change="togglePickAll"
                aria-label="Alle auswählen"
              />
              <span v-if="pickedCount" class="pp-datagrid__pick-count">{{ pickedCount }}</span>
            </th>
            <th
              v-if="expandable"
              class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__cell--ctrl"
            ></th>
            <th
              v-if="selectable"
              class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__cell--ctrl"
              :class="{ 'pp-datagrid__pin pp-datagrid__pin--first': !expandable }"
            >
              <input
                type="checkbox"
                class="pp-datagrid__check"
                :checked="allSelected"
                :indeterminate.prop="someSelected"
                @change="toggleAll"
                aria-label="Alle auswählen"
              />
            </th>
            <th
              v-for="(c, ci) in cols"
              :key="c.key"
              class="pp-datagrid__cell pp-datagrid__cell--th"
              :class="{
                'pp-datagrid__cell--right':  c.align === 'right',
                'pp-datagrid__cell--center': c.align === 'center',
                'pp-datagrid__pin': c.pin,
                'pp-datagrid__pin--first': c.pin && ci === 0 && leadCols === 0,
                'is-sorted': sortKey === c.key,
                'is-draggable': reorderable,
                'is-dragover': dragOverKey === c.key,
              }"
              :style="c.width ? { width: c.width + 'px' } : null"
              :aria-sort="sortState(c.key)"
              :draggable="reorderable"
              @click="onSort(c.key)"
              @dragstart="onColDragStart(c.key)"
              @dragover.prevent="onColDragOver(c.key)"
              @drop.prevent="onColDrop(c.key)"
              @dragend="onColDragEnd"
            >
              <span class="pp-datagrid__th-inner">
                <span class="pp-datagrid__th-label">{{ c.label }}</span>
                <span class="pp-datagrid__sort" aria-hidden="true">
                  <ChevronUp   v-if="sortKey === c.key && sortDir === 'asc'" />
                  <ChevronDown v-else-if="sortKey === c.key && sortDir === 'desc'" />
                  <ChevronsUpDown v-else class="pp-datagrid__sort--idle" />
                </span>
              </span>
              <span v-if="resizable" class="pp-datagrid__resize" title="Breite ziehen"
                    @mousedown.stop.prevent="startResize($event, c.key)" @click.stop></span>
            </th>
          </tr>

          <!-- Filterzeile je Spalte (@7, umschaltbar über „Filter") -->
          <tr v-if="filterable && filterRowOpen" class="pp-datagrid__filterrow">
            <th v-if="showPick" class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__cell--ctrl"></th>
            <th v-if="expandable" class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__cell--ctrl"></th>
            <th v-if="selectable" class="pp-datagrid__cell pp-datagrid__cell--lead pp-datagrid__cell--ctrl"></th>
            <th
              v-for="c in cols"
              :key="'f-' + c.key"
              class="pp-datagrid__cell pp-datagrid__filtercell"
              :class="{ 'pp-datagrid__pin': c.pin }"
            >
              <input
                type="text"
                class="pp-datagrid__filterinput"
                :value="colFilters[c.key] || ''"
                placeholder="Filter …"
                @input="setFilter(c.key, $event.target.value)"
                @click.stop
              />
            </th>
          </tr>
        </thead>

        <tbody>
          <template v-for="(sec, si) in sectioned" :key="'s' + si">
            <!-- Gruppen-Kopfzeile -->
            <tr v-if="sec.label !== null" class="pp-datagrid__section">
              <td class="pp-datagrid__cell pp-datagrid__section-cell" :colspan="totalColspan">
                {{ sec.label }}
                <span class="pp-datagrid__section-count">{{ sec.rows.length }}</span>
              </td>
            </tr>

            <template v-for="row in sec.rows" :key="row.id">
              <tr
                class="pp-datagrid__row"
                :class="{
                  'is-selected': selectable && selected.has(row.id),
                  'pp-datagrid__row--picked': showPick && pickedSet.has(row.id),
                }"
                @click="onRowClick(row.id)"
                @dblclick="emit('row-dblclick', row.id)"
              >
                <!-- Picker (@5 kontrolliert, @6 nur im Picker-Modus) -->
                <td
                  v-if="showPick"
                  class="pp-datagrid__cell pp-datagrid__cell--ctrl pp-datagrid__cell--pick"
                  @click.stop
                >
                  <input
                    type="checkbox"
                    class="pp-datagrid__check"
                    :checked="pickedSet.has(row.id)"
                    @change="togglePick(row.id)"
                    :aria-label="'Zeile ' + row.id + ' auswählen'"
                  />
                </td>

                <!-- Aufklapp-Chevron -->
                <td v-if="expandable" class="pp-datagrid__cell pp-datagrid__cell--ctrl">
                  <button
                    v-if="hasChildren(row)"
                    type="button"
                    class="pp-datagrid__chevron"
                    :class="{ 'is-open': expanded.has(row.id) }"
                    :aria-expanded="expanded.has(row.id)"
                    aria-label="Zeile aufklappen"
                    @click.stop="toggleExpand(row)"
                  >
                    <ChevronRight />
                  </button>
                </td>

                <!-- Auswahl -->
                <td
                  v-if="selectable"
                  class="pp-datagrid__cell pp-datagrid__cell--ctrl"
                  :class="{ 'pp-datagrid__pin pp-datagrid__pin--first': !expandable }"
                  @click.stop
                >
                  <input
                    type="checkbox"
                    class="pp-datagrid__check"
                    :checked="selected.has(row.id)"
                    @change="toggleRowSel(row.id)"
                    :aria-label="'Zeile ' + row.id + ' auswählen'"
                  />
                </td>

                <!-- Datenzellen -->
                <td
                  v-for="(c, ci) in cols"
                  :key="c.key"
                  class="pp-datagrid__cell"
                  :class="{
                    'pp-datagrid__cell--right':  c.align === 'right',
                    'pp-datagrid__cell--center': c.align === 'center',
                    'pp-datagrid__cell--num':    c.align === 'right',
                    'pp-datagrid__pin': c.pin,
                    'pp-datagrid__pin--first': c.pin && ci === 0 && leadCols === 0,
                  }"
                  :style="c.width ? { width: c.width + 'px' } : null"
                >
                  <slot :name="'cell-' + c.key" :row="row" :value="row[c.key]" :col="c">{{ fmt(row[c.key]) }}</slot>
                </td>
              </tr>

              <!-- Detail-Unterzeilen -->
              <template v-if="hasChildren(row) && expanded.has(row.id)">
                <tr
                  v-for="(child, cii) in row._children"
                  :key="row.id + '-c' + cii"
                  class="pp-datagrid__row pp-datagrid__row--child"
                >
                  <td v-if="showPick" class="pp-datagrid__cell pp-datagrid__cell--ctrl pp-datagrid__cell--pick"></td>
                  <td v-if="expandable" class="pp-datagrid__cell pp-datagrid__cell--ctrl"></td>
                  <td
                    v-if="selectable"
                    class="pp-datagrid__cell pp-datagrid__cell--ctrl"
                    :class="{ 'pp-datagrid__pin pp-datagrid__pin--first': !expandable }"
                  ></td>
                  <td
                    v-for="(c, ci) in cols"
                    :key="c.key"
                    class="pp-datagrid__cell"
                    :class="{
                      'pp-datagrid__cell--right':  c.align === 'right',
                      'pp-datagrid__cell--center': c.align === 'center',
                      'pp-datagrid__cell--num':    c.align === 'right',
                      'pp-datagrid__pin': c.pin,
                      'pp-datagrid__pin--first': c.pin && ci === 0 && leadCols === 0,
                    }"
                    :style="c.width ? { width: c.width + 'px' } : null"
                  >
                    <slot :name="'cell-' + c.key" :row="child" :value="child[c.key]" :col="c">{{ fmt(child[c.key]) }}</slot>
                  </td>
                </tr>
              </template>
            </template>
          </template>

          <!-- Leerzustand -->
          <tr v-if="!sortedRows.length" class="pp-datagrid__row">
            <td class="pp-datagrid__cell pp-datagrid__empty" :colspan="totalColspan">
              {{ rows.length ? "Keine Treffer für den Spaltenfilter" : "Keine Daten" }}
            </td>
          </tr>
        </tbody>

        <!-- Summen-Fusszeile -->
        <tfoot v-if="hasFooter" class="pp-datagrid__foot">
          <tr>
            <td
              v-if="leadCols"
              class="pp-datagrid__cell pp-datagrid__cell--lead"
              :colspan="leadCols"
              :class="{ 'pp-datagrid__pin pp-datagrid__pin--first': cols.some((c) => c.pin) || selectable }"
            >Σ</td>
            <td
              v-for="(c, ci) in cols"
              :key="c.key"
              class="pp-datagrid__cell"
              :class="{
                'pp-datagrid__cell--right':  c.align === 'right',
                'pp-datagrid__cell--center': c.align === 'center',
                'pp-datagrid__cell--num':    c.align === 'right',
                'pp-datagrid__pin': c.pin,
                'pp-datagrid__pin--first': c.pin && ci === 0 && leadCols === 0,
              }"
              :style="c.width ? { width: c.width + 'px' } : null"
            >
              {{ c.agg ? fmt(footerValues[c.key]) : "" }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<style scoped>
.pp-datagrid {
  display: flex; flex-direction: column; min-height: 0;
  background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui);
  overflow: hidden;
  font-family: var(--pp-font-body);
  color: var(--pp-text-primary);
}

/* ---- Bulk-Leiste ---------------------------------------------- */
.pp-datagrid__bulk {
  flex: 0 0 auto;
  display: flex; align-items: center; gap: var(--pp-space-3);
  padding: var(--pp-space-2) var(--pp-space-3);
  background: rgb(var(--pp-brand-primary-rgb) / 0.08);
  border-bottom: 1px solid var(--pp-border-subtle);
}
.pp-datagrid__bulk-count { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary); }
.pp-datagrid__bulk-action {
  appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  padding: 4px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary);
}
.pp-datagrid__bulk-action:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.pp-datagrid__bulk-clear {
  appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  display: inline-flex; align-items: center; gap: 4px; margin-left: auto;
  padding: 4px var(--pp-space-2); border: 0; background: transparent; color: var(--pp-text-secondary);
  border-radius: var(--pp-radius-ui);
}
.pp-datagrid__bulk-clear:hover { color: var(--pp-text-primary); background: var(--pp-bg-hover); }
.pp-datagrid__bulk-clear :deep(svg) { width: 14px; height: 14px; }

/* ---- Spalten-Toolbar (Auswahl / Reorder / Resize) ------------- */
.pp-datagrid__toolbar {
  flex: 0 0 auto; position: relative;
  display: flex; align-items: center; gap: var(--pp-space-3);
  padding: var(--pp-space-2) var(--pp-space-3);
  border-bottom: 1px solid var(--pp-border-subtle);
}
.pp-datagrid__colreset {
  appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  padding: 4px var(--pp-space-2); border: 0; background: transparent;
  color: var(--pp-text-secondary); border-radius: var(--pp-radius-ui);
}
.pp-datagrid__colreset:hover { color: var(--pp-brand-primary); background: var(--pp-bg-hover); }
.pp-datagrid__toolbar-hint { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); margin-left: auto; }

/* Filter-Umschalter + Filterzeile (@7) */
.pp-datagrid__filterbtn {
  appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px var(--pp-space-2); border: 1px solid var(--pp-border-default);
  background: var(--pp-bg-surface); color: var(--pp-text-secondary); border-radius: var(--pp-radius-ui);
}
.pp-datagrid__filterbtn:hover { color: var(--pp-brand-primary); border-color: var(--pp-brand-primary); }
.pp-datagrid__filterbtn.is-active { color: var(--pp-brand-primary); border-color: var(--pp-brand-primary);
  background: color-mix(in oklab, var(--pp-brand-primary) 8%, transparent); }
.pp-datagrid__filterbadge { font-size: 10px; font-weight: var(--pp-weight-bold); line-height: 1;
  color: var(--pp-text-on-accent); background: var(--pp-brand-primary); padding: 1px 5px; border-radius: var(--pp-radius-full); }
.pp-datagrid__filterrow th { position: static; background: var(--pp-bg-surface);
  padding: 4px var(--pp-space-3); border-bottom: 1px solid var(--pp-border-subtle); }
.pp-datagrid__filterinput {
  width: 100%; appearance: none; font-family: inherit; font-size: var(--pp-fs-12, 12px);
  color: var(--pp-text-primary); padding: 4px var(--pp-space-2);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base);
  text-transform: none; letter-spacing: normal; font-weight: var(--pp-weight-regular, 400);
}
.pp-datagrid__filterinput:focus { outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 2px rgb(var(--pp-brand-primary-rgb) / 0.15); }

/* Reorder/Resize am Spaltenkopf (Kopf-th ist sticky = positionierter Anker) */
.pp-datagrid__cell--th.is-draggable { cursor: grab; }
.pp-datagrid__cell--th.is-dragover { box-shadow: inset 3px 0 0 var(--pp-brand-primary); }
.pp-datagrid__resize { position: absolute; top: 0; right: 0; width: 7px; height: 100%; cursor: col-resize; z-index: 3; }
.pp-datagrid__resize:hover {
  background: linear-gradient(90deg, transparent 0 40%, var(--pp-brand-primary) 40% 60%, transparent 60% 100%);
}

/* ---- Scroll-Container ----------------------------------------- */
.pp-datagrid__scroll { flex: 1 1 auto; min-height: 0; overflow: auto; }

.pp-datagrid__table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: var(--pp-fs-14); }
.pp-datagrid__table.is-fixed { table-layout: fixed; }

/* ---- Zellen-Basis --------------------------------------------- */
/* Zeilenhoehe nach dem Klickdummy-Master (Anrufe): luftiger als das frühere
   space-2, damit zweizeilige Zellen (Name über Firma) nicht kleben. */
.pp-datagrid__cell {
  padding: 11px var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle);
  text-align: left; vertical-align: middle;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pp-datagrid__cell--right  { text-align: right; }
.pp-datagrid__cell--center { text-align: center; }
.pp-datagrid__cell--num    { font-variant-numeric: tabular-nums; }
.pp-datagrid__cell--ctrl   { width: 40px; text-align: center; padding-left: 0; padding-right: 0; }

/* ---- Kopfzeile (sticky) --------------------------------------- */
.pp-datagrid__head th {
  position: sticky; top: 0; z-index: 2;
  background: var(--pp-bg-sunken);
  padding: var(--pp-space-2) var(--pp-space-4);
  font-size: 11px; font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide); text-transform: uppercase;
  color: var(--pp-text-tertiary);
  border-bottom: 1px solid var(--pp-border-default);
}
/* zweite Kopf-Zeile (Spalten) sitzt unter der Gruppen-Zeile */
.pp-datagrid__head .pp-datagrid__group th { top: 0; z-index: 3; }

.pp-datagrid__cell--th { cursor: pointer; user-select: none; }
.pp-datagrid__cell--th:hover { color: var(--pp-text-secondary); background: var(--pp-bg-hover); }
.pp-datagrid__cell--th.is-sorted { color: var(--pp-brand-primary); }

.pp-datagrid__th-inner { display: inline-flex; align-items: center; gap: 4px; }
.pp-datagrid__cell--right .pp-datagrid__th-inner  { flex-direction: row-reverse; }
.pp-datagrid__cell--center .pp-datagrid__th-inner { justify-content: center; }
.pp-datagrid__th-label { overflow: hidden; text-overflow: ellipsis; }
.pp-datagrid__sort { display: inline-flex; flex: 0 0 auto; color: var(--pp-brand-primary); }
.pp-datagrid__sort :deep(svg) { width: 13px; height: 13px; display: block; }
/* Ruhe-Chevron erst beim Hover zeigen — der Master-Kopf (Klickdummy „Anrufe")
   traegt reine Beschriftungen; ein Pfeil in JEDER Spalte macht ihn unruhig.
   Die aktive Sortierspalte behaelt ihren Pfeil sichtbar. */
.pp-datagrid__sort--idle { color: var(--pp-text-disabled); opacity: 0; }
.pp-datagrid__cell--th:hover .pp-datagrid__sort--idle { color: var(--pp-text-tertiary); opacity: 1; }

/* Uebergruppen-Kopf */
.pp-datagrid__th-group {
  text-align: center;
  border-bottom: 1px solid var(--pp-border-subtle);
  color: var(--pp-text-secondary);
}
.pp-datagrid__th-group--named { border-left: 1px solid var(--pp-border-subtle); }

/* ---- Fixierte (pin) Spalte ------------------------------------ */
.pp-datagrid__pin {
  position: sticky; left: 0; z-index: 1;
  background: var(--pp-bg-surface);
}
/* Kopf-Pin liegt ueber Zeilen-Pin (sticky in beide Richtungen) */
.pp-datagrid__head .pp-datagrid__pin { z-index: 4; background: var(--pp-bg-sunken); }
/* Keine Trennkante an der fixierten Spalte: im Master (Klickdummy „Anrufe")
   laeuft die Zeile durch. Die Kante gehoert zu horizontalem Scroll, nicht zum
   Ruhezustand — und stand hier permanent mitten in der Tabelle. */

/* ---- Datenzeilen: nur Trennlinie + Hover ---------------------- */
/* Kein Zebra — der Master trennt die Zeilen ausschliesslich per Linie. */
.pp-datagrid__row { cursor: pointer; }
.pp-datagrid__row:hover td { background: var(--pp-bg-hover); }
.pp-datagrid__row.is-selected td { background: rgb(var(--pp-brand-primary-rgb) / 0.10); }
.pp-datagrid__row.is-selected td.pp-datagrid__pin { background: rgb(var(--pp-brand-primary-rgb) / 0.10); }

/* Detail-Unterzeile */
.pp-datagrid__row--child td { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); font-size: var(--pp-fs-13, 13px); }
.pp-datagrid__row--child td:first-of-type { box-shadow: inset 2px 0 0 var(--pp-border-default); }
.pp-datagrid__row--child:hover td { background: var(--pp-bg-hover); }

/* ---- Gruppen-Sektion ------------------------------------------ */
.pp-datagrid__section-cell {
  background: var(--pp-bg-sunken);
  font-size: 11px; font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide); text-transform: uppercase;
  color: var(--pp-text-secondary);
  border-bottom: 1px solid var(--pp-border-default);
}
.pp-datagrid__section-count {
  margin-left: var(--pp-space-2);
  font-size: 10px; font-weight: var(--pp-weight-bold);
  color: var(--pp-text-on-accent); background: var(--pp-brand-primary);
  padding: 1px 6px; border-radius: var(--pp-radius-full); letter-spacing: 0;
}

/* ---- Kontrollierter Picker (@5) ------------------------------- */
.pp-datagrid__cell--pick { position: relative; }
.pp-datagrid__head .pp-datagrid__cell--pick { white-space: nowrap; }
.pp-datagrid__pick-count {
  display: inline-block; margin-left: 4px; vertical-align: middle;
  font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0;
  color: var(--pp-text-on-accent); background: var(--pp-brand-primary);
  padding: 1px 6px; border-radius: var(--pp-radius-full);
}
.pp-datagrid__row--picked td { background: rgb(var(--pp-brand-primary-rgb) / 0.08); }
.pp-datagrid__row--picked td.pp-datagrid__pin { background: rgb(var(--pp-brand-primary-rgb) / 0.08); }

/* ---- Checkbox / Chevron --------------------------------------- */
.pp-datagrid__check { width: 15px; height: 15px; accent-color: var(--pp-brand-primary); cursor: pointer; }
.pp-datagrid__chevron {
  appearance: none; cursor: pointer; display: inline-grid; place-items: center;
  width: 22px; height: 22px; padding: 0;
  background: transparent; border: 1px solid transparent; border-radius: var(--pp-radius-ui);
  color: var(--pp-text-tertiary);
}
.pp-datagrid__chevron:hover { background: var(--pp-bg-hover); color: var(--pp-brand-primary); border-color: var(--pp-border-subtle); }
.pp-datagrid__chevron :deep(svg) { width: 15px; height: 15px; display: block; transition: transform var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-datagrid__chevron.is-open :deep(svg) { transform: rotate(90deg); }

/* ---- Fusszeile (Summen) --------------------------------------- */
.pp-datagrid__foot td {
  position: sticky; bottom: 0; z-index: 2;
  background: var(--pp-bg-sunken);
  font-weight: var(--pp-weight-bold);
  color: var(--pp-text-primary);
  border-top: 1px solid var(--pp-border-default);
  border-bottom: 0;
}
.pp-datagrid__foot .pp-datagrid__pin { z-index: 3; background: var(--pp-bg-sunken); }

/* ---- Leerzustand ---------------------------------------------- */
.pp-datagrid__empty { text-align: center; color: var(--pp-text-tertiary); padding: var(--pp-space-6); }

/* letzte Datenzeile ohne Trennlinie, wenn kein Footer folgt */
.pp-datagrid__table tbody tr:last-child td { border-bottom: 0; }
</style>
