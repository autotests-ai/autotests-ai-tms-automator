---
name: give-manual-testcase
description: >-
  По запросу «дай ручную» придумывает и создаёт ручной тест-кейс в текущем
  Allure TestOps проекте, проверяет workflow, поднимает automator если не
  слушает, следит за инфраструктурой. В конце отдаёт ссылки на TestOps, CI run
  и код автотеста в GitHub. Use when user asks for a manual test case to
  review before automation.
disable-model-invocation: true
---

# Give Manual Test Case → ручная проверка → быстрая автоматизация

Base: `autotests-ai-tms-automator/`.  
Связанный skill: `automate-manual-test` — генерация Java после статуса **✨ Автоматизировать (5)**.

## Триггер

| Фраза | Действие |
|-------|----------|
| «дай ручную» | создать кейс + health check + ссылки |
| «дай ручной кейс» | то же |
| «создай ручной тест» | то же |

## Цель

1. Придумать **новый** кейс, который **быстро автоматизируется** (UI из `templates/vanilla-ui/`).
2. Создать в **текущем** TestOps-проекте (workflow «Ручные тесты»).
3. Проверить workflow и что **automator слушает**; если нет — поднять.
4. Отдать ссылки пользователю для ручной проверки.
5. После «✨ Автоматизировать» — дождаться automator/CI и выдать **финальные три ссылки**.

**Не автоматизировать в этом skill** — только создать ручной кейс и наблюдать за инфрой.

## Workflow

### 0. Health check (кратко, перед созданием)

| Проверка | Как |
|----------|-----|
| Project context | `python scripts/resolve_testops_project.py {project_id} --json` |
| Automator | `pgrep -fl automator.main` или `docker compose ps` |
| `.env` | `MONITOR_PROJECT_IDS`, `DRY_RUN=false`, `ALLURE_API_TOKEN` |
| GitHub repo | `gh repo view autotests-cloud/{repo_name}` |
| CI | `gh run list -R autotests-cloud/{repo_name} -L 3` — красные → предупредить |
| Selenoid / баланс | CI timeout/hub errors → предупредить, не гонять лишнее |

Критичные блокеры — остановиться и отчитаться.

### 1. Создать ручной кейс

```bash
cd autotests-ai-tms-automator

# project_id из MONITOR_PROJECT_IDS или явно
python scripts/create_manual_testcase.py {project_id} --auto --start-automator --json
```

Скрипт:
- resolve workflow + draft status из API (не из README);
- при неполных mapping'ах — auto `sync_testops_layer_mappings` для project_id;
- выбирает сценарий из `src/automator/manual_case_catalog.py` без дублей;
- создаёт кейс через `AllureTestOpsClient.create_manual_test_case` с **Test Layer = Manual Tests** (`--layer manual`, default);
- комментарий в TestOps с прогнозом класса/метода.

После автоматизации upload проставит **E2E Tests** через `@Layer("e2e")` (RAG `test-layers`).

Кастомный кейс:

```bash
python scripts/create_manual_testcase.py 5267 \
  --name "…" \
  --steps-file steps.json \
  --layer manual \
  --start-automator
```

`steps.json`:

```json
[
  {"body": "Открыть login.html?ru", "expected_result": "Форма входа видна"},
  {"body": "…", "expected_result": "…"}
]
```

**Правила сценария:**
- ≤ 5 шагов, happy-path или простой негатив;
- только login-форма one-page-form (`login-input`, `password-input`, `submit-button`, `welcome-message`, `error-message`);
- **без header** — GitHub CI (`ci.properties`) смотрит на `qa-guru.github.io/one-page-form/`, не vanilla-ui embed;
- не дублировать уже автоматизированные кейсы;
- не требовать нового UI.

### 2. Ответ сразу после создания (phase: created)

Шаблон — **обязательно три пункта** (run и код — прогноз):

```markdown
## Ссылки

- **TestOps:** [#{id}](https://allure.qa.guru/project/{project_id}/test-cases/{id})
- **Код автотеста:** появится после «✨ Автоматизировать» (ожидается `tests.LoginTests.methodNameTest`)
- **GitHub Actions run:** появится после «✨ Автоматизировать»

Проверь шаги в TestOps. Когда готов — переведи в **✨ Автоматизировать**.
Automator: {status}
```

URL TestOps: `{ALLURE_ENDPOINT}/project/{project_id}/test-cases/{test_case_id}`

### 3. После «✨ Автоматизировать» — финальные ссылки

Следить за automator / CI. Когда код запушен и прогон завершён:

```bash
python scripts/automation_links.py {project_id} {test_case_id} --watch --json
```

**Финальный ответ — обязательно три кликабельные ссылки:**

```markdown
## Ссылки

- **TestOps:** [#{id}]({testops_url})
- **Код автотеста:** [`tests.LoginTests.methodNameTest`]({github_blob_url})
- **GitHub Actions run:** [прогон]({ci_run_url}) (`{conclusion}`)

Опционально: [Allure 3 отчёт]({allure_report_url})
```

| Ссылка | Источник |
|--------|----------|
| TestOps | `automation_links.py` → `testops_url` |
| Код | `@AllureId("{id}")` в `projects/{repo}/` или `gh search code` → blob `#L{line}` |
| CI run | commit `TestOps #{id}` → `gh run list --commit {sha}` |

Если `--watch` истёк без ссылок — triage CI (`e2e-debug-run`, `fix-flaky-test`), комментарий в TestOps.

### 4. Инфраструктура

| Риск | Действие |
|------|----------|
| Automator не слушает | `docker compose up -d --build` или `python -m automator.main` (фон) |
| `DRY_RUN=true` | исправить `.env`, перезапустить |
| CI red / Selenoid down | предупредить пользователя, не создавать лишние кейсы |
| Launch не закрыт | кейс застрял в «Автоматизировать» → close launch |
| Нет GitHub repo | skill `bootstrap-project-repo` при первом кейсе |

## Session cleanup

- HTTP `:3000` — гасить по rule `session-cleanup`, если поднимали для preview.
- **Automator не гасить** после «дай ручную», пока пользователь не закончил цикл автоматизации.

## Don't

- Не ставить «✨ Автоматизировать» без запроса пользователя.
- Не придумывать UI без `data-testid`.
- Не копировать workflow/status id из другого проекта.
- Не автоматизировать в этом skill — для этого `automate-manual-test`.
- **Не завершать чат без трёх финальных ссылок**, если пользователь уже перевёл кейс в «Автоматизировать» и CI отработал.

## Cursor prompt

```
Use skill give-manual-testcase.

Дай ручную в текущем TestOps-проекте.
Подними automator если не слушает.
После создания — ссылка на TestOps.
После моего «Автоматизировать» — дождись CI и дай три ссылки:
TestOps, GitHub Actions run, код автотеста в GitHub.
```

См. `examples.md`.
