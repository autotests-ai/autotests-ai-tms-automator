---
name: automate-manual-test
description: >-
  Generates Java Selenide + JUnit 5 + Allure e2e tests from manual Allure
  TestOps test cases. Creates or updates a per-project GitHub repo under
  autotests-cloud, runs Selenoid CI, posts progress to TestOps comments,
  attaches video. Use when automating manual tests or on status
  «Автоматизировать».
---

# Automate Manual Test → GitHub repo + CI

Base: `autotests-ai-tms-automator/` (канон skill — **только здесь**).

## Architecture

```
TestOps trigger (status → 5)
  → automator infers @Feature and class name (e.g. LoginTests)
  → method name from scenario (e.g. successfulAuthorizationTest)
  → first time: create github.com/autotests-cloud/{project-name}-{projectId}
  → push or append method in src/test/java/tests/{FeatureClass}.java
  → GitHub Actions (Selenoid + Allure 3 on Pages + allurectl → TestOps)
  → comments + video attachment in TestOps
```

**Repo naming:** `{project_name_with_spaces_as_dashes}-{testops_project_id}`  
Example: `qa_guru_automator_ethalon-5267` (project `5267`)

**Эталон (разработка):** `templates/tests-java/` — pyramid, PO, visual baselines, RAG patterns.  
**Генератор Python:** `src/automator/generator/` — step + `[data-testid=…]` для TestOps-кейсов.  
**GitHub bootstrap:** trim из `templates/tests-java/` (`prepare_bootstrap_workdir`) — infra без e2e test classes.  
**Local project copy:** `projects/{repo_name}/`

См. skill `bootstrap-project-repo` для первого repo.

## Naming rules

| Уровень | Источник | Пример |
|---------|----------|--------|
| `@Feature` | смысл всего кейса (страница, область) | `Авторизация` |
| **Класс** | `@Feature` → English + `Tests` | `LoginTests` |
| **Метод** | сценарий кейса | `successfulAuthorizationTest` |
| `@DisplayName` класса | название фичи | `Авторизация` |
| `@DisplayName` метода | название кейса из TestOps | `Успешная авторизация…` |

**Один класс — много `@Test`:** второй кейс на логин добавляется в существующий `LoginTests.java`.

**Без дублей:** `SignInTests` / `AuthorizationTests` → тот же класс `LoginTests`.

**Создаём только запрошенный кейс** — пустой `LoginTests` заранее не кладём.

## Workflow for agent

0. **Resolve project context (обязательно при новом `project_id`):** не брать status/workflow id из README, `.env` или другого проекта.
   ```bash
   cd autotests-ai-tms-automator
   python scripts/resolve_testops_project.py {project_id} --test-case-id {test_case_id}
   ```
   Используй вывод: `workflow.id`, `status_ids.automate_trigger`, `status_ids.automated_done`, `github.repo_name`.
   Если `env_drift.workflow_id=true` — для **этого** проекта опирайся на API, не на `.env`.
1. **RAG (обязательно):** rule `rag-retrieval.mdc` — `docs/rag/` (`test-taxonomy`, `po-locators`, `po-step`, `test-style-ladder`; header — `e2e-header/*`).
2. Read manual case from TestOps (name, steps, expected).
3. Infer `@Feature` and class (`LoginTests`, `RegistrationTests`, …).
4. Name method from scenario (`successfulAuthorizationTest`).
5. **Стиль:** для fail-fast, tags, `@Layer` — из `templates/tests-java/`; mapping TestOps — RAG `test-layers` (`e2e` → **E2E Tests**, не UI Tests). Шаги сгенерированного теста — `step()` + `[data-testid=…]` (как `src/automator/generator/test_java.py`). Ручная доработка — PO из `LoginPage` / `LoggedInPage`.
6. If equivalent class exists in repo — append `@Test`; else create class with one method.
7. Do **not** add `LoginTests.java` unless automating a login case.
8. Rule: `.cursor/rules/java-e2e-tests.mdc`, `.cursor/rules/rag-retrieval.mdc`
9. RAG: `docs/rag/e2e/` — config keys, locators, taxonomy

## Test structure (generated)

```java
@Layer("e2e")
@Epic("…")
@Feature("Авторизация")
@DisplayName("Авторизация")
public class LoginTests extends TestBase {
    private static final String LOGIN_PAGE = "login.html?ru";

    @Test
    @AllureId("{id}")
    @Tag("positive")
    @DisplayName("{name from TestOps}")
    void successfulAuthorizationTest() {
        step("…", () -> …);
    }
}
```

## CI / TestOps

Workflow: `templates/tests-java/.github/workflows/selenoid-autotests-cloud_github.yml` (`name: qa_guru_automator_ethalon-5267 Tests`).

```bash
./gradlew test --tests tests.LoginTests.successfulAuthorizationTest -Denv=ci
```

Vars: `ALLURE_PROJECT_ID`, `ALLURE_ENDPOINT`; secret: `ALLURE_TOKEN`.  
Upload: `allurectl upload build/allure-results` + **close launch** (`POST /api/rs/launch/{id}/close`).  
После close TestOps ставит `automated=true` и статус **Active (-3)** в workflow 6.

## Cursor SDK prompt

```
Use skill automate-manual-test.

Manual test case:
- project_id: {project_id}
- id: {test_case_id}
- name: {name}
- steps: …

Add tests.LoginTests.{methodName} for GitHub repo {repo_name}.
Infer @Feature from the case; append to existing LoginTests if present.
```

См. `examples.md`.
