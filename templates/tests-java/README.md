# tests-java — эталон e2e (Java)

Selenide + JUnit 5 + Allure. **Единственный канон** стиля и структуры e2e в template-project.

**Фаза 4a ✓** — login/logout на `frontend/login.html`.  
**Фаза 4b.1 ✓** — header smoke на `frontend/header.html`.  
**Фаза 4.visual ✓** — screenshot baselines (`*BaselineTests`, `ScreenshotBaseline`).  
**Фаза 4.pyramid ✓** — testing pyramid: unit / component / integration / e2e / manual.  
**Фаза 6 ✓** — login embed (`LoginEmbedTests`).  

**E2e stack release-ready** (4a + 4b.1 + 4.visual + 4.pyramid) — канон для bootstrap; curriculum — отдельно в `tests-java-curriculum/`.

Паттерны login: ADR 002, чанки [`docs/rag/e2e/`](../docs/rag/e2e/).  
Учебная ladder (negative, listener, LogoutTests): [`tests-java-curriculum/`](../tests-java-curriculum/) — не CI.  
Header (4b): ADR 003, чанки [`docs/rag/e2e-header/`](../docs/rag/e2e-header/). Индекс: [`docs/rag/README.md`](../docs/rag/README.md).

## Prerequisites

- JDK 17+
- Chrome (local) или Selenoid (remote profiles)
- **`frontend/`** — единый static root в репо (или override `basePath` / `-DbaseUrl`)
- Gradle 9+ (локально установленный `gradle`, wrapper не используем)

## Target (login + header)

Все harness-страницы в `frontend/`:

| Harness | Путь при `baseUrl=http://localhost:3000/` |
|---------|---------------------------------------------|
| Login | `/login.html` |
| Header | `/header.html` |

PO: `open("/login.html")`, `open("/header.html")` — без config path keys.

Подробнее: [`src/test/resources/pages/README.md`](src/test/resources/pages/README.md).

### Запуск полного suite

`header.js` — ES module; **нужен HTTP** (не `file://`).

```bash
# терминал 1 — cwd = frontend/
cd frontend
python -m http.server 3000

# терминал 2
cd tests-java
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
gradle allureReport
# file:// блокируется во встроенном браузере Cursor — открывать через HTTP:
# cd build/reports/allure-report/allureReport && python -m http.server 5050
# → http://localhost:5050/
# или в системном браузере: open build/reports/allure-report/allureReport/index.html
```

## Env profiles

| File | Когда |
|------|-------|
| `local.properties` | Default (`-Denv=local`). `frontend/` HTTP `:3000` |
| `header-local.properties` | Alias `local` |
| `one-page-form-local.properties` | `frontend/` HTTP + Selenoid hub |
| `one-page-form-prod.properties` | GitHub Pages one-page-form (login only) |
| `selenoid-local.properties` | Remote hub, prod URL |
| `selenoid.autotests.cloud-prod.properties` | Cloud Selenoid |

Выбор: `-Denv=<name>` → `classpath:config/<name>.properties`.

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
