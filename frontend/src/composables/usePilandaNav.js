// Pull the Pilanda shell navigation (SSOT: pilanda.api.get_modules) and map it
// to the shape PpSidebar expects. Only used in Pilanda mode; fails soft when
// the pilanda app isn't installed.
import { ref } from 'vue'
import { call } from 'frappe-ui'

const zones = ref([])
const modules = ref([])
const loaded = ref(false)
const available = ref(true)

export function usePilandaNav() {
  async function load() {
    if (loaded.value) return
    try {
      const data = await call('pilanda.api.get_modules')
      zones.value = (data?.zones || []).map((z) => ({
        code: z.code,
        key: z.key,
        label: z.label,
        subtitle: z.subtitle,
      }))
      modules.value = (data?.modules || []).map((m) => ({
        id: m.slug,
        name: m.label,
        icon: m.icon, // string name; PpSidebar falls back to a dot without a resolver
        zone: m.zone,
        status: m.status,
        target: m.target || m.path,
        path: m.path,
        accessible: m.accessible,
      }))
      loaded.value = true
    } catch (e) {
      available.value = false
    }
  }
  return { zones, modules, loaded, available, load }
}
