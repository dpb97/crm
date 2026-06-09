# LCS CRM Mobile (Capacitor Wrapper)

> Wraps the Frappe CRM Vue SPA into installable iOS / Android apps via
> [Capacitor](https://capacitorjs.com/), so requirements M-01..M-05
> of `CRM_Anforderungen_12.05.2026.docx` can be met without rewriting
> the frontend.

## Why a wrapper, not a native app

The CRM requirements call for "vollzugriff auf Kontakte, Pipeline,
Angebote und Aufgaben von unterwegs" (M-02) with "minimaler
Schulungsaufwand" (M-05). A Capacitor wrapper around the existing SPA
reuses 100 % of the Vue codebase and the entire Frappe API surface, so
features stay in sync between desktop and mobile. Native plugins are
added only for the things the SPA cannot do in a browser tab:

| Native Need | Capacitor Plugin | Requirement |
|-------------|------------------|-------------|
| Push notifications | `@capacitor/push-notifications` | W-03, MS-04 |
| Camera (business cards, site photos) | `@capacitor/camera` | PR-06 |
| Filesystem (offline cache) | `@capacitor/filesystem` | M-03, M-04, PR-04 |
| Microphone access | Native WebView API + `@capacitor/voice-recorder` (optional) | PR-01, PR-03 |
| Network status | `@capacitor/network` | M-04 (online/offline indicator) |

A fully offline-capable bidirectional sync (M-04) is **not** part of
this skeleton — it requires a queue / delta-resolver against the
Frappe API and several weeks of work. The skeleton supports
*offline-read* via a Service Worker that caches the last response per
endpoint, which covers M-03 and the "letzter Stand auf der Baustelle"
case the team most often hits.

## Layout

```
repo/mobile/
├── README.md              (this file)
├── package.json           Capacitor + plugin pins
├── capacitor.config.json  App id, name, web-dir, plugin config
└── scripts/
    ├── build-android.sh   Wrap the production SPA, open Android Studio
    └── build-ios.sh       Same for Xcode
```

The wrapper does NOT contain a copy of the SPA. It points to the
production build of `repo/frontend/` (`webDir`). On every release the
SPA is built first, then `npx cap sync` copies the bundle into the
native projects.

## Prerequisites

- Node 20+, Yarn 1.22+, the same toolchain that builds `repo/frontend/`
- Android: JDK 17, Android Studio Hedgehog or newer
- iOS: Xcode 15+ on a Mac (no Windows path)

## Building locally

```bash
# 1. Build the SPA so dist/ is fresh
cd repo/frontend
yarn install
yarn build

# 2. Sync into the Capacitor wrapper
cd ../mobile
yarn install
npx cap add android   # first time only
npx cap add ios       # first time only, Mac only
npx cap sync

# 3. Open the IDE
npx cap open android
npx cap open ios
```

## PWA — already built into the upstream SPA

The upstream Frappe CRM frontend already ships a PWA setup via
`vite-plugin-pwa` (Workbox runtime, manifest, service worker
auto-registration). When you run the production build (`yarn build`)
the SPA is installable as-is and the Workbox SW caches assets for
offline shell access — covering M-03 out of the box.

So there is **no LCS-side PWA wiring needed**. If we ever want to
override branding ("LCS CRM" instead of "Frappe CRM") or tune the
caching strategy, the right place is the `VitePWA(...)` block in
`repo/frontend/vite.config.js` — but that's a deliberate upstream
touch and is intentionally not done in this iteration.

The Capacitor wrapper below remains the path for installable iOS /
Android with native plugins (push, camera, etc.).

## Push notifications wiring

LCS follow-up reminders dispatch through
`lcs_integrations.followups.service.dispatch_due_reminders`. The
mobile app subscribes to the `lcs_followup_due` realtime event and
shows it as a system notification (via `@capacitor/push-notifications`
on iOS / Android, falls back to the in-app toast in the browser).

## Status

This directory ships only the wrapper config. The first
device-installable build is gated on:
1. Hosted endpoint reachable from the device (https-only)
2. CSP / CORS configured on the bench to accept the Capacitor scheme
3. Apple Developer + Google Play account provisioned
4. Push notification certificates (APNs key, FCM service account)

None of those are blockers for desktop/PWA usage — they are required
only for the app-store distribution path.
