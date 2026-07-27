---
id: hdr-target
domain: testing-header
phase: 4b
adr: 003
tags: [header, selenide]
---
# Target page header

**id:** `hdr-target`

## Файлы

`local_e2e.properties`, `local_visual.properties`

## Входы

baseUrl http://localhost:3000/ (сервер cwd = `projects/design-system-home/design-system/preview/`)

## Assert

open("/header.html") — preview (минимальный mount). Gallery: `header-examples.html`, не e2e target.

## Do

HTTP :3000 из `projects/design-system-home/design-system/preview/`

## Don't

file:// без проверки CORS/module

