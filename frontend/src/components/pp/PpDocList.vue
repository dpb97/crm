<!-- PP_REV: PpDocList@1 -->
<!--
  PpDocList.vue — Dokument-Liste (SSOT-Baustein).

  Für Norm-PDFs, Zeichnungen, Prüfberichte u. ä.: je Zeile Icon, Titel und eine
  Meta-Zeile (Dokumentart, Sprache, Ausgabe, Größe …). Klick öffnet (Link oder
  @open); rechts ein Slot für Zeilen-Aktionen.

  ECHTE props-in / events-out Komponente — kein Store, kein Backend.

  Props:
    docs  Array<{ id, title, meta?, icon?, href?, kind? }>
          · meta   Array<string | { label?, value }>  → als Chips gezeigt
          · icon   Komponente (lucide) — sonst Ableitung aus `kind`/Endung
          · href   optionaler Link (öffnet in neuem Tab statt @open)
          · kind   'pdf' | 'dwg' | 'doc' | 'xls' | 'img' (steuert Default-Icon)

  Emits:
    open    (doc)               Zeile geöffnet (nur wenn kein href gesetzt)
    action  ({ action, doc })   optional aus dem #actions-Slot (App verdrahtet)

  Slots:
    #actions={ doc }   rechte Zeilen-Aktionen (Buttons); die App emittiert selbst

  Scoped, Prefix `pp-doclist`. STRIKT --pp-*-Tokens, hell + dunkel.
-->
<script setup>
import IconFileText from "~icons/lucide/file-text";
import IconRuler from "~icons/lucide/ruler";
import IconFileSpreadsheet from "~icons/lucide/file-spreadsheet";
import IconImage from "~icons/lucide/image";
import IconFile from "~icons/lucide/file";
import IconExternalLink from "~icons/lucide/external-link";

defineProps({
  docs: { type: Array, default: () => [] }, // [{ id, title, meta?, icon?, href?, kind? }]
});
const emit = defineEmits(["open", "action"]);

const KIND_ICON = {
  pdf: IconFileText,
  dwg: IconRuler,
  doc: IconFileText,
  xls: IconFileSpreadsheet,
  img: IconImage,
};
function iconOf(doc) {
  if (doc.icon) return doc.icon;
  if (doc.kind && KIND_ICON[doc.kind]) return KIND_ICON[doc.kind];
  return IconFile;
}
const metaLabel = (m) => (typeof m === "object" ? m.value : m);
const metaKey = (m) => (typeof m === "object" ? m.label : null);

function onRow(doc) {
  if (doc.href) return; // Link übernimmt via <a>
  emit("open", doc);
}
</script>

<template>
  <ul class="pp-doclist">
    <li v-for="doc in docs" :key="doc.id" class="pp-doclist__item">
      <component
        :is="doc.href ? 'a' : 'button'"
        :href="doc.href || undefined"
        :target="doc.href ? '_blank' : undefined"
        :rel="doc.href ? 'noopener' : undefined"
        :type="doc.href ? undefined : 'button'"
        class="pp-doclist__main"
        @click="onRow(doc)"
      >
        <span class="pp-doclist__icon"><component :is="iconOf(doc)" /></span>
        <span class="pp-doclist__body">
          <span class="pp-doclist__title">
            {{ doc.title }}
            <IconExternalLink v-if="doc.href" class="pp-doclist__ext" />
          </span>
          <span v-if="doc.meta && doc.meta.length" class="pp-doclist__meta">
            <span v-for="(m, i) in doc.meta" :key="i" class="pp-doclist__chip">
              <span v-if="metaKey(m)" class="pp-doclist__chip-key">{{ metaKey(m) }}:</span>
              {{ metaLabel(m) }}
            </span>
          </span>
        </span>
      </component>
      <span class="pp-doclist__actions">
        <slot name="actions" :doc="doc" />
      </span>
    </li>

    <li v-if="!docs.length" class="pp-doclist__empty">Keine Dokumente</li>
  </ul>
</template>

<style scoped>
.pp-doclist {
  list-style: none; margin: 0; padding: 0;
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); overflow: hidden;
  font-family: var(--pp-font-body); color: var(--pp-text-primary);
}
.pp-doclist__item {
  display: flex; align-items: center; gap: var(--pp-space-2);
  border-bottom: 1px solid var(--pp-border-subtle);
}
.pp-doclist__item:last-child { border-bottom: 0; }
.pp-doclist__item:hover { background: var(--pp-bg-hover); }

.pp-doclist__main {
  appearance: none; cursor: pointer; text-align: left; text-decoration: none;
  display: flex; align-items: center; gap: var(--pp-space-3);
  flex: 1 1 auto; min-width: 0;
  padding: var(--pp-space-3); border: 0; background: transparent;
  color: inherit; font-family: inherit;
}
.pp-doclist__icon {
  display: grid; place-items: center; flex-shrink: 0;
  width: 34px; height: 34px; border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-sunken); color: var(--pp-brand-primary);
}
.pp-doclist__icon :deep(svg) { width: 18px; height: 18px; }
.pp-doclist__body { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.pp-doclist__title {
  display: flex; align-items: center; gap: var(--pp-space-1);
  font-size: var(--pp-fs-14); font-weight: var(--pp-weight-medium, 500); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pp-doclist__ext { width: 13px; height: 13px; color: var(--pp-text-tertiary); flex-shrink: 0; }
.pp-doclist__meta { display: flex; flex-wrap: wrap; gap: var(--pp-space-1); }
.pp-doclist__chip {
  font-size: 11px; color: var(--pp-text-secondary);
  background: var(--pp-bg-sunken); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-full); padding: 1px 8px;
}
.pp-doclist__chip-key { color: var(--pp-text-tertiary); }
.pp-doclist__actions { display: flex; align-items: center; gap: var(--pp-space-1); padding-right: var(--pp-space-3); flex-shrink: 0; }

.pp-doclist__empty { padding: var(--pp-space-6); text-align: center; color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); }
</style>
