import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from automator.config import Settings
from automator.links import (
    WORKFLOW_DIAGRAM_FILENAME,
    format_creation_comment,
    format_links_markdown,
    format_workflow_onboarding_markdown,
    github_blob_url,
    predict_test_names,
    resolve_automation_links,
    testops_test_case_url,
)


class LinksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            allure_api_token="token",
            allure_endpoint="https://allure.example.test",
            github_org="autotests-cloud",
        )

    def test_testops_url(self) -> None:
        url = testops_test_case_url(self.settings, 5267, 45118)
        self.assertEqual(url, "https://allure.example.test/project/5267/test-cases/45118")

    def test_github_blob_with_line(self) -> None:
        url = github_blob_url("autotests-cloud", "repo-5267", "src/test/java/tests/LoginTests.java", line=25)
        self.assertIn("/blob/main/src/test/java/tests/LoginTests.java#L25", url)

    def test_format_created_phase(self) -> None:
        links = resolve_automation_links(
            self.settings,
            5267,
            99,
            repo_name="repo-5267",
            test_case={"name": "Неуспешный логин с неверным паролем", "automated": False},
            step_bodies=["Открыть login.html?ru"],
        )
        md = format_links_markdown(links, phase="created")
        self.assertIn("TestOps", md)
        self.assertIn("появится после", md)
        self.assertIn("wrongPassword", md)
        self.assertIn("](https://github.com/autotests-cloud/repo-5267/blob/main/", md)

    def test_format_workflow_onboarding_embeds_attachment(self) -> None:
        md = format_workflow_onboarding_markdown(
            attachment_content_path="/api/testcase/attachment/5470/content",
        )
        self.assertIn("![Путь тест-кейса: от черновика до автоматизации](/api/testcase/attachment/5470/content)", md)
        self.assertIn("Автоматизированные тесты", md)
        self.assertNotIn("workflow =", md)

    def test_format_creation_comment(self) -> None:
        links = resolve_automation_links(
            self.settings,
            5269,
            45118,
            repo_name="Automator-Sandbox-5269",
            test_case={"name": "Переключение языка в шапке login.html", "automated": False},
            step_bodies=["Открыть login.html?ru"],
        )
        md = format_creation_comment(
            links,
            attachment_content_path="/api/testcase/attachment/5470/content",
        )
        self.assertIn("/api/testcase/attachment/5470/content", md)
        self.assertIn("give-manual-testcase", md)
        self.assertIn("[45118](https://allure.example.test/project/5269/test-cases/45118)", md)
        self.assertIn("Код автотеста (прогноз):", md)
        self.assertIn("](https://github.com/autotests-cloud/Automator-Sandbox-5269/blob/main/", md)
        self.assertNotIn("`Automator-Sandbox-5269`", md)

    def test_grep_allure_id_local(self) -> None:
        with TemporaryDirectory() as tmp:
            projects_dir = Path(tmp)
            repo_root = projects_dir / "repo-5267"
            test_file = repo_root / "src/test/java/tests/LoginTests.java"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                'class LoginTests {\n    @AllureId("777")\n    void demoTest() {}\n}\n',
                encoding="utf-8",
            )
            links = resolve_automation_links(
                self.settings,
                5267,
                777,
                repo_name="repo-5267",
                projects_dir=projects_dir,
            )
            self.assertIsNotNone(links.github_code_url)
            self.assertIn("LoginTests.java#L2", links.github_code_url or "")


if __name__ == "__main__":
    unittest.main()
