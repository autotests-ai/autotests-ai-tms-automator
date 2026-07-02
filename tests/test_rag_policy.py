import json
import unittest
from pathlib import Path

from automator.generator.test_java import generate_test_java
from automator.rag.loader import bootstrap_chunk_ids
from automator.rag.policy import load_generator_policy, policy_path


REPO_ROOT = Path(__file__).resolve().parents[1]
RAG_DIR = REPO_ROOT / "docs" / "rag"


class GeneratorPolicyTests(unittest.TestCase):
    def test_bootstrap_includes_gen_python_policy(self) -> None:
        self.assertIn("gen-python-policy", bootstrap_chunk_ids())

    def test_load_policy_from_vendored_rag(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        self.assertEqual(policy.locator("login_input"), "login-input")
        self.assertEqual(policy.layer, "e2e")
        self.assertEqual(policy.default_epic, "Одностраничная форма")

    def test_policy_file_exists(self) -> None:
        path = policy_path(RAG_DIR)
        self.assertTrue(path.is_file(), msg=str(path))
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["id"], "gen-python-policy")

    def test_infer_negative_tag(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        self.assertEqual(policy.infer_tag("Авторизация с неверным паролем"), "negative")
        self.assertEqual(policy.infer_tag("Успешная авторизация"), "positive")

    def test_translate_expected_ru_page(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        translated = policy.translate_expected("Wrong login or password", "login.html?ru")
        self.assertEqual(translated, "Неверный логин или пароль")

    def test_normalize_login_page(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        self.assertEqual(policy.normalize_page_path("login.html"), "login.html?ru")


class GenerateWithPolicyTests(unittest.TestCase):
    def test_generated_login_uses_policy_locators(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        generated = generate_test_java(
            45118,
            {"name": "Успешная авторизация с валидными учётными данными"},
            [
                "Открыть страницу логина login.html",
                'Ввести логин "user1"',
                'Ввести пароль "password1"',
                "Нажать кнопку Submit",
                'Проверить текст "Welcome, user1!"',
            ],
            policy=policy,
        )
        login_testid = policy.locator("login_input")
        welcome_testid = policy.locator("welcome_message")
        self.assertIn(f'[data-testid={login_testid}]', generated.method_source)
        self.assertIn(f'[data-testid={welcome_testid}]', generated.method_source)
        self.assertIn('@Tag("positive")', generated.method_source)

    def test_generated_negative_tag(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        generated = generate_test_java(
            45120,
            {"name": "Авторизация не проходит с неверным паролем"},
            ["Открыть login.html"],
            policy=policy,
        )
        self.assertEqual(generated.tag, "negative")

    def test_unquoted_welcome_expected_text(self) -> None:
        policy = load_generator_policy(RAG_DIR)
        generated = generate_test_java(
            45353,
            {"name": "Вход покупателя в личный кабинет интернет-магазина"},
            [
                "Открыть login.html?ru",
                "Ввести логин user1",
                "Ввести пароль password1",
                "Нажать кнопку submit",
                "Проверить приветствие Welcome, user1! в success-panel",
            ],
            policy=policy,
        )
        self.assertIn("Добро пожаловать, user1!", generated.method_source)
        self.assertNotIn('text("...")', generated.method_source)

    def test_catalog_wrong_password_scenario(self) -> None:
        from automator.manual_case_catalog import pick_scenario

        policy = load_generator_policy(RAG_DIR)
        scenario = pick_scenario([])
        generated = generate_test_java(
            46001,
            {"name": scenario.name},
            scenario.step_bodies(),
            policy=policy,
        )
        self.assertEqual(generated.tag, "negative")
        self.assertIn("[data-testid=error-message]", generated.method_source)
        self.assertIn("Неверный логин или пароль", generated.method_source)
        self.assertNotIn("fail(", generated.method_source)

    def test_catalog_success_login_scenario(self) -> None:
        from automator.manual_case_catalog import pick_scenario

        policy = load_generator_policy(RAG_DIR)
        scenario = pick_scenario(["Неуспешный логин с неверным паролем"])
        generated = generate_test_java(
            46002,
            {"name": scenario.name},
            scenario.step_bodies(),
            policy=policy,
        )
        self.assertEqual(generated.tag, "positive")
        self.assertIn("[data-testid=welcome-message]", generated.method_source)
        self.assertIn("Добро пожаловать, user1!", generated.method_source)
        self.assertNotIn("fail(", generated.method_source)


if __name__ == "__main__":
    unittest.main()
