"""URL builders and link resolution for TestOps ↔ GitHub automation."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from automator.config import Settings
from automator.generator.naming import TestNames, build_test_names


@dataclass(frozen=True)
class AutomationLinks:
    project_id: int
    test_case_id: int
    testops_url: str
    github_repo_full: str
    github_code_url: str | None
    github_code_path: str | None
    github_code_line: int | None
    qualified_test_name: str | None
    ci_run_url: str | None
    ci_run_conclusion: str | None
    allure_report_url: str | None
    automated: bool
    status_name: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "test_case_id": self.test_case_id,
            "testops_url": self.testops_url,
            "github_repo_full": self.github_repo_full,
            "github_code_url": self.github_code_url,
            "github_code_path": self.github_code_path,
            "github_code_line": self.github_code_line,
            "qualified_test_name": self.qualified_test_name,
            "ci_run_url": self.ci_run_url,
            "ci_run_conclusion": self.ci_run_conclusion,
            "allure_report_url": self.allure_report_url,
            "automated": self.automated,
            "status_name": self.status_name,
        }


def testops_test_case_url(settings: Settings, project_id: int, test_case_id: int) -> str:
    return f"{settings.allure_endpoint.rstrip('/')}/project/{project_id}/test-cases/{test_case_id}"


def github_blob_url(
    org: str,
    repo_name: str,
    relative_path: str,
    *,
    branch: str = "main",
    line: int | None = None,
) -> str:
    base = f"https://github.com/{org}/{repo_name}/blob/{branch}/{relative_path}"
    if line is not None:
        return f"{base}#L{line}"
    return base


def predict_test_names(name: str, step_bodies: list[str], test_case_id: int) -> TestNames:
    return build_test_names(name, step_bodies, test_case_id)


def predict_github_code_url(
    settings: Settings,
    repo_name: str,
    names: TestNames,
) -> str:
    return github_blob_url(settings.github_org, repo_name, names.relative_path)


def _grep_allure_id_in_tree(root: Path, test_case_id: int) -> tuple[str, int] | None:
    marker = f'@AllureId("{test_case_id}")'
    tests_dir = root / "src" / "test" / "java" / "tests"
    if not tests_dir.is_dir():
        return None
    for path in sorted(tests_dir.rglob("*.java")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            if marker in line:
                relative = path.relative_to(root).as_posix()
                return relative, index
    return None


def _gh_json(cmd: list[str]) -> Any:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    stdout = result.stdout.strip()
    if not stdout:
        return None
    return json.loads(stdout)


def _find_github_code(
    settings: Settings,
    repo_full: str,
    repo_name: str,
    projects_dir: Path,
    test_case_id: int,
) -> tuple[str | None, str | None, int | None]:
    local_root = projects_dir / repo_name
    if local_root.is_dir():
        match = _grep_allure_id_in_tree(local_root, test_case_id)
        if match:
            relative, line = match
            return (
                github_blob_url(settings.github_org, repo_name, relative, line=line),
                relative,
                line,
            )

    search = _gh_json(
        [
            "gh",
            "search",
            "code",
            f'@AllureId("{test_case_id}")',
            "repo:" + repo_full,
            "--json",
            "path,textMatches",
            "--limit",
            "1",
        ]
    )
    if search:
        item = search[0]
        relative = str(item.get("path") or "")
        line = None
        for match in item.get("textMatches") or []:
            fragment = str(match.get("fragment") or "")
            if f'@AllureId("{test_case_id}")' in fragment:
                line = int(match.get("startLine") or 0) or None
                break
        if relative:
            return (
                github_blob_url(settings.github_org, repo_name, relative, line=line),
                relative,
                line,
            )
    return None, None, None


def _find_ci_run(org: str, repo_name: str, test_case_id: int) -> tuple[str | None, str | None, str | None]:
    repo_full = f"{org}/{repo_name}"
    commits = _gh_json(
        [
            "gh",
            "search",
            "commits",
            f"TestOps #{test_case_id}",
            "-R",
            repo_full,
            "--json",
            "sha",
            "--limit",
            "1",
        ]
    )
    if not commits:
        return None, None, None

    sha = str(commits[0].get("sha") or "")
    if not sha:
        return None, None, None

    runs = _gh_json(
        [
            "gh",
            "run",
            "list",
            "-R",
            repo_full,
            "--workflow",
            "selenoid-autotests-cloud_github.yml",
            "--commit",
            sha,
            "--json",
            "databaseId,url,conclusion",
            "--limit",
            "1",
        ]
    )
    if not runs:
        return None, None, None

    run = runs[0]
    run_id = int(run["databaseId"])
    run_url = str(run["url"])
    conclusion = run.get("conclusion")
    report_url = f"https://{org}.github.io/{repo_name}/reports/{run_id}/awesome/index.html"
    return run_url, conclusion, report_url


def resolve_automation_links(
    settings: Settings,
    project_id: int,
    test_case_id: int,
    *,
    repo_name: str,
    test_case: dict[str, Any] | None = None,
    step_bodies: list[str] | None = None,
    projects_dir: Path | None = None,
) -> AutomationLinks:

    testops_url = testops_test_case_url(settings, project_id, test_case_id)
    repo_full = f"{settings.github_org}/{repo_name}"
    root = projects_dir or Path("projects")

    automated = bool((test_case or {}).get("automated"))
    status = (test_case or {}).get("status") or {}
    status_name = status.get("name")

    code_url, code_path, code_line = _find_github_code(settings, repo_full, repo_name, root, test_case_id)
    run_url, conclusion, report_url = _find_ci_run(settings.github_org, repo_name, test_case_id)

    qualified: str | None = None
    if test_case and step_bodies is not None:
        name = str(test_case.get("name") or "").strip()
        names = predict_test_names(name, step_bodies, test_case_id)
        qualified = names.qualified_test_name
        if code_url is None:
            code_url = predict_github_code_url(settings, repo_name, names)
            code_path = names.relative_path

    return AutomationLinks(
        project_id=project_id,
        test_case_id=test_case_id,
        testops_url=testops_url,
        github_repo_full=repo_full,
        github_code_url=code_url,
        github_code_path=code_path,
        github_code_line=code_line,
        qualified_test_name=qualified,
        ci_run_url=run_url,
        ci_run_conclusion=conclusion,
        allure_report_url=report_url if run_url else None,
        automated=automated,
        status_name=status_name,
    )


def format_links_markdown(links: AutomationLinks, *, phase: str = "final") -> str:
    """phase: 'created' (after manual case) or 'final' (after automation)."""
    lines = ["## Ссылки", ""]

    lines.append(f"- **TestOps:** [{links.test_case_id}]({links.testops_url})")

    if links.github_code_url:
        label = links.qualified_test_name or links.github_code_path or "код"
        code_heading = "Код автотеста (прогноз)" if phase == "created" else "Код автотеста"
        lines.append(f"- **{code_heading}:** [`{label}`]({links.github_code_url})")
    elif phase == "created":
        predicted = links.qualified_test_name or "tests.*.*Test"
        lines.append(
            f"- **Код автотеста:** появится после «✨ Автоматизировать» (ожидается `{predicted}`)"
        )
    else:
        lines.append("- **Код автотеста:** _ещё не найден в GitHub_")

    if links.ci_run_url:
        status = f" (`{links.ci_run_conclusion}`)" if links.ci_run_conclusion else ""
        lines.append(f"- **GitHub Actions run:** [прогон]({links.ci_run_url}){status}")
        if links.allure_report_url:
            lines.append(f"- **Allure 3 отчёт:** [открыть]({links.allure_report_url})")
    elif phase == "created":
        lines.append("- **GitHub Actions run:** появится после «✨ Автоматизировать»")
    else:
        lines.append("- **GitHub Actions run:** _ещё не найден_")

    if links.automated:
        lines.append("")
        lines.append(f"Статус TestOps: **{links.status_name or 'automated'}**")
    return "\n".join(lines)


WORKFLOW_DIAGRAM_FILENAME = "testops-automation-flow-qa.png"


def format_workflow_onboarding_markdown(*, attachment_content_path: str) -> str:
    """Markdown for the workflow diagram (use /api/testcase/attachment/{id}/content URL)."""
    return "\n".join(
        [
            "## Как устроен путь автоматизации",
            "",
            f"![Путь тест-кейса: от черновика до автоматизации]({attachment_content_path})",
            "",
            "### Основной путь",
            "",
            "1. **Черновик** — кейс в работе, шаги и ожидания можно править.",
            "2. **На ревью** *(опционально)* — согласование перед автоматизацией.",
            "3. **✨ Автоматизировать** — запуск автоматизации: ИИ генерирует e2e-тест по шагам кейса.",
            "",
            "### Результат",
            "",
            "| Исход | Что происходит |",
            "|-------|----------------|",
            "| **Успех** | Кейс переходит в воркфлоу **«Автоматизированные тесты»**, статус — **«Автоматизировано с ИИ»**. |",
            "| **Ошибка** | Статус **«❌ Автоматизация не удалась»** — смотрите комментарии ниже, исправьте кейс и снова выставьте **✨ Автоматизировать**. |",
            "",
            "> Повторный запуск после ошибки безопасен: автоматизатор подхватит кейс заново.",
        ]
    )


def format_creation_comment(links: AutomationLinks, *, attachment_content_path: str | None = None) -> str:
    """TestOps comment after give-manual-testcase creates a draft case."""
    sections: list[str] = []
    if attachment_content_path:
        sections.extend(
            [
                format_workflow_onboarding_markdown(attachment_content_path=attachment_content_path),
                "",
                "---",
                "",
            ]
        )
    sections.extend(
        [
            "## Создано skill give-manual-testcase",
            "",
            "После ручной проверки переведите кейс в **✨ Автоматизировать**.",
            "",
            format_links_markdown(links, phase="created"),
        ]
    )
    return "\n".join(sections)
