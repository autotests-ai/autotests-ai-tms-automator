---
id: react-app-reference
domain: config
phase: 9.react-pilot
tags: [react, spa, vite, spring, pwa, reference-app, consumer]
related: [react-toolchain, frontend-artifacts, 007-react-component-library]
---
# reference-app React SPA (topology memo)

**id:** `react-app-reference`  
**ADR:** [007-react-component-library](../../adr/007-react-component-library.md) — Phase 5 (consumer migration)  
**Zone:** `projects/reference-home/reference-app/` (nested clone, own git)

Первый consumer, мигрированный с server-rendered HTML на React SPA поверх library `@zero-design-system/react`. Backend не меняет роль: Spring Boot отдаёт статику и REST `/api/*`.

## Topology

| Слой | Путь |
|------|------|
| Frontend SPA | `frontend-react/` — Vite 6 + React 19 + react-router-dom 7 |
| Backend | `backend/` — Spring Boot, REST `/api/*` + раздача статики |
| Build output | `backend/src/main/resources/static/` (Vite `outDir`) |
| Design-system embed | тот же static dir: `css/`, `js/`, `templates/` (materialized `sync-app-static.sh`) |

Vite `outDir` указывает **в** backend static с `emptyOutDir: false` — static dir общий с design-system embed, preview-каталогом и allure-shell, стирать нельзя. Стабильные (без hash) имена ассетов держат committed diff чистым:

```ts
build: {
  outDir: resolve(__dirname, '../backend/src/main/resources/static'),
  emptyOutDir: false,
  rollupOptions: { output: {
    entryFileNames: 'assets/[name].js',
    chunkFileNames: 'assets/[name].js',
    assetFileNames: 'assets/[name][extname]',
  } },
}
```

## Alias `@zero-design-system/react`

Vite resolve alias напрямую на исходники library (не на dist) — pilot без publish:

```ts
resolve: { alias: {
  '@zero-design-system/react': resolve(__dirname, '../../../../packages/react-ui/src/index.ts'),
} }
```

Primitive CSS доставляется как peer-embed: `sync-app-static.sh` materializes `css/js/templates` из design-system в static, React импортирует классы, не переписывает дизайн в CSS-in-JS (ADR 007 §1).

## AppHeader embed

Header markup и burger — SSOT в `design-system/js/header.js`. Consumer рендерит library `<AppHeader config={headerConfig} />` (не JSX duplicate):

- `frontend-react/src/lib/headerConfig.ts` — config (раньше inline в `index.html`)
- `App.tsx` — `<AppHeader />` над `<Routes>`
- `index.html` — только `#root`; script inject делает `AppHeader`

Demo pilot (`packages/react-ui/demo/reference-app/`) — тот же embed, не локальный JSX header.

## SPA fallback

Client-side routing (react-router). Spring форвардит клиентские маршруты на bundled `index.html`:

```java
@GetMapping({"/login", "/register"})
public String spa() { return "forward:/index.html"; }
```

`SecurityConfig` permit-all статику и SPA-маршруты (`/`, `/index.html`, `/login`, `/register`, `/assets/**`, `/icons/**`, `/manifest.webmanifest`, `/sw.js`). REST-аутентификация — на `/api/auth/*` (login/register/logout permit, `/api/auth/me` authenticated).

## PWA baseline

`vite-plugin-pwa` (`registerType: autoUpdate`, `injectRegister: null` — регистрация в `src/pwa/registerServiceWorker.ts`):

- `manifest.webmanifest` — standalone, icons 192/512 + maskable 512 (`icons/`).
- `sw.js` (Workbox) precache **только** app shell: `index.html`, `assets/index.{js,css}`, `manifest.webmanifest`, оба icon.
- `navigateFallback: index.html`; `navigateFallbackDenylist: [/^\/api\//]` — `/api/*` всегда online, без offline-кэша API/JWT.
- `devOptions.enabled: false` — SW не мешает dev.

Baseline = installable + offline app shell. **Не** входит: push, background sync, offline API.

## Build → backend static

`scripts/sync-app-static.sh` (запускается в CI/deploy):

1. `wire-ui.sh` + rsync design-system `css/js/templates` → static (если monorepo root найден; standalone CI использует committed embed).
2. rsync `app-static/` → static.
3. `cd frontend-react && npm ci && npm run build` → `index.html` + `assets/` + PWA в static.

React-билд последний: materialized CSS доступен Vite-сборке.

## Tests

| Слой | Где |
|------|-----|
| React unit/component (Vitest + React Testing Library) | `frontend-react/src/**/*.test.{ts,tsx}` — pages (Home/Login/Register), auth, api, SW register, header nav |
| Java pyramid | `tests/` — unit → api → integration → e2e → component |
| Visual | Selenide screenshot baselines — `tests/src/test/resources/screenshots/` (login, home-layout, welcome-panel, …), Gradle `testVisual` |

Java-пирамида зелёная включая visual. React component tests — отдельная ось React Testing Library (см. `react-component-layer.md`), не заменяет Java `@Layer("component")` на `/components.html`.

## login.html removed

Server-rendered `login.html` / `register.html` удалены — теперь SPA-маршруты `/login`, `/register` (React Router + Spring forward). `SecurityConfig` сохраняет legacy `*.html` permit-all для обратной совместимости старых ссылок.

## Do

- Vite build только через `sync-app-static.sh` (materialize CSS первым).
- `emptyOutDir: false` — не стирать общий static dir.
- Alias на library src, primitive CSS как embed — не дублировать классы.

## Don't

- Не менять backend-роль (SPA-only forward + REST).
- Не кэшировать `/api/*` в SW.
- Не хешировать имена ассетов (committed static diff).
- Не переписывать design-system CSS в React.
