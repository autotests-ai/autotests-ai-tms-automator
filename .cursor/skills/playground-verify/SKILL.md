---
name: playground-verify
description: Проверить components.html и header.html визуально и по размерам. Use when user asks to verify playground, check components catalog, validate header preview, or validate UI after CSS changes.
---

# Playground verify

Цель: `templates/vanilla-ui/components.html` — эталон примитивов; `templates/vanilla-ui/header.html` — harness header (e2e + size audit); `templates/vanilla-ui/header-examples.html` — gallery вариантов config.

## 1. Preview (без сервера по умолчанию)

Rule `frontend-preview`: после правок **не** поднимать `http.server` — дать пользователю `file://` через symlink `templates/tests-java/app-path-local/` (шаблон `app-path-local.example`). **Не давать** `http://localhost:3000/...` в ответе.

| Harness | file:// (symlink) | Примечание |
|---------|-------------------|------------|
| `components.html` | `…/templates/tests-java/app-path-local/components.html` | полный preview |
| `header.html` | `…/app-path-local/header.html` | CSS only; mount header — только e2e / явный HTTP-запрос |
| `header-examples.html` | `…/app-path-local/header-examples.html` | CSS only |

Сервер `:3000` из **`templates/vanilla-ui/`** — **только внутренне** для e2e (`e2e-debug-run`) или behavior header (lang/theme) по явному запросу; не в ссылках пользователю.

## 2. Screenshot breakpoints

Проверить **обе** страницы:

| Width | Что смотреть |
|-------|----------------|
| 390px | каталог/header читаемы, нет horizontal scroll; nav/search скрыты на mobile |
| 768px | граница mobile/desktop |
| 1280px | demo-row / header inner не ломается |

## 3. Size audit — components.html

### Icon / icon-btn

В DevTools console:

```javascript
[...document.querySelectorAll('.icon')].map(el => ({
  testid: el.dataset.testid,
  w: el.getBoundingClientRect().width,
  h: el.getBoundingClientRect().height
}))
```

Ожидание: все `w` и `h` ≈ **18** (±0.5px).

```javascript
[...document.querySelectorAll('.icon-btn')].map(el => ({
  testid: el.dataset.testid,
  w: el.getBoundingClientRect().width
}))
```

Ожидание: все `w` ≈ **36**.

## 4. Size audit — header.html

Fixed header вверху страницы (mount `#app-header`).

```javascript
const langBtn = document.querySelector('[data-testid="header-lang-toggle"]');
const langIcon = langBtn?.querySelector('.icon');
({
  langHit: langBtn?.getBoundingClientRect().width,
  langIcon: langIcon?.getBoundingClientRect().width,
})
```

Ожидание: `langHit` ≈ **36**, `langIcon` ≈ **18**.

Все `.icon-btn` в `[data-testid="header-tools"]` → hit area ≈ **36**.

## 5. Header behavior (manual)

- [ ] Nav: один `is-active`, корректный `aria-current`
- [ ] Lang toggle: click → RU ↔ EN, label и `aria-label` обновляются
- [ ] Theme toggle: click → `html.theme-light` toggle
- [ ] Mobile 768px: nav и search скрыты, tools на месте

Config initial state (`lang.default`, `theme.default`) — skill `header-config`; variant-страницы — iframe на `header-examples.html`.

## 6. Регрессии (components.html)

- [ ] Нет скачка font-size при resize через 768px
- [ ] focus-visible виден на кнопках и полях
- [ ] disabled состояния визуально отличимы

## 7. Если размеры разъехались

1. Убрать `width`/`height` с SVG
2. Обернуть в `.icon`
3. Не чинить «на глаз» — только `docs/component-sizes.md`

Lang toggle — составной примитив (`lang-toggle.css`), не ad-hoc inline styles.
