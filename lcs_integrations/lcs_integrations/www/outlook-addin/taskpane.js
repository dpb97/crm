/* LCS CRM Outlook Add-in — Task Pane
   ---------------------------------
   Flow:
     1. Office.onReady → read current email subject + sender
     2. POST /api/method/lookup_email_context
     3. Render matching projects / offers / contacts / organizations
     4. Actions: "Zu Projekt loggen" / "Lead anlegen" / "Neues Projekt"
*/

// Hard-coded Frappe base — served from the same host the manifest lists.
// In prod, this is the site's public URL.
const API_BASE = "https://lcs.local";

let currentContext = null;  // response from lookup_email_context
let currentMail = null;     // { sender, subject, body }

// --- Office.onReady -----------------------------------------------------

Office.onReady(info => {
  if (info.host !== Office.HostType.Outlook) {
    showError("Nur für Outlook gedacht.");
    return;
  }
  document.getElementById("refresh-btn").addEventListener("click", loadContext);
  document.getElementById("btn-log").addEventListener("click", openProjectPicker);
  document.getElementById("btn-new-project").addEventListener("click", createProject);
  document.getElementById("btn-create-lead").addEventListener("click", createLead);
  document.getElementById("picker-search").addEventListener("input", onPickerSearch);

  loadContext();
});

// --- Load email context -------------------------------------------------

async function loadContext() {
  showState("loading");
  try {
    currentMail = await readCurrentMail();
    const res = await apiCall("lcs_integrations.outlook_addin.api.lookup_email_context", {
      sender_email: currentMail.sender,
      subject: currentMail.subject,
    });
    currentContext = res.message || res;
    render(currentContext);
  } catch (err) {
    console.error(err);
    showError(err.message || "Unbekannter Fehler");
  }
}

function readCurrentMail() {
  return new Promise((resolve, reject) => {
    try {
      const item = Office.context.mailbox.item;
      if (!item) return reject(new Error("Keine Nachricht ausgewählt"));
      const sender = (item.from && item.from.emailAddress) || "";
      const subject = item.subject || "";
      // Grab body only if we'll need it (defer for performance)
      resolve({ sender, subject, body: "" });
    } catch (e) { reject(e); }
  });
}

async function readFullBody() {
  return new Promise((resolve) => {
    Office.context.mailbox.item.body.getAsync("text", { asyncContext: null }, r => {
      resolve(r.status === Office.AsyncResultStatus.Succeeded ? r.value : "");
    });
  });
}

// --- Render -------------------------------------------------------------

function render(ctx) {
  if (!ctx.matched) {
    showState("no-match");
    return;
  }
  showState("matched");

  document.getElementById("sender-email").textContent = ctx.sender;
  document.getElementById("status-line").textContent =
    `${ctx.projects.length} Projekte · ${ctx.offers.length} Angebote`;

  renderProjects(ctx.projects);
  renderOffers(ctx.offers);
  renderOrganizations(ctx.organizations);
  renderContacts(ctx.contacts);
}

function renderProjects(projects) {
  const block = document.getElementById("block-projects");
  const list = document.getElementById("projects-list");
  const count = document.getElementById("count-projects");
  count.textContent = projects.length;
  list.innerHTML = "";
  if (!projects.length) { block.classList.add("hidden"); return; }
  block.classList.remove("hidden");
  for (const p of projects) {
    const card = document.createElement("div");
    card.className = "card";
    card.tabIndex = 0;
    card.addEventListener("click", () => openFrappeRecord("LCS Project", p.name));
    card.addEventListener("keydown", e => { if (e.key === "Enter") card.click(); });
    card.innerHTML = `
      <div class="card-main">
        <div class="card-title">${escape(p.project_name)}</div>
        <div class="card-meta">
          <span class="card-number">${escape(p.project_number)}</span>
          ${p.probability ? `· <span>🎯 ${Math.round(p.probability)}%</span>` : ""}
          ${p.estimated_value ? `· <span>${formatCurrency(p.estimated_value)}</span>` : ""}
        </div>
      </div>
      <span class="pill ${phasePill(p.phase)}"><span class="pill-dot"></span>${escape(p.phase || "")}</span>
    `;
    list.appendChild(card);
  }
}

function renderOffers(offers) {
  const block = document.getElementById("block-offers");
  const list = document.getElementById("offers-list");
  document.getElementById("count-offers").textContent = offers.length;
  list.innerHTML = "";
  if (!offers.length) { block.classList.add("hidden"); return; }
  block.classList.remove("hidden");
  for (const o of offers) {
    const card = document.createElement("div");
    card.className = "card";
    card.tabIndex = 0;
    card.addEventListener("click", () => openFrappeRecord("LCS Offer", o.name));
    card.innerHTML = `
      <div class="card-main">
        <div class="card-title">${escape(o.offer_title)} <span style="color:var(--muted);font-weight:400">v${o.version}</span></div>
        <div class="card-meta">
          ${o.value ? `<span>${formatCurrency(o.value)}</span>` : ""}
          ${o.valid_until ? `· <span>bis ${formatDate(o.valid_until)}</span>` : ""}
        </div>
      </div>
      <span class="pill ${offerPill(o.status)}"><span class="pill-dot"></span>${escape(o.status)}</span>
    `;
    list.appendChild(card);
  }
}

function renderOrganizations(orgs) {
  const block = document.getElementById("block-organizations");
  const list = document.getElementById("organizations-list");
  list.innerHTML = "";
  if (!orgs.length) { block.classList.add("hidden"); return; }
  block.classList.remove("hidden");
  for (const o of orgs) {
    const card = document.createElement("div");
    card.className = "card";
    card.addEventListener("click", () => openFrappeRecord("CRM Organization", o.name));
    card.innerHTML = `
      <div class="card-main">
        <div class="card-title">${escape(o.organization_name)}</div>
        ${o.industry ? `<div class="card-meta">${escape(o.industry)}</div>` : ""}
      </div>
    `;
    list.appendChild(card);
  }
}

function renderContacts(contacts) {
  const block = document.getElementById("block-contacts");
  const list = document.getElementById("contacts-list");
  list.innerHTML = "";
  if (!contacts.length) { block.classList.add("hidden"); return; }
  block.classList.remove("hidden");
  for (const c of contacts) {
    const card = document.createElement("div");
    card.className = "card";
    card.addEventListener("click", () => openFrappeRecord("Contact", c.name));
    card.innerHTML = `
      <div class="card-main">
        <div class="card-title">${escape(c.full_name || c.name)}</div>
        ${c.designation || c.company_name ? `<div class="card-meta">${escape(c.designation || "")} ${c.company_name ? "· " + escape(c.company_name) : ""}</div>` : ""}
      </div>
    `;
    list.appendChild(card);
  }
}

// --- State switching ----------------------------------------------------

function showState(which) {
  ["loading", "error", "matched", "no-match"].forEach(s => {
    document.getElementById(`state-${s}`).classList.toggle("hidden", s !== which);
  });
}

function showError(msg) {
  showState("error");
  document.getElementById("error-detail").textContent = msg || "";
}

// --- Actions ------------------------------------------------------------

async function openProjectPicker() {
  const picker = document.getElementById("picker");
  picker.classList.remove("hidden");
  document.getElementById("picker-search").value = "";
  document.getElementById("picker-search").focus();
  // Pre-populate with our current-context projects
  renderPickerResults(currentContext?.projects || []);
}

function closePicker() {
  document.getElementById("picker").classList.add("hidden");
}
window.closePicker = closePicker; // exposed for backdrop onclick

let pickerDebounceTimer = null;
function onPickerSearch(e) {
  const q = e.target.value.trim();
  clearTimeout(pickerDebounceTimer);
  if (q.length < 2) {
    renderPickerResults(currentContext?.projects || []);
    return;
  }
  pickerDebounceTimer = setTimeout(async () => {
    try {
      const res = await apiCall("lcs_integrations.outlook_addin.api.search_projects", { query: q, limit: 20 });
      renderPickerResults(res.message || res || []);
    } catch (err) {
      console.error(err);
    }
  }, 250);
}

function renderPickerResults(projects) {
  const container = document.getElementById("picker-results");
  container.innerHTML = "";
  if (!projects.length) {
    container.innerHTML = '<p class="muted" style="padding:14px;text-align:center">Keine Treffer.</p>';
    return;
  }
  for (const p of projects) {
    const card = document.createElement("div");
    card.className = "card";
    card.addEventListener("click", () => logEmailToProject(p.name, p.project_name));
    card.innerHTML = `
      <div class="card-main">
        <div class="card-title">${escape(p.project_name)}</div>
        <div class="card-meta">
          <span class="card-number">${escape(p.project_number || "")}</span>
          ${p.phase ? `· <span>${escape(p.phase)}</span>` : ""}
          ${p.organization ? `· <span>${escape(p.organization)}</span>` : ""}
        </div>
      </div>
    `;
    container.appendChild(card);
  }
}

async function logEmailToProject(projectName, displayName) {
  const btn = document.getElementById("btn-log");
  btn.disabled = true;
  try {
    // Lazy-load the body only when logging
    if (!currentMail.body) currentMail.body = await readFullBody();
    const res = await apiCall("lcs_integrations.outlook_addin.api.log_email_to_project", {
      project: projectName,
      subject: currentMail.subject,
      body: currentMail.body,
      sender: currentMail.sender,
    });
    toast(`Gespeichert unter ${displayName}`, "success");
    closePicker();
  } catch (err) {
    toast("Fehler: " + (err.message || "unbekannt"), "error");
  } finally {
    btn.disabled = false;
  }
}

async function createLead() {
  const btn = document.getElementById("btn-create-lead");
  btn.disabled = true;
  try {
    const senderName = Office.context.mailbox.item.from?.displayName || "";
    const res = await apiCall("lcs_integrations.outlook_addin.api.create_lead_from_email", {
      sender: currentMail.sender,
      sender_name: senderName,
      subject: currentMail.subject,
    });
    const payload = res.message || res;
    toast(payload.created ? "Lead angelegt" : "Lead existierte bereits", "success");
    setTimeout(loadContext, 800); // reload to show the new lead
  } catch (err) {
    toast("Fehler: " + (err.message || "unbekannt"), "error");
  } finally {
    btn.disabled = false;
  }
}

function createProject() {
  // Deep-link to the CRM SPA new-project route with sender prefilled
  const url = `${API_BASE}/crm/projects?prefill_email=${encodeURIComponent(currentMail.sender)}`;
  Office.context.ui.displayDialogAsync(url, { height: 80, width: 70 }, () => {});
}

function openFrappeRecord(doctype, name) {
  const slug = doctype.toLowerCase().replace(/\s+/g, "-");
  let url;
  if (doctype.startsWith("LCS Project")) {
    url = `${API_BASE}/crm/projects/${encodeURIComponent(name)}`;
  } else if (doctype.startsWith("LCS Offer")) {
    url = `${API_BASE}/app/${slug}/${encodeURIComponent(name)}`;
  } else {
    url = `${API_BASE}/app/${slug}/${encodeURIComponent(name)}`;
  }
  Office.context.ui.displayDialogAsync(url, { height: 80, width: 60 }, () => {});
}

// --- API helper ---------------------------------------------------------

async function apiCall(method, params) {
  const r = await fetch(`${API_BASE}/api/method/${method}`, {
    method: "POST",
    credentials: "include", // SSO cookie from existing browser session
    headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Frappe-CSRF-Token": "token" },
    body: new URLSearchParams(params).toString(),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return await r.json();
}

// --- Misc ---------------------------------------------------------------

function toast(msg, kind = "") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${kind}`;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3000);
}

function escape(s) {
  if (s == null) return "";
  return String(s).replace(/[<>&"']/g, c => ({ "<":"&lt;", ">":"&gt;", "&":"&amp;", "\"":"&quot;", "'":"&#39;" }[c]));
}

function formatCurrency(v) {
  return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v || 0);
}

function formatDate(d) {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(d));
}

function phasePill(phase) {
  const slug = (phase || "").toLowerCase().replace(/\s+/g, "-");
  return `pill-${slug}` || "pill-inquiry";
}

function offerPill(status) {
  const slug = (status || "").toLowerCase().replace(/\s+/g, "-");
  return `pill-${slug}`;
}
