---
name: header-config
description: Настройка наполнения header через window.headerConfig (nav, brand, lang, theme). Use when user asks to change header links, active nav item, brand URL, default language/theme, or header embed config — after layout is done (header-layout).
---

# Header config

Конфигурация **наполнения** и **начального состояния** header без правок layout CSS. Layout — skill `header-layout`; embed в сторонние страницы — skill `embed-header`.

## Scope

| В scope | Out of scope |
|---------|--------------|
| `window.headerConfig` API | `templates/vanilla-ui/css/header.css` (layout, spacing) |
| `templates/vanilla-ui/js/header.js` — apply после fetch, клики lang/theme | Копирование монолитного header CSS из consumer-репо |
| `lang.default`, `theme.default` — initial state на mount | Embed в consumer-страницы — skill `embed-header` |
| Пример на `templates/vanilla-ui/header.html` (harness) | Новые иконки tools без `add-component` |
| Дефолты и URL в `templates/header.html` (fallback без JS) | E2E — фаза 4 |

## Предусловие

Layout собран: `templates/header.html`, `templates/vanilla-ui/css/header.css`, `templates/vanilla-ui/js/header.js`, `templates/vanilla-ui/header.html`.

## API: `window.headerConfig`

Задаётся **до** `<script type="module" src="js/header.js">` на странице-хосте.

```javascript
window.headerConfig = {
  brand: {
    href: 'https://qa.guru/',
  },
  nav: [
    { href: 'https://qa.guru/', label: 'Главная', active: true, testid: 'header-nav-home' },
    { href: '#', label: 'Курсы', testid: 'header-nav-courses' },
    { href: 'https://qa.guru/about', label: 'О школе', testid: 'header-nav-about' },
  ],
  lang: {
    default: 'ru', // 'ru' | 'en' — начальный язык на mount
  },
  theme: {
    default: 'dark', // 'dark' | 'light' — начальная тема на mount
  },
};
```

### Поля

| Поле | Тип | Описание |
|------|-----|----------|
| `brand.href` | string | URL логотипа; если не задан — дефолт из `header.js` |
| `nav` | array | Полная замена ссылок в `.header__nav` |
| `nav[].href` | string | URL |
| `nav[].label` | string | Текст ссылки |
| `nav[].active` | boolean | `is-active` + `aria-current="page"` |
| `nav[].testid` | string | optional; default `header-nav-${index}` |
| `lang.default` | `'ru'` \| `'en'` | Начальный `data-lang`, label (RU/EN), `aria-label` на lang-toggle |
| `theme.default` | `'dark'` \| `'light'` | Начальное состояние: `light` → `document.documentElement.classList.add('theme-light')` |

Merge: поверх `DEFAULT_HEADER_CONFIG` в `header.js` — shallow merge корня, `brand`, `lang`, `theme`; массив `nav` заменяется целиком, если передан.

### Runtime (клики)

Обработчики в `bindHeaderControls()` (`header.js`), вызывается после `applyHeaderConfig`:

| Элемент | testid | Поведение |
|---------|--------|-----------|
| Lang toggle | `header-lang-toggle` | click → toggle `ru`/`en`, обновить label и `aria-label` |
| Theme toggle | `header-theme-toggle` | click → toggle класс `theme-light` на `<html>` |

Клики **не** пишут обратно в `window.headerConfig` — только DOM/runtime state.

## Известные URL qa.guru

| Пункт | URL | Статус |
|-------|-----|--------|
| Главная / логотип | `https://qa.guru/` | ✓ |
| О школе | `https://qa.guru/about` | ✓ |
| GitHub org (tools) | `https://github.com/qa-guru` | ✓ |
| Курсы (отдельная страница) | — | **TODO** — `/courses` 404; пока `#` или anchor на главной |
| GitHub Pages (tools icon) | `https://qa.guru` | ✓ (как в шаблоне) |

Неизвестный URL → `#` + комментарий `TODO` в конфиге страницы, не выдумывать path.

## Файлы на правку

| Файл | Что менять |
|------|------------|
| `templates/vanilla-ui/js/header.js` | `DEFAULT_HEADER_CONFIG`, `applyHeaderConfig`, `applyLangDefault`, `applyThemeDefault`, `bindHeaderControls` |
| `templates/vanilla-ui/header.html` | inline `window.headerConfig` (harness / e2e) |
| `templates/vanilla-ui/header-examples.html` | gallery inline config + iframe variants |
| `templates/header.html` | дефолтные href и fallback lang/theme attrs |

## Подключение на странице

```html
<div id="app-header"></div>
<script>
  window.headerConfig = { /* … */ };
</script>
<script type="module" src="js/header.js"></script>
```

CSS — как в `header-layout` (tokens, link, input, icon, icon-btn, lang-toggle, header, page).

## Проверка

**Preview в ответе пользователю** — rule `frontend-preview`: `file://…/templates/tests-java/app-path-local/header.html` (symlink `app-path-local` → `../frontend`). Без `http://localhost:3000` в чате.

**Behavior (active, lang, theme, клики)** — только при явном запросе или e2e: сервер `:3000` из `templates/vanilla-ui/` (rule `e2e-debug-run`), не ссылка пользователю.

Чеклист на harness / gallery:

1. Active на «Главная», href в DevTools совпадают с конфигом. Gallery — `…/app-path-local/header-examples.html`.
2. Сменить `active` на другой пункт — один `is-active`, корректный `aria-current`.
3. `lang.default: 'en'` — label EN, `data-lang="en"` до первого клика.
4. `theme.default: 'light'` — `html.theme-light` до первого клика theme.
5. Клик lang/theme — toggle без перезагрузки.

Интерактивный редактор — skill `header-config` → `templates/vanilla-ui/playground.html`.  
Skill `playground-verify` — секция header.html.

## Запреты

- Не копировать монолитный header HTML/CSS из consumer-репо
- Не менять layout/spacing CSS без необходимости
- Не трогать `.header__slot` в этом skill (downstream inject)

## После изменений

Если появился новый паттерн config API или ограничение → чат `sync-agent-meta`. Иначе — ничего.
