---
id: alr-data-sources
domain: analytics
phase: 7.analytics
adr: 002
tags: [allure, analytics, index]
---
# Analytics data sources

**id:** `alr-data-sources`

## Файлы

| Артефакт | Путь | Назначение |
|----------|------|------------|
| Raw results | `tests-java/build/allure-results/*-result.json` | Источник для `analytics-index.json` |
| History | `tests-java/history.jsonl` | Тренды run → `historyRuns` в index |
| Agent output | `tests-java/build/agent-output/` | Manifest после `-DallureAgentMode=inspect` |
| Index | `tests-java/build/analytics-index.json` | Контракт для dashboard charts + `qualityGate` |
| Known issues | `tests-java/known.json` | Quality gate baseline |
| Config | `tests-java/allurerc.mjs` | Plugins awesome + dashboard, categories |

Gradle: `./gradlew allureAnalyticsIndex` · Script: `tests-java/scripts/build-analytics-index.mjs` (`--config allurerc.mjs` для `charts.failureTaxonomy`)

## Входы / Assert

- После `test` или `allureReport` с `allureReportMode≠none` и непустым `build/allure-results/`
- `./gradlew allureAnalyticsIndex` → `build/analytics-index.json`, schema `analytics-index/v1`
- `qualityGate` в index — те же rules, что `./gradlew allureQualityGate` (`allurerc.mjs`, `known.json`)

## Do

- Dashboard читает index через HTTP: `../tests-java/build/analytics-index.json` или symlink `projects/design-system-home/design-system/preview/allure-report/analytics-index.json`
- Агент triage — skill `allure-agent-inspect` (agent-output), не raw JSON
- Нормализация charts — только через index builder, не ad-hoc в `allure-dashboard.js`

## Don't

- Не коммитить `build/analytics-index.json`, `build/allure-results/`, `build/agent-output/`
- Не парсить `*-result.json` в браузере — только pre-built index
- Не смешивать agent inspect и dashboard layout в одном чате
