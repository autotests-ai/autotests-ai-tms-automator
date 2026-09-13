# Autotests AI TMS Automator

GitHub: [autotests-ai/autotests-ai-tms-automator](https://github.com/autotests-ai/autotests-ai-tms-automator)

Сервис мониторит смену workflow-статусов тест-кейсов в Allure TestOps и автоматизирует ручные тесты.

## Два контура (не смешивать)

| Контур | Owner | GitHub |
|--------|-------|--------|
| Curriculum matrix cells | `generate-matrix-cell` → verify → publish | [`autotests-ai/<profile-id>`](https://github.com/autotests-ai) (витрина ≤100, GitHub template) |
| Runtime: TestOps manual → AI test | **tms-automator** poller | `autotests-cloud/{name}-{projectId}` |

Runtime-репо создаётся так: `gh repo create --template autotests-ai/java-junit5-rest_assured-selenide` (ячейка каталога). Не trim `templates/tests-java` и не `git push --force`. Catalog cell не несёт `selenoid-qa-guru_github.yml` — automator после clone overlay'ит этот workflow обычным commit+push.

Curriculum ≠ runtime: org `autotests-ai` не принимает project repos; poller не публикует ячейки матрицы.

## Workflow и статусы

Workflow **6** — «Ручные тесты» (`allure.qa.guru`).

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

## greedy.guru crystals

Отдельный workflow **«greedy.guru crystals»** (Active / Outdated). Не workflow **5** «Автоматизированные тесты». Аппрув кристалла — поле `crystal_status` + JSON в git, не статус «На ревью».

```bash
PYTHONPATH=src python scripts/patch_crystal_status.py --ensure-workflow --testcase 50707
# mill ids → testdata/testops-cases.json in greedy-guru (project 5366)
```

## Что делает automator

1. Логирует ручной кейс в комментарий TestOps
2. При первом кейсе проекта создаёт репозиторий `https://github.com/autotests-cloud/{name}-{projectId}` через `gh repo create --template` каталог-ячейки
3. Генерирует Java-тест в `src/test/java/tests/`, пушит в GitHub
4. Запускает GitHub Actions (Selenoid, Allure 3 на GitHub Pages, upload в TestOps через allurectl)
5. Пишет в TestOps комментарии со ссылками на Actions и отчёт
6. Прикрепляет видео прогона к тест-кейсу

При создании repo automator также включает **GitHub Pages** (ветка `gh-pages`) для Allure-отчётов.

## Templates и agent meta

| Путь | Роль |
|------|------|
| GitHub template | Catalog cell [`autotests-ai/java-junit5-rest_assured-selenide`](https://github.com/autotests-ai/java-junit5-rest_assured-selenide) — runtime `gh repo create --template` |
| `templates/tests-java/` | Локальный e2e эталон (pyramid, visual, header, embed). **Не** GitHub bootstrap |
| `templates/vanilla-ui/` | Static UI (login/header) для local и генерации HTML |
| `docs/rag/` | Vendored RAG (SSOT maintainer: zero-design-system) |
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
Workflow: `templates/tests-java/.github/workflows/selenoid-qa-guru_github.yml` (`name: qa_guru_automator_ethalon-5267 Tests`).

```bash
gh variable set ALLURE_PROJECT_ID --body 5267 -R autotests-cloud/qa_guru_automator_ethalon-5267
gh variable set ALLURE_ENDPOINT --body https://allure.qa.guru -R autotests-cloud/qa_guru_automator_ethalon-5267
gh secret set ALLURE_TOKEN -R autotests-cloud/qa_guru_automator_ethalon-5267
```

GitHub bootstrap: `GitHubClient.create_repo_from_template()` → `gh repo create --template $GITHUB_TEMPLATE` (по умолчанию `autotests-ai/java-junit5-rest_assured-selenide`), wait contents, clone, overlay `selenoid-qa-guru_github.yml` если нет. Не `prepare_bootstrap_workdir()` и не force-push.

### RAG (vendored)

Maintainer: `zero-design-system/docs/rag/`. Runtime: `docs/rag/`. Skill: `sync-rag`.

```bash
python scripts/sync_rag_from_template_project.py          # обновить копию
python scripts/sync_rag_from_template_project.py --check  # проверить sync
python scripts/sync_testops_layer_mappings.py --project-id 5311,5271,5267,5263  # Key→Test Layer в TestOps (5311 = Multistack etalon)
python scripts/sync_testops_layer_mappings.py --list-mapping
python scripts/patch_crystal_status.py --dry-run --from-json greedy-observe.json
```

## greedy.guru `crystal_status` (тонкий PATCH)

Поле TestOps `crystal_status` **не** `from_test_result` (нет cfschema/label mapping). 3 зелёных Playwright → `pending_review`; Approve — `greedy approve` (diff IR + файл JSON) и этот скрипт PATCH. Allowlist auto-Live только `login`. Не `@Layer("manual")`. Не bootstrap GitHub/Java.

```bash
python scripts/patch_crystal_status.py --ensure-values --project-id 5274 --dry-run
python scripts/patch_crystal_status.py --testcase 12345 --status pending_review --dry-run
go run ./cmd/greedy observe --id login-user1 --eligible --pw-green 3 | \
  python scripts/patch_crystal_status.py --from-json - --dry-run
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
