---
name: bootstrap-project-repo
description: >-
  Creates or clones a per-project GitHub test repo from templates/tests-java
  (trimmed by automator). Sets CI vars, local projects/ copy, and Gradle smoke.
  Use when bootstrapping autotests-cloud repo or first test for a TestOps project.
---

# Bootstrap project test repo

Base: `autotests-ai-tms-automator/`

## Naming

```
{project_name_with_dashes}-{testops_project_id}
```

Пример: `qa_guru_automator_ethalon-5267` → `https://github.com/autotests-cloud/qa_guru_automator_ethalon-5267`

## Источники

| Путь | Роль |
|------|------|
| `templates/tests-java/` | **SSOT** — полный эталон + infra для GitHub bootstrap |
| `templates/vanilla-ui/` | Static root для локального `-Denv=local` |
| `docs/rag/` | **Vendored RAG** — sync skill `sync-rag` |
| `template-project/docs/rag/` | SSOT maintainer — правки + `python scripts/sync_rag_from_template_project.py` |

GitHub bootstrap: `src/automator/github/template.py` → `prepare_bootstrap_workdir()` копирует из `tests-java` **без**:
- `src/test/java/tests/*.java` кроме `TestBase.java`
- `src/test/java/pages/`
- `src/test/java/tests/component/`
- `src/test/resources/screenshots/`
- локальных артефактов (`build/`, `history.jsonl`, `app-path-local*`)

## Что копируется в GitHub

| Источник | Содержимое |
|----------|------------|
| `templates/tests-java/` (trim) | TestBase, CI, config, helpers, unit tests |
| skill `automate-manual-test` | добавляет тесты по кейсам TestOps |

Локальная копия: `projects/{repo_name}/`

## Режимы trim (consumer workspace, не GitHub)

При bootstrap **отдельного** consumer repo из эталона — см. RAG + ADR 002:

| Режим | Тесты |
|-------|-------|
| `login-only` | LoginTests, LoginFormTests, *Baseline login |
| `login+header` | + HeaderTests, HeaderLayoutTests, header baselines |
| `login+embed` | + LoginEmbedTests |

Источник файлов: `templates/tests-java/src/test/java/`.

## Workflow for agent

### 0. RAG retrieval (обязательно)

Перед bootstrap или первым тестом — rule `rag-retrieval.mdc`:

1. Читать `docs/rag/manifest.jsonl` в **этом** репо (vendored)
2. Минимум: `e2e-config-keys`, `test-taxonomy`, `test-style-ladder`, `po-locators`, `po-step`, `base-lifecycle`, `cfg-env-profile`
3. Header-кейсы: + `e2e-header/hdr-selectors.md`, `hdr-behavior.md`

Automator при `ensure_repository()` копирует канон RAG в `docs/rag/` project repo.

### 1. Проверить существование

```bash
gh repo view autotests-cloud/{repo_name} 2>/dev/null && echo exists || echo missing
ls autotests-ai-tms-automator/projects/{repo_name}/
```

### 2. Создать repo (если нет)

Через automator (предпочтительно):

```bash
cd autotests-ai-tms-automator
python -m pip install -e .
# .env: ALLURE_API_TOKEN, gh auth
```

`ProjectRepositoryService.ensure_repository()` → `prepare_bootstrap_workdir()` из `templates/tests-java/`.

### 3. GitHub vars/secrets (TestOps upload)

```bash
gh variable set ALLURE_PROJECT_ID --body {project_id} -R autotests-cloud/{repo_name}
gh variable set ALLURE_ENDPOINT --body https://allure.qa.guru -R autotests-cloud/{repo_name}
gh secret set ALLURE_TOKEN -R autotests-cloud/{repo_name}
```

### 3.1 TestOps layer mappings (обязательно для нового project_id)

```bash
cd autotests-ai-tms-automator
python scripts/sync_testops_layer_mappings.py --project-id {project_id}
```

Канон — RAG `test-layers`. Upload policy: `test_layer ← from_test_result`.

### 4. Локальный smoke эталона

```bash
cd templates/vanilla-ui && python -m http.server 3000 &
cd templates/tests-java
gradle test -DincludeTags=smoke -DexcludeTags=visual
```

### 5. Smoke project repo

```bash
cd projects/{repo_name}
./gradlew test -Denv=ci
```

Первый тест — skill `automate-manual-test`, не заранее.

## Layout в project repo

```
src/test/java/tests/
  TestBase.java
  LoginTests.java          # только после автоматизации кейса
```

## Rules

- `.cursor/rules/rag-retrieval.mdc`
- `.cursor/rules/java-e2e-tests.mdc`
- `.cursor/rules/project-map.mdc`
- RAG: `docs/rag/config/e2e-config-keys.md`, `test-taxonomy.md`

## DoD

- [ ] `gradle test -Denv=ci` green после первого сгенерированного теста
- [ ] allurectl upload в workflow (vars + secret)
- [ ] TestOps layer mappings (`sync_testops_layer_mappings.py --project-id {id}`)
- [ ] infra правится только в `templates/tests-java/` — отдельный sync не нужен
- [ ] vendored `docs/rag/` актуален (`python scripts/sync_rag_from_template_project.py --check`)
