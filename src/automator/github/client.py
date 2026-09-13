import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from automator.errors import AutomationError, RepositoryNotFoundError
from automator.video import VideoCapture, find_selenoid_video_url, scan_tree_for_selenoid_video_url

logger = logging.getLogger(__name__)


def is_repo_not_found(detail: str) -> bool:
    lower = detail.lower()
    return (
        "could not resolve to a repository" in lower
        or "repository not found" in lower
        or "name or repository not known" in lower
    )


def _command_detail(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or "").strip()


def _raise_command_failed(result: subprocess.CompletedProcess[str], action: str) -> None:
    detail = _command_detail(result)
    raise AutomationError(f"{action}: {detail}" if detail else action)


@dataclass
class WorkflowRunInfo:
    run_id: int
    run_url: str
    status: str
    conclusion: str | None
    report_url: str | None


# Curriculum catalog cell (GitHub template). Runtime repos live in autotests-cloud.
DEFAULT_TEMPLATE_REPO = "autotests-ai/java-junit5-rest_assured-selenide"
RUNTIME_WORKFLOW_FILE = "selenoid-qa-guru_github.yml"


class GitHubClient:
    def __init__(
        self,
        org: str,
        *,
        repo_public: bool = True,
        template_repo: str = DEFAULT_TEMPLATE_REPO,
        runtime_workflow: Path | None = None,
    ) -> None:
        self._org = org
        self._repo_public = repo_public
        self._template_repo = template_repo
        self._runtime_workflow = runtime_workflow

    def _run(
        self,
        cmd: list[str],
        *,
        cwd: Path | None = None,
        action: str | None = None,
        check: bool = True,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        if check and result.returncode != 0:
            _raise_command_failed(result, action or " ".join(cmd))
        return result

    def _git_remote_url(self, repo_full: str) -> str:
        token = self._run(["gh", "auth", "token"], action="gh auth token").stdout.strip()
        return f"https://x-access-token:{token}@github.com/{repo_full}.git"

    def repo_exists(self, repo_name: str) -> bool:
        result = subprocess.run(
            ["gh", "repo", "view", f"{self._org}/{repo_name}", "--json", "name"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def github_pages_enabled(self, repo_name: str) -> bool:
        repo_full = f"{self._org}/{repo_name}"
        result = subprocess.run(
            ["gh", "api", f"repos/{repo_full}/pages"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def _branch_exists(self, repo_name: str, branch: str) -> bool:
        repo_full = f"{self._org}/{repo_name}"
        result = subprocess.run(
            ["gh", "api", f"repos/{repo_full}/branches/{branch}"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def ensure_gh_pages_branch(self, repo_name: str) -> None:
        """Create ``gh-pages`` from ``main`` when missing (required before Pages enable)."""
        repo_full = f"{self._org}/{repo_name}"
        if self._branch_exists(repo_name, "gh-pages"):
            return

        main_ref = self._run(
            ["gh", "api", f"repos/{repo_full}/git/ref/heads/main", "--jq", ".object.sha"],
            action=f"resolve main SHA for {repo_full}",
        )
        sha = main_ref.stdout.strip()
        if not sha:
            raise AutomationError(f"Could not resolve main SHA for {repo_full}")

        create = self._run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"repos/{repo_full}/git/refs",
                "-f",
                "ref=refs/heads/gh-pages",
                "-f",
                f"sha={sha}",
            ],
            check=False,
            action=f"create gh-pages branch for {repo_full}",
        )
        if create.returncode == 0:
            logger.info("Created gh-pages branch for %s from main", repo_full)
            return
        detail = _command_detail(create).lower()
        if "reference already exists" in detail or "already exists" in detail:
            return
        _raise_command_failed(create, f"create gh-pages branch for {repo_full}")

    def ensure_github_pages(self, repo_name: str) -> None:
        """Enable GitHub Pages from gh-pages branch (idempotent)."""
        repo_full = f"{self._org}/{repo_name}"
        if self.github_pages_enabled(repo_name):
            logger.debug("GitHub Pages already enabled for %s", repo_full)
            return

        self.ensure_gh_pages_branch(repo_name)

        result = self._run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"repos/{repo_full}/pages",
                "-f",
                "build_type=legacy",
                "-f",
                "source[branch]=gh-pages",
                "-f",
                "source[path]=/",
            ],
            check=False,
            action=f"enable GitHub Pages for {repo_full}",
        )
        if result.returncode == 0:
            logger.info(
                "Enabled GitHub Pages for %s → https://%s.github.io/%s/",
                repo_full,
                self._org,
                repo_name,
            )
            return

        detail = _command_detail(result).lower()
        if "already exists" in detail or "already enabled" in detail:
            return
        _raise_command_failed(result, f"enable GitHub Pages for {repo_full}")

    def _wait_for_template_contents(self, repo_name: str, timeout_sec: int = 90) -> None:
        """GitHub fills template repos asynchronously; clone before contents → empty tree."""
        repo_full = f"{self._org}/{repo_name}"
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo_full}/contents"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                try:
                    payload = json.loads(result.stdout or "[]")
                except json.JSONDecodeError:
                    payload = []
                if isinstance(payload, list) and payload:
                    return
            time.sleep(2)
        raise AutomationError(f"Timed out waiting for template contents in {repo_full}")

    @staticmethod
    def _workdir_bootstrapped(workdir: Path) -> bool:
        return (workdir / "build.gradle").is_file() or (workdir / "build.gradle.kts").is_file()

    def _configure_allure_ci(
        self,
        repo_name: str,
        allure_project_id: int,
        allure_endpoint: str,
        allure_token: str,
    ) -> None:
        repo_full = f"{self._org}/{repo_name}"
        self._run(
            ["gh", "variable", "set", "ALLURE_PROJECT_ID", "--body", str(allure_project_id), "-R", repo_full],
            action=f"gh variable set ALLURE_PROJECT_ID for {repo_full}",
        )
        self._run(
            ["gh", "variable", "set", "ALLURE_ENDPOINT", "--body", allure_endpoint.rstrip("/"), "-R", repo_full],
            action=f"gh variable set ALLURE_ENDPOINT for {repo_full}",
        )
        self._run(
            ["gh", "secret", "set", "ALLURE_TOKEN", "--body", allure_token, "-R", repo_full],
            action=f"gh secret set ALLURE_TOKEN for {repo_full}",
        )

    def _runtime_workflow_path(self, workdir: Path) -> Path:
        return workdir / ".github" / "workflows" / RUNTIME_WORKFLOW_FILE

    def _ensure_runtime_workflow(self, repo_name: str, workdir: Path) -> None:
        """Catalog cell has composite actions but no dispatch workflow. Overlay without force-push."""
        dest = self._runtime_workflow_path(workdir)
        if dest.is_file():
            return
        source = self._runtime_workflow
        if source is None or not Path(source).is_file():
            raise AutomationError(
                f"{self._org}/{repo_name} has no {RUNTIME_WORKFLOW_FILE} after template clone. "
                "Set runtime_workflow to templates/tests-java/.github/workflows/"
                f"{RUNTIME_WORKFLOW_FILE}."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        rel = dest.relative_to(workdir).as_posix()
        repo_full = f"{self._org}/{repo_name}"
        self._run(["git", "add", rel], cwd=workdir, action=f"git add {rel}")
        commit = self._run(
            [
                "git",
                "commit",
                "-m",
                f"Add runtime workflow {RUNTIME_WORKFLOW_FILE} from automator\n\n[skip ci]",
            ],
            cwd=workdir,
            check=False,
            action=f"git commit workflow for {repo_full}",
        )
        if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
            _raise_command_failed(commit, f"Git commit workflow to {repo_full} failed")
        if commit.returncode != 0:
            return
        self._run(
            ["git", "push", "origin", "main"],
            cwd=workdir,
            action=f"git push workflow to {repo_full}",
        )

    def create_repo_from_template(
        self,
        repo_name: str,
        workdir: Path,
        allure_project_id: int,
        allure_endpoint: str,
        allure_token: str,
        description: str,
        template_repo: str | None = None,
    ) -> str:
        """Create runtime repo via ``gh repo create --template`` (catalog cell).

        Does not trim ``templates/tests-java`` and does not ``git push --force``.
        """
        repo_full = f"{self._org}/{repo_name}"
        repo_url = f"https://github.com/{repo_full}"
        template = template_repo or self._template_repo
        created = False

        if not self.repo_exists(repo_name):
            create_cmd = [
                "gh",
                "repo",
                "create",
                repo_full,
                "--template",
                template,
                "--description",
                description,
            ]
            if self._repo_public:
                create_cmd.append("--public")
            else:
                create_cmd.append("--private")
            result = self._run(create_cmd, check=False, action=f"gh repo create {repo_full}")
            if result.returncode != 0:
                if "already exists" not in _command_detail(result).lower():
                    hint = "Check org access (autotests-cloud may block private repos due to trade controls)."
                    detail = _command_detail(result)
                    raise AutomationError(
                        f"Failed to create repo {repo_full} from template {template}: {detail}. {hint}"
                        if detail
                        else f"Failed to create repo {repo_full} from template {template}. {hint}"
                    )
            else:
                created = True
                logger.info("Created GitHub repo %s from template %s", repo_url, template)

        if created:
            self._wait_for_template_contents(repo_name)

        self.clone_repo(repo_name, workdir)
        if not self._workdir_bootstrapped(workdir) and created:
            self._wait_for_template_contents(repo_name)
            self.clone_repo(repo_name, workdir)
        if not self._workdir_bootstrapped(workdir):
            raise AutomationError(
                f"{repo_full} has no Gradle build after clone. Runtime repos must come from "
                f"`gh repo create --template {template}`; automator does not force-push "
                "trimmed templates/tests-java."
            )
        self._ensure_runtime_workflow(repo_name, workdir)
        self._configure_allure_ci(repo_name, allure_project_id, allure_endpoint, allure_token)
        self.ensure_github_pages(repo_name)
        return repo_url

    def clone_repo(self, repo_name: str, workdir: Path) -> None:
        repo_full = f"{self._org}/{repo_name}"
        workdir.parent.mkdir(parents=True, exist_ok=True)
        if workdir.exists():
            shutil.rmtree(workdir)
        clone = self._run(
            ["gh", "repo", "clone", repo_full, str(workdir), "--", "--depth", "1"],
            action=f"gh repo clone {repo_full}",
            check=False,
        )
        if clone.returncode != 0:
            detail = _command_detail(clone)
            if is_repo_not_found(detail):
                raise RepositoryNotFoundError(f"gh repo clone {repo_full}: {detail}")
            _raise_command_failed(clone, f"gh repo clone {repo_full}")
        self._run(
            ["git", "remote", "set-url", "origin", self._git_remote_url(repo_full)],
            cwd=workdir,
            action="git remote set-url",
        )

    def push_test_file(
        self,
        repo_name: str,
        workdir: Path,
        relative_path: str,
        content: str,
        message: str,
        remove_paths: list[str] | None = None,
    ) -> None:
        repo_full = f"{self._org}/{repo_name}"
        self._run(
            ["git", "remote", "set-url", "origin", self._git_remote_url(repo_full)],
            cwd=workdir,
            action="git remote set-url",
        )
        pull = self._run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=workdir,
            check=False,
            action=f"git pull from {repo_full}",
        )
        if pull.returncode != 0 and "no tracking information" not in _command_detail(pull).lower():
            logger.warning("git pull failed for %s: %s", repo_full, _command_detail(pull))
        target = workdir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._run(["git", "add", relative_path], cwd=workdir, action="git add")
        for path in remove_paths or []:
            full_path = workdir / path
            if full_path.exists():
                full_path.unlink()
            self._run(["git", "add", path], cwd=workdir, action=f"git add {path}")
        commit_message = message if "[skip ci]" in message.lower() else f"{message}\n\n[skip ci]"
        self._run(["git", "commit", "-m", commit_message], cwd=workdir, action="git commit")
        self._run(["git", "push", "origin", "main"], cwd=workdir, action=f"git push to {repo_full}")

    def _latest_dispatch_run_id(self, repo_full: str) -> int | None:
        result = self._run(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                RUNTIME_WORKFLOW_FILE,
                "-R",
                repo_full,
                "--event",
                "workflow_dispatch",
                "--limit",
                "5",
                "--json",
                "databaseId",
            ],
            action=f"gh run list for {repo_full}",
        )
        runs = json.loads(result.stdout or "[]")
        if not runs:
            return None
        return max(int(run["databaseId"]) for run in runs if run.get("databaseId") is not None)

    def dispatch_workflow(
        self,
        repo_name: str,
        test_class: str | None = None,
        test_case_id: int | None = None,
    ) -> WorkflowRunInfo:
        repo_full = f"{self._org}/{repo_name}"
        before_run_id = self._latest_dispatch_run_id(repo_full)
        cmd = ["gh", "workflow", "run", RUNTIME_WORKFLOW_FILE, "-R", repo_full]
        if test_class:
            cmd.extend(["-f", f"test_class={test_class}"])
        if test_case_id is not None:
            cmd.extend(["-f", f"test_case_id={test_case_id}"])
        self._run(cmd, action=f"gh workflow run {RUNTIME_WORKFLOW_FILE} for {repo_full}")

        list_cmd = [
            "gh",
            "run",
            "list",
            "--workflow",
            RUNTIME_WORKFLOW_FILE,
            "-R",
            repo_full,
            "--event",
            "workflow_dispatch",
            "--limit",
            "5",
            "--json",
            "databaseId,url,status,conclusion",
        ]
        # gh run list can briefly still show the previous completed dispatch —
        # only accept a run newer than the pre-dispatch snapshot.
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            result = self._run(
                list_cmd,
                action=f"gh run list for {repo_full}",
            )
            runs = json.loads(result.stdout or "[]")
            for run in runs:
                run_id = int(run["databaseId"])
                if before_run_id is not None and run_id <= before_run_id:
                    continue
                if run.get("status") in {"queued", "in_progress", "completed", "waiting"}:
                    return WorkflowRunInfo(
                        run_id=run_id,
                        run_url=run["url"],
                        status=run["status"],
                        conclusion=run.get("conclusion"),
                        report_url=None,
                    )
            time.sleep(2)

        raise AutomationError(f"Timed out waiting for workflow_dispatch run in {repo_full}")

    def wait_for_run(self, repo_name: str, run_id: int, timeout_sec: int = 900) -> WorkflowRunInfo:
        repo_full = f"{self._org}/{repo_name}"
        self._run(
            ["gh", "run", "watch", str(run_id), "-R", repo_full, "--exit-status"],
            check=False,
            timeout=timeout_sec,
            action=f"gh run watch {run_id} for {repo_full}",
        )
        result = self._run(
            ["gh", "run", "view", str(run_id), "-R", repo_full, "--json", "databaseId,url,status,conclusion"],
            action=f"gh run view {run_id} for {repo_full}",
        )
        run = json.loads(result.stdout)
        repo_short = repo_name
        report_url = f"https://{self._org}.github.io/{repo_short}/reports/{run_id}/awesome/index.html"
        return WorkflowRunInfo(
            run_id=int(run["databaseId"]),
            run_url=run["url"],
            status=run["status"],
            conclusion=run.get("conclusion"),
            report_url=report_url,
        )

    def extract_selenoid_video_url_from_run_log(self, repo_name: str, run_id: int) -> str | None:
        repo_full = f"{self._org}/{repo_name}"
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "-R", repo_full, "--log"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return None
        log_text = result.stdout or result.stderr or ""
        url = find_selenoid_video_url(log_text)
        if url:
            return url
        for line in log_text.splitlines():
            if "VIDEO_URL=" not in line:
                continue
            match = re.search(r"VIDEO_URL=(https://[^\s]+)", line)
            if match:
                return match.group(1).rstrip("`")
        return None

    def download_video_artifact(
        self,
        repo_name: str,
        run_id: int,
        destination: Path,
    ) -> VideoCapture:
        repo_full = f"{self._org}/{repo_name}"
        selenoid_url = self.extract_selenoid_video_url_from_run_log(repo_name, run_id)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = subprocess.run(
                ["gh", "run", "download", str(run_id), "-R", repo_full, "-D", tmp],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                selenoid_url = selenoid_url or scan_tree_for_selenoid_video_url(tmp_path)
                for mp4 in tmp_path.rglob("*.mp4"):
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(mp4, destination)
                    return VideoCapture(
                        path=destination,
                        selenoid_url=selenoid_url,
                        attachment_name=mp4.name,
                    )
        return VideoCapture(path=None, selenoid_url=selenoid_url)
