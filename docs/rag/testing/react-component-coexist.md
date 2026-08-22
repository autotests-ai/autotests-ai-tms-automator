---
id: react-component-coexist
domain: testing
phase: 9.react-pilot
tags: [react, java, component, scope, framework, selenoid-ui, ci]
related: [react-component-layer, react-rtl-allure]
---
# React component — CI + Java coexistence

Hub: `react-component-layer`.

## CI job

```bash
yarn --cwd ui install --frozen-lockfile   # selenoid-ui
cd projects/design-system-home/react-ui && yarn test
# или
cd projects/selenoid-home/selenoid-ui/ui && yarn test
```

Target: < 2 min pilot; selenoid-ui RTL suite ~20–32 tests.

## Coexistence с Java component tests

| | Java `@Layer("component")` | React Testing Library |
|--|---------------------------|------------------------|
| Target | browser DOM (Selenide) | isolated jsdom |
| Tool | Selenide + Gradle | Vitest |
| layer | `component` | `component` |
| scope | `browser` | `react` |
| framework | `selenide` | `react-testing-library` |

### Java side — `@Scope` / `@Framework`

Не через `ALLURE_LABEL_*` (это RTL/Vitest), а class-level annotations на `TestBase`:

- `annotations/Scope.java` — `@LabelAnnotation(name = "scope")`
- `annotations/Framework.java` — `@LabelAnnotation(name = "framework")`

```java
@Scope("browser")
@Framework("selenide")
public class TestBase { ... }
```

`@Inherited` → все наследники получают labels. `@Layer` остаётся на классах. **Не затронуты:** `ApiTestBase`, unit.

Locations: `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/tests/java/tests-java-gradle-junit5-allure3-selenide/src/test/java/annotations/`.

## selenoid-ui status

**v2 closed** (React 18.3.1 + Vite 6 + Vitest 3 + RTL + allure-vitest, yarn-only, Node 26).

**v3 shipped** on [selenoid.qa.guru](https://selenoid.qa.guru) (UI **v3.0.43**; hub **v3.0.13** / cm **v3.0.3**): AppHeader embed, library `Input`/`Badge`, design-system static sync. Отдельного UI 2.x / v2.3+ стенда нет. Deferred leftovers — только по явному запросу, не maintenance UI 2.x в git.
