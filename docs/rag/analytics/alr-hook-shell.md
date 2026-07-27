---
id: alr-hook-shell
domain: analytics
phase: 7.analytics
tags: [allure, dashboard, shell, iframe, highcharts]
---
# Allure shell hook (dashboard preview)

**id:** `alr-hook-shell`

## Файлы

| Файл | Роль |
|------|------|
| `projects/design-system-home/design-system/preview/allure-shell.js` | iframe load, theme sync, resize, `AllureShell.*` API |
| `projects/design-system-home/design-system/preview/allure-shell.css` | `.panel-card-dashboard`, `.dashboard-frame`, `.metrics-panel` |
| `projects/design-system-home/design-system/preview/allure-dashboard.html` | Preview: header embed + metrics + iframe |
| `projects/design-system-home/design-system/js/allure-dashboard.js` | URL probe, theme bridge, Highcharts init |
| `projects/design-system-home/design-system/preview/dashboard-overrides.css` | CSS overrides внутри iframe srcdoc |
| `projects/design-system-home/design-system/css/chart-tile.css` | Примитив контейнера chart |

Skill: `.cursor/skills/allure-dashboard-layout/`

## DOM-контракт

```html
<iframe
  id="dashboard-frame"
  class="dashboard-frame"
  data-dashboard-url="<absolute-or-relative-dashboard-index>"
  title="Allure dashboard"
></iframe>
```

- `allure-shell.js` на `DOMContentLoaded` → `loadDashboardFrame` (fetch HTML → `srcdoc` + `<base>` + overrides link).
- `data-dashboard-ready="true"` после load — e2e может ждать attribute (consumer pattern).

## Theme sync

| Источник | Механизм |
|----------|----------|
| Canonical header | `document.documentElement.classList` `theme-light` → light/dark |
| Allure iframe | `localStorage.theme` JSON + `data-theme` на iframe document |
| Shell chrome | `data-theme` на host + `dashboard-theme-change` event |
| Highcharts | `chart.update({ chart: { backgroundColor } })` в `allure-dashboard.js` |

Bridge: click `[data-testid="header-theme-toggle"]` → `AllureShell.applyDashboardTheme(frame, theme)`.

## Локальный report

```bash
cd tests-java && ./gradlew allureReport
ln -sfn ../tests-java/build/reports/allure-report/allureReport ../frontend/allure-report
# HTTP cwd = `projects/design-system-home/design-system/preview/`, :3000
```

Dashboard path в report: `dashboard/index.html` (RU) — язык Allure из `allurerc.mjs` `reportLanguage`.

## Custom vs native

| Зона | Технология | Когда |
|------|------------|-------|
| iframe | Allure 3 dashboard plugin | history, pyramid, dynamics из `allurerc.mjs` `plugins.dashboard.layout` |
| Awesome report | Allure 3 awesome plugin | charts из `allurerc.mjs` `plugins.awesome.options.charts` (в т.ч. `testingPyramid` → `#charts`) |
| `.metrics-panel` | Highcharts + `.chart-tile` | KPI из `analytics-index.json`; linked filters — backlog Tier 3 |

Decision matrix — RAG `alr-metrics-catalog`, `alr-chart-matrix`.
