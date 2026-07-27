---
id: allure-reporting-requirements
domain: testing
phase: 4a
adr: 002
tags: [allure, layer, steps, attachments, quality-gate]
related: [allure-attach, po-step, allure-selenide-listener, test-layers]
---
# Allure steps & attachments — требования по @Layer

**id:** `allure-reporting-requirements`

## SSOT

- Java lifecycle: `TestBase` / `UiTestBase` / `PlaywrightTestBase`, `allure/Attachments.java`
- Quality gate: `_ethalon/allure/quality-gate-custom.mjs` → `minStepsForLayers`, `minAttachmentsForLayers`
- Env profiles: `gen-env-configs.py` — `e2e` overlay включает `attachLastScreenshot=true`

## Требования по слою

| @Layer | Steps | Attachments |
|--------|-------|-------------|
| `unit` | опционально | не требуются |
| `component` | рекомендуется 1 scenario step | не требуются |
| `api` | обязательно (`@Step` на API и/или `Allure.step`) | opt-in |
| `integration` | обязательно | opt-in |
| `e2e` | обязательно (PO `@Step` **или** `Allure.step` **или** listener — один источник) | `attachLastScreenshot=true` в e2e env |
| `manual` | обязательно (`Allure.step`) | `attachLastScreenshot` + `attachPageSource` в manual overlay |
| Go unit (CI) | не требуются (JUnit→Allure flat) | coverage — отдельно |

## Quality gate (Allure 3)

В `allurerc.mjs` через `createAllureConfig`:

- `minStepsForLayers`: `api`, `integration`, `e2e`, `manual` — 0 шагов → fail
- `minAttachmentsForLayers`: `e2e` — 0 attachments → fail
- Go (`framework=go`, `layer=unit`) — исключены из обоих правил

## Do

- Новый `@Layer("api"|"integration"|"e2e")` — минимум один Allure step в отчёте
- Browser e2e — env `*_e2e` с `attachLastScreenshot=true`; Playwright — `PlaywrightTestBase` → `Attachments.png`

## Don't

- Смешивать `Allure.step` и `AllureSelenide` в одном тесте (дубли шагов)
- Требовать steps/attachments для Java `unit` / `component` в quality gate
- `attachHarLogs=true` до реализации `Attachments.harLogs()`
