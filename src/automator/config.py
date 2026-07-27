from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    allure_endpoint: str = "https://allure.qa.guru"
    allure_api_token: str
    allure_api_prefix: str = "/api/rs"

    workflow_id: int = 6
    automated_workflow_id: int = Field(
        default=5,
        validation_alias=AliasChoices("AUTOMATED_WORKFLOW_ID"),
    )

    status_draft_id: int = -1
    status_review_id: int = 14
    status_automate_id: int = 5
    status_ai_automating_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("STATUS_AI_AUTOMATING_ID"),
    )
    status_ai_failed_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("STATUS_AI_FAILED_ID"),
    )
    status_automated_ai_id: int = Field(
        default=13,
        validation_alias=AliasChoices("STATUS_AUTOMATED_DONE_ID", "STATUS_AUTOMATED_AI_ID"),
    )

    poll_interval_sec: int = 30
    project_page_size: int = 100
    testcase_page_size: int = 100
    max_concurrent_project_requests: int = 5

    # Comma-separated project IDs. Empty = monitor all accessible projects.
    monitor_project_ids: str = "5267"

    database_path: str = "/app/data/automator.db"
    dry_run: bool = False
    log_level: str = "INFO"

    github_org: str = "autotests-cloud"
    github_repo_public: bool = True
    github_template_dir: str = "templates/tests-java"
    github_projects_dir: str = "projects"
    template_project_dir: str = "/Users/stanislav/zero-design-system"
    automation_ci_timeout_sec: int = 900

    def resolve_template_project_dir(self) -> Path:
        return Path(self.template_project_dir)

    def resolve_rag_canon_dir(self, repo_root: Path) -> Path:
        """Vendored RAG inside automator — always read this path at runtime."""
        return repo_root / "docs" / "rag"

    def resolve_path(self, configured: str, *, runtime_root: Path) -> Path:
        """Absolute path as-is; relative paths resolve against runtime_root."""
        path = Path(configured).expanduser()
        if not path.is_absolute():
            path = runtime_root / path
        return path.resolve()


def resolve_runtime_root(package_file: Path | None = None) -> Path:
    """Directory that owns templates/, docs/, projects/.

    Editable/dev layout: ``…/repo/src/automator/main.py`` → parents[2]=repo.
    ``pip install`` in Docker puts the package under site-packages — then CWD
    (WORKDIR=/app) or ``/app`` must be used, not parents[2].
    """
    here = (package_file or Path(__file__)).resolve()
    candidates = [
        Path.cwd(),
        Path("/app"),
        here.parents[2],  # repo root when running from src/ tree
        here.parents[1],  # src/ when package_file is src/automator/*.py
    ]
    for root in candidates:
        if (root / "templates" / "tests-java").is_dir() and (root / "docs" / "rag").is_dir():
            return root.resolve()
    return Path.cwd().resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
