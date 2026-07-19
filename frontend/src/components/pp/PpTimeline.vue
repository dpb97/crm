<!-- PP_REV: PpTimeline@1 -->
<!--
  PpTimeline.vue — vertikale Aktivitäts-Timeline (SSOT-Baustein).

  Einträge {kind, dir, subject, who, ago}. kind→lucide-Icon (email→mail,
  call→phone, note→sticky-note, task→square-check, event→calendar; sonst info).
  Richtungs-Badge REIN/RAUS für dir 'in'/'out' bei email/call. Reine Anzeige,
  keine Events.

  Struktur-CSS in pilanda_theme_components.css (.pp-timeline__*, unlayered SSOT).
  STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
import IconMail  from "~icons/lucide/mail";
import IconPhone from "~icons/lucide/phone";
import IconNote  from "~icons/lucide/sticky-note";
import IconTask  from "~icons/lucide/square-check";
import IconEvent from "~icons/lucide/calendar";
import IconInfo  from "~icons/lucide/info";

defineProps({
  items: { type: Array, required: true }, // [{ kind, dir, subject, who, ago }]
});

const ICONS = { email: IconMail, call: IconPhone, note: IconNote, task: IconTask, event: IconEvent };
function dirBadge(a) {
  if ((a.kind === "email" || a.kind === "call") && a.dir === "in")  return "REIN";
  if ((a.kind === "email" || a.kind === "call") && a.dir === "out") return "RAUS";
  return null;
}
</script>

<template>
  <ol class="pp-timeline">
    <li v-for="(a, i) in items" :key="i" class="pp-timeline__item">
      <span class="pp-timeline__icon"><component :is="ICONS[a.kind] || IconInfo" /></span>
      <div class="pp-timeline__body">
        <div class="pp-timeline__top">
          <span v-if="dirBadge(a)" :class="['pp-timeline__dir', 'is-' + a.dir]">{{ dirBadge(a) }}</span>
          <span class="pp-timeline__subject">{{ a.subject }}</span>
        </div>
        <div class="pp-timeline__meta">
          <span class="pp-timeline__who">{{ a.who }}</span>
          <span class="pp-timeline__dot">·</span>
          <span class="pp-timeline__ago">{{ a.ago }}</span>
        </div>
      </div>
    </li>
  </ol>
</template>
