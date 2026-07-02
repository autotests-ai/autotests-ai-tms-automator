---
id: test-pyramid
domain: e2e
phase: 4.pyramid
adr: 002
tags: [structure, junit, layer, pyramid]
related: [005-pyramid-gradle-tasks]
---
# Testing pyramid (канон)

**id:** `test-pyramid`

Ярусы тестов в **`tests-java/`** — единственный канон для CI и bootstrap. Роль теста: `@Layer` + `@Tag` + `@Epic`. Имена классов **без** Smoke / Visual / Mount в названии.

## Файлы (канон)

| Layer | Путь / классы | Target |
|-------|---------------|--------|
| unit | `helpers/*Test`, `config/ConfigReaderTest` | pure Java |
| component | `tests/component/*Tests` | `/components.html` |
| integration | `HeaderLayoutTests`, `LoginFormTests`, `LoginEmbedTests` | `/header.html`, `/login.html` mount + embed |
| api | `tests/api/*Tests` | Rest Assured HTTP (`hubUrl` / `apiBaseUrl`) |
| e2e | `HeaderTests`, `LoginTests`, `*BaselineTests` | harness + screenshot diff |
| manual | `@Manual` в `LoginTests`, `HeaderTests` | exploratory stubs (`@Tag("manual")` на методе) |

Login: `LoginFormTests` (integration) → `LoginTests` (e2e smoke) → `LoginBaselineTests` / `LoggedInBaselineTests` (visual).  
Header: `HeaderLayoutTests` (integration) → `HeaderTests` (e2e smoke) → `HeaderBaselineTests` (visual).

Учебная ladder-градация стилей — ethalon **`tests-java/src/test/java/_ethalon/ladder/`**, чанк **`test-style-ladder`**. Не смешивать с каноном.

## Gradle

**Full suite** (`./gradlew test`) ≠ **CI slices** — default env `local-e2e`; исключены `@Tag("ladder-ethalon")` и `@Tag("api")` (api — только `testApi` / hub). Slices: convenience tasks (ADR 005) или эквивалентные `-D`.

| Task | Эквивалент |
|------|------------|
| `testUnit` | `--tests 'helpers.*Test' config.*Test` + `-Denv=local-unit` (auto skip health check) |
| `testComponent` | `-Denv=local-component -DincludeTags=component` |
| `testIntegration` | `-Denv=local-integration -DincludeTags=layout,mount` |
| `testApi` | `-Denv=local-api -DincludeTags=api` (hub: `-DpyramidStand=selenoid-local`) |
| `testE2e` | `-Denv=local-e2e -DincludeTags=smoke -DexcludeTags=visual` |
| `testVisual` | `-Denv=local-visual -DincludeTags=visual` |
| `testManual` | `-Denv=local-manual -DincludeTags=manual` |

```bash
./gradlew testUnit
./gradlew testE2e
./gradlew testApi -DpyramidStand=selenoid-local   # selenoid-local-api.properties
./gradlew testVisual -DupdateBaselines=true
./gradlew testE2e -DpyramidStand=one-page-form-prod   # → one-page-form-prod-e2e.properties
```

`visual` / `manual` — режимы прогона (`@Tag` + env), не всегда отдельный `@Layer` на классе.

TestOps mapping (`e2e` → E2E Tests, не UI Tests) — чанк **`test-layers`**.

## Do

- Новый сценарий: выбрать ярус → один класс на concern (`LoginTests` = smoke + `@Manual` exploratory).
- Stack-слои (`config/`, `pages/`, `TestBase`, `api/`) — чанки `e2e-layers`, `test-api-layer`.

## Don't

- Возвращать учебную ladder (negative inline, listener demo) в `tests-java/LoginTests`.
- Смешивать `@Tag("smoke")` и `@Tag("visual")` в одном `@Test`.
- Дублировать logout ladder в каноне — см. `test-logout-flow` (RAG).
