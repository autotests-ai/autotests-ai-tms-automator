---
id: ci-workflow-ethalon
domain: config
phase: 4a
adr: 002
tags: [config, ci, github-actions, workflow, ethalon]
---
# CI workflow ethalon

SSOT GitHub Actions в `tests-java/.github/_ethalon/`.  
Inbox: `_new.yml`, `_modified.yml`. Skill: `sync-github-workflows-ethalon`.

Папка `_ethalon/` — workflow **не исполняется** GHA. Bootstrap копирует в consumer `.github/workflows/` **под тем же именем**, что в ethalon (`{env_base}.yml` / `{env_base}-orchestrator.yml`).

## Именование (= env_base из config)

| Ethalon | Роль | Default `-Denv=` |
|---------|------|------------------|
| `{env_base}.yml` | App browser e2e (один Java job) | `{env_base}_e2e` |
| `{env_base}-orchestrator.yml` | Multi-source: Go matrix + Java + merge Allure + `repository_dispatch` | `{env_base}_e2e` |
| `{env_base}-pyramid.yml` | Monolith full pyramid on GHA (ci + prod jobs, несколько `-Denv=`) | `reference_ci_*`, `reference_prod_*` |
| `{service}_github-build.yml` | Artifact build (JAR/image/static); **не** test pyramid | — |

Visual slice — через input `env_profile={env_base}_visual`, не отдельный ethalon-файл.

### Эталоны в template-project

| Ethalon | Stand | Consumer reference |
|---------|-------|-------------------|
| `reference_github-pyramid.yml` | reference ci + prod pyramid | `projects/reference-home/reference-app/` |
| `reference_github-build-backend.yml` | backend bootJar + Docker image | `projects/reference-home/reference-app/` |
| `selenoid-qa-guru_github.yml` | app e2e на Pages + cloud hub | tms-automator |
| `selenoid_github-orchestrator.yml` | hub stack (Go + Java) | selenoid-home/selenoid-tests |

Имя runnable-файла = имя ethalon. Не использовать короткие repo-specific имена (`workflow.yml` и т.п.).

## Build vs test (разные archetype)

| Контур | Файл | `name:` | Deploy |
|--------|------|---------|--------|
| **Build** | `{service}_github-build.yml` | `{repo-or-service} build {part}` | **нет** — только artifact / optional registry push |
| **Test pyramid** | `{env_base}-pyramid.yml`, `{env_base}.yml` | `{github-repo-slug} Tests` | Allure Pages / TestOps |
| **Deploy** | `deploy.yml` или `{service}_github-deploy.yml` | `Deploy production` | prod host / Pages |
| **Stack orchestrator** | `{env_base}-orchestrator.yml` | `{tests-repo-slug} Tests` | merge + dispatch smoke |

**Build** — compile/package (Gradle `bootJar`, `docker compose build`, static sync). **Test** — `@Layer` slices. Не смешивать: pyramid может вызвать `compose up --build` как setup, но release-image SSOT — build-workflow.

### `reference_github-build-backend.yml`

SSOT: `projects/reference-home/reference-app/.github/workflows/reference_github-build-backend.yml`

| Step | Назначение |
|------|------------|
| `sync-app-static.sh` | materialize UI → `backend/.../static/` (continue-on-error в standalone clone) |
| `./gradlew test bootJar` | unit gate + JAR |
| `docker compose build backend` | image |
| upload-artifact | `backend/build/libs/*.jar` |
| optional push | `vars.DOCKER_IMAGE` + `secrets.DOCKER_REGISTRY_TOKEN` (skip on PR) |

Сibling (future): `reference_github-build-static.yml` — wire-ui + static artifact / GitHub Pages, когда frontend станет отдельным deployable.

Microservice split: `backend-api_github-build.yml` в repo сервиса; pyramid/orchestrator остаётся в tests/app repo.

## README dashboard

SSOT: `generators/ethalon/readme/README-CANON.md` · blocks `generators/ethalon/readme/blocks/`.  
CI readme assets: `generate-readme-badge.sh` + `capture-dashboard-preview.mjs` в report job orchestrator/pyramid.

## Два слоя CI

| Слой | Файл | Что задаёт |
|------|------|------------|
| **Properties** | `config/{stand-base}_{deployment}_{layer}.properties` | baseUrl, remoteUrl, attach*, allureReportMode |
| **Workflow** | `_ethalon/{stand-base}_{deployment}.yml` или `{stand-base}-orchestrator.yml` | triggers, TestOps, Pages, `GRADLE_ARGS` overrides |

Merge: `-Dkey=value` в workflow **перекрывает** properties.

**Gradle:** везде `./gradlew` из `tests-java/` (wrapper 9.6.0). CI: `setup-gradle` + `gradle-version: wrapper`.

## App — `selenoid-qa-guru_github.yml`

### GRADLE_ARGS (минимум)

```bash
GRADLE_ARGS=(
  -Denv="${ENV_PROFILE}"                    # default: selenoid-qa-guru_github_e2e
  -DbrowserVersion="${BROWSER_VERSION}"
  -Djunit.jupiter.execution.parallel.enabled=false
  -DincludeTags=smoke -DexcludeTags=visual  # или visual slice
)
```

Параллелизм — **`junit.jupiter.execution.parallel.enabled=false`** (Selenide thread-local). `reference_github-pyramid` prod-pyramid: то же на `testE2e`; `*_prod_e2e` — `closeBrowserAfterEach=true`.

Не дублировать ключи из `selenoid-qa-guru_github_e2e.properties`.

### workflow_dispatch inputs

| Input | Default | Назначение |
|-------|---------|------------|
| `env_profile` | `selenoid-qa-guru_github_e2e` | `-Denv=` |
| `include_tags` | *(empty → slice default)* | override tags |
| `exclude_tags` | *(empty)* | override tags |
| `test_class` | *(empty)* | `--tests` single method |
| `test_case_id` | *(empty)* | TestOps launch name |

## Orchestrator — `selenoid_github-orchestrator.yml`

Jobs: `go-unit` (matrix) → `java-e2e` (+ CI Selenoid stack) → `java-cm` (optional, skip prod cloud) → `report` (merge artifacts, Allure 3 quality gate, TestOps, Pages, deploy-smoke callback).

Ethalon companions (service repos): `smoke-complete.yml` (receive callback artifact), `smoke-trigger-callback.yml` (`workflow_call` — dispatch + wait).

### Java GRADLE_ARGS (минимум)

```bash
GRADLE_ARGS=(
  -Denv="${ENV_PROFILE}"       # default: selenoid_github_e2e
  -DskipHealthCheck=true
  -DincludeTags=smoke,api
  -DexcludeTags=resilience,local-only,playwright
)
```

Не дублировать: `allureReportMode`, `logToConsole`, `remoteUrl`, `hubUrl` — уже в env profile / `default.properties`.

Go scripts (`scripts/run-go-unit.sh`) — **consumer bootstrap** (selenoid-home), не копировать в template-project без ADR.

### Cross-repo trigger (`repository_dispatch`)

Service repo после deploy → `repository_dispatch` type `deploy-smoke` → tests repo (orchestrator).

| Payload field | Назначение |
|---------------|------------|
| `source_repo` | имя/URL triggering repo → `executor.json`, TestOps launch name |
| `source_version` | deployed version/tag |
| `test_tags` | optional override JUnit tags (`api`, `smoke`, …) |
| `env_profile` | optional `-Denv=` (prod hub: `selenoid_qa_guru_api`, `selenoid_qa_guru_e2e`) |
| `skip_go_unit` | `true` — пропустить Go unit matrix (post-deploy prod smoke) |
| `source_ref` | Git ref for Go/service checkout in selenoid-tests |
| `trigger_run_id` | GitHub run id triggering repo — для smoke-complete callback |
| `source_variant` | `playwright` \| `webdriver` — slice override в orchestrator |

### Deploy-smoke callback chain

1. Service repo `release.yml` / `publish.yml` → `workflow_call` **`smoke-trigger-callback.yml`** (dispatch + wait artifact).
2. `selenoid-tests` orchestrator → `repository_dispatch` **`smoke-complete`** → `${SOURCE_REPO}` с `stats`, `quality_gate`, report URLs.
3. Service repo **`smoke-complete.yml`** → artifact `smoke-result-{trigger_run_id}`.

Secrets: `SELENOID_TESTS_DISPATCH_TOKEN` (dispatch to selenoid-tests), `SELENOID_SMOKE_CALLBACK_TOKEN` (callback PAT on triggering repo; fallback `SELENOID_QA_GURU_DISPATCH_TOKEN` in orchestrator).

## Secrets / vars (consumer)

| Name | Kind | Назначение |
|------|------|------------|
| `ALLURE_TOKEN` | secret | TestOps upload |
| `ALLURE_PROJECT_ID` | var | opt-in allurectl |
| `ALLURE_ENDPOINT` | var | default `https://allure.qa.guru` |

## Shared report steps (app + orchestrator)

1. Load/restore Allure history (`gh-pages` / `history.jsonl`)
2. allurectl (if `ALLURE_PROJECT_ID`)
3. **`./gradlew allureQualityGate`** — rules в `allurerc.mjs`; RAG `alr-quality-gate`
   - **app / prod pyramid:** inline в конце shell шага с `test` (не отдельный GHA step)
   - **orchestrator `report`:** один run-step `gate + allureReport` после merge artifacts
4. `executor.json` (+ app ethalon: перед `allureReport` в том же job, если не orchestrator combined step)
5. `./gradlew allureReport` (orchestrator: в том же step, что gate)
6. peaceiris/actions-gh-pages (`keep_files: true` — retain `reports/<run-id>/` on gh-pages; URLs stable for posts/CI)
7. allurectl upload (+ close launch для app ethalon)
8. Job summary — fail при `TEST_EXIT≠0` или `QUALITY_GATE_EXIT≠0` (app); orchestrator `report` job — отдельный fail step для gate

Orchestrator delta: download-artifact merge (`allure-go-*` + `allure-java`).

## Consumer sources (read-only)

| Pipeline | Ethalon | Monorepo consumer |
|----------|---------|-------------------|
| App e2e | `selenoid-qa-guru_github.yml` | `projects/autotests-ai-home/autotests-ai-app/tests-java/.github/_ethalon/selenoid-qa-guru_github.yml` |
| Hub orchestrator | `selenoid_github-orchestrator.yml` | `projects/selenoid-home/selenoid-tests/.github/workflows/selenoid_github-orchestrator.yml` |
| greedy-token pytest | `test.yml` + `gha-actions.yaml` | nested repo `projects/greedy-token-home/greedy-token/.github/_ethalon/` → sync `scripts/sync-github-workflows.sh` |

Action pins (checkout@v7, setup-node@v6, …) — SSOT `gha-actions.yaml` в greedy-token; тот же уровень версий, что `tests-java` ethalon.

Migrate consumer: `-Denv=ci` → `{stand-base}_{deployment}_{layer}`; см. skill `sync-github-workflows-ethalon` § C.

## Don't

- `-Denv=ci`, `ci.properties`
- Hardcoded `ALLURE_PROJECT_ID` в ethalon
- Имена workflow-файлов, отличные от ethalon (`{env_base}.yml`)
- Копировать `.github/scripts/*` из consumer в template-project без ADR
- Дублировать attach/remote keys в GRADLE_ARGS, если они в env profile
