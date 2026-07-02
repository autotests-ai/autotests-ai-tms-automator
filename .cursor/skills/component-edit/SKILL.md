---
name: component-edit
description: Микроправка одного UI-примитива (цвет, отступ, состояние). Use when user asks to tweak button, input, icon, badge, lang-toggle, or other single component in templates/vanilla-ui/.
---

# Component edit

## Scope

- **Один** компонент, 1–2 файла, ≤15 строк CSS
- Файл: `templates/vanilla-ui/css/<component>.css` (для lang-toggle — `lang-toggle.css`)
- Не трогать соседние компоненты и `tokens.css` без причины

## Before edit

1. Read `docs/component-sizes.md` — не ломать утверждённые размеры
2. Read текущий `templates/vanilla-ui/css/<component>.css`
3. Сравни с соседней секцией на `components.html`

## Size rules

- Hit area controls → `--control-height-md` (36px)
- Иконки → `.icon` + `--icon-size-md` (18px), **не** width/height на SVG
- Lang toggle — составной: icon-btn 36×36 + label overlay (см. `component-sizes.md`)
- Не копировать px из сторонних источников — только токены из `component-sizes.md`

## After edit

Запусти проверку по skill `playground-verify` (секция изменённого компонента; для lang-toggle — также `header.html`).  
В ответе — `file://…/templates/tests-java/app-path-local/components.html` (rule `frontend-preview`), без `:3000`.

## Out of scope

- Header layout / spacing между блоками → skill `header-layout` (`header.css`, только gap на `.header__inner`)
- Header config (nav, lang.default, theme.default) → skill `header-config`
- Новый компонент с нуля → skill `add-component`
