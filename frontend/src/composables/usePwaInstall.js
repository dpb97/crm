// PWA-Install: fängt das `beforeinstallprompt`-Event ab (Chrome/Edge/Android)
// und stellt einen eigenen Install-Einstieg bereit. iOS/Safari feuert das Event
// nicht — dort zeigen wir stattdessen die „Zum Home-Bildschirm"-Anleitung.
import { ref, computed } from 'vue'

const deferred = ref(null)
const installed = ref(false)
let _wired = false

function standalone() {
  if (typeof window === 'undefined') return false
  return window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true
}
function ios() {
  if (typeof navigator === 'undefined') return false
  return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream
}

export function usePwaInstall() {
  if (!_wired && typeof window !== 'undefined') {
    _wired = true
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      deferred.value = e
    })
    window.addEventListener('appinstalled', () => {
      installed.value = true
      deferred.value = null
    })
  }

  const canPrompt = computed(() => !!deferred.value && !installed.value && !standalone())

  async function install() {
    if (!deferred.value) return false
    deferred.value.prompt()
    let outcome = 'dismissed'
    try {
      ({ outcome } = await deferred.value.userChoice)
    } catch (e) {
      /* user closed the prompt */
    }
    if (outcome === 'accepted') installed.value = true
    deferred.value = null
    return outcome === 'accepted'
  }

  return { canPrompt, install, isIOS: ios(), isStandalone: standalone(), installed }
}
