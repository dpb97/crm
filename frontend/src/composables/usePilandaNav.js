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
      allgemein.value = data?.allgemein || []
      wissen.value = data?.wissen || []
      loaded.value = true
    } catch (e) {
      available.value = false
    }
  }
  return { zones, modules, allgemein, wissen, loaded, available, load }
}
