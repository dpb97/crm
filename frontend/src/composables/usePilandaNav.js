// Pull the Pilanda shell navigation and map it to the shape PpSidebar@5
// expects. SSOT: pilanda.api.get_nav_v2 — EXAKT dasselbe Modell wie
// frappe.boot.pilanda_nav['v2'] im Desk (Module mit groups-Baum; das
// frühere get_modules()-Landing-Format hatte keine Menüpunkte → die
// Sidebar blieb leer, 20.07.2026). Fails soft when pilanda isn't installed.
import { ref } from 'vue'
import { call } from 'frappe-ui'

const zones = ref([])
const modules = ref([])
// Rohe SSOT-Blöcke „Allgemein" + „Wissen" (wie im Desk): der Host baut daraus
// die ANZEIGE-Struktur (allgemeinDisplay/wissenDisplay) — get_nav_v2 liefert
// beide (allgemein = flache ALLGEMEIN-Liste, wissen = {id,sub}-Verweise).
const allgemein = ref([])
const wissen = ref([])
const loaded = ref(false)
const available = ref(true)

export function usePilandaNav() {
  async function load() {
    if (loaded.value) return
    try {
      const data = await call('pilanda.api.get_nav_v2')
      zones.value = (data?.zonen || []).map((z) => ({
        code: z.code,
        key: z.key ?? z.code,
        label: z.label,
        subtitle: z.subtitle,
      }))
      // PpSidebar-Vertrag: { id, name, icon, zone, g: [{ sec, items }] }
      modules.value = (data?.module || []).map((m) => ({
        ...m,
        id: m.slug ?? m.id,
        name: m.label ?? m.name,
        icon: m.icon,
        zone: m.zone,
        status: m.status,
        target: m.target || m.path,
        g: m.groups || m.g || [],
      }))
      // Vertrieb nav = the klickdummy design master IA (pilanda-navigation.html,
      // Vertrieb module). The backend get_nav_v2 is still on the older flat
      // ordering, so override the Vertrieb module's groups here to match the
      // master: sub:1 marks a child of the preceding level-1 item; PpSidebar's
      // buildTree renders the nesting and keeps icons on level 1 only.
      // "#" targets are master placeholders still awaiting a page (Chancen).
      const _vt = modules.value.find((m) => m.id === 'vertrieb')
      if (_vt) {
        _vt.g = [{ sec: '', items: [
          { n: 'Pilot',               t: '/app/pilot-workbench',   icon: 'radar',         k: 'cust', x: true, d: 'Ausschreibungs-Scout — liefert Chancen in den Vertriebsfluss' },
          { n: 'Chancen',             t: '/crm/chances',           icon: 'activity',      k: 'cust', x: true, d: 'Alle Chancen mit Quelle als Info — daraus entstehen Leads' },
          { n: 'Leads',               t: '/crm/leads',             icon: 'user-plus',     k: 'cust', x: true, d: 'Phase Lead' },
          { n: 'Calls',               t: '/crm/call-logs',         k: 'cust', x: true, sub: 1, d: 'Anruf-Protokolle über alle Leads' },
          { n: 'Notizen',             t: '/crm/notes',             k: 'cust', x: true, sub: 1, d: 'Notizen über Leads, Deals und Projekte' },
          { n: 'Aufgaben',            t: '/crm/tasks',             k: 'cust', x: true, sub: 1, d: 'Aufgaben über Leads, Deals und Projekte' },
          { n: 'Sales Meeting',       t: '/crm/sales-meeting',     icon: 'calendar-days', k: 'cust', x: true, d: 'Vertriebsbesprechung mit Forecast-Einblicken' },
          { n: 'Vertriebsprojekte',   t: '/crm/projects',          icon: 'folder-kanban', k: 'cust', x: true, d: 'Vertriebsprojekte (Deal=Projekt)' },
          { n: 'Markteinteilung',     t: '/crm/market-assignment', icon: 'globe',         k: 'cust', x: true, d: 'Territorien mit genau EINER verantwortlichen Person' },
          { n: 'Projektlandkarte',    t: '/crm/projects-map',      k: 'cust', x: true, sub: 1, d: 'Anlagen & Projekte auf der Landkarte' },
          { n: 'Verkäufer & Agenten', t: '/crm/sales-agents',       k: 'cust', x: true, sub: 1, d: 'Verkäufer, Agenten und JV je Territorium' },
          { n: 'Prognose',            t: '/crm/forecasting',       icon: 'trending-up',   k: 'cust', x: true, d: 'Umsatz-Forecast über die Pipeline' },
          { n: 'Netzwerk',            t: '/crm/network',           icon: 'share-2',       k: 'cust', x: true, d: 'Kontaktnetzwerk — Netzwerk-Ansicht im CRM' },
          { n: 'Firmen',              t: '/crm/organizations',     k: 'cust', x: true, sub: 1, d: 'Firmen im CRM' },
          { n: 'Personen',            t: '/crm/contacts',          k: 'cust', x: true, sub: 1, d: 'Ansprechpartner im CRM' },
          { n: 'Produktportfolio',    t: '/app/product-portfolio', icon: 'radar',         k: 'cust', x: true, d: 'Produktübersicht & Lebenszyklus (PLM)' },
        ] }]
      }
      allgemein.value = data?.allgemein || []
      wissen.value = data?.wissen || []

      // Phased rollout (26.07.2026): only the Vertrieb module is live today.
      // Hide every other module — plus the now-empty zones and the
      // cross-module "Allgemein" / "Wissen" blocks — until each module is
      // actually rolled out. Reversible: add its id to VISIBLE_MODULES when it
      // goes live. Quick Note stays because it is injected into Vertrieb above.
      const VISIBLE_MODULES = new Set(['vertrieb'])
      modules.value = modules.value.filter((m) => VISIBLE_MODULES.has(m.id))
      const zonesInUse = new Set(modules.value.map((m) => m.zone).filter((z) => z != null))
      zones.value = zones.value.filter((z) => zonesInUse.has(z.code) || zonesInUse.has(z.key))
      allgemein.value = []
      wissen.value = []

      loaded.value = true
    } catch (e) {
      available.value = false
    }
  }
  return { zones, modules, allgemein, wissen, loaded, available, load }
}
