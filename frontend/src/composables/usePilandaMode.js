// Pilanda mode (embedded in the Pilanda shell) is the DEFAULT — the CRM runs
// inside the Pilanda ERP (Marco, 20.07.2026: EINE Shell, kein Umschalt-Button).
// "CRM-only" (standalone, Dominiks Labor-Ansicht) bleibt als Escape erreichbar:
// ?mode=crm in der URL oder localStorage crm_pilanda_mode='0'.
import { ref } from 'vue'

const KEY = 'crm_pilanda_mode'

const _url = new URLSearchParams(window.location.search).get('mode')
if (_url === 'pilanda') localStorage.removeItem(KEY)
else if (_url === 'crm') localStorage.setItem(KEY, '0')

// Module-level singleton so every consumer shares one reactive flag.
const pilandaMode = ref(localStorage.getItem(KEY) !== '0')

export function usePilandaMode() {
  function setMode(on) {
    pilandaMode.value = !!on
    if (on) localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, '0')
  }
  function toggle() {
    setMode(!pilandaMode.value)
  }
  return { pilandaMode, setMode, toggle }
}
