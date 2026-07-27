---
id: alr-metrics-catalog
domain: analytics
phase: 7.analytics
adr: 002
tags: [allure, metrics, dashboard]
---
# Analytics metrics catalog

**id:** `alr-metrics-catalog`

Tier-метрики для фазы **7.analytics**. Источник полей — `analytics-index.json` (`summary`, `charts`, `tests`, `historyRuns`).

## Tier 1 — KPI (дашборд сейчас)

| Метрика | Поле index | Формула |
|---------|------------|---------|
| Pass rate | `summary.passRate` | `passed / (passed+failed+broken)` |
| Totals | `summary.*` | count по status |
| Avg duration | `summary.avgDurationSec` | mean `tests[].durationSec` |
| Pass/fail pie | `charts.passRate` | series для Highcharts pie |
| Failure taxonomy | `charts.failureTaxonomy` | donut по `allurerc.mjs` categories |

## Tier 2 — следующие виджеты

| Метрика | Источник | Chart | Статус |
|---------|----------|-------|--------|
| Per-test table | `tests[]` | HTML table + badge + duration bar | ✓ 7.analytics MVP |
| Per-test duration | `charts.duration` | column | ✓ 7.analytics |
| Flaky flip | `history.jsonl` status diff | line / sparkline | ✓ 8.3 HTML fallback |
| Visual failures | `tests` where label `visual` + status failed | table filter | follow-up |
| Duration trend per test | `tests[].history` | SVG sparkline (HTML table) | ✓ 8.3 |
| Live run feed | partial index during test | polling `?live=1` | ✓ 8.4 |

## Tier 3 — follow-up (после 8.analytics-grid)

Linked filters status / category / layer ✓ (slice 8.5). Backlog: epic click-filter, timeline Gantt, step failure funnel, viewport heatmap (390/768/1280).

## Do

- Новый виджет → проверить tier; данные добавить в `build-analytics-index.mjs`, не в HTML
- Native Allure dynamics — iframe dashboard plugin (`allurerc.mjs`), не дублировать без причины

## Don't

- Не хардкодить sample data в production path — fallback только если index 404
- Не выдумывать метрики вне каталога без ADR
