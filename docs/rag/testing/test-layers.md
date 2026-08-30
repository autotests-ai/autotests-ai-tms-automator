---
id: test-layers
domain: testing
phase: 4.pyramid
adr: 002
tags: [layer, pyramid, testops, allure]
related: [test-pyramid]
---
# Test layers — код ↔ Allure TestOps

**id:** `test-layers`

Единый SSOT для `@Layer` в Java и Test Layer в Allure TestOps.

## Ключ в коде → Test Layer (TestOps)

| Key (`@Layer`) | Test Layer (admin) | Gradle slice |
|----------------|-------------------|--------------|
| `unit` | Unit Tests | `testUnit` |
| `component` | Component Tests | `testComponent` |
| `integration` | Integration Tests | `testIntegration` |
| `api` | API Tests | `testApi` |
| `ui` | **UI Tests** | `-DincludeTags=ui` (mock stand) |
| `e2e` | **E2E Tests** | `-DincludeTags=e2e` (live stand) |
| `manual` | Manual Tests | `testManual` |

**Multistack etalon (ADR 016):** browser-on-stub → `@Layer("ui")` / **UI Tests**; browser-on-live-backend → `@Layer("e2e")` / **E2E Tests**. Не складывать оба в один ключ `e2e`.

Named Gradle slices = kit `_tests-meta/_ethalon/build.gradle`. Runnable ethalon tests: `./gradlew test -DincludeTags=<layer>` (no `testUnit`/`testApi` tasks).

**Не `@Layer`:** visual — `@Layer("e2e")` на классе + `@Tag("visual")` + env `*_visual` + `testVisual` (CI slice). Ключ `visual` не добавлять в таблицу `@Layer` и не в `testingPyramid.layers`.

**Не `@Layer`:** `crystal` — IR mill greedy.guru / слот `tests-go-cdp`. Четвёртый столбец `/stack/` (`in_stack: true`). Статус — TestOps field `crystal_status`, не layer. ADR 015.

**Не `@Layer`:** `performance` — load-слоты JMeter (Java JMX / Groovy JSR223), Gatling (Java / Kotlin / Scala / JavaScript / TypeScript SDK), k6 (JavaScript / TypeScript), Locust (Python), Yandex.Tank (Python) на `/stack/` Tests board. Не пирамида и не TestOps Test Layer.

## TestOps project setup

1. **Admin** (`/admin/testlayer`): seven layers above must exist (UI / E2E / Component / Integration / Manual — custom; Unit / API often built-in).
2. **Project → Settings → Test layers:** Key → Test Layer mapping (same keys as `@Layer`).
3. **Project → Settings → Upload:** `test_layer` policy = `from_test_result`.

Sync script (automator):

```bash
cd projects/autotests-ai-home/autotests-ai-tms-automator
python scripts/sync_testops_layer_mappings.py --project-id 5311,5271,5267,5263,5274
python scripts/sync_testops_layer_mappings.py --list-mapping
```

Manual case creation (`create_manual_testcase.py`, skill `give-manual-testcase`): default `--layer manual` → **Manual Tests**; auto-runs layer sync if project mappings incomplete.

API: `POST /api/testlayerschema` (key + testLayerId), `POST /api/testcaseupdateschema` (field `test_layer`).

## Allure label

`annotations/Layer.java` → `@LabelAnnotation(name = "layer")`. Upload via `allurectl upload`; mapping resolves key → Test Layer.

## Allure report charts (Allure 3 local)

`allurerc.mjs` / `allurerc.mjs` → `name`: **название отчёта/launch** = `{github-repo-slug} Tests` (напр. `template-project Tests`, `one-page-form-tests-java Tests`, `selenoid-tests Tests`) — **не** Test Layer и **не** `@Layer`.  
`plugins.dashboard.options.reportName` → `{slug} Tests` (Allure hub tile: **Dashboard {slug} Tests**); canonical CI link → `reports/{runId}/awesome/index.html`; dashboard analytics → `.../dashboard/index.html`.  
`plugins.csv.options.fileName` → `{slug}.csv`.  
`testingPyramid` — в `plugins.awesome.options.charts` (Awesome `#charts`) и в `plugins.dashboard.options.layout` (native dashboard iframe).  
`testingPyramid.layers`: ключи `@Layer` (`unit`, `component`, `integration`, `api`, `ui`, `e2e`, `manual`).

## GitHub Actions (consumer workflow)

Runnable-файл: `autotests-ai-multistack-app` = `ci.yml`; Selenoid = имя ethalon (`selenoid_github-orchestrator.yml`). Top-level `name:` = **`{github-repo-slug} Tests`** — как `allurerc.name`; на TestOps не влияет.

| Repo (GitHub slug) | `allurerc.name` | workflow `name:` |
|--------------------|-----------------|------------------|
| `template-project` | template-project Tests | template-project Tests |
| `qa_guru_automator_ethalon-5267` | qa_guru_automator_ethalon-5267 Tests | qa_guru_automator_ethalon-5267 Tests |
| `one-page-form-tests-java` | one-page-form-tests-java Tests | one-page-form-tests-java Tests |
| `selenoid-tests` | selenoid-tests Tests | selenoid-tests Tests |
| `autotests-ai-multistack-app` | autotests-ai-multistack-app Tests | autotests-ai-multistack-app Tests |

Не путать с `allurerc.name` (отчёт) и Test Layer (`e2e` → **E2E Tests** в TestOps).

### GitHub Actions job display name (`jobs.<id>.name`)

Канон для selenoid-stack orchestrator: **`{component}-{layer}-go-test`** (job) и **`{component}[-{facet}]-{layer}-{lang}-test`** (step). Сборка без тестов — **`-build`** (напр. `selenoid-ui-frontend-build`), без `-test`.

| Job id | Display name | Пример |
|--------|--------------|--------|
| `go-unit` | `${{ matrix.repo }}-unit-go-test` | `selenoid-unit-go-test`, `selenoid-ui-unit-go-test`, `cm-unit-go-test` |
| `go-cm` | `cm-integration-go-test` | CM pyramid (integration slice) |
| `go-hub` | `selenoid-pyramid-go-test` | hub-all / hub-prod pyramid gate |

Job id (`go-unit`, `go-hub`, …) и artifact prefix (`allure-go-*`) не менять без ADR — только display `name:`.

**Steps** (внутри job): `{component}[-{facet}]-{layer}-{lang}-test` — **lang** = язык тестов (`go`, `typescript`), не runner (`vitest`). Facet (`frontend` / `backend`) — когда у одного `@Component` несколько runtime.

| Step | Смысл |
|------|--------|
| `selenoid-ui-frontend-component-typescript-test` | Vitest + RTL, `@Layer("component")`, `ui/src/**/*.test.tsx` |
| `selenoid-ui-frontend-build` | `yarn build` — gate, не слой, без `-test` |
| `selenoid-ui-backend-unit-go-test` | Go unit бэкенда selenoid-ui |

Go JSON parser unit tests — `tests/unit/fixture/` (`@Layer("unit")`), slice `unit` (вместе с `internal/*`). **`@Layer("component")`** в orchestrator CI — только RTL (`selenoid-ui-frontend-component-typescript-test`).

Внутри `go-hub` (`selenoid-pyramid-go-test`) push/prod gate — steps по слоям; JSON parsers в `selenoid-unit-go-test`; deploy-smoke `TEST_TAGS` — step `Deploy smoke pyramid slices`.

Сервисный фильтр **Component** (cm / selenoid / …) — отдельно: RAG `test-components`, `@Component`, sync `sync_testops_component_mappings.py`.

## Do

- Новый автотест: `@Layer` по таблице (без `visual`); `@Tag` для CI slice (`smoke`, `api`, `visual`, `manual`).
- Ручной кейс TestOps: Test Layer = UI Tests / E2E Tests / Manual Tests / … по сценарию.
- Автоматизация manual → `@Layer("ui")` (chrome на стабе) или `@Layer("e2e")` (живой бэкенд) — skill `automate-manual-test`.

## Don't

- `@Layer("UI Tests")` (display name) в Java — ключ **`ui`**, не строка TestOps.
- Два верхних слоя на один кейс (`ui` + `e2e` на одном методе).
- Монтировать SPA на WireMock и ставить `@Layer("e2e")`.
