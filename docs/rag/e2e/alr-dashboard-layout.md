---
id: alr-dashboard-layout
domain: e2e-analytics
phase: 7.analytics
adr: 002
tags: [allure, dashboard, layout, shell]
---
# Dashboard layout canon

**id:** `alr-dashboard-layout`

## Сетка (фаза 7)

```
Row 0: canonical header (#app-header)
Row 1: .metrics-charts — 3× chart-tile (pass rate, duration, failure taxonomy)
Row 1b: .tests-panel — HTML table из `tests[]` (status badge, duration bar)
Row 2: .metrics-stack — tech badges
Row 3: iframe#dashboard-frame — Allure 3 native dashboard
```

Skill: `allure-dashboard-layout` · Shell API: `AllureShell.loadDashboardFrame`

## URL probe order

1. `frontend/allure-report/dashboard/index.html` (symlink после `allureReport`)
2. `../tests-java/build/reports/.../dashboard/index.html`
3. Analytics: `../tests-java/build/analytics-index.json`

## Linked filters ✓ (8.5)

Click pass-rate / failure-taxonomy / testing-pyramid / epic-breakdown → filter `#tests-table`.

## Do

- Один чат = layout **или** agent inspect, не оба
- После нового tile → `alr-chart-matrix` + `component-sizes` для `chart-tile`

## Don't

- Demo-header consumer one-page-form — только canonical header embed
- Парсить raw allure-results в JS
