import unittest

from automator.generator.naming import build_test_names, canonical_class_name
from automator.generator.java_tests import (
    append_method,
    find_equivalent_class,
    load_existing_test_classes,
    normalize_class_file,
    resolve_target_class,
)
from automator.generator.test_java import generate_test_java


class BuildTestNamesTests(unittest.TestCase):
    def test_successful_authorization(self) -> None:
        steps = ["Открыть страницу логина login.html"]
        names = build_test_names("Успешная авторизация с валидными учётными данными", steps, 45118)
        self.assertEqual(names.class_name, "LoginTests")
        self.assertEqual(names.method_name, "successfulAuthorizationTest")
        self.assertEqual(names.feature, "Авторизация")
        self.assertEqual(names.class_display_name, "Авторизация")

    def test_wrong_password_authorization(self) -> None:
        steps = ["Открыть login.html"]
        names = build_test_names("Авторизация не проходит с неверным паролем", steps, 45120)
        self.assertEqual(names.class_name, "LoginTests")
        self.assertEqual(names.method_name, "wrongPasswordAuthorizationTest")

    def test_wrong_password_login(self) -> None:
        steps = ["Открыть login.html"]
        names = build_test_names("Неуспешный логин с неправильным паролем", steps, 45114)
        self.assertEqual(names.class_name, "LoginTests")
        self.assertEqual(names.method_name, "wrongPasswordLoginTest")

    def test_registration_feature(self) -> None:
        steps = ["Открыть registration.html"]
        names = build_test_names("Успешная регистрация нового пользователя", steps, 500)
        self.assertEqual(names.class_name, "RegistrationTests")
        self.assertEqual(names.method_name, "successfulRegistrationTest")
        self.assertEqual(names.feature, "Регистрация")

    def test_method_suffix(self) -> None:
        names = build_test_names("Успешная авторизация с валидными учётными данными", ["login.html"], 45118)
        suffixed = names.with_method_suffix(45118)
        self.assertEqual(suffixed.method_name, "successfulAuthorizationTest45118")
        self.assertEqual(suffixed.class_name, "LoginTests")

    def test_canonical_class_name(self) -> None:
        self.assertEqual(canonical_class_name("SignInTests"), "LoginTests")


class JavaMergeTests(unittest.TestCase):
    SAMPLE_CLASS = """package tests;

public class SignInTests extends TestBase {
    private static final String LOGIN_PAGE = "login.html?ru";

    @Test
    @AllureId("1")
    void existingTest() {
    }
}
"""

    def test_append_method(self) -> None:
        method = """    @Test
    @AllureId("2")
    void newTest() {
    }"""
        merged = append_method(self.SAMPLE_CLASS, method)
        self.assertIn("existingTest", merged)
        self.assertIn("newTest", merged)

    def test_normalize_class_name(self) -> None:
        normalized = normalize_class_file(self.SAMPLE_CLASS, "LoginTests")
        self.assertIn("public class LoginTests extends TestBase", normalized)

    def test_find_equivalent_class(self) -> None:
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tests_dir = Path(tmp)
            (tests_dir / "SignInTests.java").write_text(self.SAMPLE_CLASS, encoding="utf-8")
            existing = load_existing_test_classes(tests_dir)
            match = find_equivalent_class(existing, "LoginTests")
            self.assertIsNotNone(match)
            assert match is not None
            self.assertEqual(match.class_name, "SignInTests")

            _, canonical = resolve_target_class(existing, build_test_names("login", ["login.html"], 1))
            self.assertEqual(canonical, "LoginTests")


class GenerateTestJavaTests(unittest.TestCase):
    def test_generates_login_tests_class(self) -> None:
        generated = generate_test_java(
            45118,
            {"name": "Успешная авторизация с валидными учётными данными"},
            ["Открыть страницу логина login.html"],
        )
        self.assertEqual(generated.names.class_name, "LoginTests")
        self.assertEqual(generated.qualified_test_name, "tests.LoginTests.successfulAuthorizationTest")
        self.assertEqual(generated.names.feature, "Авторизация")
        self.assertIn("successfulAuthorizationTest", generated.method_source)


if __name__ == "__main__":
    unittest.main()
