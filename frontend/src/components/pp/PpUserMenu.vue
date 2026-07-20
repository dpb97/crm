<!-- PP_REV: PpUserMenu@1 -->
<!--
  PpUserMenu.vue — angemeldeter Nutzer mit Dropdown-Menü (SSOT-Baustein).

  Extrahiert 05.07.2026 aus dem theme-preview-Katalog „User-Avatar & Menü"
  (ThemePreviewExtra, vorher Inline-Markup) — Entscheid Marco: fertige
  Preview-Elemente als Bausteine verwenden, nicht neu bauen.

  Avatar (Initialen, rund) + Name/Rolle + Chevron; Klick öffnet Menü.
  Einträge über `items` (key/label/danger, key "sep" = Trenner);
  Auswahl emittiert `select(key)` — Navigation macht der Host.
  Root `.pp-usermenu__*` (scoped, kollisionsfrei). STRIKT --pp-*-Tokens.
-->
<script setup>
import { ref } from "vue";

defineProps({
  initials: { type: String, required: true },
  name:     { type: String, default: "" },
  role:     { type: String, default: "" },
  items:    { type: Array, default: () => [
    { key: "profil", label: "Profil" },
    { key: "einstellungen", label: "Einstellungen" },
    { key: "sep" },
    { key: "abmelden", label: "Abmelden", danger: true },
  ] },
});
const emit = defineEmits(["select"]);
const open = ref(false);

function pick(it) {
  open.value = false;
  emit("select", it.key);
}
</script>

<template>
  <div class="pp-usermenu" @keydown.esc="open = false">
    <button class="pp-usermenu__trigger" type="button" :aria-expanded="open" @click="open = !open">
      <span class="pp-usermenu__avatar">{{ initials }}</span>
      <span v-if="name" class="pp-usermenu__meta">
        <span class="pp-usermenu__name">{{ name }}</span>
        <span v-if="role" class="pp-usermenu__role">{{ role }}</span>
      </span>
      <svg class="pp-usermenu__chevron" :class="{ 'is-open': open }" viewBox="0 0 24 24"
           width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>
    <div v-if="open" class="pp-usermenu__backdrop" @click="open = false"></div>
    <div v-show="open" class="pp-usermenu__menu" role="menu">
      <template v-for="(it, i) in items" :key="i">
        <div v-if="it.key === 'sep'" class="pp-usermenu__sep"></div>
        <button v-else class="pp-usermenu__item" :class="{ 'is-danger': it.danger }"
                role="menuitem" type="button" @click="pick(it)">{{ it.label }}</button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.pp-usermenu { position: relative; display: inline-block; }
.pp-usermenu__trigger {
  appearance: none; cursor: pointer; font-family: inherit;
  display: inline-flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-1) var(--pp-space-2);
  border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default);
  background: var(--pp-bg-surface);
  transition: border-color var(--pp-duration-fast) var(--pp-ease-standard);
}
.pp-usermenu__trigger:hover { border-color: var(--pp-border-strong); }
.pp-usermenu__avatar {
  display: inline-grid; place-items: center;
  width: 28px; height: 28px; flex-shrink: 0;
  border-radius: var(--pp-radius-full);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent);
  font-size: var(--pp-fs-12); font-weight: 600; letter-spacing: 0.02em;
}
.pp-usermenu__meta { display: flex; flex-direction: column; align-items: flex-start; line-height: 1.2; }
.pp-usermenu__name { font-size: var(--pp-fs-13, 13px); font-weight: 600; color: var(--pp-text-primary); }
.pp-usermenu__role { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.pp-usermenu__chevron { transition: transform var(--pp-duration-fast) var(--pp-ease-standard);
  color: var(--pp-text-tertiary); flex-shrink: 0; }
.pp-usermenu__chevron.is-open { transform: rotate(180deg); }
.pp-usermenu__backdrop { position: fixed; inset: 0; z-index: var(--pp-z-overlay); }
.pp-usermenu__menu {
  position: absolute; top: calc(100% + var(--pp-space-1)); right: 0; z-index: calc(var(--pp-z-overlay) + 1);
  min-width: 200px; display: flex; flex-direction: column;
  padding: var(--pp-space-1);
  background: var(--pp-bg-elevated);
  border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-lg);
}
.pp-usermenu__item {
  appearance: none; cursor: pointer; text-align: left; font-family: inherit;
  font-size: var(--pp-fs-14); color: var(--pp-text-primary);
  padding: var(--pp-space-2) var(--pp-space-3);
  border: 0; border-radius: var(--pp-radius-xs); background: transparent;
  transition: background var(--pp-duration-fast) var(--pp-ease-standard);
}
.pp-usermenu__item:hover { background: var(--pp-bg-hover); }
.pp-usermenu__item.is-danger { color: var(--pp-state-danger); }
.pp-usermenu__sep { height: 1px; margin: var(--pp-space-1) 0; background: var(--pp-border-subtle); }
</style>
