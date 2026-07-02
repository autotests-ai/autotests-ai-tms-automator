---
name: header-layout
description: Декомпозиция и пошаговая сборка header из примитивов фазы 1.1. Use when user starts phase 2 header, asks for header layout, header shell, or any header block (.header__brand, __nav, __search, __slot, __tools).
---

# Header layout

Header собирается **только** из утверждённых примитивов (`docs/component-sizes.md`). Rule: `compose-from-primitives.mdc`.

**Статус фазы 2:** layout собран. Дальнейшие правки spacing/CSS — только по явному запросу; config — skill `header-config`.

## Структура header

| Блок | Класс | Содержимое | Примитивы |
|------|-------|------------|-----------|
| Shell | `.header` | fixed bar, border, surface | — |
| Inner | `.header__inner` | flex-ряд, **единственный** источник горизонтальных отступов между блоками | `gap: var(--space-4)` |
| Brand | `.header__brand` | логотип, **слева** | `.link` / img |
| Nav | `.header__nav` | ссылки + разделители | `.link--nav` |
| Search | `.header__search` | поле поиска | `.input` |
| Slot | `.header__slot` | пустой шаблон для downstream | — |
| Tools | `.header__tools` | lang-toggle, theme, ссылки, **справа** | `.lang-toggle`, `.icon-btn`, `.icon` |

Разделитель nav — CSS внутри `.header__nav` (псевдоэлемент), не отдельный примитив. Переиспользуемый `.separator` → отдельный чат `add-component`.

### Spacing (канон)

- Горизонтальные промежутки между блоками header — **только** `gap` на `.header__inner`.
- **Не** вводить `--header-*` margin tokens и **не** добавлять `margin-left`/`margin-right` на дочерние блоки для spacing между секциями.
- Исключения: внутренние отступы nav-разделителей, padding `.header__inner` (`--page-padding-x`), `margin-left: auto` на `.header__tools`.

## lang-toggle

Составной примитив — skill `add-component`, не исключение в `component-sizes.md`.

| Файл | Назначение |
|------|------------|
| `templates/vanilla-ui/css/lang-toggle.css` | обёртка + label overlay |
| `templates/lang-toggle.html` | snippet для каталога и header |
| `docs/component-sizes.md` | секция Lang toggle |

В header: `.lang-toggle` внутри `.header__tools`; стили примитива — только в `lang-toggle.css`.

## Перед стартом (новый header / блок)

1. Прочитать `docs/component-sizes.md` и секции link, input, icon-btn, lang-toggle на `components.html`.
2. Вывести gap-анализ: какие примитивы уже есть, чего не хватает.
3. Предложить план чатов (ниже). **Не начинать CSS**, пока пользователь не подтвердил порядок или не закрыты gaps.

## Порядок чатов (один блок = один чат)

```
0. lang-toggle     — add-component (если ещё не в каталоге)
1. .header         — shell + .header__inner
2. .header__brand  — лого слева
3. .header__nav    — ссылки + разделители
4. .header__search — поле поиска
5. .header__slot   — пустой контейнер-шаблон
6. .header__tools  — lang-toggle + icon buttons справа
7. Сборка          — header.css + templates/header.html + templates/vanilla-ui/js/header.js
```

## Лимиты на чат

| Шаг | Файлы |
|-----|-------|
| lang-toggle | `lang-toggle.css` + snippet + секция в `components.html` |
| Блоки 1–6 | `templates/vanilla-ui/css/header.css` (только свой блок) + фрагмент в `templates/header.html` |
| Сборка (7) | `header.css` + `header.js` + `templates/header.html` + `templates/vanilla-ui/header.html` (harness) |

Проверка: `playground-verify` — `components.html` + `header.html`; gallery — `header-examples.html`.

## Запреты

- Не копировать монолитный header CSS из consumer-репо; sync-скрипты для header HTML между репо
- Не упрощать UI (языки, иконки, поля)
- Не добавлять примитивы в том же чате — только `add-component`
- Не spacing через margin на блоках — только `gap` на `.header__inner`

## Embed preview

Harness: `templates/vanilla-ui/header.html`. Gallery: `templates/vanilla-ui/header-examples.html`.

**Ответ пользователю** — rule `frontend-preview`: `file://…/templates/tests-java/app-path-local/header.html` (symlink `ln -snf ../frontend app-path-local` из `templates/tests-java/`). Без `:3000` в чате.

Сервер из `templates/vanilla-ui/` — только e2e / behavior header (rule `e2e-debug-run`), не рутинный preview.

```html
<div id="app-header"></div>
<script>
  window.headerConfig = { /* nav, brand, lang, theme — см. header-config */ };
</script>
<script type="module" src="js/header.js"></script>
```

`header.js` загружает `templates/header.html` через `new URL('../../templates/header.html', import.meta.url)`.

Подключить CSS: `tokens.css`, `link.css`, `input.css`, `icon.css`, `icon-btn.css`, `lang-toggle.css`, `header.css`, `page.css`.

Mobile (`max-width: 768px`): `.header__nav` и `.header__search` скрыты; tools остаются.

## Config (после layout)

Skill `header-config` — `window.headerConfig` (nav, brand, lang.default, theme.default). Клики lang/theme — в `header.js`.

## Шаблон partial

```html
<!-- templates/header.html -->
<header class="header" data-testid="header">
  <div class="header__inner">
    <div class="header__brand" data-testid="header-brand"><!-- brand --></div>
    <nav class="header__nav" data-testid="header-nav"><!-- nav --></nav>
    <div class="header__search" data-testid="header-search"><!-- search --></div>
    <div class="header__slot" data-testid="header-slot"><!-- downstream --></div>
    <div class="header__tools" data-testid="header-tools"><!-- lang-toggle + icon-btn --></div>
  </div>
</header>
```
