---
name: add-component
description: Добавить новый UI-примитив в template-project. Use when user asks to add a new component, primitive, or control to the design system catalog.
---

# Add component

## Before start

- **Не выдумывать** имя, размер, иконку, состояние — уточнить у пользователя, если не задано явно.
- Проверить `components.html` и `component-sizes.md`: возможно, примитив уже есть под другим именем.
- Rule: `compose-from-primitives.mdc`.

## Checklist

1. **Имя** — kebab-case, один CSS-файл: `templates/vanilla-ui/css/<name>.css`
2. **Размеры** — из `docs/component-sizes.md`; если новый размер → сначала токен + строка в таблице
3. **CSS** — только tokens, без hex; `data-testid` на интерактиве
4. **Каталог** — секция в `templates/vanilla-ui/components.html` с `demo-sizes` подписью
5. **Snippet** — `templates/<name>.html`
6. **Проверка** — skill `playground-verify`; preview в чате — rule `frontend-preview` (`file://…/app-path-local/…`)
7. **После изменений** — если примитив меняет сборку header/form или появился паттерн → чат `sync-agent-meta`; иначе ничего

## Шаблон секции

```html
<section class="section" data-testid="section-<name>">
  <h2 class="section__title">Title</h2>
  <p class="section__desc">Описание.</p>
  <div class="section__body">...</div>
  <p class="demo-sizes"><code>размеры из tokens</code></p>
</section>
```

## Иконки

Всегда оборачивать SVG в `<span class="icon">`. SVG — только `viewBox`, без `width`/`height`.

## Запреты

- Не добавлять header/nav shell (фаза 2)
- Не копировать CSS целиком из consumer-репо
- Не пропускать `component-sizes.md`
