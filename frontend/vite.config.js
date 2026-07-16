import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig(async ({ mode }) => {
  const isDev = mode === 'development'
  const config = {
    plugins: [
      vue(),
      vueJsx(),
      VitePWA({
        // injectManifest: we ship our own service worker so we can
        // mirror successful `/api/method/frappe.client.get_list|get`
        // responses into IndexedDB. Workbox's generateSW only writes
        // the Cache API, which is opaque blobs — useless for the
        // "give me all my open deals" offline lookup the SPA needs on
        // a construction site.
        strategies: 'injectManifest',
        srcDir: 'src',
        filename: 'sw.js',
        registerType: 'autoUpdate',
        injectRegister: false,
        devOptions: {
          enabled: true,
          type: 'module',
        },
        // Explizite Precache-Konfiguration — die Defaults verloren in
        // Kombination mit dem frappeui-Buildplugin das komplette Manifest
        // (leeres self.__WB_MANIFEST -> Precache leer, offline nichts).
        // Der frappeui-Buildplugin verlegt das outDir nach
        // ../crm/public/frontend — ohne explizites globDirectory globt
        // vite-plugin-pwa im Default-dist (1 Eintrag statt ~140).
        injectManifest: {
          globDirectory: '../crm/public/frontend',
          globPatterns: ['**/*.{js,css,html,ico,png,svg,webmanifest,woff2}'],
          globIgnores: ['**/*.map', '**/apple-splash-*.jpg', 'sw.js', 'sw.mjs', 'workbox-*.js'],
          maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        },
        // LCS branding override of the upstream Frappe CRM manifest.
        // Unique `id` keeps an installed LCS instance separate from a
        // co-installed vanilla Frappe CRM. Icons live under
        // `lcs_integrations/public/manifest/` so the LCS app owns its
        // own assets and no upstream icon files are touched.
        manifest: {
          id: '/crm?app=lcs',
          display: 'standalone',
          name: 'LCS CRM',
          short_name: 'LCS CRM',
          start_url: '/crm',
          scope: '/crm',
          description:
            'LCS Cable Cranes Sales CRM — leads, deals, projects, market-split territories.',
          background_color: '#FFFFFF',
          theme_color: '#008B8B', // Brand-Cyan (Literal zwingend: PWA-Manifest kann kein var(); SSOT = pp-tokens --pp-brand-primary / --pp-brand-700)
          lang: 'de',
          orientation: 'portrait',
          categories: ['business', 'productivity'],
          // Pilanda "PA" brand-mark icons, generated into the CRM frontend
          // public dir (served at /assets/crm/frontend/) — the previous
          // lcs_integrations icons 404'd (app assets weren't symlinked) and
          // were empty placeholders.
          icons: [
            {
              src: '/assets/crm/frontend/favicon-192.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'any maskable',
            },
            {
              src: '/assets/crm/frontend/favicon-512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any maskable',
            },
          ],
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    optimizeDeps: {
      include: [
        'feather-icons',
        'tailwind.config.js',
        'prosemirror-state',
        'prosemirror-view',
        'lowlight',
        'interactjs',
      ],
    },
    server: {
      fs: {
        allow: [path.resolve(__dirname, '..')],
      },
    },
  }

  const frappeui = await importFrappeUIPlugin(isDev, config)
  config.plugins.unshift(
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        indexHtmlPath: '../crm/www/crm.html',
        emptyOutDir: true,
        sourcemap: true,
      },
    }),
  )

  return config
})

async function importFrappeUIPlugin(isDev, config) {
  if (isDev) {
    try {
      // Check if local frappe-ui has the vite plugin file
      const fs = await import('node:fs')
      const localVitePluginPath = path.resolve(__dirname, '../frappe-ui/vite')

      if (fs.existsSync(localVitePluginPath)) {
        const module = await import('../frappe-ui/vite')
        console.info('Local frappe-ui vite plugin found, using local plugin')
        config.resolve.alias = getAliases(config)
        return module.default
      } else {
        console.warn('Local frappe-ui vite plugin not found, using npm package')
      }
    } catch (error) {
      console.warn(
        'Local frappe-ui not found, falling back to npm package:',
        error.message,
      )
    }
  }
  // Fall back to npm package if local import fails
  const module = await import('frappe-ui/vite')
  return module.default
}

function getAliases(config) {
  return {
    ...config.resolve.alias,
    'frappe-ui/tailwind': path.resolve(
      __dirname,
      '../frappe-ui/tailwind/preset.js',
    ),
    'frappe-ui/style.css': path.resolve(
      __dirname,
      '../frappe-ui/src/style.css',
    ),
    'frappe-ui/frappe': path.resolve(__dirname, '../frappe-ui/frappe/index.js'),
    'frappe-ui': path.resolve(__dirname, '../frappe-ui/src/index.ts'),
  }
}
