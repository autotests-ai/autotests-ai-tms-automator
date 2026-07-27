---
id: alr-allurerc-ethalon
domain: analytics
phase: 7.analytics
adr: 006
tags: [allure, config, ethalon, quality-gate, dashboard, mjs]
---
# Allure allurerc ethalon sync (mjs)

**id:** `alr-allurerc-ethalon`

## Файлы

| Файл | Роль |
|------|------|
| `generators/ethalon/tests-java/_ethalon/allure/*.mjs` | SSOT структуры |
| `generators/ethalon/tests-java/_ethalon/allurerc.mjs` | Runnable эталон |
| `tests/allurerc.mjs` + `tests/allure/` | Runnable consumer |
| `_new.mjs`, `_modified.mjs` | Inbox consumer diff |
| `scripts/validate-allurerc.mjs` | Pyramid @ index 1, layers, import |
| `known.json`, `history.jsonl` | **не** ethalon |

Skill: `sync-allurerc-ethalon`. ADR: `006-allurerc-mjs-ethalon`. См. также `alr-quality-gate`, `alr-hook-shell`.

**Запрет:** `allurerc.json`.

## Profile-specific (rule 2 — не propagate)

- `slug` → `name` = `{slug} Tests`, `reportName`, `fileName`
- `epicCharts` (optional per-epic dashboard tiles)
- `variables.*`

## Structural (rule 1 — propagate)

- modules: `quality-gate`, `categories`, `awesome-charts`, `dashboard-layout`, `constants`
- history / known path defaults

## Инвариант: testing pyramid

Обязательно в **обоих** `charts` и `layout`:

- index **0** = `currentStatus`
- index **1** = `testingPyramid`
- `layers`: `["unit", "component", "integration", "api", "e2e", "manual"]`

`visual` — **не** layer. Удаление пирамиды — только по явному запросу.

## Assert

```bash
node generators/ethalon/tests-java/scripts/validate-allurerc.mjs path/to/allurerc.mjs
```

После sync: import OK; `./gradlew allureQualityGate` / `allureReport` с `--config allurerc.mjs`; pyramid на 2-м месте.
