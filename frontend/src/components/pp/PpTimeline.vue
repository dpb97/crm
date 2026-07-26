<!-- PP_REV: PpTimeline@2 -->
<!--
  PpTimeline.vue — vertikale Aktivitäts-Timeline (SSOT-Baustein).

  Einträge {kind, dir, subject, who, ago}. kind→lucide-Icon (email→mail,
  call→phone, note→sticky-note, task→square-check, event→calendar; sonst info).
  Richtungs-Badge REIN/RAUS für dir 'in'/'out' bei email/call. Reine Anzeige,
  keine Events.

  @2 (23.07.2026): Schlichte Verlaufs-/Verfolgungs-Form additiv unterstützt
  (Nachzug Klickdummy-`timelineCard`: Titel + einzeilige Kontext-/Datumszeile).
  Ein Eintrag darf statt {subject, who, ago} auch die Aliase `t` (Titel) und `d`
  (Kontext/Datum) tragen; ohne `kind` wird dann das Kalender-Icon genommen. Ist
  `who` leer, entfällt der führende Trenn-Punkt in der Metazeile (kein „· …").
  RÜCKWÄRTSKOMPATIBEL: {kind, dir, subject, who, ago} rendert exakt wie @1.

  Struktur-CSS in pilanda_theme_components.css (.pp-timeline__*, unlayered SSOT).
  STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
import { computed } from "vue";
import IconMail  from "~icons/lucide/mail";
import IconPhone from "~icons/lucide/phone";
import IconNote  from "~icons/lucide/sticky-note";
import IconTask  from "~icons/lucide/square-check";
import IconEvent from "~icons/lucide/calendar";
import IconInfo  from "~icons/lucide/info";

const props = defineProps({
  items: { type: Array, required: true }, // [{ kind, dir, subject, who, ago }] oder [{ t, d }]
});

const ICONS = { email: IconMail, call: IconPhone, note: IconNote, task: IconTask, event: IconEvent };

/* Aliase auflösen (@2): `t`→subject, `d`→ago; ohne kind → Kalender-Icon. */
const rows = computed(() =>
  props.items.map((a) => ({
    kind: a.kind || ((a.t !== undefined || a.d !== undefined) ? "event" : ""),
    dir: a.dir,
    subject: a.subject ?? a.t ?? "",
    who: a.who ?? "",
    ago: a.ago ?? a.d ?? "",
  })),
);
function dirBadge(a) {
  if ((a.kind === "email" || a.kind === "call") && a.dir === "in")  return "REIN";
  if ((a.kind === "email" || a.kind === "call") && a.dir === "out") return "RAUS";
  return null;
}
</script>

<template>
  <ol class="pp-timeline">
    <li v-for="(a, i) in rows" :key="i" class="pp-timeline__item">
      <span class="pp-timeline__icon"><component :is="ICONS[a.kind] || IconInfo" /></span>
      <div class="pp-timeline__body">
        <div class="pp-timeline__top">
          <span v-if="dirBadge(a)" :class="['pp-timeline__dir', 'is-' + a.dir]">{{ dirBadge(a) }}</span>
          <span class="pp-timeline__subject">{{ a.subject }}</span>
        </div>
        <div v-if="a.who || a.ago" class="pp-timeline__meta">
          <span v-if="a.who" class="pp-timeline__who">{{ a.who }}</span>
          <span v-if="a.who && a.ago" class="pp-timeline__dot">·</span>
          <span v-if="a.ago" class="pp-timeline__ago">{{ a.ago }}</span>
        </div>
      </div>
    </li>
  </ol>
</template>
