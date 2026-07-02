# RAG chunks — e2e паттерны

Retrieval-единицы для агента и bootstrap. **ADR** (`docs/adr/`) — почему и scope; **чанки** — как делать (один `id` = один файл).

## Формат файла

```yaml
---
id: <stable-id>
domain: e2e | e2e-header
phase: 4a | 4b | 4.visual
adr: 002 | 003
tags: [config, selenide, ...]
---

# Заголовок

Краткий purpose (1–2 предложения).

## Файлы
## Входы / Assert
## Do
## Don't
```

Правила:
- Один чанк ≈ один паттерн или одна таблица-справочник; без дублирования ADR-контекста.
- `id` совпадает с таблицей в ADR 002 / 003.
- Индекс для ingestion: `manifest.jsonl` (поля `id`, `path`, `domain`, `phase`, `tags`).

## Индекс

### E2e общие (фаза 4a) — `e2e/`

| id | Файл |
|----|------|
| `e2e-layers` | [e2e/e2e-layers.md](e2e/e2e-layers.md) |
| `e2e-config-keys` | [e2e/e2e-config-keys.md](e2e/e2e-config-keys.md) |
| `cfg-env-profile` | [e2e/cfg-env-profile.md](e2e/cfg-env-profile.md) |
| `cfg-base-url` | [e2e/cfg-base-url.md](e2e/cfg-base-url.md) |
| `base-lifecycle` | [e2e/base-lifecycle.md](e2e/base-lifecycle.md) |
| `po-locators` | [e2e/po-locators.md](e2e/po-locators.md) |
| `po-fluent` | [e2e/po-fluent.md](e2e/po-fluent.md) |
| `po-step` | [e2e/po-step.md](e2e/po-step.md) |
| `test-style-ladder` | [e2e/test-style-ladder.md](e2e/test-style-ladder.md) |
| `test-taxonomy` | [e2e/test-taxonomy.md](e2e/test-taxonomy.md) |
| `test-negative` | [e2e/test-negative.md](e2e/test-negative.md) |
| `test-storage-shortcut` | [e2e/test-storage-shortcut.md](e2e/test-storage-shortcut.md) |
| `allure-attach` | [e2e/allure-attach.md](e2e/allure-attach.md) |
| `allure-selenide-listener` | [e2e/allure-selenide-listener.md](e2e/allure-selenide-listener.md) |
| `remote-selenoid` | [e2e/remote-selenoid.md](e2e/remote-selenoid.md) |
| `visual-baseline` | [e2e/visual-baseline.md](e2e/visual-baseline.md) |
| `test-pyramid` | [e2e/test-pyramid.md](e2e/test-pyramid.md) |
| `test-layers` | [e2e/test-layers.md](e2e/test-layers.md) |
| `test-api-layer` | [e2e/test-api-layer.md](e2e/test-api-layer.md) |
| `test-manual` | [e2e/test-manual.md](e2e/test-manual.md) |
| `test-logout-flow` | [e2e/test-logout-flow.md](e2e/test-logout-flow.md) |
| `gen-python-policy` | [e2e/gen-python-policy.md](e2e/gen-python-policy.md) + `gen-python-policy.json` |
| `ci-workflow-ethalon` | [e2e/ci-workflow-ethalon.md](e2e/ci-workflow-ethalon.md) |
| `ci-gradle-args` | [e2e/ci-gradle-args.md](e2e/ci-gradle-args.md) |
| `alr-quality-gate` | [e2e/alr-quality-gate.md](e2e/alr-quality-gate.md) — `allureQualityGate`, `known.json`, CI enforcement |

Канон CI: `tests-java/`. Workflow SSOT: `tests-java/.github/_ethalon/`; skill `sync-github-workflows-ethalon`. Учебная ladder: ethalon `tests-java/src/test/java/_ethalon/ladder/` + RAG `test-style-ladder`, `test-pyramid`.

### Header smoke (фаза 4b) — `e2e-header/`

| id | Файл |
|----|------|
| `hdr-scope-4b` | [e2e-header/hdr-scope-4b.md](e2e-header/hdr-scope-4b.md) |
| `hdr-selectors` | [e2e-header/hdr-selectors.md](e2e-header/hdr-selectors.md) |
| `hdr-legacy-audit` | [e2e-header/hdr-legacy-audit.md](e2e-header/hdr-legacy-audit.md) |
| `hdr-target` | [e2e-header/hdr-target.md](e2e-header/hdr-target.md) |
| `hdr-behavior` | [e2e-header/hdr-behavior.md](e2e-header/hdr-behavior.md) |
| `hdr-layout-gap` | [e2e-header/hdr-layout-gap.md](e2e-header/hdr-layout-gap.md) |
| `hdr-layout-bp` | [e2e-header/hdr-layout-bp.md](e2e-header/hdr-layout-bp.md) |
| `hdr-layout-height` | [e2e-header/hdr-layout-height.md](e2e-header/hdr-layout-height.md) |
| `hdr-viewport` | [e2e-header/hdr-viewport.md](e2e-header/hdr-viewport.md) |
| `hdr-visual-opt` | [e2e-header/hdr-visual-opt.md](e2e-header/hdr-visual-opt.md) |
| `hdr-legacy-reject` | [e2e-header/hdr-legacy-reject.md](e2e-header/hdr-legacy-reject.md) |

## Когда обновлять

Новый e2e-паттерн → чанк + строка в `manifest.jsonl` + одна строка в ADR (id → path). Полный ADR переписывать не нужно.

### Planned: e2e-analytics (фаза 7.analytics)

Чанки `alr-*` — после реализации фазы 7; домен `e2e-analytics` или подпапка `e2e/analytics/`:

| id (planned) | Содержание |
|--------------|------------|
| `alr-agent-mode` | `allure agent inspect/query`, когда agent vs raw JSON |
| `alr-data-sources` | results, history, agent-output, known.json |
| `alr-metrics-catalog` | Tier 1–3 метрики + формулы |
| `alr-chart-matrix` | chart type → метрика (фаза 8) |
| `alr-dashboard-layout` | сетка, linked filters, theme sync (фаза 8) |
| `alr-native-vs-custom` | decision matrix Allure vs Highcharts |
| `alr-hook-shell` | `allure-shell.js` iframe + custom panel |
