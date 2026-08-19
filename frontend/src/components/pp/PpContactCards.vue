<!-- PP_REV: PpContactCards@1 -->
<!--
  PpContactCards.vue — Personenverzeichnis mit umschaltbarer Ansicht (SSOT-Baustein).

  Zeigt eine Personenliste in zwei Ansichten (Outlook-Stil), umschaltbar über ein
  Segment „Liste | Kontaktkarten"; Suche/Filter wirken in BEIDEN Ansichten:
    · Kontaktkarten — Karte je Person: eckiger Initialen-Avatar (--pp-Radius,
      accent-soft), Name, „Rolle · Firma", KV-Zeilen (E-Mail/Telefon/Land),
      Fußzeile „letzter Kontakt · Projekte" + Aktionsknopf.
    · Liste — kompakte Zeilen (Avatar · Name · Rolle·Firma · E-Mail · Land · Aktion).

  Reines Anzeige-/Auswahl-Element (props-in / events-out), kein Store, kein
  Backend. E-Mail/Telefon sind echte mailto:/tel:-Links (rel/target neutral).

  Props:
    people      Array   [{ id?, name, role?, company?, email?, phone?,
                          country?, lastContact?, projects? (Zahl|Array) }]
    view        String  Start-Ansicht 'cards' (default) | 'list' (v-model:view)
    actionLabel String  Beschriftung des Aktionsknopfs (default „Öffnen")
    searchable  Boolean  Suchfeld anzeigen (default true)
    placeholder String   Suchfeld-Platzhalter

  Emits: update:view · select (person) · action (person)

  STRIKT --pp-*-Tokens, hell + dunkel; kein v-html mit Nutzdaten.
-->
<script setup>
import { ref, computed } from "vue";
import IconMail from "~icons/lucide/mail";
import IconPhone from "~icons/lucide/phone";
import IconMapPin from "~icons/lucide/map-pin";
import IconGrid from "~icons/lucide/layout-grid";
import IconList from "~icons/lucide/list";
import IconSearch from "~icons/lucide/search";

const props = defineProps({
  people:      { type: Array,  default: () => [] },
  view:        { type: String, default: "cards" },
  actionLabel: { type: String, default: "Öffnen" },
  searchable:  { type: Boolean, default: true },
  placeholder: { type: String, default: "Personen suchen…" },
});
const emit = defineEmits(["update:view", "select", "action"]);

const query = ref("");

function initials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "–";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
function projectsLabel(p) {
  const v = p.projects;
  if (Array.isArray(v)) return v.length + (v.length === 1 ? " Projekt" : " Projekte");
  if (typeof v === "number") return v + (v === 1 ? " Projekt" : " Projekte");
  return v || "";
}

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return props.people;
  return props.people.filter((p) =>
    [p.name, p.role, p.company, p.email, p.country]
      .some((f) => String(f || "").toLowerCase().includes(q)));
});

function setView(v) { emit("update:view", v); }
</script>

<template>
  <div class="pp-contacts">
    <!-- Werkzeugleiste: Suche + Segment (Liste | Kontaktkarten) -->
    <div class="pp-contacts__bar">
      <label v-if="searchable" class="pp-contacts__search">
        <IconSearch class="pp-contacts__search-ic" />
        <input type="search" v-model="query" :placeholder="placeholder" aria-label="Personen suchen" />
      </label>
      <span class="pp-contacts__count">{{ filtered.length }} von {{ people.length }}</span>
      <div class="pp-contacts__seg" role="group" aria-label="Ansicht">
        <button type="button" class="pp-contacts__segbtn" :class="{ 'is-active': view === 'list' }"
                :aria-pressed="view === 'list'" title="Liste" @click="setView('list')">
          <IconList /><span>Liste</span>
        </button>
        <button type="button" class="pp-contacts__segbtn" :class="{ 'is-active': view === 'cards' }"
                :aria-pressed="view === 'cards'" title="Kontaktkarten" @click="setView('cards')">
          <IconGrid /><span>Kontaktkarten</span>
        </button>
      </div>
    </div>

    <p v-if="!filtered.length" class="pp-contacts__empty">Keine Person passt zur Suche.</p>

    <!-- Kontaktkarten -->
    <div v-else-if="view === 'cards'" class="pp-contacts__grid">
      <article v-for="(p, i) in filtered" :key="p.id || p.email || i" class="pp-contacts__card"
               tabindex="0" @click="emit('select', p)" @keydown.enter="emit('select', p)">
        <header class="pp-contacts__cardhead">
          <span class="pp-contacts__avatar" aria-hidden="true">{{ initials(p.name) }}</span>
          <span class="pp-contacts__id">
            <span class="pp-contacts__name">{{ p.name }}</span>
            <span class="pp-contacts__role">{{ [p.role, p.company].filter(Boolean).join(" · ") }}</span>
          </span>
        </header>
        <dl class="pp-contacts__kv">
          <div v-if="p.email"><dt><IconMail /></dt>
            <dd><a :href="`mailto:${p.email}`" @click.stop>{{ p.email }}</a></dd></div>
          <div v-if="p.phone"><dt><IconPhone /></dt>
            <dd><a :href="`tel:${p.phone}`" @click.stop>{{ p.phone }}</a></dd></div>
          <div v-if="p.country"><dt><IconMapPin /></dt><dd>{{ p.country }}</dd></div>
        </dl>
        <footer class="pp-contacts__foot">
          <span class="pp-contacts__meta">
            <template v-if="p.lastContact">Letzter Kontakt: {{ p.lastContact }}</template>
            <template v-if="p.lastContact && projectsLabel(p)"> · </template>
            <template v-if="projectsLabel(p)">{{ projectsLabel(p) }}</template>
          </span>
          <button type="button" class="pp-contacts__act" @click.stop="emit('action', p)">{{ actionLabel }}</button>
        </footer>
      </article>
    </div>

    <!-- Liste -->
    <ul v-else class="pp-contacts__list">
      <li v-for="(p, i) in filtered" :key="p.id || p.email || i" class="pp-contacts__row"
          tabindex="0" @click="emit('select', p)" @keydown.enter="emit('select', p)">
        <span class="pp-contacts__avatar pp-contacts__avatar--sm" aria-hidden="true">{{ initials(p.name) }}</span>
        <span class="pp-contacts__rowid">
          <span class="pp-contacts__name">{{ p.name }}</span>
          <span class="pp-contacts__role">{{ [p.role, p.company].filter(Boolean).join(" · ") }}</span>
        </span>
        <a v-if="p.email" class="pp-contacts__rowmail" :href="`mailto:${p.email}`" @click.stop>{{ p.email }}</a>
        <span v-else class="pp-contacts__rowmail pp-contacts__rowmail--muted">—</span>
        <span class="pp-contacts__rowland">{{ p.country || "—" }}</span>
        <button type="button" class="pp-contacts__act" @click.stop="emit('action', p)">{{ actionLabel }}</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.pp-contacts { display: flex; flex-direction: column; gap: var(--pp-space-3);
  font-family: var(--pp-font-body); color: var(--pp-text-primary); }

/* Werkzeugleiste */
.pp-contacts__bar { display: flex; align-items: center; gap: var(--pp-space-3); flex-wrap: wrap; }
.pp-contacts__search { position: relative; flex: 1 1 220px; min-width: 180px; display: flex; align-items: center; }
.pp-contacts__search-ic { position: absolute; left: var(--pp-space-2); width: 15px; height: 15px; color: var(--pp-text-tertiary); pointer-events: none; }
.pp-contacts__search input { width: 100%; box-sizing: border-box; font-family: inherit;
  font-size: var(--pp-fs-13, 13px); padding: 6px var(--pp-space-2) 6px calc(var(--pp-space-2) + 20px);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.pp-contacts__search input:focus-visible { outline: none; border-color: var(--pp-brand-primary); box-shadow: var(--pp-shadow-focus-ring); }
.pp-contacts__count { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }

.pp-contacts__seg { display: inline-flex; border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); overflow: hidden; margin-left: auto; }
.pp-contacts__segbtn { appearance: none; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px;
  border: 0; border-left: 1px solid var(--pp-border-subtle); background: var(--pp-bg-surface); color: var(--pp-text-secondary);
  font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-medium); padding: 6px var(--pp-space-3); }
.pp-contacts__segbtn:first-child { border-left: 0; }
.pp-contacts__segbtn:hover { background: var(--pp-bg-sunken); color: var(--pp-text-primary); }
.pp-contacts__segbtn.is-active { background: var(--pp-accent-soft); color: var(--pp-brand-primary-d, var(--pp-brand-primary)); font-weight: var(--pp-weight-semibold); }
.pp-contacts__segbtn :deep(svg) { width: 14px; height: 14px; }

.pp-contacts__empty { color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); margin: var(--pp-space-2) 0; }

/* Avatar (eckig, --pp-Radius, accent-soft) */
/* !important: a global rule ([class*="avatar"]) forces every avatar to
   --pp-radius-full (round) with !important — override it here so the contact
   avatars render square (design wish), matching the squared detail avatar. */
.pp-contacts__avatar { flex: 0 0 auto; display: inline-flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: var(--pp-radius-ui) !important; background: var(--pp-accent-soft);
  color: var(--pp-brand-primary-d, var(--pp-brand-primary)); font-size: var(--pp-fs-13, 13px);
  font-weight: var(--pp-weight-bold); letter-spacing: .02em; }
.pp-contacts__avatar--sm { width: 30px; height: 30px; font-size: var(--pp-fs-12, 12px); }

.pp-contacts__name { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-contacts__role { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Aktionsknopf (überall gleich) */
.pp-contacts__act { appearance: none; cursor: pointer; font-family: inherit; white-space: nowrap;
  font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-semibold); padding: 4px var(--pp-space-3);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-primary);
  transition: border-color var(--pp-duration-fast) var(--pp-ease-standard), color var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-contacts__act:hover { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.pp-contacts__act:focus-visible { outline: none; box-shadow: var(--pp-shadow-focus-ring); }

/* Kontaktkarten-Grid */
.pp-contacts__grid { display: grid; gap: var(--pp-space-3); grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.pp-contacts__card { display: flex; flex-direction: column; gap: var(--pp-space-3);
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); cursor: pointer;
  transition: border-color var(--pp-duration-fast) var(--pp-ease-standard), box-shadow var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-contacts__card:hover { border-color: var(--pp-border-default); box-shadow: var(--pp-shadow-sm); }
.pp-contacts__card:focus-visible { outline: none; border-color: var(--pp-brand-primary); box-shadow: var(--pp-shadow-focus-ring); }
.pp-contacts__cardhead { display: flex; align-items: center; gap: var(--pp-space-3); min-width: 0; }
.pp-contacts__id { display: flex; flex-direction: column; min-width: 0; }

.pp-contacts__kv { margin: 0; display: flex; flex-direction: column; gap: 5px; }
.pp-contacts__kv > div { display: flex; align-items: center; gap: var(--pp-space-2); min-width: 0; }
.pp-contacts__kv dt { flex: 0 0 auto; margin: 0; display: inline-flex; color: var(--pp-text-tertiary); }
.pp-contacts__kv dt :deep(svg) { width: 14px; height: 14px; }
.pp-contacts__kv dd { margin: 0; min-width: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-secondary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-contacts__kv a { color: var(--pp-text-secondary); text-decoration: none; font-variant-numeric: tabular-nums; }
.pp-contacts__kv a:hover { color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }

.pp-contacts__foot { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-2);
  padding-top: var(--pp-space-2); border-top: 1px solid var(--pp-border-subtle); }
.pp-contacts__meta { font-size: 11px; color: var(--pp-text-tertiary); min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Liste */
.pp-contacts__list { list-style: none; margin: 0; padding: 0; border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); overflow: hidden; background: var(--pp-bg-surface); }
.pp-contacts__row { display: flex; align-items: center; gap: var(--pp-space-3); cursor: pointer;
  padding: var(--pp-space-2) var(--pp-space-4); border-top: 1px solid var(--pp-border-subtle); }
.pp-contacts__row:first-child { border-top: 0; }
.pp-contacts__row:hover { background: var(--pp-bg-hover); }
.pp-contacts__row:focus-visible { outline: none; background: var(--pp-bg-hover); box-shadow: inset 0 0 0 2px var(--pp-brand-primary); }
.pp-contacts__rowid { display: flex; flex-direction: column; min-width: 0; flex: 1 1 40%; }
.pp-contacts__rowmail { flex: 1 1 30%; min-width: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-secondary);
  text-decoration: none; font-variant-numeric: tabular-nums; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-contacts__rowmail:hover { color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.pp-contacts__rowmail--muted { color: var(--pp-text-tertiary); }
.pp-contacts__rowland { flex: 0 0 auto; min-width: 44px; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
</style>
