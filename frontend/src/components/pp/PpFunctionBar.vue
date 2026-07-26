<!-- PP_REV: PpFunctionBar@3 -->
<!--
  PpFunctionBar.vue — zentrale Funktionsleiste (app-weiter Shell-Baustein, SSOT).

  Herkunft: Klickdummy `pilanda-navigation.html` (Design-Master, führt). Der
  Burger (☰) im Inspektor-Kopf (PpInspector@8) öffnet diese Vollbreiten-Bar als
  Overlay OBEN im Canvas (Mini-Ribbon mit 54er-Buttons). ESC / Außenklick / X
  schließen; ein Button-Klick feuert `action` und schließt die Bar.

  @3 (Befund 16, Marco 26.07.2026 — Zwei-Tier-Registry, Klickdummy `IBX_REG`/
  `objActions`/`ibxCompose`/`buildInspBar`, Commit 9acf524): Der Inspektor-Body
  zeigt NUR die Spezifikation — ALLE Aktionen wohnen hier. Zwei Tiers, EINE
  zentrale Misch-Mechanik (`ibxCompose`), Vue-idiomatisch als Props:
    · PAGE-Tier   `pageGroups` = { aktionen?, werkzeuge?, ausgabe?, abstiege? }
      Die je Seite kuratierte Registry des Verbrauchers (entspricht
      `IBX_REG[pageKey]` bzw. dem def-Fallback `ibxGroupsFromDef`). Jede Gruppe
      ist ein Array aus { id?, label, icon?, primary? } ODER reinen Label-Strings.
    · OBJEKT-Tier `objectActions` = [{ id?, label, icon?, primary?, group? }]
      Die Aktionen des angeklickten Objekts (früher .insp-actrow im Body).
      `group` ist 'aktion' (Default) oder 'abstieg'.
    Misch-Regel (ibxCompose):
      aktionen  = objekt(aktion)  + pageGroups.aktionen
      werkzeuge =                   pageGroups.werkzeuge
      ausgabe   =                   pageGroups.ausgabe
      abstiege  = objekt(abstieg) + pageGroups.abstiege
    Gruppen-Reihenfolge/Unterschriften überall gleich: Aktionen · Werkzeuge ·
    Ausgabe · Abstiege (nur nicht-leere Gruppen). In der Gruppe „Aktionen" ist die
    erste Aktion primär (farbig), sofern keine per `primary` gesetzt ist; ein
    explizites `primary` wirkt in JEDER Gruppe (z. B. „Öffnen (Detail)" im
    Abstieg). Volle Labels (nowrap, KEIN ellipsis), passendes Lucide-Icon je
    Funktion (`iconOf` = 1:1 zur Klickdummy-Heuristik `ibxIconSvg`), `title` an
    jedem Button.

  Der Burger selbst wohnt im PpInspector@8-Kopf (Klasse `.pp-funcbar__burger`,
  zentral in components.css); dort steuert er über `v-model:funcbarOpen` das
  Auf/Zu, das der Host mit dem `open`-v-model DIESER Bar teilt. Der Außenklick-
  Schließer ignoriert Klicks auf den Burger (`ignoreSelector`), damit der
  Öffnungs-Klick die Bar nicht sofort wieder schließt.

  Positionierung: `.pp-funcbar` ist `position:absolute` und füllt den oberen Rand
  seines positionierten Eltern-Containers (Host macht den Canvas-Wrapper
  `position:relative`). Verschiebt nichts im Fluss, wandert nicht beim Scroll.

  Props:
    open           Boolean   v-model:open — Bar sichtbar
    pageGroups     Object    { aktionen?, werkzeuge?, ausgabe?, abstiege? }
    objectActions  Array     [{ id?, label, icon?, primary?, group? }]
    groupLabels    Object    Überschriften-Override { aktionen, werkzeuge, ausgabe, abstiege }
    ariaLabel      String    a11y-Label der Toolbar
    ignoreSelector String    Außenklick-Ausnahme (Default .pp-funcbar__burger)
  Emits:
    update:open   Boolean
    action        (id)   — id des geklickten Eintrags (item.id ?? label); danach
                          schließt die Bar

  Struktur-CSS zentral in components.css (`.pp-funcbar__*`, unlayered SSOT); hier
  nur token-getriebene Logik. Radius ≤ 3px + hell/dunkel kommen aus den Tokens.
-->
<script setup>
import { computed, ref, watch, nextTick, onBeforeUnmount } from "vue";
// Kuratiertes Lucide-Set — 1:1 zur Label-Heuristik `ibxIconSvg` im Master
// (gleiche Reihenfolge → gleiche Icon-Wahl bei Mehrfach-Treffern).
import IconImport from "~icons/lucide/import";
import IconTrash from "~icons/lucide/trash-2";
import IconArchive from "~icons/lucide/archive";
import IconHandover from "~icons/lucide/arrow-right-to-line";
import IconRadar from "~icons/lucide/radar";
import IconUsers from "~icons/lucide/users";
import IconCoins from "~icons/lucide/circle-dollar-sign";
import IconNetwork from "~icons/lucide/share-2";
import IconBoard from "~icons/lucide/square-kanban";
import IconPrinter from "~icons/lucide/printer";
import IconUpload from "~icons/lucide/upload";
import IconRefresh from "~icons/lucide/refresh-cw";
import IconSearch from "~icons/lucide/search";
import IconColumns from "~icons/lucide/columns-3";
import IconFilter from "~icons/lucide/filter";
import IconPlus from "~icons/lucide/plus";
import IconEdit from "~icons/lucide/square-pen";
import IconUserPlus from "~icons/lucide/user-plus";
import IconStar from "~icons/lucide/star";
import IconCircleX from "~icons/lucide/circle-x";
import IconLanguages from "~icons/lucide/languages";
import IconFileText from "~icons/lucide/file-text";
import IconCalendar from "~icons/lucide/calendar-days";
import IconTicket from "~icons/lucide/ticket";
import IconPlay from "~icons/lucide/play";
import IconMapPin from "~icons/lucide/map-pin";
import IconLayers from "~icons/lucide/layers";
import IconCheck from "~icons/lucide/check";
import IconExternalLink from "~icons/lucide/external-link";
import IconFolder from "~icons/lucide/folder";
import IconZap from "~icons/lucide/zap";

const props = defineProps({
  open:           { type: Boolean, default: false },
  pageGroups:     { type: Object, default: () => ({}) },
  objectActions:  { type: Array, default: () => [] },
  groupLabels:    { type: Object, default: () => ({ aktionen: "Aktionen", werkzeuge: "Werkzeuge", ausgabe: "Ausgabe", abstiege: "Abstiege" }) },
  ariaLabel:      { type: String, default: "Seiten-Funktionen" },
  ignoreSelector: { type: String, default: ".pp-funcbar__burger" },
});
const emit = defineEmits(["update:open", "action"]);

const barEl = ref(null);

// Label eines Eintrags (String oder { label }).
const labelOf = (a) => (a && typeof a === "object" ? a.label : a) || "";
// Stabile Kennung für den Emit: id, sonst Label.
const idOf = (a) => (a && typeof a === "object" && a.id != null ? a.id : labelOf(a));

// Zwei-Tier-Mischung (ibxCompose): Objekt-Tier VOR Page-Tier bei Aktionen/Abstiegen.
const objAktion  = computed(() => props.objectActions.filter((a) => a && (a.group || "aktion") !== "abstieg"));
const objAbstieg = computed(() => props.objectActions.filter((a) => a && a.group === "abstieg"));
const pg = (k) => (Array.isArray(props.pageGroups[k]) ? props.pageGroups[k] : []);

// Nur nicht-leere Gruppen, feste Reihenfolge. `act` markiert die Aktionen-Gruppe
// (Auto-Primär auf dem ersten Eintrag, wenn keiner explizit primär ist).
const groups = computed(() => {
  const out = [];
  const aktionen = [...objAktion.value, ...pg("aktionen")];
  const werkzeuge = pg("werkzeuge");
  const ausgabe = pg("ausgabe");
  const abstiege = [...objAbstieg.value, ...pg("abstiege")];
  if (aktionen.length) out.push({ key: "aktionen", cap: props.groupLabels.aktionen, items: aktionen, act: true });
  if (werkzeuge.length) out.push({ key: "werkzeuge", cap: props.groupLabels.werkzeuge, items: werkzeuge });
  if (ausgabe.length) out.push({ key: "ausgabe", cap: props.groupLabels.ausgabe, items: ausgabe });
  if (abstiege.length) out.push({ key: "abstiege", cap: props.groupLabels.abstiege, items: abstiege });
  return out;
});

// Icon je Eintrag: explizit (Vue-Komponente) oder Label-Heuristik. Reihenfolge
// exakt wie `ibxIconSvg` im Klickdummy — bei Mehrfach-Treffern gewinnt der erste.
function iconOf(a) {
  if (a && typeof a === "object" && a.icon) return a.icon;
  const t = labelOf(a).toLowerCase();
  if (/import/.test(t)) return IconImport;
  if (/entfern|löschen|papierkorb/.test(t)) return IconTrash;
  if (/archiv/.test(t)) return IconArchive;
  if (/übergab|handover|pflichtenheft/.test(t)) return IconHandover;
  if (/leitstand|leitstelle/.test(t)) return IconRadar;
  if (/ressourc/.test(t)) return IconUsers;
  if (/kosten|budget/.test(t)) return IconCoins;
  if (/netzwerk/.test(t)) return IconNetwork;
  if (/board/.test(t)) return IconBoard;
  if (/pdf|drucken/.test(t)) return IconPrinter;
  if (/export|paket/.test(t)) return IconUpload;
  if (/aktualisier|neu laden|refresh|synchron|nachfass/.test(t)) return IconRefresh;
  if (/such/.test(t)) return IconSearch;
  if (/spalt/.test(t)) return IconColumns;
  if (/filter/.test(t)) return IconFilter;
  if (/neu|erfass|anleg|ansetz|hochladen|zuteil|zuordn|ordner|runde|kondition|zuweis/.test(t)) return IconPlus;
  if (/versch|verfass|beitrag|notiz|bearbeit/.test(t)) return IconEdit;
  if (/kontakt|lead/.test(t)) return IconUserPlus;
  if (/chance werten|als chance/.test(t)) return IconStar;
  if (/keine chance|verwerf|verloren/.test(t)) return IconCircleX;
  if (/sprache/.test(t)) return IconLanguages;
  if (/formular|dokument|bericht|protokoll/.test(t)) return IconFileText;
  if (/termin|einplan|forecast/.test(t)) return IconCalendar;
  if (/ticket/.test(t)) return IconTicket;
  if (/projekt start|starten/.test(t)) return IconPlay;
  if (/karte|landkarte/.test(t)) return IconMapPin;
  if (/version/.test(t)) return IconLayers;
  if (/freigeb|genehm|erledigt|mitig|abschließ|reaktiv|bestätig/.test(t)) return IconCheck;
  if (/öffnen|detail|anzeigen/.test(t)) return IconExternalLink;
  if (/projekt|liste/.test(t)) return IconFolder;
  return IconZap;
}

// Primär: explizites `primary` wirkt in jeder Gruppe; ohne explizites Primär ist
// in der Aktionen-Gruppe der erste Eintrag primär (Klickdummy buildInspBar).
function isPrimary(group, index) {
  const it = group.items[index];
  if (it && typeof it === "object" && it.primary) return true;
  if (!group.act) return false;
  const explicit = group.items.some((x) => x && typeof x === "object" && x.primary);
  return !explicit && index === 0;
}

function close() {
  if (props.open) emit("update:open", false);
}
function runItem(item) {
  // Master-Reihenfolge: erst schließen, dann Kommando feuern.
  close();
  emit("action", idOf(item));
}

// ESC schließt — und konsumiert das Event: ein Overlay soll beim Schließen den
// ESC nicht weiter durchreichen (sonst würde eine darunterliegende ESC-Bindung,
// z. B. „Seite verlassen", zusätzlich feuern). Der Listener hängt nur bei
// offener Bar, greift also nur, wenn wirklich geschlossen wird.
function onKeydown(e) {
  if (e.key === "Escape" && props.open) {
    e.stopPropagation();
    close();
  }
}
// Außenklick schließt — Burger (ignoreSelector) und die Bar selbst ausgenommen.
function onDocClick(e) {
  if (barEl.value && barEl.value.contains(e.target)) return;
  if (props.ignoreSelector && e.target.closest && e.target.closest(props.ignoreSelector)) return;
  close();
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      document.addEventListener("keydown", onKeydown);
      // Außenklick erst nach dem Öffnungs-Klick binden (rAF), sonst schließt der
      // Klick, der geöffnet hat, sofort wieder.
      requestAnimationFrame(() => document.addEventListener("click", onDocClick));
      nextTick(() => {
        const first = barEl.value && barEl.value.querySelector(".pp-funcbar__btn");
        if (first) try { first.focus(); } catch (e) { /* JSDOM/Headless-Toleranz */ }
      });
    } else {
      document.removeEventListener("keydown", onKeydown);
      document.removeEventListener("click", onDocClick);
    }
  }
);
onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("click", onDocClick);
});
</script>

<template>
  <Transition name="pp-funcbar">
    <div
      v-if="open"
      ref="barEl"
      class="pp-funcbar"
      role="toolbar"
      :aria-label="ariaLabel"
    >
      <template v-for="(group, gi) in groups" :key="group.key">
        <span v-if="gi" class="pp-funcbar__sep" aria-hidden="true"></span>
        <div class="pp-funcbar__grp">
          <div class="pp-funcbar__row">
            <button
              v-for="(item, ix) in group.items"
              :key="group.key + '-' + ix"
              type="button"
              class="pp-funcbar__btn"
              :class="{ 'pp-funcbar__btn--pri': isPrimary(group, ix) }"
              :title="labelOf(item)"
              @click="runItem(item)"
            >
              <component :is="iconOf(item)" class="pp-funcbar__ic" />
              <span class="pp-funcbar__lbl">{{ labelOf(item) }}</span>
            </button>
          </div>
          <div class="pp-funcbar__cap">{{ group.cap }}</div>
        </div>
      </template>
      <button
        type="button"
        class="pp-funcbar__x"
        aria-label="Funktions-Bar schließen"
        @click="close"
      >&times;</button>
    </div>
  </Transition>
</template>
