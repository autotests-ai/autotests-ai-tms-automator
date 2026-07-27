---
id: allure-selenide-listener
domain: testing
phase: 4a
adr: 002
tags: [selenide, junit, allure]
---
# AllureSelenide listener

**id:** `allure-selenide-listener`

## Файлы

`tests-java/src/test/java/allure/AllureSelenideListeners`, `tests/TestBase.java`

**Ethalon якорь:** `_ethalon/ladder/LoginTests.emptyLoginAuthorizationTest`

## Входы

`enableAllureSelenideListener` в env profile (`allureListenerMode`: `global_on` / `global_off`)

## Assert

В Allure — **технические** auto-steps из Selenide: `open(/login)`, `[$("…")] set value(…)`, `click()`, `should have(…)` — **не** человекочитаемые имена вроде «Open login page» (это только `step()` / `@Step`).

## Do

- Глобально: `TestBase.@BeforeAll` → `AllureSelenideListeners.setEnabled(true)` при `enableAllureSelenideListener=true` и `allureReportMode≠none`
- Реализация: `SelenideLogger.addListener("AllureSelenide", new AllureSelenide().screenshots(false).savePageSource(false))`
- Якорь listener ON: `shouldLoginWithValidCredentials` — raw inline `$()`, **без** ручных `Allure.step`

## Don't

- Ожидать в отчёте те же названия шагов, что в `step("Open login page")` — listener пишет логи Selenide
- Смешивать `Allure.step` и `AllureSelenide` в одном тесте (дубли шагов в отчёте)
- Включать listener в consumer без осознанного выбора одного источника шагов
