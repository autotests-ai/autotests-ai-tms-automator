# Component sizes (canonical)

Утверждено в **фазе 1.1**. Header (фаза 2) собирается только из этих примитивов — без ad-hoc `width`/`height` на SVG.

## Tokens (`templates/vanilla-ui/css/tokens.css`)

| Token | Value | Назначение |
|-------|-------|------------|
| `--control-height-md` | `36px` | Кнопки, icon-btn, поля ввода |
| `--icon-size-md` | `18px` | Все иконки в tool-ряду и внутри icon-btn |
| `--input-min-width` | `200px` | Минимальная ширина text input |
| `--header-height` | `56px` | Высота header shell |
| `--header-brand-logo-height` | `22px` | Высота SVG логотипа в brand (`.header__brand-logo`) |
| `--z-header` | `100` | `z-index` fixed header shell |

## По компонентам

| Компонент | CSS | Hit area / box | Примечание |
|-----------|-----|----------------|------------|
| Button | `button.css` | min-height `36px` | padding через `--space-2` / `--space-4` |
| Icon | `icon.css` | `18×18` | SVG без своих `width`/`height` |
| Icon button | `icon-btn.css` | `36×36` | иконка внутри — `.icon` |
| Input | `input.css` | min-height `36px` | |
| Textarea | `textarea.css` | min-height `72px` | многострочное поле |
| Checkbox | `checkbox.css` | box `18×18` | label рядом |
| Radio | `radio.css` | box `18×18` | label рядом; группа по `name` |
| Text | `text.css` | text flow | `.text` body; `.text--muted`, `.text--sm` |
| Link | `link.css` | text flow | nav-link — underline |
| Badge | `badge.css` | auto × ~22px | padding `--space-1` `--space-3` |
| Chip | `chip.css` | auto × ~22px | как badge; интерактивная метка (button); `.chip--active`, `.chip--static` |
| Segmented control | `segmented-control.css` | btn `min-height: 36px`, 50/50 flex | 2 опции; `.segmented-control__btn--active` |
| Tab | `tab.css` | auto × ~30px | `.tabs` + `.tab`; `.tab--active` |
| Grid | `grid.css` | layout flow | 2/3/4 колонки desktop; 1 колонка ≤768px |
| Lang toggle | `lang-toggle.css` | hit area `36×36` | составной: `.icon-btn` + label overlay |
| Choice card shell | `choice-card.css` | padding `--space-2` `--space-3`, gap `--space-2` | общий shell для `.radio-card` / `.checkbox-card`; checked/hover через border + surface |
| Radio group | `choice-card.css` | title `--font-size-sm`, uppercase | `.radio-group` + `.radio-group__title`; input — `.radio__input` из `radio.css` |
| Checkbox group | `choice-card.css` | title `--font-size-sm`, uppercase | `.checkbox-group` + `.checkbox-group__title`; input — `.checkbox__input` из `checkbox.css` |

## Lang toggle (составной примитив)

Добавлен через skill `add-component`. **Не** исключение из таблицы — полноценная строка и секция в каталоге.

| Часть | Размер / источник |
|-------|-------------------|
| Кнопка | `.icon-btn` → `36×36` (`--control-height-md`) |
| Иконка globe | `.icon` → `18×18` (`--icon-size-md`) |
| Label (RU/EN) | `8px`, `font-weight: 600`, overlay `bottom: 5px; right: 5px` |
| Обёртка | `position: relative; display: inline-block` |

Snippet: `templates/lang-toggle.html`. В header — внутри `.header__tools` как `.lang-toggle`; стили примитива — только в `lang-toggle.css`.

Начальное состояние lang — `window.headerConfig.lang.default` (skill `header-config`).

## Инварианты (обязательны)

1. **Один размер иконки** — только `--icon-size-md`; не копировать произвольные `18`/`20` из сторонних SVG.
2. **Размер задаёт CSS**, не атрибуты SVG (`width`/`height` на `<svg>` — убрать или оставить пустыми; слот — `.icon`).
3. **Одинаковые соседние controls** — в ряду header tools все элементы `--control-height-md`.
4. **Header spacing** — горизонтальные промежутки между блоками только через `gap` на `.header__inner`; без `--header-*` margin tokens.
5. Новый примитив → строка в эту таблицу + секция в `components.html` + snippet в `templates/`.

## Проверка

На `components.html`: DevTools → все `.icon` в одной секции имеют `getBoundingClientRect().width === 18` (±0.5px).

На `header.html`: lang-toggle hit area ≈ 36px; icon внутри ≈ 18px.

Skill: `playground-verify`.
