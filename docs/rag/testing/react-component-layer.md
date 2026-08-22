---
id: react-component-layer
domain: testing
phase: 9.react-pilot
tags: [react, react-testing-library, vitest, allure-vitest, component, pyramid, allure]
related: [react-rtl-allure, react-component-coexist, test-pyramid, test-components, 007-react-component-library]
---
# React component layer (Vitest + React Testing Library)

**id:** `react-component-layer`  
**ADR:** [007-react-component-library](../../adr/007-react-component-library.md)

Слой пирамиды для **React UI** (Vitest + React Testing Library): `projects/design-system-home/react-ui/` (library) и consumers (`autotests-ai-multistack-app`, `selenoid-ui` v3). Не путать с Java `@Layer("component")` (Selenide в browser) и TestOps custom field **Component** (сервис/repo).

## Место в пирамиде

```text
unit (TS pure)
  ↓
react-component (Vitest + React Testing Library)   ← этот документ
  ↓
integration (Java Selenide mount)
  ↓
api
  ↓
e2e smoke
  ↓
visual (Playwright baseline)
```

**React Testing Library — отдельный инструмент**, но **layer в Allure = `component`**. Различение React vs Java/Selenide — labels (`scope=react` vs `scope=browser`), не отдельный layer.

## Chunks (retrieval)

| id | Содержание |
|----|------------|
| `react-rtl-allure` | RTL → Allure wiring, labels, dashboard mapping, selenoid-ui reference-only |
| `react-component-coexist` | CI job, Java coexistence (`@Scope`/`@Framework`), v2/v3 status |

## Границы ответственности

### Тестируем (React Testing Library)

| Concern | Пример |
|---------|--------|
| Props → render | `variant="primary"` → `.btn--primary`; `PlaqueFieldSeg` → `radiogroup` 2 btn; `Panel variant="terminal"` |
| User events | theme/lang toggle; seg `onValueChange`; `PlaqueSelect` / `PlaqueTagstrip` |
| a11y | `aria-label`, `role`, `disabled`; form controls — `id` or `name` (auth: `login.md` `formControls`) |
| Conditional UI | loading / error states |
| Callbacks | `onClick`, `onChange` invoked |

### Не тестируем (React Testing Library)

| Concern | Слой |
|---------|------|
| HTTP / SSE | integration / e2e |
| Routing across pages | e2e |
| Pixel-perfect layout | visual |
| Full header embed in Spring static | Java component / integration |
| Backend contracts | api |

## Структура файлов

```text
projects/design-system-home/react-ui/
  src/*.tsx + *.test.tsx
  demo/*Screen.tsx + *.test.tsx
  vitest.config.ts
  src/test/setup.ts
```

Naming: `*.test.tsx` / `*.test.ts` рядом с модулем.

## Do

- Один describe на компонент; user-visible behavior (`getByRole`).
- Import CSS в test setup или component file.
- Allure labels через `ALLURE_LABEL_*` env в test script — см. `react-rtl-allure`.
- Добавлять тест при каждом новом wrapper.

## Don't

- Snapshot всего DOM без причины.
- Mock React internals / implementation details.
- Заменять Java component tests на RTL.
- Путать `@Component("selenoid-ui")` (TestOps) с react component layer.
- Сокращать framework label — всегда `react-testing-library`.
- Копировать архитектуру selenoid-ui v2 (router v5, rxjs-hooks, react-input-autosize).
