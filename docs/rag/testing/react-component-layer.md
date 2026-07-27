---
id: react-component-layer
domain: testing
phase: 9.react-pilot
tags: [react, react-testing-library, vitest, allure-vitest, component, pyramid, allure]
related: [test-pyramid, test-components, 007-react-component-library]
---
# React component layer (Vitest + React Testing Library)

**id:** `react-component-layer`  
**ADR:** [007-react-component-library](../../adr/007-react-component-library.md)

Слой пирамиды для **React UI** (Vitest + React Testing Library): `packages/react-ui/` (pilot) и `qa-guru/selenoid-ui` (v2 maintenance). Не путать с Java `@Layer("component")` (Selenide в browser) и TestOps custom field **Component** (сервис/repo).

## Место в пирамиде

```text
unit (TS pure)
  ↓
react-component (Vitest + React Testing Library)   ← этот документ
  ↓
integration (Java Selenide mount)
  ↓
api
  ↓
e2e smoke
  ↓
visual (Playwright baseline)
```

**React Testing Library — отдельный инструмент**, но **layer в Allure = `component`** (общий уровень пирамиды). Различение React vs Java/Selenide — через дополнительные labels (`scope=react` vs `scope=browser`), а не через отдельный layer.

## Границы ответственности

### Тестируем (React Testing Library)

| Concern | Пример |
|---------|--------|
| Props → render | `variant="primary"` → `.btn--primary`; `variant="nav"` → `.link--nav` |
| User events | click theme toggle → `theme-light` class; click lang toggle → label `RU` |
| a11y | `aria-label`, `role`, `disabled` |
| Conditional UI | loading / error states |
| Callbacks | `onClick`, `onChange` invoked |

### Не тестируем (React Testing Library)

| Concern | Слой |
|---------|------|
| HTTP / SSE | integration / e2e |
| Routing across pages | e2e |
| Pixel-perfect layout | visual |
| Full header embed in Spring static | Java component / integration |
| Backend contracts | api |

## Структура файлов

```text
packages/react-ui/                    # pilot library
  src/
    Button.tsx
    Button.test.tsx
    Link.tsx
    Link.test.tsx
    LangToggle.tsx
    LangToggle.test.tsx
    Badge.tsx
    Badge.test.tsx
  vitest.config.ts
  src/test/setup.ts

projects/selenoid-home/selenoid-ui/ui/  # v2 consumer (yarn)
  src/
    components/Stats/Status.test.jsx
    util/uiFeed.ts
    util/uiFeed.test.ts
  vite.config.ts
  src/test/setup.ts
```

Naming: `*.test.tsx` / `*.test.ts` / `*.test.jsx` рядом с модулем.

## Канонический паттерн: RTL → Allure (единый стандарт)

Единый способ связать **React Testing Library + Vitest** с Allure для **всех** React apps — без `beforeEach`-хардкода labels в каждом файле. Labels задаются один раз через `ALLURE_LABEL_*` env в `package.json` test script.

Reference wiring: `projects/selenoid-home/selenoid-ui/ui/` (v2). **Копировать оттуда только этот Allure-wiring**, не архитектуру (см. ниже).

**1. deps** (`devDependencies`):

```json
"allure-js-commons": "^3.0.7",
"allure-vitest": "^3.0.7"
```

**2. Vitest config** (`vite.config.ts` или `vitest.config.ts`) — setup + reporter:

```ts
test: {
  environment: "jsdom",
  css: true,                                    // CSS imports в тестах
  globals: true,
  include: ["src/**/*.test.{ts,tsx,js,jsx}"],
  setupFiles: ["./src/test/setup.ts", "allure-vitest/setup"],
  reporters: [
    "default",
    ["allure-vitest/reporter", { resultsDir: "allure-results" }],
  ],
}
```

**3. `package.json` test script** — labels через `ALLURE_LABEL_*` env (не хардкод в тестах):

```json
"test": "ALLURE_LABEL_epic=<app-name> ALLURE_LABEL_layer=component ALLURE_LABEL_scope=react ALLURE_LABEL_framework=react-testing-library vitest run",
"test:watch": "vitest"
```

Стандартные значения labels для всех React apps:

| Label | Значение | Примечание |
|-------|----------|------------|
| `ALLURE_LABEL_epic` | `<app-name>` | `selenoid-ui` \| `reference-app` \| `react-ui` |
| `ALLURE_LABEL_layer` | `component` | общий уровень пирамиды |
| `ALLURE_LABEL_scope` | `react` | отличает от Java/Selenide (`browser`) |
| `ALLURE_LABEL_framework` | `react-testing-library` | никогда не сокращать |

`allure-vitest/setup` читает любые `ALLURE_LABEL_<name>=<value>` из env и вешает их на каждый тест. Так весь suite получает единые `epic` / `layer` / `scope` / `framework` без правки тест-файлов. Per-test `Feature` / `Story` — внутри теста через `allure-js-commons`.

**Минимальный вариант без Allure** (только прогон тестов, без результатов в `allure-results/`):

```json
"test": "vitest run"
```

Использовать **только** для локального smoke без dashboard. Канон для CI и merged dashboard — вариант с `ALLURE_LABEL_*` выше.

**Проверка** (один result из `allure-results/*-result.json`):

```json
"labels": [
  { "name": "framework", "value": "react-testing-library" },
  { "name": "layer", "value": "component" },
  { "name": "epic", "value": "selenoid-ui" },
  { "name": "scope", "value": "react" }
]
```

> `allure-vitest` по умолчанию также добавляет `framework=vitest` — это ожидаемо; фильтр dashboard идёт по `scope=react` + `layer=component`, поэтому дубль `framework` не мешает.

## selenoid-ui — reference только для Allure wiring

selenoid-ui/ui — **reference example исключительно для RTL → Allure label wiring** (deps + `vite.config.ts` test block + `ALLURE_LABEL_*` script).

**НЕ копировать его архитектуру** в новые React apps:

- `react-router-dom` **v5** (`<Switch>`, `useHistory`) — legacy, в новых app использовать v6/v7 data router.
- `rxjs-hooks` (`useEventCallback`) — unmaintained; не тащить в новые app.
- `react-input-autosize` — unmaintained, peer react ≤16; не использовать в новых app.

Это v2 maintenance-код с зафиксированным стеком; ценность для канона — только паттерн Allure labels.

## Allure / dashboard mapping

| Поле | Значение |
|------|----------|
| Epic | `react-ui` (pilot) / `selenoid-ui` / `reference-app` (consumers) |
| Layer | `component` (общий с Java `@Layer("component")`) |
| scope | `react` (React Testing Library) / `browser` (Java Selenide) |
| framework | `react-testing-library` / `selenide` |
| Feature | имя компонента (`Button`, `Status`, `Viewport`) |
| Story | сценарий теста |
| tags | `react`, `vitest`, `jsdom` |

Фильтры в merged dashboard:

- весь component-слой: `layer=component`
- только React Testing Library: `layer=component` + `scope=react`
- только Java/Selenide: `layer=component` + `scope=browser`

**Не** вводить отдельный layer `react-component` — disambiguation через labels.

### selenoid-ui v2 (уровень A)

`yarn test` в `ui/` → `allure-results/`; artifact `allure-ui-react-testing-library` в CI.

### selenoid-tests merge (уровень B)

Оркестратор скачивает `allure-ui-react-testing-library` и мержит в `build/allure-results` вместе с Go unit и Java e2e.

## CI job

```bash
# install (frozen lockfile — yarn.lock коммитится)
yarn --cwd ui install --frozen-lockfile

# run
cd packages/react-ui && yarn test
# или
cd projects/selenoid-home/selenoid-ui/ui && yarn test
```

Target: < 2 min на pilot (4–8 tests); selenoid-ui React Testing Library suite ~20 tests.

## Coexistence с Java component tests

Java `@Layer("component")` и RTL `layer=component` **сосуществуют** на одном уровне пирамиды; различение — через `scope`.

| | Java `@Layer("component")` | React Testing Library (Vitest) |
|--|---------------------------|--------------------------------|
| Target | browser DOM (Selenide) | isolated jsdom |
| Tool | Selenide + Gradle | Vitest |
| layer | `component` | `component` |
| scope | `browser` | `react` |
| framework | `selenide` | `react-testing-library` |

Оба слоя дополняют друг друга: React Testing Library — быстрая регрессия UI behavior; Java component — реальный DOM/CSS в browser.

### Java side — реализовано (не только теория)

`scope=browser` / `framework=selenide` на Java-стороне задаются **не** через `ALLURE_LABEL_*` (это только RTL/Vitest), а через class-level label-annotations на `TestBase`, по образцу существующего `@Layer`:

- `annotations/Scope.java` — `@LabelAnnotation(name = "scope")`
- `annotations/Framework.java` — `@LabelAnnotation(name = "framework")`

Обе с `@Inherited`, `@Documented`, `@Retention(RUNTIME)`, `@Target({TYPE, METHOD})`. На `tests/TestBase.java`:

```java
@Scope("browser")
@Framework("selenide")
public class TestBase { ... }
```

За счёт `@Inherited` все наследники `TestBase` (`component`, `integration`, `e2e`) получают `scope=browser` + `framework=selenide` автоматически — вешать аннотации на каждый тест-класс не нужно. `@Layer` остаётся на конкретных классах (`@Layer("component")` и т.д.) — его значения не меняются.

**Не затронуты:** `ApiTestBase` (не extends `TestBase`) и unit-тесты — остаются без `scope`/`framework`.

Locations: `stacks/java-spring/tests/src/test/java/annotations/` (канон) + синхронизировано в `projects/reference-home/reference-app/tests/`.

Проверено на `LangToggleTests` (`./gradlew testComponent --tests "*LangToggle*" -DallureReportMode=allure3`) — в `build/allure-results/*-result.json`:

```json
"labels": [
  { "name": "layer", "value": "component" },
  { "name": "scope", "value": "browser" },
  { "name": "framework", "value": "selenide" }
]
```

> Allure также добавляет default `framework=junit-platform` — как и `framework=vitest` на RTL-стороне, это ожидаемо и фильтру не мешает (dashboard фильтрует по `scope=browser` + `layer=component`).

## Do

- Один describe на компонент; тесты по user-visible behavior (`getByRole`, `#sse-status` / `#selenoid-status`).
- Import CSS в test setup или component file.
- Allure labels через `ALLURE_LABEL_*` env в test script (единый стандарт), не хардкод в каждом тесте.
- Добавлять тест при каждом новом wrapper.
- selenoid-ui — брать только Allure wiring.

## Don't

- Snapshot всего DOM дерева без причины.
- Mock React internals или test implementation details (class names only as last resort).
- Заменять Java component tests на React Testing Library.
- Путать `@Component("selenoid-ui")` (TestOps repo) с react component layer.
- Сокращать framework label — всегда `react-testing-library`.
- Копировать архитектуру selenoid-ui (router v5, rxjs-hooks, react-input-autosize) в новые app.
- Использовать npm для selenoid-ui — проект на **yarn** (`yarn.lock`).

## selenoid-ui v2 status & deferred (v3)

**v2 = React 18 stabilization** (closed): React **18.3.1** + Vite 6 + Vitest 3 + React Testing Library + allure-vitest. **yarn-only** (`yarn.lock`, без `package-lock.json`). Node **24** (`.nvmrc`). Baseline зелёный — `yarn install` / `yarn test` (7 файлов, 22 теста) / `yarn build` / `yarn preview` (HTTP 200). Удалён неиспользуемый `rxjs-compat` (0 usages; весь `rxjs` — modern 6.x imports `rxjs` / `rxjs/operators` / `rxjs/ajax`, без legacy `rxjs/add/*` / `rxjs/Observable`).

> **Peer warnings под yarn (non-fatal):** `react-input-autosize@2.2.2` объявляет stale peer `react "^0.14 || ^15 || ^16"` и формально конфликтует с React 18. Пакет работает с React 18 в runtime; yarn выдаёт **предупреждение**, но install не падает — флаги вроде `--legacy-peer-deps` (npm-специфичные) **не нужны**. Замена пакета — deferred v3.

**Deferred → v3 (НЕ делать в v2):**

| Item | Причина откладывания |
|------|----------------------|
| React 18 → **React 19** | breaking (StrictMode effects, `ReactDOM.render` removed, ref-as-prop); отдельное окно с прогоном всех RTL tests |
| `react-router-dom` **v5 → v7** | data router API, `<Switch>`→`<Routes>`, `useHistory`→`useNavigate` — массовый рефактор роутинга |
| замена **`react-input-autosize`** | unmaintained, peer react ≤16 (источник peer-warning под yarn); кандидат `@react-input/*` / собственный autosize |
| замена **`rxjs-hooks`** | unmaintained (`useEventCallback`); мигрировать на rxjs 7 + собственный hook или убрать rxjs из UI-слоя |
| design-system header / **`@zero-design-system/react`** | v3 UI unification — **in progress** (AppHeader embed, pilot screen, library primitives) |
| VNC canvas **`willReadFrequently`** warning | косметический Chrome perf-hint из noVNC (`display.js` — `getImageData` на backbuffer при resize `VncCard/VncScreen.js`); не security/critical → **не** в maintenance v2.3.0. Фикс в v3: `patch-package` на `@novnc/novnc`, флаг **только** на backbuffer-context (видимый canvas оставить на GPU) |

v3 pilot (2026-07-13): `AppHeader` embed + `FilterInput` on library `Input`; design-system static in `ui/public/` (`scripts/sync-design-system-static.sh`). RTL suite **32 tests** green.

v3.3 (2026-07-13): `Status.js` on library `Badge`; `rxjs-hooks` removed from Capabilities/Sessions/Videos delete hooks. reference-app consumer `HomePage.tsx` uses `Badge` for health status (`health-status-badge`).

**Deferred → v3+ (НЕ делать в v2):**
