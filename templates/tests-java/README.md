# tests-java — эталон e2e (Java)

Selenide + JUnit 5 + Allure. **SSOT** e2e в `autotests-ai-tms-automator`.

**Static root (local):** `templates/vanilla-ui/` — `python -m http.server 3000`.  
**RAG:** [`docs/rag/testing/`](../../docs/rag/testing/), [`docs/rag/testing-header/`](../../docs/rag/testing-header/).  
**ADR:** [`docs/adr/002-e2e-canonical-patterns.md`](../../docs/adr/002-e2e-canonical-patterns.md), [`003-header-smoke-e2e.md`](../../docs/adr/003-header-smoke-e2e.md), [`004-fast-testops-warm-pool.md`](../../docs/adr/004-fast-testops-warm-pool.md).

**GitHub bootstrap:** тот же каталог — automator копирует infra через `prepare_bootstrap_workdir()` (без e2e test classes, `pages/`, baselines).  
**CI workflow:** `.github/workflows/selenoid-qa-guru_github.yml` (`name: qa_guru_automator_ethalon-5267 Tests`).

## Prerequisites

- JDK 17+
- Chrome (local) или Selenoid (remote profiles)
- **`templates/vanilla-ui/`** — static root (или override `basePath` / `-DbaseUrl`)
- Gradle 9+ (локально установленный `gradle`, wrapper не используем)

## Target (login + header)

Все harness-страницы в `templates/vanilla-ui/`:

| Harness | Путь при `baseUrl=http://localhost:3000/` |
|---------|---------------------------------------------|
| Login | `/login.html` |
| Header | `/header.html` |

PO: `open("/login.html")`, `open("/header.html")` — без config path keys.

Подробнее: [`src/test/resources/pages/README.md`](src/test/resources/pages/README.md).

### Запуск полного suite

`header.js` — ES module; **нужен HTTP** (не `file://`).

```bash
# терминал 1 — cwd = templates/vanilla-ui/
cd templates/vanilla-ui
python -m http.server 3000

# терминал 2
cd templates/tests-java
gradle test
```

`local.properties`: `baseUrl=http://localhost:3000/`.

Перед `test` Gradle запускает **`healthCheck`**: `GET baseUrl/login.html` → HTTP 200. Иначе fail с подсказкой запустить сервер из `frontend/`. Пропуск: `-DskipHealthCheck=true` (unit-only без HTTP).

```bash
gradle healthCheck -Denv=local
gradle test --tests 'config.ConfigReaderTest' -DskipHealthCheck=true
```

### Режимы baseUrl / basePath

| Режим | Конфиг | Когда |
|-------|--------|-------|
| **A. Local HTTP** (рекомендуется) | `baseUrl=http://localhost:3000/` + сервер из **`frontend/`** | `gradle test` — login + header |
| **B. Login-only file://** | `baseUrl=` (пусто), `basePath=../frontend` | Без сервера; только login/logout |
| **C. Prod / remote** | `baseUrl=https://qa-guru.github.io/one-page-form/` | Login на GitHub Pages |

Приоритет резолва: `baseUrl` → `basePath` → fail fast. Override: `-DbaseUrl` / `-DbasePath`.

## Структура

```
src/test/java/
├── config/          TestConfig, ConfigReader, *Test (unit)
├── helpers/         ViewportHelper, HeaderLayout, LayoutCss, ScreenshotBaseline, *Test (unit)
├── tests/           TestBase, e2e + integration *Tests
│   └── component/   @Layer("component") — components.html
├── pages/           Page Objects (@Step)
├── allure/          Attachment helpers
└── annotations/     @Layer, @Manual → Allure labels

src/test/resources/
├── config/          Env profiles (*.properties)
└── junit-platform.properties
```

## Запуск

Из каталога `tests-java/`:

```bash
# полный suite (сервер :3000 из frontend/ — см. выше)
gradle test

# по ярусам пирамиды
gradle test --tests 'helpers.*Test' --tests 'config.*Test'   # unit
gradle test -DincludeTags=component                          # component
gradle test -DincludeTags=layout,mount                       # integration
gradle test -DincludeTags=smoke -DexcludeTags=visual         # e2e smoke
gradle test -DincludeTags=manual                             # exploratory @Manual
gradle test -DincludeTags=visual                             # baselines (nightly)
gradle test -DincludeTags=visual -DupdateBaselines=true

# другой profile
gradle test -Denv=one-page-form-prod

# только login e2e
gradle test --tests 'tests.LoginTests'

# только header e2e
gradle test --tests 'tests.HeaderTests'

# override отдельных ключей
gradle test -Dheadless=true -DcloseBrowserAfterEach=true

# unit без HTTP-сервера
gradle test --tests 'config.ConfigReaderTest' -DskipHealthCheck=true

# отладочный параллельный прогон (rule e2e-debug-run)
gradle test -Dheadless=true -DcloseBrowserAfterEach=false \
  -Djunit.jupiter.execution.parallel.config.fixed.parallelism=3
```

### Release verification (CI slices)

Prerequisite: HTTP server из `frontend/` на `:3000` (см. выше). Прогнано при release freeze ✓.

```bash
gradle test -DincludeTags=smoke -DexcludeTags=visual   # e2e smoke — LoginTests, HeaderTests
gradle test -DincludeTags=visual                         # baselines — nightly / opt-in PR
gradle test -DincludeTags=manual                         # exploratory stubs (3 tests)
gradle test -DincludeTags=layout,mount                   # integration — HeaderLayoutTests, LoginFormTests, LoginEmbedTests
```

Allure report (после прогона):

```bash
./gradlew allureQualityGate   # exit 1 если rules в allurerc.json не прошли (см. alr-quality-gate)
./gradlew allureReport
# file:// блокируется во встроенном браузере Cursor — открывать через HTTP:
# cd build/reports/allure-report/allureReport && python -m http.server 5050
# → http://localhost:5050/
# или в системном браузере: open build/reports/allure-report/allureReport/index.html
```

### Quality gate

Allure 3 quality gate — отдельный шаг после `test`, до `allureReport` / TestOps upload.

| Артефакт | Назначение |
|----------|------------|
| `allurerc.json` → `qualityGate.rules` | Правила (default: `maxFailures: 0`) |
| `known.json` | Known issues по `historyId` (не считаются в `maxFailures`) |
| Gradle `allureQualityGate` | `npx allure@<allureVersion> quality-gate build/allure-results` |

```bash
gradle test -DincludeTags=smoke -DexcludeTags=visual && gradle allureQualityGate
# или hook на test:
gradle test -DallureQualityGate=true -DincludeTags=smoke -DexcludeTags=visual
```

CI: шаг **Allure 3 quality gate** после Run app e2e tests; job fail при `TEST_EXIT≠0` или `QUALITY_GATE_EXIT≠0`. RAG: [`alr-quality-gate`](../../docs/rag/analytics/alr-quality-gate.md).

## Env profiles

| File | Когда |
|------|-------|
| `local.properties` | Default (`-Denv=local`). `frontend/` HTTP `:3000` |
| `header-local.properties` | Alias `local` |
| `one-page-form-local.properties` | `frontend/` HTTP + Selenoid hub |
| `one-page-form-prod.properties` | GitHub Pages one-page-form (login only) |
| `selenoid-local.properties` | Remote hub, prod URL |
| `selenoid.qa.guru-prod.properties` | Cloud Selenoid |
| `ci.properties` | GHA + Selenoid cloud, full Allure attachments (Run 3 diagnostic) |
| `fast-testops.properties` | Co-located Jenkins + warm pool: lean browser, Allure minimal (Run 1/2) |

Выбор: `-Denv=<name>` → `classpath:config/<name>.properties`.

### Fast TestOps (3-run)

Run 1/2: `-Denv=fast-testops` — `allure3` без attachments, `@AllureId` в generated test, `allurectl upload`.  
Run 3: `-Denv=ci` — video, screenshot, pageSource, debug logs.

```bash
export TEST_CLASS='tests.LoginTests.shouldLoginWithValidCredentials'
export PREOPEN_URL='https://qa-guru.github.io/one-page-form/login.html'
chmod +x scripts/testops-fast-launch.example.sh
./scripts/testops-fast-launch.example.sh
```

См. [`docs/adr/004-fast-testops-warm-pool.md`](../../docs/adr/004-fast-testops-warm-pool.md), warm pool: `selenoid-home/selenoid-warm-pool/`.

## Config keys

| Key | Default (local) | Описание |
|-----|-----------------|----------|
| `baseUrl` | `http://localhost:3000/` | HTTP(S) корень — приоритет над `basePath` |
| `basePath` | *(empty)* | Локальная папка → `file://` (login-only без сервера) |
| `browser` | `chrome` | |
| `browserVersion` | `148` | |
| `browserSize` | `1920x1280` | |
| `headless` | `true` | |
| `closeBrowserAfterEach` | `false` | `true` — изолированный debug; иначе reset в `BrowserSessionHelper` |
| `visualDiffThreshold` | `0.015` | Pixel diff ratio для `@Tag("visual")`; override: `-DvisualDiffThreshold=0.02` |
| `baselinesDir` | `screenshots` | Classpath/resources: `src/test/resources/{baselinesDir}/` |
| `updateBaselines` | `false` | `true` — перезапись PNG; compare-only в CI |
| `remoteUrl` | *(empty)* | Selenoid / Grid |
| `enableVnc`, `enableHar` | `false` | Selenoid capabilities |
| `enableVideo` | `false` | Запись видео на Selenoid |
| `attachVideo` | `false` | HTML-attachment с видео в Allure |
| `videoFolder` | *(empty)* | URL-prefix до mp4 на Selenoid |
| `enableAllureSelenideListener` | `false` | Selenide steps в Allure |
| `attachBrowserConsoleLogs` | `false` | |
| `attachPageSource` | `false` | |
| `attachLastScreenshot` | `false` | |
| `attachHarLogs` | `false` | **Не реализовано** — не включать |

**Video в Allure (Selenoid):** нужны **оба** флага — `enableVideo=true` и `attachVideo=true`. Плюс `remoteUrl`, `videoFolder`.

Полный список: `TestConfig.java`, ADR 002.

## Tests (pyramid)

Роль теста — `@Layer` + `@Tag` + `@Epic`. Имена классов **без** Smoke / Visual / Mount.

| Layer | Classes | Target |
|-------|---------|--------|
| unit | `helpers/*Test`, `config/ConfigReaderTest` | pure Java |
| component | `tests/component/*Tests` | `/components.html` |
| integration | `HeaderLayoutTests`, `LoginFormTests`, `LoginEmbedTests` | `/header.html`, `/login.html` mount + embed |
| e2e | `HeaderTests`, `LoginTests`, `*BaselineTests` | harness pages + screenshot diff |
| manual | `@Manual` в `LoginTests`, `HeaderTests` | exploratory stubs (`@Tag("manual")` на методе) |

### Login (4a)

| Class | Layer | Tags | Сценарий |
|-------|-------|------|----------|
| `LoginFormTests` | integration | mount | Form fields visible, no submit flow |
| `LoginEmbedTests` | integration | mount | Embedded `#app-header` → `data-testid="header"` visible |
| `LoginTests` | e2e | smoke, positive; `@Manual` manual | Valid login via PO; invalid creds / empty fields (exploratory) |
| `LoginBaselineTests` | e2e | visual | Login form screenshot baselines |
| `LoggedInBaselineTests` | e2e | visual | Welcome panel after submit-flow |

Target: `frontend/login.html`. Epic: **One Page Form**.

### Header (4b)

| Class | Layer | Tags | Сценарий |
|-------|-------|------|----------|
| `HeaderTests` | e2e | smoke; `@Manual` manual | External href, theme toggle, lang label; mobile toggles when nav hidden |
| `HeaderLayoutTests` | integration | layout | Gap 16px, height ~56px, nav/search visibility |
| `HeaderBaselineTests` | e2e | visual | Header screenshot baselines |

Target: `frontend/header.html`. Epic: **Template Header**.

### Screenshot baselines

```bash
gradle test -DincludeTags=visual -DupdateBaselines=true
```

## Preview symlink

`tests-java/app-path-local` → `../frontend` — rule `frontend-preview`, `file://` в чате.

## Не в scope

- Landing / dashboard screenshot — legacy only
- `qa-guru-home/` legacy
- CI bootstrap — skill `bootstrap-test-repo` (**active**, scope в `docs/downstream-map.md`)
