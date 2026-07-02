---
id: hdr-visual-opt
domain: e2e-header
phase: 4.visual
adr: 003
tags: [header, selenide, visual]
---
# Header screenshot

**id:** `hdr-visual-opt`

Header-часть cross-epic visual. Общий паттерн: чанк **`visual-baseline`**.

## Файлы

`HeaderBaselineTests`, `ScreenshotBaseline`, `[data-testid=header]`

## Входы

baseline PNG в `screenshots/header/`

## Assert

pixel ratio ≤ threshold

## Do

-DupdateBaselines=true

## Don't

Baselines в PR 4b.1; отдельный helper `HeaderScreenshot` — использовать `ScreenshotBaseline`

