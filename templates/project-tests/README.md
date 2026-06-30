# UI tests (Java)

Автотесты для [one-page-form](https://qa-guru.github.io/one-page-form/) на Selenide и JUnit 5.

Bootstrap-шаблон для новых GitHub-репозиториев automator. Эталон для разработки и образец стиля: `tests-java/` в корне automator-репозитория (там же `LoginTests.java` — только для локальной разработки, в новые проекты не копируется).

## Prerequisites

- Java 21
- Google Chrome installed locally

## Run tests

From this directory:

```bash
./gradlew test
```

Run a single test method:

```bash
./gradlew test --tests tests.LoginTests.successfulAuthorizationTest
```

Open the HTML report after a run:

```bash
open build/reports/tests/test/index.html
```

## Project layout

```
src/test/
├── java/
│   ├── tests/
│   │   ├── TestBase.java
│   │   └── {GeneratedTest}.java
│   ├── config/
│   └── annotations/
└── resources/
    └── config/
        └── local.properties
```

## Configuration

Browser settings live in `TestBase.java` and `src/test/resources/config/*.properties`:

- **Browser:** Chrome (default)
- **Window size:** 1920×1280
- **Base URL:** `https://qa-guru.github.io/one-page-form/` (override via `baseUrl` in properties)

## Dependencies

- Selenide 7.16.2
- JUnit Jupiter 5.11.4
