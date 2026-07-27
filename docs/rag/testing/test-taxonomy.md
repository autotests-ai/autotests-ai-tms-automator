---
id: test-taxonomy
domain: testing
phase: 4a
adr: 002
tags: [selenide, junit, allure]
---
# Фильтры Allure

**id:** `test-taxonomy`

## Файлы

`@Layer, @Epic, @Feature, @Story, @Tag`

## Входы

—

## Assert

Labels в отчёте

## Do

smoke/positive/negative; epic One Page Form для login; `@Feature` / `@Story` на **классе** (иерархия Epic → Feature → Story для Allure stability charts); `@Manual` exploratory — на **методе** в `LoginTests`, `@Tag("manual")` (чанк `test-manual`); TestOps layer mapping — чанк `test-layers`

## Don't

Смешивать epic header и login
- Искать ladder negative в `tests-java/LoginTests` — канон smoke only (`test-pyramid`)

