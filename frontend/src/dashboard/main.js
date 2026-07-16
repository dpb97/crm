// IIFE-Einstieg: stellt window.PilandaSalesDashboard.{mount,unmount} bereit.
// KEIN Auto-Mount — die Desk-Page sales-dashboard ruft mount(el) gezielt auf.
if (typeof window !== "undefined" && typeof window.process === "undefined") {
  window.process = { env: { NODE_ENV: "production" } };
}

import { createApp } from "vue";
import App from "./DashboardApp.vue";

let app = null;

export function mount(target, ctx = {}) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return;
  unmount();
  app = createApp(App, { ctx });
  app.config.errorHandler = (err, _i, info) =>
    console.error("[sales-dashboard] Vue error", info, err);
  app.mount(el);
}

export function unmount() {
  if (app) {
    try { app.unmount(); } catch (e) { /* noop */ }
    app = null;
  }
}
