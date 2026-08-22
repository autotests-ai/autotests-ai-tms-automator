---
id: visual-baseline
domain: testing
phase: 4.visual
adr: 002, 003
tags: [visual, baseline]
---
# Visual baselines (cross-epic)

**id:** `visual-baseline`

Общая инфраструктура pixel diff для **всех** `@Tag("visual")` тестов. Не только header.

## Файлы

| Файл | Назначение |
|------|------------|
| `helpers/ScreenshotBaseline.java` | Selenide capture + compare + write baseline |
| `config/TestConfig.java` | `updateBaselines`, `baselinesDir`, `visualDiffThreshold` |
| `tests/LoginBaselineTests.java` | login form (`@Epic("Authentication")` / one-page-form: `@Epic("One Page Form")`) |
| `tests/WelcomePanelBaselineTests.java` | Multistack: `[data-testid='welcome-panel']` на `/` после login |
| `tests/LoggedInBaselineTests.java` | one-page-form: welcome на `/logged-in.html` (ADR 002) |
| `tests/e2e/HomeLayoutBaselineTests.java` | `@Epic("Home")` — home на `/` (Multistack layout) |
| `src/test/resources/screenshots/{mock|stage|prod}/{os}/{browser}/{area}/` | living PNG (`login`, `welcome-panel`, `home-layout`). Canon: `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/_contract/visual-snapshots.md` |

Header-специфика (селекторы, viewports preview) — чанк `hdr-visual-opt`.

## Входы

- `-DupdateScreenshots=true` — перезаписать PNG вместо compare (локально / clone `ci.yml` dispatch `update_mock_screenshots` / `update_stage_screenshots` / `update_ci_screenshots` / `update_e2e_screenshots` на Linux)
- `-DvisualDiffThreshold=0.02` — tuning pixel diff без перекомпиляции
- `baselinesDir` — подкаталог `src/test/resources/` (default `screenshots`)
- env profile (`local_e2e`, `local_visual`, …) — тот же stand, другой **CI slice** (не `@Layer`)
- viewport: **390**, **768**, **1280** (`layout-standard.md`)

## Assert

pixel diff ratio ≤ `visualDiffThreshold` (default `0.015`); размер PNG не меняется. CI: compare-only — без baseline PNG тест **FAIL** (не auto-record). **CI SSOT:** baselines сняты на Linux headless Chrome 148 (clone `ci.yml` jobs `ui-mock-tests` / `ui-ci-tests` / `e2e-tests-stage` / `e2e-tests`). `ui-ci-tests` пишет в `screenshots/prod/` с `-Denv=ci` (local compose, не live prod).

## Allure attachments (`{area}-{viewport}`)

Имена из `*BaselineTests` (`login-390`, `welcome-panel-768`, …; one-page-form: `logged-in-*`). `TestBase` «Last screenshot» — отдельно, full page.

Вложения группируются под родительским step в helper: `Compare screenshot: {area}-{viewport}` (или `Update baseline:` / `Record baseline:`).

| Режим | Вложения |
|-------|----------|
| compare OK | `{area}-{viewport}` |
| compare FAIL | `-baseline`, `-actual`, `-diff` (diff — подсветка пикселей) |
| `-DupdateBaselines=true`, baseline есть | `-baseline-old`, `-baseline-new` |
| `-DupdateBaselines=true`, baseline нет | `-baseline-new` |
| compare, baseline нет | FAIL + `-actual-unmatched` |

## Do

- Отдельный test-класс на visual (`*BaselineTests`), не смешивать с `@Tag("smoke")` / `@Tag("layout")`; на классе `@Layer("e2e")`, slice — `@Tag("visual")` + `testVisual` / `*_visual` (чанк `test-pyramid`)
- Один `@Test` — один screenshot assert (не layout probe + screenshot)
- Baselines: Multistack — `screenshots/login/`, `screenshots/welcome-panel/`, `screenshots/home-layout/`; one-page-form — `screenshots/login/`, `screenshots/logged-in/` (ADR 002)
- **design-system plaque-seg 2-opt** — Python gate `scripts/plaque-seg-visual.py` + fixture `preview/plaque-seg-visual.html` + baselines `preview/baselines/plaque-seg/` (RAG `script-plaque-seg-visual`); pair with static `configurator-boolean-audit.py`
- Multistack: login → `/` → crop `[data-testid='welcome-panel']`; one-page-form — welcome на `/logged-in.html`; localStorage shortcut — `test-storage-shortcut`
- Запуск suite: `./gradlew test -DincludeTags=visual` (`@Tag("visual")`); перезапись — `-DupdateBaselines=true`
- Allure Suites: class-level `@Suite` + `@SubSuite("visual")` → `Login > visual`, `Welcome panel > visual` (Multistack); one-page-form — `Logged-in > visual`

## Don't

- Отдельный флаг на epic (`updateHeaderBaselines`, `updateLoginBaselines`)
- Legacy `updateNavBaselines` / `NavScreenshot` — не копировать в канон
- Screenshot в том же `@Test`, что behavioral smoke или layout probe
- Baselines в PR smoke/layout (4a, 4b)
- `attachLastScreenshot=true` в рутинных visual-прогонах — redundant с element crop из `ScreenshotBaseline`; full page только для opt-in отладки
- Playwright visual в SPA **нет**. Java-канон visual = Selenide; папки `mock/` · `stage/` · `prod/` тем же раннером (`visual-snapshots.md`). RTL живёт в `frontend/typescript/frontend-typescript-react/src/test/`.
