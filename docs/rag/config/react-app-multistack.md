---
id: react-app-multistack
domain: config
phase: 9.react-pilot
tags: [react, spa, vite, spring, pwa, multistack, consumer]
related: [react-toolchain, frontend-artifacts, 007-react-component-library, pwa-baseline]
---
# Multistack React SPA (topology memo)

**id:** `react-app-multistack`  
**ADR:** [007-react-component-library](../../adr/007-react-component-library.md) — Phase 5 (consumer migration)  
**Ethalon (SSOT):** `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/`  
**Live clone:** `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/` (nested git)  
**Pair URL:** [backend-java-spring / frontend-typescript-react](https://autotests.ai/stack/backend-java-spring/frontend-typescript-react/)

Teaching cell is a **split** SPA + API: nginx routes `/stack/{backend}/{frontend}/` to the frontend container; `/api/*` on the same pair goes to the backend. There is no `frontend-react/` directory and no Vite `outDir` into Spring `static/`.

## Topology

| Слой | Путь |
|------|------|
| Frontend SPA | `frontend/typescript/frontend-typescript-react/` — Vite 8 + React 19 + react-router-dom 7 (pins: `react-toolchain`) |
| Module vendor | `vendor/react-ui/` — alias `@zero-design-system/react`; `vendor/ds/` — tokens/primitives (`src/styles.ts`, Dockerfile `COPY vendor/ds`). Not `projects/design-system-home/react-ui` from the module. |
| Sync hub | `frontend/_shared/` — kit for `sync-react-ui.sh` / `sync-ds-runtime.sh` fan-out into each module `vendor/`. Not runtime: no Vite alias, no Docker COPY. |
| Backend API | `backend/java/backend-java-spring/` — Spring Boot REST `/api/*` only |
| Tests | `tests/java/tests-java-gradle-junit5-allure3-selenide/` |
| Live pair | `/stack/backend-java-spring/frontend-typescript-react/` |

Vite `base` is `./` so one `dist` works under the nested `/stack/…/` mount. `pinMountAssets` rewrites injected `./assets/*` into `document.write` against the absolute mount. `outDir` is **`dist`**, `emptyOutDir: true`.

```ts
const reactUiSrc = resolve(__dirname, 'vendor/react-ui/src/index.ts');

export default defineConfig({
  base: './',
  resolve: {
    dedupe: ['react', 'react-dom'],
    alias: { '@zero-design-system/react': reactUiSrc },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rolldownOptions: { output: {
      entryFileNames: 'assets/[name].js',
      chunkFileNames: 'assets/[name].js',
      assetFileNames: 'assets/[name][extname]',
    } },
  },
});
```

Vite 8 бандлит Rolldown: `build.rollupOptions` deprecated → **`build.rolldownOptions`**.

## Alias `@zero-design-system/react`

Ethalon alias points at this module's `vendor/react-ui` (fan-out from hub `frontend/_shared/frontend-react-ui`, which syncs from `projects/design-system-home/react-ui` via `frontend/scripts/sync-react-ui.sh`). Vite does not alias `_shared`. `dedupe: ['react', 'react-dom']` — otherwise two Reacts → "Invalid hook call".

Primitive CSS is not rewritten in CSS-in-JS (ADR 007). The SPA imports tokens/primitives from `vendor/ds/css/` in `src/styles.ts`. The frontend Dockerfile copies `vendor/ds` into nginx html next to Vite `dist`.

## AppHeader embed

Header markup and burger stay SSOT in `design-system/js/header.js`. Consumer renders library `<AppHeader />` (not a JSX duplicate):

- `src/lib/headerConfig.ts` — brand **Multistack**, nav hrefs via `appPath()` for `/stack/{backend}/{frontend}/`
- `App.tsx` — `<AppHeader config={headerConfig} scriptSrc={appPath('/js/header.js')} />` above routes
- `index.html` — `#root` + mount boot; no inline header markup

Library playground (wrappers only, not the SPA): `projects/design-system-home/react-ui/demo/`.

## SPA vs API

Client-side routing (react-router) lives in the **frontend** container. Backend `SecurityConfig` permits REST only (`GET /api/health|/api/items`, `POST /api/auth/*`). It does **not** `forward:/index.html` for `/login` / `/register`.

## PWA baseline

**SSOT primitive:** [`pwa-baseline`](pwa-baseline.md) — `design-system/js/pwa-register.js`. Heirs generate `sw.js`; register through the primitive.

Vite heir (`registerType: autoUpdate`, `injectRegister: null`):

- Manifest / icons — `icons/pwa-{192,512,maskable-512}.png`; `name` / `short_name` **Multistack**.
- Workbox precache: `index.html`, `assets/index.js`, `assets/index.css`, `manifest.webmanifest`, icons.
- `navigateFallback: index.html`; denylist `/api/` **and** static extensions (nested-route MIME).
- `devOptions.enabled: false`.

Baseline = installable + offline app shell. **Not** in: push, background sync, offline API.

## Tests

| Слой | Где |
|------|-----|
| React unit/component (Vitest + RTL) | `frontend/typescript/frontend-typescript-react/src/test/**` |
| Java pyramid | `tests/java/tests-java-gradle-junit5-allure3-selenide/` |
| Visual | Selenide baselines under that tests module `src/test/resources/screenshots/{e2e,mock}/` — Gradle `testVisual`. Not Playwright in the SPA. |

## Form controls (id / name)

Chrome Issues: *A form field element should have an id or name attribute*.

| Control | `id` | `name` | `autocomplete` |
|---------|------|--------|----------------|
| Login | `login-input` | `username` | `username` |
| Password | `password-input` | `password` | `current-password` / `new-password` |
| Confirm | `confirm-password-input` | `confirm-password` | `new-password` |

SSOT: [`projects/autotests-ai-multistack-home/autotests-ai-multistack-app/_contract/flows/login.md`](../../../projects/autotests-ai-multistack-home/autotests-ai-multistack-app/_contract/flows/login.md) `formControls` · library `PlaqueField` defaults `name` from `paramId` / `id` when omitted · DS `templates/plaque-field.html` examples include both.

## Do

- Edit the default cell in `autotests-ai-multistack-app`, then `python scripts/deploy-ethalon-modules.py --sync-from-default --dry-run` for Flyway siblings (skill `deploy-ethalon-modules`; not concat onto `schema.sql`).
- Keep Vite `base: './'` + pin-mount boot for nested `/stack/` URLs.
- Alias this module's `vendor/react-ui`; `dedupe` React. Keep `frontend/_shared` as the sync hub only.
- Auth `PlaqueField`: always `id` + `name` (canon table above).

## Don't

- Do not revive `frontend-react/` or Vite `outDir` into Spring `static/`.
- Do not treat the backend as the SPA host (no Spring `forward:/index.html` on the teaching pair).
- Do not cache `/api/*` in the service worker.
- Do not hash asset file names (stable `assets/[name].js`).
- Do not rewrite design-system CSS in React.
- Do not leave `input`/`select` without both `id` and `name`.
