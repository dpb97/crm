// Mode toggle: "CRM-only" (standalone, the default) vs "Pilanda" (embedded in
// the Pilanda shell — Pilanda sidebar/nav). Kept in localStorage so it sticks;
// ?mode=pilanda / ?mode=crm in the URL forces it (handy for testing).
import { ref } from 'vue'

const KEY = 'crm_pilanda_mode'

const _url = new URLSearchParams(window.location.search).get('mode')
if (_url === 'pilanda') localStorage.setItem(KEY, '1')
else if (_url === 'crm') localStorage.removeItem(KEY)

// Module-level singleton so every consumer shares one reactive flag.
const pilandaMode = ref(localStorage.getItem(KEY) === '1')

export function usePilandaMode() {
  function setMode(on) {
    pilandaMode.value = !!on
    if (on) localStorage.setItem(KEY, '1')
    else localStorage.removeItem(KEY)
  }
  function toggle() {
    setMode(!pilandaMode.value)
  }
  return { pilandaMode, setMode, toggle }
}
