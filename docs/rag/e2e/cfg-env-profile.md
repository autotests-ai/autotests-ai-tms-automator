---
id: cfg-env-profile
domain: e2e
phase: 4a
adr: 002
tags: [selenide, junit, allure]
---
# Выбор окружения

**id:** `cfg-env-profile`

## Файлы

`TestConfig, config/*.properties`

## Входы

-Denv=local-e2e

## Assert

Config без NPE

## Do

MERGE system + classpath; @DefaultValue на опциональных ключах

## Don't

Хардкод URL в тестах

