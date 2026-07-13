<!-- PP_REV: PpCommandPalette@2 -->
<!--
  PpCommandPalette.vue — Strg+K-Befehlspalette (SSOT-Baustein).

  ECHTE props-in / events-out Komponente — kein Store, kein Backend.
  Overlay + zentrierte Box nach dem Kern-Muster .pp-cmdk (components.css,
  Abschnitt 9). Filter-Input mit Substring- UND Subsequence-Fuzzy-Match,
  Tastatur (↑/↓ + Enter, Esc schließt), Maus (Hover setzt aktiv, Klick wählt).

  Props:
    items    Array<{ id, label, group?, icon?, kbd? }>
             · group  Überschrift; Items ohne group landen unter "".
             · icon   optionale Icon-Komponente (z.B. ~icons/lucide/*)
             · kbd    optionaler Shortcut-Hinweis (rechts, .pp-kbd)
    open     Boolean (v-model:open) — Sichtbarkeit
    placeholder  String
    hotkey   Boolean (default true) — Strg/⌘+K global zum Umschalten
    filter   Boolean (default true) — internes Fuzzy-Matching. Auf false
             setzen, wenn die App serverseitig sucht und `items` selbst
             schon zur Eingabe passend liefert (Eingabe via update:query).

  Emits:
    update:open   (Boolean)
    update:query  (String) — aktuelle Sucheingabe (für Server-Suche @2)
    select        (item)

  STRIKT --pp-*-Tokens, hell + dunkel. Struktur-CSS = globale .pp-cmdk*.
-->
<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import Search from "~icons/lucide/search";

const props = defineProps({
  items:       { type: Array,   default: () => [] },
  open:        { type: Boolean, default: false },
  placeholder: { type: String,  default: "Springen zu, Aktion ausführen, suchen…" },
  hotkey:      { type: Boolean, default: true },
  filter:      { type: Boolean, default: true },
});
const emit = defineEmits(["update:open", "update:query", "select"]);

const query   = ref("");
const active  = ref(0);
const inputEl = ref(null);

/* Substring bevorzugt, sonst Subsequence-Fuzzy (Zeichen der Reihe nach). */
function matches(label, q) {
  if (!q) return true;
  const l = label.toLowerCase();
  if (l.includes(q)) return true;
  let i = 0;
  for (const ch of l) { if (ch === q[i]) i++; if (i === q.length) return true; }
  return false;
}

/* Gefiltert + gruppiert (Gruppen in Reihenfolge des ersten Auftretens). */
const groups = computed(() => {
  const q = query.value.trim().toLowerCase();
  const order = [];
  const map = new Map();
  for (const it of props.items) {
    if (props.filter && !matches(it.label, q)) continue;
    const g = it.group || "";
    if (!map.has(g)) { map.set(g, []); order.push(g); }
    map.get(g).push(it);
  }
  return order.map((g) => ({ label: g, items: map.get(g) }));
});
const flat = computed(() => groups.value.flatMap((g) => g.items));

watch(query, (v) => { active.value = 0; emit("update:query", v); });
watch(() => props.open, (v) => {
  if (v) { query.value = ""; active.value = 0; nextTick(() => inputEl.value?.focus()); }
});

function close() { emit("update:open", false); }
function choose(item) { if (!item) return; emit("select", item); close(); }
function nav(dir) {
  const n = flat.value.length;
  if (!n) return;
  active.value = (active.value + dir + n) % n;
}
function onEnter() { choose(flat.value[active.value]); }

function onKeydown(e) {
  if (props.hotkey && (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    emit("update:open", !props.open);
    return;
  }
  if (props.open && e.key === "Escape") { e.preventDefault(); close(); }
}
onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div v-if="open" class="pp-cmdk-overlay" @click.self="close">
    <div class="pp-cmdk" role="dialog" aria-modal="true" aria-label="Befehlspalette">
      <div class="pp-cmdk__input-row">
        <Search />
        <input ref="inputEl" v-model="query" class="pp-cmdk__input" type="text"
               :placeholder="placeholder"
               @keydown.down.prevent="nav(1)" @keydown.up.prevent="nav(-1)"
               @keydown.enter.prevent="onEnter" />
        <span class="pp-cmdk__kbd">Esc</span>
      </div>
      <div class="pp-cmdk__list">
        <template v-for="g in groups" :key="g.label">
          <div v-if="g.label" class="pp-cmdk__group">{{ g.label }}</div>
          <button v-for="it in g.items" :key="it.id" type="button" class="pp-cmdk__item"
                  :class="{ 'is-active': flat[active] === it }"
                  @mouseenter="active = flat.indexOf(it)" @click="choose(it)">
            <component :is="it.icon" v-if="it.icon" />
            <span class="pp-cmdk__item-label">{{ it.label }}</span>
            <span v-if="it.kbd" class="pp-kbd">{{ it.kbd }}</span>
          </button>
        </template>
        <div v-if="!flat.length" class="pp-cmdk__group">Keine Treffer</div>
      </div>
    </div>
  </div>
</template>
