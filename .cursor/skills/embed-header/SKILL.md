---
name: embed-header
description: >-
  Встроить канонический header (header.js + templates/header.html) в стороннюю
  HTML-страницу через #app-header и window.headerConfig. Use when user asks to
  embed header, replace inline/demo header, or wire header into login or consumer page.
---

# Embed header

Подключение **готового** header из template-project к странице-хосту. Layout и примитивы — skill `header-layout`; наполнение — skill `header-config`.

## Scope

| В scope | Out of scope |
|---------|--------------|
| Mount `#app-header` + CSS + `header.js` на одной странице | Правки `templates/vanilla-ui/css/header.css` (layout) |
| `window.headerConfig` под контекст страницы | Копирование монолитного header HTML/CSS из consumer-репо |
| Удаление inline / demo-header блока на пилотной странице | Массовый replace всех HTML в consumer |
| Smoke e2e страницы-хоста (напр. `LoginTests`) | Visual baselines host-страницы — отдельный чат после embed |
| Пилот: `templates/vanilla-ui/login.html` | Sync-скрипты между репо |

## Предусловие

Фазы 2–4 закрыты: `templates/header.html`, `templates/vanilla-ui/js/header.js`, `header-config` API, harness `templates/vanilla-ui/header.html`.

## Канонический snippet

Как в `playground.js` → `buildEmbedSnippet()`:

```html
<div id="app-header"></div>
<script>
  window.headerConfig = {
    brand: { href: 'https://qa.guru/' },
    nav: [
      { href: 'https://qa.guru/', label: 'Главная', active: true, testid: 'header-nav-home' },
      { href: '#', label: 'Курсы', testid: 'header-nav-courses' },
      { href: 'https://qa.guru/about', label: 'О школе', testid: 'header-nav-about' },
    ],
    lang: { default: 'en' },
    theme: { default: 'light' },
  };
</script>
<script type="module" src="js/header.js"></script>
```

`window.headerConfig` — **до** `header.js`. Поля — skill `header-config`.

## CSS (обязательный порядок)

```html
<link rel="stylesheet" href="css/tokens.css">
<link rel="stylesheet" href="css/link.css">
<link rel="stylesheet" href="css/input.css">
<link rel="stylesheet" href="css/icon.css">
<link rel="stylesheet" href="css/icon-btn.css">
<link rel="stylesheet" href="css/lang-toggle.css">
<link rel="stylesheet" href="css/header.css">
```

`css/page.css` — только если main использует канон padding под fixed header (`calc(var(--header-height) + …)`). Страница со своим layout (login card) — без `page.css`.

Тема: `html.theme-light` и/или `headerConfig.theme.default` (`light` | `dark`). Не смешивать с legacy `data-theme` / `AllureShell.initDemoHeader` на той же странице.

## Файлы на правку (пилот template-project)

| Файл | Действие |
|------|----------|
| `templates/vanilla-ui/login.html` | Убрать `<!-- demo-header:start/end -->`, вставить snippet + CSS |
| `templates/vanilla-ui/js/header.js` | не менять без нового API |
| `templates/vanilla-ui/js/theme-icons.js` | копировать вместе с `header.js` (SVG sun/moon для theme toggle) |
| `templates/header.html` | не менять |

Consumer-репо — **отдельный workspace** (`docs/downstream-map.md`).

## Удалить при embed

- Inline `<header class="header">…</header>` (demo / legacy)
- `AllureShell.initDemoHeader({ i18n, applyPage })` — только для старого demo-header
- I18N-ключи header (`navMenu`, `langEng`, …) — lang/theme в `header.js`

Логика страницы (login form, footer) остаётся; i18n формы — отдельно от header.

## Lang sync (consumer listener)

Header **не** меняет текст формы/host — только lang-toggle в shell. При mount и при клике `header.js` шлёт на `document`:

| Константа | Значение |
|-----------|----------|
| `HEADER_LANG_CHANGE` | `'header:lang-change'` (export из `header.js`, дубль `window.HEADER_LANG_CHANGE`) |
| `event.detail.lang` | `'ru'` \| `'en'` |

На host-странице — listener **до** или **после** `header.js` (событие приходит после mount):

```javascript
document.addEventListener('header:lang-change', (event) => {
  const lang = event.detail?.lang === 'ru' ? 'ru' : 'en';
  // URL (?lang=), labels формы, localStorage — по логике страницы
});
```

Референс: `templates/vanilla-ui/login.html` (`syncLoginPageLangUrl`, `applyLoginI18n`). Канон события — `docs/layout-standard.md` § Embed header.

## Fetch template

`header.js` грузит `templates/header.html` через `fetch`. Symlink `templates/vanilla-ui/templates` → `../templates` (cwd HTTP = `templates/vanilla-ui/`).

**Нужен HTTP**, не `file://` — иначе fetch 404/CORS.

## Проверка

### Preview (без сервера в чате)

Rule `frontend-preview`: harness `file://…/templates/tests-java/app-path-local/header.html`.

### E2e smoke страницы-хоста

Из `templates/tests-java/`, сервер из `templates/vanilla-ui/`:

```bash
cd frontend && python -m http.server 3000
```

```bash
cd tests-java
gradle test -Denv=local --tests 'tests.LoginTests' \
  -Dheadless=true -DcloseBrowserAfterEach=false \
  -Djunit.jupiter.execution.parallel.config.fixed.parallelism=3
```

Login embed → `LoginTests`. Header harness → `HeaderTests`. После embed на host со своим layout — `LoginBaselineTests` + `LoggedInBaselineTests`; при +8px на форме от bleed `tokens.css` → `body { line-height: normal }` в inline host (без `page.css`).

```bash
gradle test -Denv=local --tests 'tests.LoginBaselineTests' --tests 'tests.LoggedInBaselineTests' \
  -Dheadless=true -DcloseBrowserAfterEach=false \
  -Djunit.jupiter.execution.parallel.config.fixed.parallelism=3
```

Перезапись эталонов: `-DupdateBaselines=true`.

## Запреты

- Не копировать монолитный header из consumer (ADR 001)
- Не выдумывать nav/tools — только `headerConfig` и шаблон
- Не массовый diff по всем HTML
- Не менять layout CSS header «под страницу»

## После пилота

Фаза 6 ✓ на `templates/vanilla-ui/login.html`. Перенос в consumer — чеклист `docs/downstream-map.md`. Новый host-page embed → тот же skill; мета — `sync-agent-meta`.
