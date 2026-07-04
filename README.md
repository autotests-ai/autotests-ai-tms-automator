# Autotests AI TMS Automator

GitHub: [autotests-ai/autotests-ai-tms-automator](https://github.com/autotests-ai/autotests-ai-tms-automator)

Сервис мониторит смену workflow-статусов тест-кейсов в Allure TestOps и автоматизирует ручные тесты.

## Workflow и статусы

Workflow **6** — «Ручные тесты» (`allure.autotests.cloud`).

| id | Название в UI / API |
|----|---------------------|
| **-1** | Черновик (API: `Draft`) |
| **14** | На ревью |
| **5** | ✨ Автоматизировать с AI |
| **17** | AI автоматизирует — automator ставит при старте job |
| **16** | Сломано AI — automator ставит при ошибке CI/генерации |

**Успех:** workflow **5 «Автоматизированные тесты»**, статус **13 «Автоматизировано с AI»**.

**Триггер автоматизации:** переход в **✨ Автоматизировать с AI (5)** с любого другого статуса; **5 → 5** игнорируется.

**В процессе:** automator переводит кейс в **17 AI автоматизирует** после постановки job.

**Ошибка:** automator переводит кейс в **16 Сломано AI**; повтор — вручную вернуть в **5**.

**После успешного CI:** automator закрывает launch; TestOps ставит `automated=true`, затем automator переводит кейс в workflow **5** / статус **13**.

## Что делает automator

1. Логирует ручной кейс в комментарий TestOps
2. При первом кейсе проекта создаёт репозиторий `https://github.com/autotests-cloud/{name}-{projectId}`
3. Генерирует Java-тест в `src/test/java/tests/`, пушит в GitHub
4. Запускает GitHub Actions (Selenoid, Allure 3 на GitHub Pages, upload в TestOps через allurectl)
5. Пишет в TestOps комментарии со ссылками на Actions и отчёт
6. Прикрепляет видео прогона к тест-кейсу

При создании repo automator также включает **GitHub Pages** (ветка `gh-pages`) для Allure-отчётов.

## Templates и agent meta

| Путь | Роль |
|------|------|
| `templates/tests-java/` | **SSOT** e2e эталон (pyramid, visual, header, embed) + GitHub bootstrap (trim в automator) |
| `templates/vanilla-ui/` | Static UI (login/header) для local и генерации HTML |
| `docs/rag/` | Vendored RAG (SSOT maintainer: template-project) |
| `projects/{repo_name}/` | Локальная копия GitHub project repo |
| `.cursor/skills/automate-manual-test` | Канон TestOps → Java (только здесь) |

Индекс skills: [`docs/skills-map.md`](docs/skills-map.md).

### Локальный прогон эталона

```bash
cd templates/vanilla-ui && python -m http.server 3000
cd templates/tests-java && gradle test -DincludeTags=smoke -DexcludeTags=visual
```

### Upload в TestOps (CI)

Vars: `ALLURE_PROJECT_ID`, `ALLURE_ENDPOINT`; secret: `ALLURE_TOKEN`.  
Workflow: `templates/tests-java/.github/workflows/selenoid-autotests-cloud_github.yml` (`name: qa_guru_automator_ethalon-5267 Tests`).

```bash
gh variable set ALLURE_PROJECT_ID --body 5267 -R autotests-cloud/qa_guru_automator_ethalon-5267
gh variable set ALLURE_ENDPOINT --body https://allure.autotests.cloud -R autotests-cloud/qa_guru_automator_ethalon-5267
gh secret set ALLURE_TOKEN -R autotests-cloud/qa_guru_automator_ethalon-5267
```

GitHub bootstrap: `prepare_bootstrap_workdir()` копирует `templates/tests-java/` без e2e-классов, `pages/` и visual baselines.

### RAG (vendored)

Maintainer: `template-project/docs/rag/`. Runtime: `docs/rag/`. Skill: `sync-rag`.

```bash
python scripts/sync_rag_from_template_project.py          # обновить копию
python scripts/sync_rag_from_template_project.py --check  # проверить sync
python scripts/sync_testops_layer_mappings.py --project-id 5271,5267,5263  # Key→Test Layer в TestOps
python scripts/sync_testops_layer_mappings.py --list-mapping
```

## Запуск automator

```bash
cp .env.example .env   # ALLURE_API_TOKEN + gh auth login
docker compose up --build
```

Локально:

```bash
python -m pip install -e .
python -m automator.main
```

Требуется `gh` CLI с доступом к организации `autotests-cloud`.
