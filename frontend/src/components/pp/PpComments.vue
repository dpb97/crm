<!-- PP_REV: PpComments@1 -->
<!--
  PpComments.vue — Kommentar-Thread mit @Mention (SSOT-Baustein).

  ECHTE props-in / events-out Komponente: kein Store, keine Daten.
    props:  comments = [{ id, author, time, text, mentions? }]
            users    = String[]  (Namen für das @-Mention-Dropdown)
    emits:  submit (String)      — neuer Kommentartext

  Darstellung nach .pp-comments-Demo: Avatar (Initialen) + Kopf (Name/Zeit) +
  Text; @Mentions werden ohne v-html als getönte Spans gerendert (Tokenizer,
  kein HTML-Injection). Eingabezeile mit Live-@-Dropdown (Fragment vor dem
  Cursor → gefilterte User; Klick/Enter fügt „@Name " ein).
  Struktur-CSS global in components.css (.pp-comments / .pp-comment* /
  .pp-mention / .pp-comment-form). STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  comments: { type: Array, default: () => [] },
  users:    { type: Array, default: () => [] },
});
const emit = defineEmits(["submit"]);

/* ---- Anzeige-Helfer ---- */
function initials(name) {
  return String(name || "?")
    .split(/\s+/).filter(Boolean).slice(0, 2)
    .map((w) => w[0].toUpperCase()).join("") || "?";
}
// Text → Token-Liste; @Wort wird als Mention markiert (kein v-html).
function tokenize(text) {
  const parts = String(text || "").split(/(@[\p{L}\d._-]+)/u);
  return parts
    .filter((p) => p !== "")
    .map((p) => ({ t: p, mention: /^@[\p{L}\d._-]+$/u.test(p) }));
}

/* ---- Eingabe + @-Mention-Dropdown ---- */
const draft = ref("");
const inputRef = ref(null);
const caret = ref(0);

const mentionFrag = computed(() => {
  const before = draft.value.slice(0, caret.value);
  const m = before.match(/@([\p{L}\d._-]*)$/u);
  return m ? m[1] : null;
});
const mentionOpts = computed(() => {
  if (mentionFrag.value === null) return [];
  const q = mentionFrag.value.toLowerCase();
  return props.users.filter((u) => u.toLowerCase().includes(q)).slice(0, 6);
});

function syncCaret(e) { caret.value = e.target.selectionStart ?? draft.value.length; }
function onInput(e) { draft.value = e.target.value; syncCaret(e); }

function insertMention(name) {
  const before = draft.value.slice(0, caret.value).replace(/@[\p{L}\d._-]*$/u, "");
  const after = draft.value.slice(caret.value);
  const insert = `@${name} `;
  draft.value = before + insert + after;
  const pos = (before + insert).length;
  // Cursor hinter die Einfügung setzen.
  requestAnimationFrame(() => {
    if (inputRef.value) { inputRef.value.focus(); inputRef.value.setSelectionRange(pos, pos); caret.value = pos; }
  });
}

function submit() {
  const t = draft.value.trim();
  if (!t) return;
  emit("submit", t);
  draft.value = "";
  caret.value = 0;
}
</script>

<template>
  <div class="pp-comments-wrap">
    <div class="pp-comments">
      <div v-for="c in comments" :key="c.id" class="pp-comment">
        <span class="pp-comment__avatar">{{ initials(c.author) }}</span>
        <div class="pp-comment__body">
          <div class="pp-comment__head">
            <span class="pp-comment__name">{{ c.author }}</span>
            <span class="pp-comment__time">{{ c.time }}</span>
          </div>
          <div class="pp-comment__text">
            <template v-for="(tok, i) in tokenize(c.text)" :key="i"><span v-if="tok.mention" class="pp-mention">{{ tok.t }}</span><template v-else>{{ tok.t }}</template></template>
          </div>
        </div>
      </div>
    </div>

    <div class="pp-comment-form">
      <div class="pp-comments__inputwrap">
        <input
          ref="inputRef"
          v-model="draft"
          placeholder="Kommentar… (@ für Mention)"
          @input="onInput"
          @click="syncCaret"
          @keyup="syncCaret"
          @keydown.enter="submit"
        >
        <div v-if="mentionOpts.length" class="pp-comments__mentions">
          <button
            v-for="u in mentionOpts"
            :key="u"
            type="button"
            class="pp-comments__mention-opt"
            @mousedown.prevent="insertMention(u)"
          >
            <span class="pp-comments__mention-av">{{ initials(u) }}</span>{{ u }}
          </button>
        </div>
      </div>
      <button type="button" class="pp-comments__send" @click="submit">Senden</button>
    </div>
  </div>
</template>

<style scoped>
.pp-comments__inputwrap { position: relative; flex: 1; }
.pp-comments__inputwrap input { width: 100%; box-sizing: border-box; }
.pp-comments__mentions {
  position: absolute; bottom: calc(100% + var(--pp-space-1)); left: 0; right: 0;
  z-index: var(--pp-z-overlay); background: var(--pp-bg-elevated);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-lg); padding: var(--pp-space-1); max-height: 200px; overflow: auto;
}
.pp-comments__mention-opt {
  display: flex; align-items: center; gap: var(--pp-space-2); width: 100%; text-align: left;
  appearance: none; border: 0; background: transparent; cursor: pointer; font-family: inherit;
  font-size: var(--pp-fs-14); color: var(--pp-text-secondary);
  padding: var(--pp-space-1) var(--pp-space-2); border-radius: var(--pp-radius-ui);
}
.pp-comments__mention-opt:hover { background: var(--pp-bg-hover); color: var(--pp-text-primary); }
.pp-comments__mention-av {
  width: 22px; height: 22px; flex-shrink: 0; border-radius: var(--pp-radius-full);
  display: grid; place-items: center; font-size: 10px; font-weight: var(--pp-weight-semibold);
  background: rgb(var(--pp-brand-primary-rgb) / 0.12); color: var(--pp-brand-primary);
}
.pp-comments__send {
  appearance: none; cursor: pointer; font-family: inherit; font-weight: var(--pp-weight-semibold);
  font-size: var(--pp-fs-14); padding: 0 var(--pp-space-4); border: 0; border-radius: var(--pp-radius-ui);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent);
}
.pp-comments__send:hover { background: var(--pp-brand-primary-d); }
</style>
