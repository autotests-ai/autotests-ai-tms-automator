from unittest import TestCase
from unittest.mock import MagicMock, patch

from automator.github.client import GitHubClient


class GitHubPagesTests(TestCase):
    def setUp(self) -> None:
        self.client = GitHubClient("autotests-cloud")

    @patch.object(GitHubClient, "github_pages_enabled", return_value=True)
    def test_ensure_github_pages_skips_when_already_enabled(self, enabled: MagicMock) -> None:
        with patch.object(GitHubClient, "_run") as run:
            self.client.ensure_github_pages("demo-5267")
            run.assert_not_called()

    @patch.object(GitHubClient, "github_pages_enabled", return_value=False)
    def test_ensure_github_pages_enables_legacy_gh_pages(self, enabled: MagicMock) -> None:
        with patch.object(GitHubClient, "_run") as run:
            run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            self.client.ensure_github_pages("demo-5267")
            run.assert_called_once()
            cmd = run.call_args.args[0]
            self.assertEqual(cmd[:4], ["gh", "api", "--method", "POST"])
            self.assertIn("repos/autotests-cloud/demo-5267/pages", cmd)
            self.assertIn("source[branch]=gh-pages", cmd)

    @patch.object(GitHubClient, "github_pages_enabled", return_value=False)
    def test_ensure_github_pages_tolerates_already_exists(self, enabled: MagicMock) -> None:
        with patch.object(GitHubClient, "_run") as run:
            run.return_value = MagicMock(
                returncode=422,
                stdout="",
                stderr="GitHub Pages site already exists",
            )
            self.client.ensure_github_pages("demo-5267")
