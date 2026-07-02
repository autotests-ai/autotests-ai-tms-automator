# Стандарт адаптивной вёрстки

Черновик v0. Уточняется по результатам playground и header preview.

## Breakpoint

**768px** — единая граница mobile ↔ desktop:

```css
@media (min-width: 769px) { /* desktop */ }
@media (max-width: 768px) { /* mobile */ }
```

Новые breakpoints (640, 1024…) — только по явному запросу + ADR.

## Shell

| Параметр | Значение |
|----------|----------|
| Высота header | `56px` (`--header-height`) |
| z-index header | `100` (`--z-header`) |
| Max-width контента | `min(1300px, calc(100% - 32px))` |
| Горизонтальный padding страницы | `16px` (`--space-4`, `--page-padding-x`) |

## Header layout

| Элемент | Правило |
|---------|---------|
| `.header__inner` | `display: flex; align-items: center; gap: var(--space-4)` |
| Spacing между блоками | **только** `gap` на `.header__inner` |
| Запрет | `--header-*` margin tokens; `margin-left`/`margin-right` на секциях для межблочного spacing |
| Допустимо | `margin-left: auto` на `.header__tools`; внутренние отступы nav-разделителей |
| Mobile | `@media (max-width: 768px)` — скрыть `.header__nav`, `.header__search` |

Harness (e2e, size audit): `templates/vanilla-ui/header.html`. Gallery вариантов: `templates/vanilla-ui/header-examples.html`. Сервер cwd = `templates/vanilla-ui/`.

## Типографика

При resize и смене breakpoint **текст не прыгает**:

- Не менять `html { font-size }` и rem через `vw` / `clamp()`.
- Не менять `font-size` / `font-weight` в `@media` для уже видимого текста.
- Адаптив — через layout: `flex`, `gap`, `overflow`, скрытие блоков, drawer.

## Design tokens

Все компоненты используют переменные из `templates/vanilla-ui/css/tokens.css`:

- spacing: `--space-1` … `--space-6`
- colors: `--color-surface`, `--color-text`, `--color-primary`
- radius: `--radius-sm`
- motion: `--duration-fast`, `--ease-out`

Не хардкодить hex в компонентных файлах без причины.

## Селекторы для тестов

Интерактивные элементы: `data-testid="…"`.  
Классы — для стилей, не для e2e (кроме стабильных layout-контейнеров).

E2E smoke header — **4b.1 ✓** (`templates/tests-java/`, ADR `003-header-smoke-e2e.md`); login e2e — **4a ✓**.

## Проверка

1. Browser screenshot: **390px**, **768px**, **1280px** — `components.html` и `header.html` (harness); gallery — `header-examples.html`.
2. Медленный resize через 768px — нет смены кегля.
3. Нет horizontal scroll в header на 320px.

## Embed header (фаза 6)

```html
<div id="app-header"></div>
<script>
  window.headerConfig = { /* nav, brand, lang, theme — см. header-config skill */ };
</script>
<script type="module" src="/js/header.js"></script>
```

Skill `embed-header` — **active**, фаза 6 ✓ (пилот `templates/vanilla-ui/login.html`). См. `docs/adr/001-greenfield-not-copy-legacy.md`.

### Lang sync на host-странице

`header.js` диспатчит на `document` кастомное событие **`header:lang-change`** (`HEADER_LANG_CHANGE` — export и `window.HEADER_LANG_CHANGE`):

- **Когда:** на mount (`applyLangDefault`) и при каждом клике lang-toggle.
- **Payload:** `event.detail.lang` — `'ru'` | `'en'`.

Consumer слушает событие и обновляет i18n страницы (не через `window.headerConfig`):

```javascript
document.addEventListener('header:lang-change', (event) => {
  const lang = event.detail?.lang === 'ru' ? 'ru' : 'en';
  // sync URL, form labels, …
});
```

Пилот: `templates/vanilla-ui/login.html` — `syncLoginPageLangUrl` + `applyLoginI18n()`.
