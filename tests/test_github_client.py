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
    @patch.object(GitHubClient, "ensure_gh_pages_branch")
    def test_ensure_github_pages_enables_legacy_gh_pages(
        self, ensure_branch: MagicMock, enabled: MagicMock
    ) -> None:
        with patch.object(GitHubClient, "_run") as run:
            run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            self.client.ensure_github_pages("demo-5267")
            ensure_branch.assert_called_once_with("demo-5267")
            run.assert_called_once()
            cmd = run.call_args.args[0]
            self.assertEqual(cmd[:4], ["gh", "api", "--method", "POST"])
            self.assertIn("repos/autotests-cloud/demo-5267/pages", cmd)
            self.assertIn("source[branch]=gh-pages", cmd)

    @patch.object(GitHubClient, "github_pages_enabled", return_value=False)
    @patch.object(GitHubClient, "ensure_gh_pages_branch")
    def test_ensure_github_pages_tolerates_already_exists(
        self, ensure_branch: MagicMock, enabled: MagicMock
    ) -> None:
        with patch.object(GitHubClient, "_run") as run:
            run.return_value = MagicMock(
                returncode=422,
                stdout="",
                stderr="GitHub Pages site already exists",
            )
            self.client.ensure_github_pages("demo-5267")

    @patch.object(GitHubClient, "_branch_exists", return_value=False)
    def test_ensure_gh_pages_branch_creates_from_main(self, exists: MagicMock) -> None:
        with patch.object(GitHubClient, "_run") as run:
            run.side_effect = [
                MagicMock(returncode=0, stdout="abc123\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            self.client.ensure_gh_pages_branch("demo-5267")
            self.assertEqual(run.call_count, 2)
            create_cmd = run.call_args_list[1].args[0]
            self.assertIn("ref=refs/heads/gh-pages", create_cmd)
            self.assertIn("sha=abc123", create_cmd)
