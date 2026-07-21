# Examples: give-manual-testcase

## Создание

```bash
cd autotests-ai-tms-automator
python scripts/create_manual_testcase.py 5267 --auto --start-automator
```

## Финальные ссылки после автоматизации

```bash
python scripts/automation_links.py 5267 45118 --watch
```

Пример вывода:

```markdown
## Ссылки

- **TestOps:** [45118](https://allure.qa.guru/project/5267/test-cases/45118)
- **Код автотеста:** [`tests.LoginTests.successfulAuthorizationTest`](https://github.com/autotests-cloud/qa_guru_automator_ethalon-5267/blob/main/src/test/java/tests/LoginTests.java#L25)
- **GitHub Actions run:** [прогон](https://github.com/autotests-cloud/qa_guru_automator_ethalon-5267/actions/runs/28310825835) (`success`)
- **Allure 3 отчёт:** [открыть](https://autotests-cloud.github.io/qa_guru_automator_ethalon-5267/reports/28310825835/awesome/index.html)
```

## Чат-пrompt

```
Use skill give-manual-testcase.
Дай ручную. Project 5267.
```

После ручной проверки:

```
Кейс #45351 проверен, перевёл в «Автоматизировать».
Дождись CI и дай три ссылки: TestOps, run, код в GitHub.
```
