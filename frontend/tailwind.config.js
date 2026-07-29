import frappeUIPreset from 'frappe-ui/tailwind'

/**
 * LCS Tailwind config.
 *
 * The colour tokens below are kept in TWO synchronised places — here
 * (so utility classes like `bg-lcs-primary` work) and as CSS custom
 * properties in `src/index.css` (so a runtime theme override or dark
 * mode can change them without rebuild).
 *
 * Rule: never hard-code an LCS hex value in a component — always use
 * the `lcs-*` utility class so the tokens stay the single source of
 * truth.
 */
export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: [
    { pattern: /!(text|bg)-/, variants: ['hover', 'active'] },
  ],
  theme: {
    // Radius-Skala auf die Pilanda-Theme-Tokens gemappt (SSOT: pilanda_theme,
    // injiziert als --pp-radius-ui via after_request). Alle rounded-*-Klassen
    // folgen damit Live-AEnderungen in den Theme-Settings ohne Rebuild.
    // rounded-full bleibt echt rund (Avatare, Pills, Status-Dots).
    borderRadius: {
      none: "0",
      sm: "var(--pp-radius-xs, 2px)",
      DEFAULT: "var(--pp-radius-ui, 3px)",
      md: "var(--pp-radius-ui, 3px)",
      lg: "var(--pp-radius-ui, 3px)",
      xl: "var(--pp-radius-ui, 3px)",
      "2xl": "var(--pp-radius-ui, 3px)",
      "3xl": "var(--pp-radius-ui, 3px)",
      full: "9999px",
    },
    extend: {
      colors: {
        // LCS corporate identity. Bare-hex literals are required so
        // Tailwind opacity modifiers (`bg-lcs-primary/10`,
        // `text-lcs-primary/60`) work cleanly — `var(--…)` color values
        // collide with PostCSS opacity modifier parsing.
        // Runtime theming uses the matching CSS variables from
        // index.css inside the `@layer components` block (.lcs-card,
        // .lcs-kpi, …) — those don't go through Tailwind opacity logic.
        lcs: {
          // Live-Theming: pilanda_theme liefert --pp-brand-primary-rgb als
          // space-separiertes Triple genau fuer dieses Tailwind-Muster —
          // Opacity-Modifier (bg-lcs-primary/10) funktionieren damit UND die
          // Farbe folgt dem Theme ohne Rebuild. Fallback = LCS-Logo-Blau.
          primary:   'rgb(var(--pp-brand-primary-rgb, 0 139 139) / <alpha-value>)',
          // Secondary folgt jetzt DEMSELBEN Brand-Cyan wie primary (Marken-
          // Konsolidierung: Alt-Fremdblau raus). Gleiches rgb(var(--…))-Muster,
          // damit Opacity-Modifier (border-lcs-secondary/60) weiter greifen und
          // die Farbe dem Theme (inkl. Dark) ohne Rebuild folgt.
          secondary: 'rgb(var(--pp-brand-primary-rgb, 0 139 139) / <alpha-value>)',
          accent:    '#F5A524',
          success:   '#16A34A',
          warning:   '#D97706',
          danger:    '#DC2626',
          muted:     '#6B7280',
          surface:   '#F8FAFC',
        },
        // Marken-Konsolidierung: die Tailwind-`blue`-Palette wird auf einen
        // Türkis-Ramp (Brand-Cyan #008b8b) umgebogen, damit alle hartkodierten
        // `blue-*`-Klassen in Alt-Komponenten (Badges, Pills, Dialoge) im neuen
        // Türkis statt im Fremd-Blau erscheinen — ohne jede Komponente zu ändern.
        blue: {
          50:  '#e7f4f4',
          100: '#c9e6e6',
          200: '#99d2d2',
          300: '#5cbcbc',
          400: '#28a3a3',
          500: '#008b8b',
          600: '#017c7c',
          700: '#036767',
          800: '#055353',
          900: '#064242',
          950: '#032b2b',
        },
      },
      fontFamily: {
        // Klickdummy-Master typeface (Noto Sans), self-hosted via @font-face.
        sans: ['Noto Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        lcs: ['Noto Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      // Soft elevation matching LCS card aesthetic
      boxShadow: {
        'lcs-card': '0 1px 2px 0 rgb(0 0 0 / 0.03), 0 1px 1px 0 rgb(0 0 0 / 0.02)',
        'lcs-card-hover': '0 4px 12px 0 rgb(var(--pp-brand-primary-rgb, 0 139 139) / 0.08)',
      },
    },
  },
  plugins: [],
  // Dark mode driven by the same data-theme attribute frappe-ui's
  // useTheme() composable already toggles in App.vue.
  darkMode: ['class', '[data-theme="dark"]'],
}
