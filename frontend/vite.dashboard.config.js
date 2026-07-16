// Vite library build fuer das Vertrieb-Modul-Dashboard (N10, Master ENTWICKLUNGSPLAN §6.2).
// Erzeugt window.PilandaSalesDashboard + eine eigene CSS-Datei mit festen Namen,
// die die Desk-Page sales-dashboard statisch laedt.
// Output -> ../pilanda_sales/public/dist (Frappe symlinkt nach
// /assets/pilanda_sales/dist/). emptyOutDir:false — kuenftige weitere Bundles
// (Dateinamen disjunkt) bleiben erhalten.
//
// frappe-ui/vite wired die ~icons/lucide/*-Virtual-Imports der kopierten
// Pp*-Bausteine (PpDataGrid). Muster identisch zu pilanda_pls (Stack-Standard).
import { defineConfig } from "vite";
import frappeui from "frappe-ui/vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [
    frappeui({ frappeProxy: false, jinjaBootData: false, buildConfig: false, lucideIcons: true }),
    vue(),
  ],
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: {
    target: "es2020",
    lib: {
      entry: fileURLToPath(new URL("./src/dashboard/main.js", import.meta.url)),
      formats: ["iife"],
      name: "PilandaSalesDashboard",
      fileName: () => "sales_dashboard.js",
    },
    outDir: fileURLToPath(new URL("../pilanda_sales/public/dist", import.meta.url)),
    emptyOutDir: false,
    cssCodeSplit: false,
    sourcemap: false,
    minify: "esbuild",
    rollupOptions: {
      output: {
        assetFileNames: (info) =>
          info.name && info.name.endsWith(".css")
            ? "sales_dashboard.css"
            : "sales_dashboard-[name][extname]",
      },
    },
  },
});
