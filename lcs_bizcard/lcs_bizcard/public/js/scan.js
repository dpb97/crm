// LCS Bizcard scanner — vanilla JS module so it runs as a normal
// Frappe www page without any build step. State machine:
//
//   capture  -> preview -> review -> done
//
// Talks to Frappe via fetch /api/method/lcs_bizcard.api.*.
// When loaded with `?embed=1` the page emits postMessage to its
// parent on (created, cancelled, errored) so the embedding SPA
// can close the iframe and link the new Contact.

const root = document.getElementById('bizcard-app')
const embed = root.dataset.embed === '1'
document.body.dataset.embed = embed ? '1' : '0'

const csrfToken = window.csrf_token || (window.frappe && window.frappe.csrf_token) || 'token'

const state = {
  step: 'capture',
  mediaStream: null,
  capturedBlob: null,
  capturedDataUrl: null,
  parsed: null,
  bannerKind: null,
  bannerText: '',
}

const FIELDS = [
  { key: 'first_name',   label: 'First Name',  type: 'text' },
  { key: 'last_name',    label: 'Last Name',   type: 'text' },
  { key: 'company_name', label: 'Company',     type: 'text', full: true },
  { key: 'designation',  label: 'Designation', type: 'text', full: true },
  { key: 'email_id',     label: 'Email',       type: 'email' },
  { key: 'mobile_no',    label: 'Mobile',      type: 'tel' },
  { key: 'phone',        label: 'Phone',       type: 'tel' },
  { key: 'website',      label: 'Website',     type: 'url',  full: true },
  { key: 'address',      label: 'Address',     type: 'text', full: true },
]

// --- helpers ---------------------------------------------------------------

function notify(parentMessage) {
  if (embed && window.parent && window.parent !== window) {
    window.parent.postMessage({ source: 'lcs.bizcard', ...parentMessage }, '*')
  }
}

function setBanner(kind, text) {
  state.bannerKind = kind
  state.bannerText = text
  render()
}

function setStep(step) {
  state.step = step
  render()
}

async function callFrappe(method, body) {
  const r = await fetch(`/api/method/${method}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': csrfToken,
      'Accept': 'application/json',
    },
    body: JSON.stringify(body || {}),
  })
  const json = await r.json()
  if (!r.ok || json.exc_type) {
    const msg = json._server_messages || json.exc || `HTTP ${r.status}`
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return json.message
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onloadend = () => {
      const s = r.result || ''
      // strip data:*;base64, prefix
      const idx = s.indexOf(',')
      resolve(idx >= 0 ? s.slice(idx + 1) : s)
    }
    r.onerror = reject
    r.readAsDataURL(blob)
  })
}

// --- camera ---------------------------------------------------------------

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 } },
      audio: false,
    })
    state.mediaStream = stream
    const video = document.getElementById('bz-video')
    if (video) {
      video.srcObject = stream
      await video.play()
    }
  } catch (e) {
    setBanner('warn',
      'Camera not available — please use "Upload file" instead. (' + e.message + ')')
  }
}

function stopCamera() {
  if (state.mediaStream) {
    state.mediaStream.getTracks().forEach((t) => t.stop())
    state.mediaStream = null
  }
}

async function captureFromVideo() {
  const video = document.getElementById('bz-video')
  if (!video || !video.videoWidth) {
    setBanner('error', 'Camera not ready')
    return
  }
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  canvas.toBlob(async (blob) => {
    state.capturedBlob = blob
    state.capturedDataUrl = canvas.toDataURL('image/jpeg', 0.9)
    stopCamera()
    setStep('preview')
  }, 'image/jpeg', 0.9)
}

async function pickFile(ev) {
  const file = ev.target.files && ev.target.files[0]
  if (!file) return
  state.capturedBlob = file
  state.capturedDataUrl = await new Promise((resolve) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.readAsDataURL(file)
  })
  stopCamera()
  setStep('preview')
}

// --- scan ----------------------------------------------------------------

async function runScan() {
  setBanner(null, '')
  const statusEl = document.getElementById('bz-status')
  if (statusEl) {
    statusEl.dataset.state = ''
    statusEl.textContent = 'Scanning…'
  }
  try {
    const image_base64 = await blobToBase64(state.capturedBlob)
    const parsed = await callFrappe('lcs_bizcard.api.scan_card', {
      image_base64,
      mime_type: state.capturedBlob.type || 'image/jpeg',
    })
    state.parsed = parsed || {}
    setStep('review')
  } catch (e) {
    setBanner('error', 'Scan failed: ' + e.message)
    setStep('preview')
  }
}

// --- review --------------------------------------------------------------

function collectForm() {
  const out = {}
  for (const f of FIELDS) {
    const el = document.getElementById('bz-f-' + f.key)
    out[f.key] = el ? el.value.trim() : ''
  }
  return out
}

async function saveContact() {
  setBanner(null, '')
  const payload = collectForm()
  try {
    const result = await callFrappe('lcs_bizcard.api.create_contact_from_scan', payload)
    notify({ type: 'created', contact: result.name, created: !!result.created })
    state.parsed = { ...payload, _saved: result }
    setStep('done')
  } catch (e) {
    setBanner('error', 'Could not save contact: ' + e.message)
  }
}

function reset() {
  state.capturedBlob = null
  state.capturedDataUrl = null
  state.parsed = null
  setStep('capture')
  startCamera()
}

function cancel() {
  notify({ type: 'cancelled' })
  if (!embed) {
    window.history.back()
  }
}

// --- render --------------------------------------------------------------

function escape(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c])
}

function tplCapture() {
  return `
    <div class="bz-card">
      <h1 class="bz-title">${embed ? 'Visitenkarte scannen' : 'LCS Bizcard Scanner'}</h1>
      <p class="bz-subtitle">Halte die Karte gerade ins Bild oder lade ein Foto hoch.</p>
      <video id="bz-video" class="bz-video" playsinline muted></video>
      <div class="bz-actions">
        <button class="bz-btn bz-btn--primary" id="bz-capture">📷 Aufnehmen</button>
        <label class="bz-btn">
          📁 Datei wählen
          <input type="file" accept="image/*" style="display:none" id="bz-file">
        </label>
        <button class="bz-btn bz-btn--ghost" id="bz-cancel">Abbrechen</button>
      </div>
    </div>
  `
}

function tplPreview() {
  return `
    <div class="bz-card">
      <h1 class="bz-title">Vorschau</h1>
      <p class="bz-subtitle">Schick die Aufnahme zum OCR oder mach ein neues Bild.</p>
      <img class="bz-preview" src="${state.capturedDataUrl}" alt="">
      <div class="bz-status" id="bz-status"></div>
      <div class="bz-actions">
        <button class="bz-btn bz-btn--primary" id="bz-scan">🔍 Scannen</button>
        <button class="bz-btn" id="bz-retake">↺ Neu aufnehmen</button>
        <button class="bz-btn bz-btn--ghost" id="bz-cancel">Abbrechen</button>
      </div>
    </div>
  `
}

function tplReview() {
  const p = state.parsed || {}
  const fields = FIELDS.map((f) => {
    const val = p[f.key] || ''
    const filled = val ? ' bz-field--filled' : ''
    const cls = (f.full ? 'bz-field bz-field--full' : 'bz-field') + filled
    return `
      <div class="${cls}">
        <label for="bz-f-${f.key}">${f.label}</label>
        <input type="${f.type}" id="bz-f-${f.key}" value="${escape(val)}">
      </div>
    `
  }).join('')
  return `
    <div class="bz-card">
      <h1 class="bz-title">Daten prüfen</h1>
      <p class="bz-subtitle">Korrigiere die OCR-Vorschläge, bevor der Kontakt angelegt wird. Konfidenz: ${
        ((p.confidence || 0) * 100).toFixed(0)
      }% · ${p.polished ? 'mit LLM-Polish' : 'rein heuristisch'}</p>
      <div class="bz-form">${fields}</div>
      <div class="bz-actions">
        <button class="bz-btn bz-btn--success" id="bz-save">✓ Kontakt anlegen</button>
        <button class="bz-btn" id="bz-back">↺ Neu scannen</button>
        <button class="bz-btn bz-btn--ghost" id="bz-cancel">Abbrechen</button>
      </div>
      <details>
        <summary style="cursor:pointer;font-size:11px;color:var(--lcs-muted);margin-top:12px;">Rohtext (OCR)</summary>
        <pre class="bz-raw">${escape(p.raw_text || '')}</pre>
      </details>
    </div>
  `
}

function tplDone() {
  const saved = state.parsed?._saved || {}
  return `
    <div class="bz-card">
      <h1 class="bz-title">${saved.created ? 'Kontakt angelegt' : 'Kontakt erkannt'}</h1>
      <p class="bz-subtitle">${
        saved.created
          ? 'Der neue Frappe Contact wurde erstellt.'
          : 'Der Kontakt existierte bereits (gleiche E-Mail).'
      }</p>
      <div style="background:var(--lcs-surface);padding:12px;border-radius:8px;font-family:monospace;font-size:13px;">${
        escape(saved.name || '')
      }</div>
      <div class="bz-actions">
        ${embed
          ? `<button class="bz-btn bz-btn--primary" id="bz-close">✓ Schließen</button>`
          : `<a class="bz-btn bz-btn--primary" href="/app/contact/${encodeURIComponent(saved.name || '')}">→ Im Desk öffnen</a>`
        }
        <button class="bz-btn" id="bz-again">↺ Weitere Karte</button>
      </div>
    </div>
  `
}

function render() {
  const banner = state.bannerKind
    ? `<div class="bz-banner" data-kind="${state.bannerKind}">${escape(state.bannerText)}</div>`
    : ''
  const body =
    state.step === 'capture' ? tplCapture()
    : state.step === 'preview' ? tplPreview()
    : state.step === 'review' ? tplReview()
    : tplDone()
  root.innerHTML = banner + body

  // Wire up handlers (idempotent, fresh per render)
  document.getElementById('bz-capture')?.addEventListener('click', captureFromVideo)
  document.getElementById('bz-file')?.addEventListener('change', pickFile)
  document.getElementById('bz-cancel')?.addEventListener('click', cancel)
  document.getElementById('bz-scan')?.addEventListener('click', runScan)
  document.getElementById('bz-retake')?.addEventListener('click', reset)
  document.getElementById('bz-save')?.addEventListener('click', saveContact)
  document.getElementById('bz-back')?.addEventListener('click', reset)
  document.getElementById('bz-again')?.addEventListener('click', reset)
  document.getElementById('bz-close')?.addEventListener('click', () => notify({ type: 'closed' }))

  if (state.step === 'capture') startCamera()
}

// kick off
render()
notify({ type: 'ready' })
