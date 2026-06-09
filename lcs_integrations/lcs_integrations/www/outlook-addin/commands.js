/* Ribbon action handlers — run without showing the task pane.
   Referenced from manifest.xml under <ExecuteFunction>.
*/

const API_BASE = "https://lcs.local";

Office.onReady(() => {
  // Register functions so Outlook can call them from the ribbon
  if (Office.actions) {
    Office.actions.associate("quickLogToCRM", quickLogToCRM);
  }
});

/**
 * One-click "Log to CRM" — tries to find a matching project for the
 * sender and logs the email directly. If multiple matches, opens the
 * task pane for user pick.
 */
async function quickLogToCRM(event) {
  try {
    const item = Office.context.mailbox.item;
    const sender = item.from?.emailAddress || "";
    const subject = item.subject || "";

    if (!sender) {
      notify(event, "error", "Kein Absender");
      return;
    }

    // 1. Look up matching projects
    const ctxRes = await apiCall("lcs_integrations.outlook_addin.api.lookup_email_context", {
      sender_email: sender,
      subject,
    });
    const ctx = ctxRes.message || ctxRes;

    if (!ctx.projects || !ctx.projects.length) {
      notify(event, "informationalMessage", "Kein passendes Projekt — Task Pane öffnen für Picker");
      // Can't open task pane from command without user gesture; notify only.
      return;
    }
    if (ctx.projects.length > 1) {
      notify(event, "informationalMessage", `${ctx.projects.length} Projekte gefunden — Task Pane öffnen zum Wählen`);
      return;
    }

    // 2. Single match → log directly
    const project = ctx.projects[0];
    const body = await getBodyText();
    await apiCall("lcs_integrations.outlook_addin.api.log_email_to_project", {
      project: project.name,
      subject,
      body,
      sender,
    });
    notify(event, "success", `Gespeichert unter ${project.project_name}`);
  } catch (err) {
    console.error(err);
    notify(event, "error", "Fehler: " + (err.message || "unbekannt"));
  }
}

function getBodyText() {
  return new Promise(resolve => {
    Office.context.mailbox.item.body.getAsync("text", {}, r => {
      resolve(r.status === Office.AsyncResultStatus.Succeeded ? r.value : "");
    });
  });
}

async function apiCall(method, params) {
  const r = await fetch(`${API_BASE}/api/method/${method}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(params).toString(),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return await r.json();
}

function notify(event, kind, msg) {
  Office.context.mailbox.item.notificationMessages.replaceAsync("lcs-crm", {
    type: kind === "error" ? "errorMessage" : kind === "success" ? "informationalMessage" : "informationalMessage",
    message: msg.slice(0, 150),
    icon: "Icon.16",
    persistent: false,
  });
  event.completed();
}
