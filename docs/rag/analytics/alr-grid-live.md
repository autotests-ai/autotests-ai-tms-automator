---
id: alr-grid-live
domain: analytics
phase: 8.analytics-grid
adr: 002
tags: [allure, dashboard, grid, sparklines, live]
---
# Analytics grid & live feed

**id:** `alr-grid-live` · **Plan:** `docs/plans/8-analytics-grid.md`

Фаза **8.analytics-grid** — допил таблицы тестов после MVP в 7.analytics (`#tests-table`, `tests-table.css`).

**Канон:** DIY grid — HTML `#tests-table` + `tests-table.css` + SVG renderers в `allure-dashboard.js`. Highcharts Grid Pro не цель.

## MVP (7.analytics) ✓

| Колонка | Источник |
|---------|----------|
| Test | `tests[].label` / `name` |
| Status | `tests[].status` → badge |
| Duration | `tests[].durationSec` → bar |
| Category | `tests[].failureCategory` |

## Grid columns (8.analytics-grid)

| Колонка | Источник | Renderer |
|---------|----------|----------|
| Duration trend | `tests[].history[]` | SVG sparkline (`renderDurationSparkline`) |
| Stability | `flakyFlips` + history | status dots + flaky badge |
| Duration | `tests[].durationSec` | bar (MVP) |
| Live status | partial index | polling `analytics-index.json` ✓ |

## Index extensions (8.1) ✓

В `build-analytics-index.mjs` — поля на каждом `tests[]`:

```json
"tests": [{
  "uuid": "...",
  "historyId": "...",
  "layer": "e2e",
  "epic": "One Page Form",
  "history": [{ "runId": "...", "status": "passed", "durationSec": 1.2, "timestamp": 1782988865690 }],
  "flakyFlips": 0
}]
```

`layer` / `epic` — из Allure labels (`labelValue`). Epic нужен для будущего linked filter; в preview пока нет epic-chart.

Ключ сопоставления прогонов: `fullName` + `name` (historyId в jsonl может отличаться от текущих results).

## DIY grid (8.2) ✓

- Sort: `#tests-table` headers `data-sort` → `testsTableState` (name, status, stability, duration, category)
- Pagination: toolbar `#tests-table-toolbar`, page sizes 10/25/50

## Sparklines (8.3) ✓

- `renderDurationSparkline` — area+line SVG, accent из `getChartTheme`
- `renderStabilityCell` — status dots + flaky badge
- Theme toggle → `syncShellTheme()` → `initTestsTable()` перерисовывает sparklines

## Linked filters Tier 3 (8.5) ✓

| Источник клика | Filter key | Chip |
|----------------|------------|------|
| Pass rate pie `#chart-pass-rate` | `status` | Статус: … |
| Failure taxonomy pie `#chart-failure-taxonomy` | `category` | Категория: … |
| Testing pyramid bar `#chart-testing-pyramid` | `layer` | Слой: … |
| Epic breakdown bar `#chart-epic-breakdown` | `epic` | Epic: … |

- Chips: `#tests-filters` / `#tests-filters-chips`; сброс — `#tests-filters-clear`
- Chart highlight: `updateChartFilterHighlights()` (opacity/sliced)
- `charts.epicBreakdown` в index — агрегат по Allure label `epic`; tile скрыт, если нет тестов с `@Epic`

## Live feed (8.4) ✓

| Поле index | Значение |
|------------|----------|
| `runState` | `in_progress` (partial rebuild) / `complete` (final) |

### Gradle

```bash
cd tests-java
./gradlew test -DanalyticsLive=true -Denv=local_unit --tests 'helpers.LayoutCssTest'
```

- `-DanalyticsLive=true` — фоновый `watch-analytics-index.mjs` (каждую 1s, `--partial`)
- `./gradlew test` всегда финализирует `allureAnalyticsIndex` (полный index, `runState: complete`)

Отдельный watcher (два терминала):

```bash
node scripts/watch-analytics-index.mjs \
  --results build/allure-results \
  --history history.jsonl \
  --config allurerc.mjs \
  --output build/analytics-index.json
```

### Preview

```bash
tests-java/scripts/run-live-dashboard-preview.sh
# → открывает http://localhost:3000/allure-dashboard.html?live=1
# → simulate-live-analytics-index.mjs (mock, 8 шагов)
```

Ручная сборка:

```bash
cd frontend
ln -sfn ../tests-java/build/analytics-index.json analytics-index.json
node ../tests-java/scripts/simulate-live-analytics-index.mjs \
  --output ../tests-java/build/analytics-index.json --steps 8 --interval 3000
# http://localhost:3000/allure-dashboard.html?live=1
```

Mock-источник: `projects/design-system-home/design-system/preview/analytics-index.mock.json` (14 тестов, sparklines, flaky, taxonomy).

- Polling: `?poll=MS` (100–5000, default 500) при `?live=1` или `runState: in_progress`
- Badge `#tests-live-badge` — «Ожидание прогона…» при `?live=1` + stale `complete`, «Live» при `in_progress`
- Остановка polling при `runState: complete` после наблюдённого `in_progress` в этой сессии
- Быстрый mock: `run-live-dashboard-preview.sh --poll 200` (генератор + preview синхронно)

## Do

- Один чат = один slice из плана 8 (`8.1` … `8.5`)
- DIY grid только на `allure-dashboard.html` (`#tests-table`, `tests-table.css`)
- Sparklines — inline SVG в `allure-dashboard.js`

## Don't

- Парсить `*-result.json` в браузере
- Тащить Grid Pro / Highcharts Grid CDN
- Тащить grid в `components.html`
- Смешивать с `allure-agent-inspect` в одном чате
