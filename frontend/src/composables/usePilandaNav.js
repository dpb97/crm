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
      // CRM-owned tool the shell nav-spec doesn't list yet — keep Quick Note reachable.
      const _vt = modules.value.find((m) => m.id === 'vertrieb')
      if (_vt) {
        if (!_vt.g || !_vt.g.length) _vt.g = [{ sec: '', items: [] }]
        const _items = _vt.g[0].items || (_vt.g[0].items = [])
        if (!_items.some((i) => (i.t || i.target) === '/crm/quick-note')) {
          const _at = _items.findIndex((i) => (i.t || i.target) === '/crm/sales-meeting')
          _items.splice(_at >= 0 ? _at + 1 : _items.length, 0, {
            n: 'Quick Note', t: '/crm/quick-note', k: 'cust', x: true, d: 'Schnellnotiz',
          })
        }
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
