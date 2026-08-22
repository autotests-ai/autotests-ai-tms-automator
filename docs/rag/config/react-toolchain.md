---
id: react-toolchain
domain: config
phase: 9.react-pilot
tags: [react, typescript, vite, vitest, pnpm, toolchain, angular, vue]
related: [007-react-component-library]
---
# Frontend toolchain (memo)

**id:** `react-toolchain`  
**ADR:** [007-react-component-library](../../adr/007-react-component-library.md)

Канон для monorepo + учебных фронтов `autotests-ai-multistack-app`: **Node ≥26**, **Vite 8**, **Vitest 4**.  
TypeScript — **два пина** (см. ниже): React/общий → **7**, Angular → **6**.

## Runtime

| Tool | Pin |
|------|-----|
| **Node.js** | **26** (`.nvmrc`, CI `node-version: 26`, `engines.node >=26`) |
| **@types/node** | **26.2.0** |

Не держать Node 20/24 между зонами — один канон.

## TypeScript (dual pin)

| Зона | Pin | Почему |
|------|-----|--------|
| React / react-ui / stacks / vanilla / jquery (TS) | **`typescript@7.0.2`** | канон monorepo |
| **Angular** (`frontend-*-angular`) | **`typescript@6.0.3`** (`~6.0`) | `@angular/compiler-cli@22` peer: `>=6.0 <6.1`. **TS 7 нельзя** — нет Compiler API до TS 7.1 |
| **Vue TS** (`frontend-typescript-vue`) | **`typescript@6.0.3`** | `vue-tsc@3.3.9` резолвит `typescript/lib/tsc`; в TS 7 этого пути нет в `exports` → `ERR_PACKAGE_PATH_NOT_EXPORTED`. Снять пин, когда vue-tsc научится TS 7 |

- CI: `tsc --noEmit` / package `typecheck`.
- При bump TS React — monorepo + docs; Angular — только вместе с поддерживаемым `@angular/*`.
- **Не** форсить TS 7 на Angular через `--legacy-peer-deps` — упадёт compile, не только peer.

### Не делать

- Один «везде 7» без исключений Angular / Vue TS.
- Откат React на TS5/TS6 «локально для pilot».
- `@typescript/native-preview` в consumer apps без benchmark log.

## Bundler

| Tool | Pin | Use |
|------|-----|-----|
| **Vite** | **^8.2.1** | Demo / HMR / app production (Rolldown) |
| Library build | **tsup ^8.5.1** | ESM only — `.d.ts` эмитит tsc, см. ниже |
| **@vitejs/plugin-react** | **^6.0.5** | React Fast Refresh (не 4.x) |
| **@vitejs/plugin-vue** | **^6.0.8** | Vue SFC |
| **@analogjs/vite-plugin-angular** | **^2.6.4** | Angular под Vite |
| **vite-plugin-pwa** | **^1.3.0** | PWA baseline |
| **@rolldown/plugin-babel** | **^0.2.3** | Babel-проход под Vite 8 (JS Angular decorators) |

Единый major Vite для monorepo (`projects/design-system-home/react-ui`, stacks/examples) и `autotests-ai-multistack-app`. Не оставлять Vite 6/7 без README-причины.

### Vite 8 = Rolldown

| Было (Rollup) | Стало |
|---|---|
| `build.rollupOptions` | **`build.rolldownOptions`** (`rollupOptions` — deprecated alias) |
| `output.manualChunks(id)` | **`output.codeSplitting.groups: [{ name, test }]`** |
| `vite-plugin-babel` | **`@rolldown/plugin-babel`** — `vite-plugin-babel` делает `import babel from '@babel/core'`, а Babel 8 ESM-only без default export → config не грузится. Rolldown-плагин **не читает** `babel.config.*`, plugins передаются inline |

**Не делать сейчас:** Webpack, CRA, Next.js для design-system library. Full Bundle Mode / `tsdown` вместо `tsup` — только через ADR.

### Library build (`projects/design-system-home/react-ui`)

`tsup` бандлит `rollup-plugin-dts`, собранный против TypeScript 5 internals; на TS 7 падает `useCaseSensitiveFileNames`. Поэтому `dts: false` в `tsup.config.ts`, а декларации эмитит локальный tsc: `build: "tsup && tsc -p tsconfig.build.json"`.

## Test

| Tool | Pin |
|------|-----|
| **Vitest** | **^4.1.10** |
| **@vitest/coverage-v8** | **^4.1.10** (тот же minor, что Vitest) |
| **jsdom** | **^30.0.1** |
| **@testing-library/jest-dom** | **^7.0.0** |
| **@testing-library/react** | **^16.3.2** |
| **@testing-library/user-event** | **^14.6.3** |
| **allure-vitest** + **allure-js-commons** | **^3.10.2** (пара, одинаковый version) |

При bump Vite ↔ Vitest — одновременно. Target: suite < 30s local, CI < 2 min.

### Vitest 4 — обязательное в каждом модуле

1. **Allure reporter — инстанс, не строка.** `reporters: ['default', new AllureReporter({ resultsDir: 'allure-results' })]` + `import AllureReporter from 'allure-vitest/reporter'`. Строку `['allure-vitest/reporter', …]` Vitest резолвит вне каталога модуля и берёт `allure-vitest`, поднятый выше по дереву; тот в `onInit` подставляет свой `setup.js` + `runner.js` → два Vitest-runtime в одном worker → `TypeError: … (reading 'delete')` на collect. Особенно бьёт по `autotests-ai-multistack-app`, который физически лежит внутри monorepo с hoisted `node_modules`.
2. **`NODE_OPTIONS=--no-experimental-webstorage`** в `test`-скрипте: на Node 26 рантаймовый пустой `localStorage` перебивает jsdom.
3. **`resolve.dedupe: ['react', 'react-dom']`**, если alias библиотеки ведёт наружу пакета — иначе две копии React и «Invalid hook call».
4. **Tags** (`test.tags` + `--tagsFilter`) — smoke-сьют в reference-модулях (`frontend-typescript-vanilla`, `frontend-typescript-react`), скрипт `test:smoke`. `strictTags` включён по умолчанию: незадекларированный тег роняет ран.

**Stale lockfile.** При смене major (`@vitejs/plugin-react` 4→6, Vite 6→8) `npm install` падает ERESOLVE, пока лежит старый `package-lock.json` + `node_modules`. Лечится `rm -rf node_modules package-lock.json && npm install`, лок перегенерировать и закоммитить.

## Framework pins (учебные стенды)

| Framework | Pin | Notes |
|-----------|-----|-------|
| **React** / react-dom | **^19.2.8** | + `@types/react` / `@types/react-dom` ^19.2 |
| **react-router-dom** | **^7.18.2** | data-router: `createBrowserRouter` + `RouterProvider`; в тестах тот же массив routes через `createMemoryRouter`. Не `BrowserRouter` + `<Routes>` |
| **Vue** | **^3.5.41** | |
| **vue-router** | **^5.2.0** | major; peer Vite 7/8. `createRouter` + `createWebHistory` не изменились; `experimental_createRouter` / новый matcher — не брать |
| **vue-tsc** | **^3.3.9** | тянет `typescript@6` (см. dual pin) |
| **Angular** (`@angular/*`) | **^22.1.1** | TS-стек: вместе с `typescript@6.0.3` + `@angular/build@^22` |
| **jquery** | **^4.0.0** | + `@types/jquery@^4`. Вендоренная копия (`vendor/jquery.min.js`) — то, что реально грузится: после bump обязателен `npm run vendor:jquery` |
| **Babel** (JS Angular only) | **^8** (`@babel/core` + decorator plugins) | |

## Package manager

| | pnpm (recommended) | npm |
|--|-------------------|-----|
| Disk | content-addressable store, hard links | дубли per project |
| Monorepo | `pnpm-workspace.yaml`, strict deps | workspaces OK, слабее isolation |
| CI cache | `pnpm store path` + lockfile | `npm ci` + `~/.npm` |

**Pilot:** npm в root `package.json` workspaces (минимальный diff).

## Monorepo layout

```
package.json          # workspaces: ["projects/design-system-home/react-ui"]
projects/design-system-home/react-ui/
    package.json      # @zero-design-system/react
    src/
    demo/             # Vite pilot screen
    tsup.config.ts
    vitest.config.ts
```

## CI / disk

- Cache key: lockfile hash + node version; не `node_modules` в artifacts.
- `npm run clean:frontend` — `projects/design-system-home/react-ui/{node_modules,dist,coverage,.vite}`, `*.tsbuildinfo`.
- Не коммитить `node_modules/`, `dist/`, `.vite/`.

## Do / Don't

- Pin versions в каждом frontend `package.json` по этой таблице; bump majors — одним проходом по всем модулям.
- Не mixed Vite 6/8 или Vitest 3/4 между учебными фронтами. Root `node_modules` monorepo тоже: stale hoisted Vitest 3 ломает вложенные модули на Vitest 4 (см. reporter-инстанс выше).
- Не Storybook / Playwright component CT в одном pilot PR без ADR.
