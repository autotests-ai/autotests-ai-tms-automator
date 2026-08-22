---
id: react-rtl-allure
domain: testing
phase: 9.react-pilot
tags: [react, react-testing-library, vitest, allure-vitest, labels, dashboard]
related: [react-component-layer, react-component-coexist]
---
# React RTL → Allure wiring

Hub: `react-component-layer`.

Единый способ связать **RTL + Vitest** с Allure — без `beforeEach`-хардкода labels. Labels через `ALLURE_LABEL_*` env в `package.json` test script.

Reference wiring: `projects/selenoid-home/selenoid-ui/ui/` (v2). **Копировать только Allure-wiring**, не архитектуру.

**1. deps** (`devDependencies`):

```json
"allure-js-commons": "^3.0.7",
"allure-vitest": "^3.0.7"
```

**2. Vitest config** — setup + reporter:

```ts
import AllureReporter from "allure-vitest/reporter";

test: {
  environment: "jsdom",
  css: true,
  globals: true,
  include: ["src/**/*.test.{ts,tsx,js,jsx}"],
  setupFiles: ["./src/test/setup.ts", "allure-vitest/setup"],
  reporters: ["default", new AllureReporter({ resultsDir: "allure-results" })],
}
```

**Reporter — инстанс, не строка `["allure-vitest/reporter", …]`.** Строку Vitest резолвит вне каталога модуля и может взять `allure-vitest`, поднятый выше по дереву (hoist monorepo root). Тот reporter в `onInit` подставляет **свой** `setup.js` и **свой** `runner.js` → в одном worker два Vitest-runtime → `TypeError: Cannot read properties of undefined (reading 'delete')`, ни один тест не собирается.

**Node 26:** в `test`-скрипт обязателен `NODE_OPTIONS=--no-experimental-webstorage` — иначе пустой рантаймовый `localStorage` перебивает jsdom-овский и падает `localStorage.clear()`.

**3. `package.json` test script**:

```json
"test": "ALLURE_LABEL_epic=<app-name> ALLURE_LABEL_layer=component ALLURE_LABEL_scope=react ALLURE_LABEL_framework=react-testing-library vitest run",
"test:watch": "vitest"
```

| Label | Значение | Примечание |
|-------|----------|------------|
| `ALLURE_LABEL_epic` | `<app-name>` | `selenoid-ui` \| `autotests-ai-multistack-app` \| `react-ui` |
| `ALLURE_LABEL_layer` | `component` | общий уровень пирамиды |
| `ALLURE_LABEL_scope` | `react` | vs Java/Selenide (`browser`) |
| `ALLURE_LABEL_framework` | `react-testing-library` | никогда не сокращать |

Per-test `Feature` / `Story` — внутри теста через `allure-js-commons`.

Минимальный smoke без Allure: `"test": "vitest run"` — только локально; CI/dashboard — с `ALLURE_LABEL_*`.

Проверка labels в `allure-results/*-result.json`:

```json
"labels": [
  { "name": "framework", "value": "react-testing-library" },
  { "name": "layer", "value": "component" },
  { "name": "epic", "value": "selenoid-ui" },
  { "name": "scope", "value": "react" }
]
```

`allure-vitest` также добавляет `framework=vitest` — ожидаемо; фильтр dashboard: `scope=react` + `layer=component`.

## selenoid-ui — reference только для Allure wiring

**НЕ копировать** в новые apps: `react-router-dom` v5, `rxjs-hooks`, `react-input-autosize`.

## Allure / dashboard mapping

| Поле | Значение |
|------|----------|
| Epic | `react-ui` / `selenoid-ui` / `autotests-ai-multistack-app` |
| Layer | `component` |
| scope | `react` (RTL) / `browser` (Java Selenide) |
| framework | `react-testing-library` / `selenide` |
| Feature | имя компонента |
| Story | сценарий теста |
| tags | `react`, `vitest`, `jsdom` |

Фильтры: `layer=component`; RTL — `+ scope=react`; Java — `+ scope=browser`. **Не** вводить layer `react-component`.

### CI artifacts

- selenoid-ui: `yarn test` → `allure-results/`; artifact `allure-ui-react-testing-library`
- selenoid-tests orchestrator мержит artifact с Go unit + Java e2e
