# QA Guru TMS Automator

GitHub: [qa-guru/qa-guru-tms-automator](https://github.com/qa-guru/qa-guru-tms-automator)

Сервис мониторит смену workflow-статусов тест-кейсов в Allure TestOps и автоматизирует ручные тесты.

## Workflow и статусы

Workflow **4** — «Автоматизация ручных тестов с ИИ» (`allure.autotests.cloud`).

| id | Название в UI / API |
|----|---------------------|
| **-1** | Черновик (API: `Draft`) |
| **-2** | На ревью (API: `Review`) |
| **5** | ✨ Автоматизировать |
| **13** | Автоматизировано с ИИ |

**Триггер автоматизации:** переход в **✨ Автоматизировать (5)** с любого другого статуса (в т.ч. **-2 → 5**, **-1 → 5**); **5 → 5** игнорируется — защита от повторного срабатывания, если статус не менялся.

Повторный запуск для уже автоматизированного кейса (**13 → 5** и т.п.) пока не поддерживается — один прогон на тест-кейс.

**После успешного CI:** workflow-статус **13** («Автоматизировано с ИИ») и тип «автоматизированный» выставляет **TestOps** при обработке upload с `@AllureId` — automator статус не меняет.

## Что делает automator

1. Логирует ручной кейс в комментарий TestOps
2. При первом кейсе проекта создаёт репозиторий `https://github.com/autotests-cloud/{name}-{projectId}`
3. Генерирует Java-тест в `src/test/java/tests/`, пушит в GitHub
4. Запускает GitHub Actions (Selenoid, Allure 3 на GitHub Pages, upload в TestOps через allurectl)
5. Пишет в TestOps комментарии со ссылками на Actions и отчёт
6. Прикрепляет видео прогона к тест-кейсу

### Upload в TestOps (CI)

Если в репозитории заданы `vars.ALLURE_PROJECT_ID` + `vars.ALLURE_ENDPOINT` и secret `ALLURE_TOKEN`, после прогона `./gradlew test` результаты отправляются в TestOps через `allurectl upload` (отдельный шаг: падение upload не красит job, если тесты прошли). Без credentials — только Pages + artifact.

`BROWSER_VERSION` задаётся в workflow (`env`, передаётся как `-DbrowserVersion`); в `ci.properties` версии браузера нет.

При создании репозитория automator прописывает `ALLURE_PROJECT_ID`, `ALLURE_ENDPOINT` и `ALLURE_TOKEN` из `.env`. Для уже существующих репозиториев — один раз вручную:

```bash
gh variable set ALLURE_PROJECT_ID --body 5267 -R autotests-cloud/qa_guru_automator_ethalon-5267
gh variable set ALLURE_ENDPOINT --body https://allure.autotests.cloud -R autotests-cloud/qa_guru_automator_ethalon-5267
gh secret set ALLURE_TOKEN -R autotests-cloud/qa_guru_automator_ethalon-5267
```

Шаблон репозитория: `templates/project-tests/` (инфраструктура без эталонных тестов)  
Эталон для разработки: `tests-java/` → после правок синхронизировать в `templates/project-tests/` (исключая `LoginTests.java`)  
Локальная копия проекта: `projects/{repo_name}/` (имя = GitHub-репозиторий, напр. `qa_guru_automator_ethalon-5267`)  
Образец стиля автотестов (только локально): `tests-java/src/test/java/tests/LoginTests.java`

## Запуск

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
