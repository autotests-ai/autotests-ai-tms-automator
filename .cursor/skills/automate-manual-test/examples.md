# Examples: manual case → generated autotest

**Etalon infra + PO:** `templates/tests-java/src/test/java/tests/LoginTests.java` (`shouldLoginWithValidCredentials`)  
**Generated style:** step + `[data-testid=…]` — `src/automator/generator/test_java.py`  
**Output:** `projects/{repo_name}/src/test/java/tests/`

## Example — TestOps #45118

**Manual case:** Успешная авторизация с валидными учётными данными

| Поле | Значение |
|------|----------|
| `@Feature` | Авторизация |
| Класс | `LoginTests` |
| Метод | `successfulAuthorizationTest` |

```bash
cd qa-guru-tms-automator/projects/qa_guru_automator_ethalon-5267
./gradlew test --tests tests.LoginTests.successfulAuthorizationTest -Denv=ci
```

## Example — второй кейс в том же классе

Automator **добавляет** метод в существующий `LoginTests.java`, не создаёт `SignInTests`.

## Equivalent classes (merge into one)

| Не создавать | Использовать |
|--------------|--------------|
| `SignInTests`, `AuthTests` | `LoginTests` |
| `SignUpTests`, `RegisterTests` | `RegistrationTests` |
