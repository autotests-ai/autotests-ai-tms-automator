---
id: e2e-config-keys
domain: e2e
phase: 4a
adr: 002
tags: [config, properties, selenide, allure, testops]
---
# Config keys e2e

Ключи `TestConfig` / `config/*.properties`. Override: `-Dkey=value` или `-Denv=profile`.

Owner merge (приоритет ↓): `system:properties` → `config/${env}.properties` → `default.properties` → `@DefaultValue`.

`default.properties` — runtime defaults (= `@DefaultValue` в `TestConfig`); не env-профиль (`env` ≠ `default`). SSOT структуры — `_ethalon.properties`.

Четыре независимых слоя — не смешивать:

| Слой | Ключи | Назначение |
|------|-------|------------|
| **Allure Report** | `allureReportMode` | Писать `build/allure-results` + локальный HTML |
| **Allure Agent Mode** | `allureAgentMode` | Post-test `allure agent inspect/query` → `build/agent-output/` (фаза 7.analytics) |
| **Allure runtime** | `attach*`, `enableAllureSelenideListener` | Listener + attachments в `@AfterEach` |
| **Console log** | `logToConsole`, `selenideLogToConsole`, `rootLogLevel` | JVM/Selenide stdout; ≠ `attachBrowserConsoleLogs` |

## Run / driver

| Key | Default | Назначение |
|-----|---------|------------|
| `env` | `local` | `config/${env}.properties` |
| `baseUrl` | `""` | HTTP(S) корень |
| `basePath` | `""` | Локальная папка → `file://` |
| `apiBaseUrl` | `""` | Rest Assured base URI; пустой → `hubUrl` |
| `browser` | `chrome` | |
| `browserVersion` | `148` | remote |
| `browserSize` | `1920x1280` | |
| `headless` | `false` | |
| `closeBrowserAfterEach` | `false` | |
| `closeBrowserAfterAll` | `true` | |
| `includeTags` | `""` | JUnit `@Tag` include (comma-separated), напр. `visual` |
| `excludeTags` | `""` | JUnit `@Tag` exclude (comma-separated) |
| `remoteUrl` | `""` | Selenoid / Grid |
| `enableVnc`, `enableVideo`, `enableHar` | `false` | selenoid:options |
| `videoFolder` | `""` | prefix для video URL |

## Selenoid hub / Playwright

Ключи из `selenoid-home` (hub smoke, Java+Playwright, Go unit — отдельный pipeline). SSOT: `_ethalon.properties`, `TestConfig.java`.

| Key | Default | Назначение |
|-----|---------|------------|
| `hubUrl` | `http://127.0.0.1:4444/` | Selenoid hub status API |
| `uiUrl` | `http://127.0.0.1:8080/` | Selenoid UI |
| `smokeUrl` | `https://example.com/` | URL для hub smoke-тестов |
| `playwrightWsEndpoint` | `ws://127.0.0.1:4444/playwright/…` | Playwright CDP через Selenoid |
| `playwrightSessionName` | `java-playwright-tests` | имя сессии |
| `playwrightSessionTimeout` | `5m` | timeout сессии |
| `playwrightEnableVnc` | `false` | VNC для Playwright-сессии |
| `playwrightEnableVideo` | `false` | video для Playwright-сессии |

Inbox ключей из consumer-репо (selenoid, selenoid-ui): `_new.properties` → merge в эталон. Selenide e2e-профили (`local`, `selenoid-*`) hub-ключи не задают — defaults из `TestConfig`.

### Env profiles (`{stand-base}_{deployment}_{layer}`)

Stand-only файлы **не используются**. Один файл = стенд × слой пирамиды.  
Сегменты разделяются `_`; внутри имени стенда допустимы `-` (напр. `selenoid-autotests-cloud`).

`-Denv=<stand-base>_<deployment>_<layer>` → `config/<stand-base>_<deployment>_<layer>.properties`  
Без deployment-сегмента: `-Denv=local_e2e` → `config/local_e2e.properties`

| Stand | Назначение |
|-------|------------|
| `local` | `frontend/` HTTP `:3000` |
| `header-local` | alias `local` |
| `one-page-form_local` | local HTTP + Docker Selenoid |
| `one-page-form_prod` | GitHub Pages + cloud hub |
| `selenoid_local` | GitHub Pages + local Docker hub |
| `selenoid_github` | selenoid-home — GitHub Actions |
| `selenoid_jenkins` | selenoid-home — Jenkins |
| `selenoid-ui_github` | selenoid-ui — GitHub Actions |
| `selenoid-ui_local` | selenoid-ui — local dev |
| `selenoid-autotests-cloud_github` | cloud hub + CI attachments |
| `selenoid-autotests-cloud_local` | cloud hub — local workstation |

| Layer | Gradle slice | Tags |
|-------|--------------|------|
| `unit` | `./gradlew testUnit` | glob; auto skip health check |
| `component` | `./gradlew testComponent` | `-DincludeTags=component` |
| `integration` | `./gradlew testIntegration` | `-DincludeTags=layout,mount` |
| `api` | `./gradlew testApi` | `-DincludeTags=api`; auto skip health check |
| `e2e` | `./gradlew testE2e` | `-DincludeTags=smoke -DexcludeTags=visual` |
| `visual` | `./gradlew testVisual` | `-DincludeTags=visual` |
| `manual` | `./gradlew testManual` | `-DincludeTags=manual` |

Convenience tasks: ADR 005, `build.gradle` (`verification` group). Stand default `local`; override `-DpyramidStand=one-page-form_prod` → env `one-page-form_prod_e2e`. Эквивалент через `./gradlew test -Denv=…` сохранён.

### `healthCheck` (auto skip)

`healthCheck` перед `test` пропускается, если:

- `-DskipHealthCheck=true`;
- `-Denv` оканчивается на `_unit` или `_api`;
- `-DincludeTags=api` (только api, без других тегов).

Pyramid tasks (`testE2e`, …) выставляют env для health check через task graph.  
Регенерация матрицы: `python scripts/gen-env-layer-configs.py`.

### `headless`

| Value | Поведение |
|-------|-----------|
| `false` | Окно браузера видно (локальная отладка) |
| `true` | Headless Chrome; при локальном driver — `--disable-gpu`, `--no-sandbox`, `--disable-dev-shm-usage`; при `remoteUrl` — `selenoid:options.headless` |

### `closeBrowserAfterEach`

| Value | Поведение |
|-------|-----------|
| `false` | Между тестами `BrowserSessionHelper.resetPageState()` (cookies/storage) |
| `true` | `closeWebDriver()` в `@AfterEach` — изолированный debug, медленнее |

### `closeBrowserAfterAll`

| Value | Поведение |
|-------|-----------|
| `true` | `closeWebDriver()` в `@AfterAll` TestBase — после всех тестов класса |
| `false` | Driver остаётся открытым после класса (если не закрыт в `@AfterEach`) |

Типичная пара для e2e/visual: `closeBrowserAfterEach=false` + `closeBrowserAfterAll=true` — reuse между тестами, закрытие в конце класса. Skill: `add-e2e-config-property`.

### `browserSize` (типовые)

| Value | Viewport |
|-------|----------|
| `1920x1280` | Desktop (default) |
| `1280x720` | HD |
| `768x1024` | Tablet portrait |
| `390x844` | Mobile |

### Selenoid capabilities (`remoteUrl` задан)

| Key | `false` | `true` |
|-----|---------|--------|
| `enableVnc` | без VNC | live view в Selenoid UI |
| `enableVideo` | без записи | mp4 на hub; для Allure нужен ещё `attachVideo=true` |
| `enableHar` | без HAR | HAR на hub; `attachHarLogs` — stub, не включать |

## Allure Report

| Key | Default | Назначение |
|-----|---------|------------|
| `allureReportMode` | `allure3` | Слой записи `build/allure-results` + способ локального HTML |

### `allureReportMode` (values)

Gradle adapter (`build.gradle`) различает только `none` vs «не none»; `allure2` и `allure3` отличаются **способом генерации HTML** после прогона.

| Value | Adapter / AspectJ | `build/allure-results` | Attachments в `TestBase` | AllureSelenide listener | Локальный HTML |
|-------|-------------------|------------------------|--------------------------|-------------------------|----------------|
| `none` | off (`autoconfigure=false`, `aspectjWeaver=false`, junit5 adapter off) | не пишется; каталог удаляется после `test` | skip (`@AfterEach` early return) | blocked | — |
| `allure2` | on | пишется | при `attach*=true` | при `enableAllureSelenideListener=true` | `allure serve build/allure-results` |
| `allure3` | on | пишется | при `attach*=true` | при `enableAllureSelenideListener=true` | `./gradlew allureReport` + `allurerc.json` → `build/reports/allure-report/allureReport/` |

Override: `-DallureReportMode=none|allure2|allure3` (Gradle system property).

## Allure Agent Mode

Ортогонально `allureReportMode`: требует `build/allure-results` (т.е. `allureReportMode≠none`). Gradle post-`test` hook — фаза **7.analytics**; `TestConfig.allureAgentMode()`; task `allureAgentInspect` в `build.gradle`.

| Key | Default | Назначение |
|-----|---------|------------|
| `allureAgentMode` | `none` | `none` — hook off; `inspect` — `allure agent inspect build/allure-results --output build/agent-output/` (agent-readable manifest + `index.md`); агент/skill читает через `allure agent query --from build/agent-output …` |

### `allureAgentMode` (values)

| Value | Gradle hook | Выход | Когда |
|-------|-------------|-------|-------|
| `none` | off | — | default; CI без agent workflow |
| `inspect` | post-`test` → `allure agent inspect` | `build/agent-output/` | разбор прогона агентом / skill `allure-agent-inspect` |

Override: `-DallureAgentMode=none|inspect`.

Ручной прогон (без Gradle hook):

```bash
npx allure agent inspect build/allure-results --output build/agent-output
npx allure agent query --from build/agent-output summary
npx allure agent query --from build/agent-output tests --status failed
```

Конфиг: `allurerc.json` (тот же, что для `./gradlew allureReport`). Skill (planned): `allure-agent-inspect`.

## Allure runtime

| Key | Default | Назначение |
|-----|---------|------------|
| `enableAllureSelenideListener` | `false` | Auto-steps Selenide → Allure |
| `attachBrowserConsoleLogs` | `false` | browser console → Allure attachment |
| `attachPageSource`, `attachLastScreenshot`, `attachHarLogs`, `attachVideo` | `false` | opt-in artifacts |
| `updateBaselines` | `false` | Перезаписать baselines PNG для `@Tag("visual")`; см. `visual-baseline` |
| `baselinesDir` | `screenshots` | Подкаталог `src/test/resources/` с baseline PNG |
| `visualDiffThreshold` | `0.015` | Max pixel diff ratio; `-DvisualDiffThreshold=0.02` |

### `enableAllureSelenideListener` / e2e-builder `allureListenerMode`

| Value / mode | Условие | Поведение |
|--------------|---------|-----------|
| `false` / `global_off` | default | Listener не регистрируется в `@BeforeAll` |
| `true` / `global_on` | + `allureReportMode≠none` | `SelenideLogger.addListener("AllureSelenide", …)` в `TestBase.setup()` |

Per-test override: `@EnableAllureSelenideListener` на методе.

### Attachments (`attach*`)

Требуют `allureReportMode≠none`. Opt-in в `@AfterEach` `TestBase`.

| Key | `false` | `true` |
|-----|---------|--------|
| `attachBrowserConsoleLogs` | skip | browser console → Allure attachment |
| `attachPageSource` | skip | HTML page source |
| `attachLastScreenshot` | skip | screenshot «Last screenshot» |
| `attachVideo` | skip | video link (нужен `enableVideo=true` на hub) |
| `attachHarLogs` | skip | **stub — бросает exception** |

### Visual baselines

| Key | default / `false` | `true` / override |
|-----|-------------------|-------------------|
| `updateBaselines` | compare PNG vs эталон | перезапись baseline PNG |
| `baselinesDir` | `screenshots` | подкаталог `src/test/resources/` |
| `visualDiffThreshold` | `0.015` | `-DvisualDiffThreshold=0.02` |

## Console log

| Key | Default | Назначение |
|-----|---------|------------|
| `logToConsole` | `true` | мастер-переключатель stdout |
| `selenideLogToConsole` | `true` | Selenide `SimpleReport` (не AllureSelenide) |
| `rootLogLevel` | `info` | `org.slf4j.simpleLogger.defaultLogLevel` |

### `logToConsole` + зависимые ключи

| `logToConsole` | `selenideLogToConsole` | `rootLogLevel` | Поведение |
|----------------|------------------------|----------------|-----------|
| `false` | *(ignored)* | *(ignored)* | SLF4J → `off`; Selenide SimpleReport не стартует |
| `true` | `false` | любой | JVM log level из `rootLogLevel`; без Selenide step report в stdout |
| `true` | `true` | см. ниже | + `SimpleReport.start/finish` на каждый тест |

### `rootLogLevel` (values)

| Value | SLF4J `defaultLogLevel` |
|-------|-------------------------|
| `trace` | trace |
| `debug` | debug |
| `info` | info (default) |
| `warn` | warn |
| `error` | error |

≠ `attachBrowserConsoleLogs` — browser console в Allure, не JVM stdout.

## TestOps (env runner'а, не TestConfig)

`ALLURE_*` — переменные окружения для CI/runner и `allurectl` (upload в TestOps). В Java-тесты и `./gradlew -D` не попадают. Ортогонально локальному HTML. Имена как в qa-guru-home CI:

| Env | Пример |
|-----|--------|
| `ALLURE_ENDPOINT` | `https://allure.autotests.cloud` |
| `ALLURE_PROJECT_ID` | per project (напр. `5263`) |
| `ALLURE_TOKEN` | secret, не в git |
| `ALLURE_RESULTS` | `build/allure-results` |
| `TEST_CASE_ID` | `@AllureId` / launch name |

### e2e-builder `testopsEnabled`

| Value | Поведение |
|-------|-----------|
| `false` | Локальный прогон; env `ALLURE_*` не обязательны |
| `true` | Обёртка `allurectl watch --results build/allure-results -- ./gradlew test …`; нужны `ALLURE_ENDPOINT`, `ALLURE_TOKEN`, `ALLURE_PROJECT_ID` |

Требует `allureReportMode≠none` (иначе конфликт в e2e-builder).

Прогон: `allurectl watch --results build/allure-results -- ./gradlew test …`

## Don't

- `attachHarLogs=true` — stub, бросает exception.
- `allureReportMode=none` + `attach*=true` или TestOps — конфликт (e2e-builder).
- `allureReportMode=none` + `allureAgentMode=inspect` — нет results для `agent inspect`.
- CI/TestOps/Selenoid consumer workflows — `qa-guru-home/`; ethalon: `tests-java/.github/_ethalon/{stand}.yml` и `{stand}-orchestrator.yml` (skill `sync-github-workflows-ethalon`).
