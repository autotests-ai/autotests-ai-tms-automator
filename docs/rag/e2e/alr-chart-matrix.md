---
id: alr-chart-matrix
domain: e2e-analytics
phase: 7.analytics
adr: 002
tags: [allure, highcharts, dashboard]
---
# Chart type matrix

**id:** `alr-chart-matrix`

Соответствие метрик и Highcharts types для `frontend/allure-dashboard.html`.

| Метрика | Chart type | Index field | Tile id |
|---------|------------|-------------|---------|
| Pass/fail mix | pie (donut) | `charts.passRate` | `#chart-pass-rate` |
| Per-test duration | column | `charts.duration` | `#chart-duration` |
| Failure taxonomy | pie (donut) | `charts.failureTaxonomy` | `#chart-failure-taxonomy` |
| Per-test table | HTML table + badge + duration bar | `tests[]` | `#tests-table` |
| Status over runs | line | `historyRuns` (planned) | — |
| Stability by feature | bar | planned Tier 2 | — |

## Do

- Контейнер — примитив `.chart-tile` (`css/chart-tile.css`)
- Theme — `getChartTheme()` + `updateChartThemes()` в `allure-dashboard.js`
- CDN — `highcharts.js` только на dashboard harness

## Don't

- AmCharts / второй chart lib без ADR
- Highcharts в `components.html` runtime catalog
