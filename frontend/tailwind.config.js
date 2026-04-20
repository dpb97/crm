import frappeUIPreset from 'frappe-ui/tailwind'

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
  safelist: [{ pattern: /!(text|bg)-/, variants: ['hover', 'active'] }],
  theme: {
    extend: {
      // LCS corporate identity — registered per global Tailwind standard so
      // utility classes like `text-lcs-primary` / `bg-lcs-accent` work anywhere.
      colors: {
        lcs: {
          primary: '#0B3A6F',   // LCS navy
          secondary: '#1E78C2', // LCS link blue
          accent: '#F5A524',    // LCS signal yellow (CTAs)
          success: '#16A34A',
          warning: '#D97706',
          danger: '#DC2626',
          muted: '#6B7280',
          surface: '#F8FAFC',
        },
      },
      fontFamily: {
        // Matches LCS brand typography; falls back to the frappe-ui default.
        lcs: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
