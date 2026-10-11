import json
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import MagicMock, patch
from urllib.parse import urlsplit

from automator.config import Settings
from automator.errors import AutomationError
from automator.github.client import DEFAULT_TEMPLATE_REPO, GitHubClient, RUNTIME_WORKFLOW_FILE

FAKE_GH_TOKEN = "gho_fake-token-for-tests"
GH_CREDENTIAL_HELPER_ARGS = [
    "-c",
    "credential.https://github.com.helper=",
    "-c",
    "credential.https://github.com.helper=!gh auth git-credential",
]
GIT_TEST_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "automator-test",
    "GIT_AUTHOR_EMAIL": "automator-test@example.invalid",
    "GIT_COMMITTER_NAME": "automator-test",
    "GIT_COMMITTER_EMAIL": "automator-test@example.invalid",
}


def _git_args(cmd: list[str]) -> list[str]:
    if cmd[:1] != ["git"]:
        return cmd
    rest = cmd[1:]
    while rest[:1] == ["-c"]:
        rest = rest[2:]
    return ["git", *rest]


class DispatchWorkflowTests(TestCase):
    def setUp(self) -> None:
        self.client = GitHubClient("autotests-cloud")

    def test_dispatch_waits_for_run_newer_than_pre_dispatch_snapshot(self) -> None:
        old_run = {"databaseId": 100, "url": "https://example/100", "status": "completed", "conclusion": "success"}
        new_run = {"databaseId": 101, "url": "https://example/101", "status": "queued", "conclusion": None}

        with patch.object(GitHubClient, "_run") as run:
            run.side_effect = [
                MagicMock(returncode=0, stdout=json.dumps([old_run]), stderr=""),  # before snapshot
                MagicMock(returncode=0, stdout="", stderr=""),  # workflow run
                MagicMock(returncode=0, stdout=json.dumps([old_run]), stderr=""),  # still old
                MagicMock(returncode=0, stdout=json.dumps([new_run, old_run]), stderr=""),  # new appears
            ]
            with patch("automator.github.client.time.sleep"):
                info = self.client.dispatch_workflow("demo-5298", test_class="tests.LoginTests.x", test_case_id=47326)

        self.assertEqual(info.run_id, 101)
        self.assertEqual(info.status, "queued")
        dispatch_cmd = run.call_args_list[1].args[0]
        self.assertEqual(dispatch_cmd[:4], ["gh", "workflow", "run", RUNTIME_WORKFLOW_FILE])
        self.assertIn("test_case_id=47326", dispatch_cmd)


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


class CreateRepoFromTemplateTests(TestCase):
    def setUp(self) -> None:
        self.client = GitHubClient(
            "autotests-cloud",
            template_repo=DEFAULT_TEMPLATE_REPO,
        )

    def test_settings_default_template_is_catalog_cell(self) -> None:
        settings = Settings(allure_api_token="token", _env_file=None)
        self.assertEqual(settings.github_template, DEFAULT_TEMPLATE_REPO)
        self.assertEqual(settings.github_org, "autotests-cloud")

    def _fake_clone(self, _repo_name: str, workdir: Path) -> None:
        workdir.mkdir(parents=True, exist_ok=True)
        (workdir / "build.gradle").write_text("plugins {}\n", encoding="utf-8")

    def _write_workflow_src(self, tmp: Path) -> Path:
        src = tmp / RUNTIME_WORKFLOW_FILE
        src.write_text("name: probe\non:\n  workflow_dispatch:\n", encoding="utf-8")
        return src

    def _create(self, workdir: Path, **kwargs):
        defaults = dict(
            repo_name="demo-5298",
            workdir=workdir,
            allure_project_id=5298,
            allure_endpoint="https://allure.qa.guru",
            allure_token="token",
            description="UI autotests for Allure TestOps project 5298 (demo)",
        )
        defaults.update(kwargs)
        return self.client.create_repo_from_template(**defaults)

    def _create_with_workflow_src(self, tmp: Path, workdir: Path, **kwargs):
        self.client._runtime_workflow = self._write_workflow_src(tmp)
        return self._create(workdir, **kwargs)

    def test_create_uses_catalog_cell_template_not_force_push(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=False),
                patch.object(GitHubClient, "_wait_for_template_contents") as wait,
                patch.object(GitHubClient, "clone_repo", side_effect=self._fake_clone) as clone,
                patch.object(GitHubClient, "ensure_github_pages") as pages,
                patch.object(GitHubClient, "_run") as run,
            ):
                run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                url = self._create_with_workflow_src(tmp_path, workdir)
                self.assertEqual(url, "https://github.com/autotests-cloud/demo-5298")
                create_cmd = run.call_args_list[0].args[0]
                self.assertEqual(create_cmd[:4], ["gh", "repo", "create", "autotests-cloud/demo-5298"])
                self.assertEqual(create_cmd[create_cmd.index("--template") + 1], DEFAULT_TEMPLATE_REPO)
                self.assertIn("--public", create_cmd)
                wait.assert_called_once_with("demo-5298")
                clone.assert_called_once_with("demo-5298", workdir)
                pages.assert_called_once_with("demo-5298")
                self.assertTrue((workdir / ".github/workflows" / RUNTIME_WORKFLOW_FILE).is_file())
                cmds = [call.args[0] for call in run.call_args_list]

        self.assertTrue(
            any(cmd[:4] == ["gh", "variable", "set", "ALLURE_PROJECT_ID"] for cmd in cmds)
        )
        self.assertTrue(
            any(_git_args(cmd)[:3] == ["git", "push", "origin"] and "--force" not in cmd for cmd in cmds)
        )
        for cmd in cmds:
            self.assertNotIn("--force", cmd)
            self.assertNotEqual(cmd[:2], ["git", "init"])

    def test_create_skips_gh_create_when_repo_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=True),
                patch.object(GitHubClient, "_wait_for_template_contents") as wait,
                patch.object(GitHubClient, "clone_repo", side_effect=self._fake_clone) as clone,
                patch.object(GitHubClient, "ensure_github_pages"),
                patch.object(GitHubClient, "_run") as run,
            ):
                run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                self._create_with_workflow_src(tmp_path, workdir)

        wait.assert_not_called()
        clone.assert_called_once()
        cmds = [call.args[0] for call in run.call_args_list]
        self.assertFalse(any(cmd[:3] == ["gh", "repo", "create"] for cmd in cmds))
        for cmd in cmds:
            self.assertNotIn("--force", cmd)

    def test_create_tolerates_already_exists_without_force_push(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=False),
                patch.object(GitHubClient, "_wait_for_template_contents") as wait,
                patch.object(GitHubClient, "clone_repo", side_effect=self._fake_clone),
                patch.object(GitHubClient, "ensure_github_pages"),
                patch.object(GitHubClient, "_run") as run,
            ):
                def side_effect(cmd, **_kwargs):
                    if cmd[:3] == ["gh", "repo", "create"]:
                        return MagicMock(
                            returncode=1,
                            stdout="",
                            stderr="Name already exists on this account",
                        )
                    return MagicMock(returncode=0, stdout="", stderr="")

                run.side_effect = side_effect
                url = self._create_with_workflow_src(tmp_path, workdir)

        self.assertEqual(url, "https://github.com/autotests-cloud/demo-5298")
        wait.assert_not_called()
        cmds = [call.args[0] for call in run.call_args_list]
        for cmd in cmds:
            self.assertNotIn("--force", cmd)

    def test_create_private_uses_private_flag(self) -> None:
        self.client = GitHubClient("autotests-cloud", repo_public=False)
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=False),
                patch.object(GitHubClient, "_wait_for_template_contents"),
                patch.object(GitHubClient, "clone_repo", side_effect=self._fake_clone),
                patch.object(GitHubClient, "ensure_github_pages"),
                patch.object(GitHubClient, "_run") as run,
            ):
                run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                self._create_with_workflow_src(tmp_path, workdir)

        create_cmd = run.call_args_list[0].args[0]
        self.assertIn("--private", create_cmd)
        self.assertNotIn("--public", create_cmd)

    def test_create_rejects_empty_clone_instead_of_force_pushing_trim(self) -> None:
        with TemporaryDirectory() as tmp:
            workdir = Path(tmp) / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=True),
                patch.object(GitHubClient, "clone_repo") as clone,
                patch.object(GitHubClient, "ensure_github_pages") as pages,
                patch.object(GitHubClient, "_run") as run,
            ):
                clone.side_effect = lambda _name, dest: dest.mkdir(parents=True, exist_ok=True)
                with self.assertRaises(AutomationError) as raised:
                    self._create(workdir)

        self.assertIn("--template", str(raised.exception))
        self.assertIn("force-push", str(raised.exception).lower())
        pages.assert_not_called()
        run.assert_not_called()

    def test_create_skips_workflow_overlay_when_already_present(self) -> None:
        def clone_with_workflow(_name: str, dest: Path) -> None:
            self._fake_clone(_name, dest)
            wf = dest / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / RUNTIME_WORKFLOW_FILE).write_text("name: from-template\n", encoding="utf-8")

        with TemporaryDirectory() as tmp:
            workdir = Path(tmp) / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=True),
                patch.object(GitHubClient, "clone_repo", side_effect=clone_with_workflow),
                patch.object(GitHubClient, "ensure_github_pages"),
                patch.object(GitHubClient, "_run") as run,
            ):
                run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                self._create(workdir)

        cmds = [call.args[0] for call in run.call_args_list]
        self.assertFalse(any(cmd[:2] == ["git", "commit"] for cmd in cmds))
        self.assertFalse(any(_git_args(cmd)[:2] == ["git", "push"] for cmd in cmds))

    def test_allure_token_reaches_gh_secret_via_stdin_not_argv(self) -> None:
        with patch.object(GitHubClient, "_run") as run:
            run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            self.client._configure_allure_ci("demo-5298", 5298, "https://allure.qa.guru/", "allure-secret")

        secret_calls = [c for c in run.call_args_list if c.args[0][:4] == ["gh", "secret", "set", "ALLURE_TOKEN"]]
        self.assertEqual(len(secret_calls), 1)
        self.assertNotIn("--body", secret_calls[0].args[0])
        self.assertEqual(secret_calls[0].kwargs["stdin"], "allure-secret")
        for c in run.call_args_list:
            self.assertNotIn("allure-secret", c.args[0])


@skipUnless(shutil.which("git"), "git is required")
class GitRemoteCredentialsTests(TestCase):
    def setUp(self) -> None:
        self.client = GitHubClient("autotests-cloud")
        self.commands: list[list[str]] = []
        env = patch.dict(os.environ, GIT_TEST_ENV)
        env.start()
        self.addCleanup(env.stop)

    @staticmethod
    def _git(cwd: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    def _init_template(self, path: Path) -> Path:
        path.mkdir(parents=True)
        (path / "build.gradle").write_text("plugins {}\n", encoding="utf-8")
        self._git(path, "init", "--quiet", "-b", "main")
        self._git(path, "add", ".")
        self._git(path, "commit", "--quiet", "-m", "template")
        return path

    def _fake_github(self, template: Path):
        real_run = GitHubClient._run

        def run(client: GitHubClient, cmd: list[str], **kwargs):
            self.commands.append(list(cmd))
            if cmd[:3] == ["gh", "auth", "token"]:
                return subprocess.CompletedProcess(cmd, 0, f"{FAKE_GH_TOKEN}\n", "")
            if cmd[:3] == ["gh", "repo", "clone"]:
                return real_run(client, ["git", "clone", "--quiet", str(template), cmd[4]])
            if cmd[0] == "gh" or _git_args(cmd)[1:2] in (["push"], ["pull"]):
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return real_run(client, cmd, **kwargs)

        return patch.object(GitHubClient, "_run", autospec=True, side_effect=run)

    def _assert_origin_has_no_credentials(self, workdir: Path) -> None:
        origin = self._git(workdir, "remote", "get-url", "origin")
        parts = urlsplit(origin)
        self.assertEqual(origin, "https://github.com/autotests-cloud/demo-5298.git")
        self.assertIsNone(parts.username)
        self.assertIsNone(parts.password)
        config = (workdir / ".git" / "config").read_text(encoding="utf-8")
        self.assertNotIn(FAKE_GH_TOKEN, config)
        self.assertNotIn("x-access-token", config)
        for cmd in self.commands:
            self.assertFalse(any(FAKE_GH_TOKEN in arg for arg in cmd), cmd)

    def _assert_remote_ops_use_gh_credential_helper(self, *subcommands: str) -> None:
        remote_ops = [cmd for cmd in self.commands if cmd[:1] == ["git"] and _git_args(cmd)[1] in subcommands]
        self.assertEqual({_git_args(cmd)[1] for cmd in remote_ops}, set(subcommands))
        for cmd in remote_ops:
            self.assertEqual(cmd[1:5], GH_CREDENTIAL_HELPER_ARGS)

    def test_create_from_template_leaves_origin_without_login_or_token(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            template = self._init_template(tmp_path / "template")
            workflow = tmp_path / RUNTIME_WORKFLOW_FILE
            workflow.write_text("name: probe\non:\n  workflow_dispatch:\n", encoding="utf-8")
            self.client._runtime_workflow = workflow
            workdir = tmp_path / "projects" / "demo-5298"
            with (
                patch.object(GitHubClient, "repo_exists", return_value=False),
                patch.object(GitHubClient, "_wait_for_template_contents"),
                patch.object(GitHubClient, "ensure_github_pages"),
                self._fake_github(template),
            ):
                self.client.create_repo_from_template(
                    repo_name="demo-5298",
                    workdir=workdir,
                    allure_project_id=5298,
                    allure_endpoint="https://allure.qa.guru",
                    allure_token="token",
                    description="UI autotests for Allure TestOps project 5298 (demo)",
                )
            self._assert_origin_has_no_credentials(workdir)
        self._assert_remote_ops_use_gh_credential_helper("push")

    def test_push_test_file_replaces_legacy_token_remote(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            template = self._init_template(tmp_path / "template")
            workdir = tmp_path / "projects" / "demo-5298"
            self._git(tmp_path, "clone", "--quiet", str(template), str(workdir))
            self._git(
                workdir,
                "remote",
                "set-url",
                "origin",
                f"https://x-access-token:{FAKE_GH_TOKEN}@github.com/autotests-cloud/demo-5298.git",
            )
            with self._fake_github(template):
                self.client.push_test_file(
                    repo_name="demo-5298",
                    workdir=workdir,
                    relative_path="src/test/java/tests/LoginTests.java",
                    content="class LoginTests {}\n",
                    message="Add LoginTests",
                )
            self._assert_origin_has_no_credentials(workdir)
        self._assert_remote_ops_use_gh_credential_helper("pull", "push")
