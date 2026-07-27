---
id: test-negative
domain: testing
phase: 4a
adr: 002
tags: [selenide, junit, allure]
---
# Validation errors

**id:** `test-negative`

## Файлы

**Ethalon:** `tests-java/src/test/java/_ethalon/ladder/LoginTests.java` — `wrongPasswordAuthorizationTest`, `emptyPasswordAuthorizationTest`, …

**Канон:** negative automation не в smoke suite; integration mount — `LoginFormTests` (без submit flow)

## Входы

empty/wrong fields

## Assert

shouldHave(text(...)) — при `test_allure_step` **внутри** `step("...")` (verify-шаг), не снаружи nested-сценария. Канон: `import static io.qameta.allure.Allure.step;`

При `assert.in_po=false` + `page_object` — действия через PO, `should*` в теле теста (≠ `shouldHave*` с `@Step` в PO — чанк `po-step`, тема `canon-smoke`)

## Do

Один assert на сценарий; nested `step()` — `emptyPasswordAuthorizationTest` (каждое Selenide-действие — свой шаг; submit + verify внутри родительского шага); raw inline — `wrongPasswordAuthorizationTest` (assert без `step()` — `steps.location=none`)
- TestOps manual — `shortLoginAuthorizationTest` (чанк `test-manual`)

## Don't

Неверный precondition
- Искать negative methods в `tests-java/LoginTests`

