<!-- PP_REV: PpAppbar@3 -->
<!--
  PpAppbar.vue — Topbar der App-Shell (SSOT-Baustein).

  @2 (Nav-Umbau 2.0 / N3, Klickdummy-Handoff 13.07.2026): Die frühere
  Headerbar entfällt (der Modul-Titel lebt jetzt im Sidebar-Dropdown). Die
  Topbar trägt: links die Marke (Klick = "home"), Mitte optional die globale
  Suche (Lupe öffnet das Such-Overlay), rechts die Fenster-Controls (E1) und
  den User-Chip mit Menü.

  Fenster-Controls (E1, ECHTES Shell-Feature — Umsetzung im Host über die
  Events): klein/minimiert → "minimize" (Host zeigt Wiederherstellen-Pille),
  mittelgroß-Toggle → "toggle-size", schließen ✕ → "logout" (Abmelden/Login).

  ECHTE props-in / events-out. Marke/Suche als Slots überschreibbar; der
  User-Chip nutzt den SSOT-Baustein <PpUserMenu>.

  @3 (21.07.2026): optionale Orientierung „Zone › Modul › Seite" in der Topbar
  (Regel 2). Das LETZTE Segment wird ellipsiert (max-width + title=Volltext), die
  Zeile bricht NIE um — Referenz: setChrome/crumbCut im Klickdummy.

  Props:
    brandSrc   String  Logo-URL (Wortmarke) — links
    brandLabel String  Fallback-Text, wenn kein Logo
    crumb      Array<String>  Orientierung, z. B. ["Vertrieb","CRM","Fjellanlegg…"].
               Leer = keine Crumb-Zeile. Letztes Segment = aktuelle Seite (ellipsiert).
    search     Boolean (default true)  Lupe/Such-Einstieg zeigen
    windowControls Boolean (default true)  Fenster-Controls zeigen
    user       Object  { initials, name, role, items? } → PpUserMenu
    height     Number (default 52)

  Emits:
    home            (Marke geklickt)
    search          (Lupe/Strg+K — Host öffnet PpSearchOverlay)
    minimize        (Fenster klein)
    toggle-size     (Fenster mittelgroß-Toggle)
    logout          (Schließen ✕)
    user-select (key)   durchgereicht von PpUserMenu

  STRIKT --pp-*-Tokens, hell/dunkel.
-->
<script setup>
import PpUserMenu from "./PpUserMenu.vue";
import Search from "~icons/lucide/search";
import Minus from "~icons/lucide/minus";
import Square from "~icons/lucide/square";
import X from "~icons/lucide/x";

defineProps({
  brandSrc:   { type: String, default: "" },
  brandLabel: { type: String, default: "PILANDA" },
  crumb:      { type: Array, default: () => [] },
  search:     { type: Boolean, default: true },
  windowControls: { type: Boolean, default: true },
  user:       { type: Object, default: () => ({ initials: "?", name: "", role: "" }) },
  height:     { type: Number, default: 52 },
});
const emit = defineEmits(["home", "search", "minimize", "toggle-size", "logout", "user-select"]);
</script>

<template>
  <header class="pp-appbar" :style="{ height: height + 'px' }">
    <!-- Marke (Home-Link) -->
    <button class="pp-appbar__brand" type="button" title="Zur Startseite" @click="emit('home')">
      <slot name="brand">
        <img v-if="brandSrc" class="pp-appbar__mark" :src="brandSrc" :alt="brandLabel" />
        <span class="pp-appbar__wm">{{ brandLabel }}</span>
      </slot>
    </button>

    <!-- Orientierung: Zone › Modul › Seite (letztes Segment ellipsiert, nie umbrechend) -->
    <nav v-if="crumb.length" class="pp-appbar__crumb" aria-label="Pfad">
      <template v-for="(seg, i) in crumb" :key="i">
        <span v-if="i > 0" class="pp-appbar__crumb-sep" aria-hidden="true">›</span>
        <span v-if="i < crumb.length - 1" class="pp-appbar__crumb-seg">{{ seg }}</span>
        <span v-else class="pp-appbar__crumb-cur" :title="seg">{{ seg }}</span>
      </template>
    </nav>

    <div class="pp-appbar__spacer"></div>

    <!-- rechts: Suche · Fenster-Controls · User -->
    <div class="pp-appbar__right">
      <button v-if="search" class="pp-appbar__icon-btn" type="button"
              title="Suche (Strg K)" aria-label="Suche öffnen" @click="emit('search')">
        <Search />
      </button>

      <div v-if="windowControls" class="pp-appbar__winctrls" role="group" aria-label="Fenster">
        <button class="pp-appbar__win" type="button" title="Fenster klein" aria-label="Fenster minimieren"
                @click="emit('minimize')"><Minus /></button>
        <button class="pp-appbar__win" type="button" title="Fenster mittelgroß" aria-label="Fenstergröße umschalten"
                @click="emit('toggle-size')"><Square /></button>
        <button class="pp-appbar__win pp-appbar__win--close" type="button" title="Pilanda schließen"
                aria-label="Schließen (Abmelden)" @click="emit('logout')"><X /></button>
      </div>

      <PpUserMenu :initials="user.initials" :name="user.name" :role="user.role"
                  :items="user.items || undefined" @select="(k) => emit('user-select', k)" />
    </div>
  </header>
</template>

<style scoped>
.pp-appbar { position: relative; display: flex; align-items: center; gap: var(--pp-space-4);
  padding: 0 var(--pp-space-4); background: var(--pp-bg-surface);
  border-bottom: 1px solid var(--pp-border-subtle); box-sizing: border-box; }
.pp-appbar::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 2px; background: var(--pp-brand-primary); }

.pp-appbar__brand { appearance: none; cursor: pointer; font-family: inherit; border: 0; background: transparent;
  display: flex; align-items: center; gap: var(--pp-space-2); padding: var(--pp-space-1); flex: 0 0 auto;
  border-radius: var(--pp-radius-ui); }
.pp-appbar__brand:hover { background: var(--pp-bg-hover); }
.pp-appbar__mark { width: 30px; height: 30px; object-fit: contain; display: block; }
.pp-appbar__wm { font-weight: var(--pp-weight-bold); letter-spacing: .18em; font-size: var(--pp-fs-15, 15px); color: var(--pp-text-primary); }

.pp-appbar__crumb { display: flex; align-items: center; gap: 7px; min-width: 0; flex: 0 1 auto;
  margin-left: var(--pp-space-4); padding-left: var(--pp-space-4);
  border-left: 1px solid var(--pp-border-subtle);
  font-size: 11.5px; font-weight: var(--pp-weight-semibold); letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--pp-text-tertiary); white-space: nowrap; overflow: hidden; }
.pp-appbar__crumb-sep { color: var(--pp-text-tertiary); font-weight: var(--pp-weight-regular); flex: 0 0 auto; }
.pp-appbar__crumb-seg { flex: 0 0 auto; }
.pp-appbar__crumb-cur { min-width: 0; max-width: 46vw; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; color: var(--pp-text-primary); }

.pp-appbar__spacer { flex: 1 1 auto; }
.pp-appbar__right { display: flex; align-items: center; gap: var(--pp-space-3); flex: 0 0 auto; }

.pp-appbar__icon-btn { appearance: none; cursor: pointer; border: 0; background: transparent;
  width: 34px; height: 34px; display: grid; place-items: center; border-radius: var(--pp-radius-ui);
  color: var(--pp-text-secondary); transition: color var(--pp-duration-fast) var(--pp-ease-standard), background var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-appbar__icon-btn:hover { color: var(--pp-brand-primary-d, var(--pp-brand-primary)); background: var(--pp-bg-hover); }
.pp-appbar__icon-btn :deep(svg) { width: 19px; height: 19px; }

.pp-appbar__winctrls { display: flex; align-items: center; gap: 2px; }
.pp-appbar__win { appearance: none; cursor: pointer; border: 0; background: transparent;
  width: 30px; height: 30px; display: grid; place-items: center; border-radius: var(--pp-radius-ui);
  color: var(--pp-text-secondary); transition: color var(--pp-duration-fast) var(--pp-ease-standard), background var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-appbar__win:hover { background: var(--pp-bg-hover); color: var(--pp-text-primary); }
.pp-appbar__win :deep(svg) { width: 14px; height: 14px; }
.pp-appbar__win--close:hover { background: var(--pp-state-danger); color: var(--pp-text-on-accent); }
</style>
