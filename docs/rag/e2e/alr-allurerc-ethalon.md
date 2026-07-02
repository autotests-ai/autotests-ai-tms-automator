---
id: alr-allurerc-ethalon
domain: e2e-analytics
phase: 7.analytics
adr: 002
tags: [allure, config, ethalon, quality-gate, dashboard]
---
# Allure allurerc ethalon sync

**id:** `alr-allurerc-ethalon`

## Файлы

| Файл | Роль |
|------|------|
| `tests-java/_ethalon/allurerc.json` | SSOT структуры |
| `tests-java/allurerc.json` | Runnable (Gradle, CLI) |
| `tests-java/_new.json`, `_modified.json` | Inbox consumer diff |
| `tests-java/known.json` | **не** ethalon — per-project flaky baseline |
| `tests-java/history.jsonl` | **не** ethalon — run history |

Skill: `sync-allurerc-ethalon`. См. также `alr-quality-gate`, `alr-hook-shell`.

## Profile-specific (rule 2 — не propagate)

- `name` → `{repo-slug} Tests`
- `plugins.dashboard.options.reportName`
- `plugins.csv.options.fileName`

## Structural (rule 1 — propagate)

- `qualityGate.rules`, `categories.rules`
- `plugins.awesome.options.charts`, `plugins.dashboard.options.layout`
- `historyPath`, `knownIssuesPath`, `appendHistory`, `historyLimit`

## Инвариант: testing pyramid

Обязательно в **обоих** `charts` и `layout`:

```json
{ "type": "testingPyramid", "title": "Пирамида тестирования", "layers": ["unit", "component", "integration", "api", "e2e", "manual"] }
```

`visual` — **не** layer. Удаление пирамиды — только по явному запросу. Канон `@Layer`: RAG `test-layers`.

## Assert

После sync: `tests-java/allurerc.json` валидный JSON; `./gradlew allureQualityGate` / `allureReport` без ошибки config; в `charts` и `layout` есть `testingPyramid` с полным `layers`.
