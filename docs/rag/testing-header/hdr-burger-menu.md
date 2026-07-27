---
id: hdr-burger-menu
domain: testing-header
phase: 9.react-pilot
tags: [header, burger, mobile, integration, mount, fixture]
related: [hdr-scope-4b, react-app-reference]
---
# Header burger menu — SSOT tests (design-system-home)

Механика мобильного бургер-меню покрывается **в design-system SSOT**, не в consumer `reference-app/tests`.

## Target

| Параметр | Значение |
|----------|----------|
| Fixture | `projects/design-system-home/design-system/preview/header-embed-fixture.html` |
| **Не** PO target | `/header.html` (playground only) |
| Harness | `python -m http.server 3000` из `design-system/preview/` |
| Tests | `projects/design-system-home/tests/.../integration/HeaderBurgerMenuTests.java` |
| Layer | `@Layer("integration")`, `@Tag("mount")` |
| Viewport | `375×812` via `ViewportHelper` (CDP, Chrome) |

## Fixture contract

- `#app-header` mount + `window.headerConfig` + `<script type="module" src="../js/header.js">`
- CSS: tokens, link, input, icon, icon-btn, lang-toggle, header, page (как header preview)

## Scenarios

1. Burger visible; inline `header-github` / `header-github-pages` hidden on mobile
2. Open menu → `header-menu-nav-*`, `header-menu-search-input`, `header-menu-github`
3. Active route mirrored in menu nav
4. Menu link click closes menu
5. Escape closes menu

## Consumer

`reference-app/tests` — только `HeaderActiveNavTests` (route-driven active nav в SPA). Burger e2e в consumer **не** дублировать.

## Run

```bash
cd projects/design-system-home/design-system/preview && python -m http.server 3000
cd projects/design-system-home/tests && ./gradlew test --tests 'tests.integration.HeaderBurgerMenuTests' -Denv=design-system_local_component
```
