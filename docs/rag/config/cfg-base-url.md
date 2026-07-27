---
id: cfg-base-url
domain: config
phase: 4a
adr: 002
tags: [selenide, junit, allure]
---
# Корень приложения

**id:** `cfg-base-url`

## Файлы

`ConfigReader.resolveBaseUrl` (REST, healthCheck — с trailing `/`); `ConfigReader.resolveWebBaseUrl` (Selenide `Configuration.baseUrl` — без trailing `/`, чтобы `open("/login")` не давал `//login`).

## Входы

baseUrl или basePath

## Assert

`open("/login")` / `open("/login.html")` резолвятся без `//path` (400)

## Do

Trim; trailing / для API; **Selenide** — `resolveWebBaseUrl()` без хвостового `/`. Fail fast если `baseUrl` и `basePath` пустые. Приоритет: `baseUrl` → `basePath`. Страницы: фиксированные пути в PO — `open("/login")`, `open("/")`. Один `./gradlew test` — один стенд.

## Don't

basePath в interface без wiring

