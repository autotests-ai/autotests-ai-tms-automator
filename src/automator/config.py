from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    allure_endpoint: str = "https://allure.autotests.cloud"
    allure_api_token: str
    allure_api_prefix: str = "/api/rs"

    workflow_id: int = 6

    status_draft_id: int = -1
    status_review_id: int = 14
    status_automate_id: int = 5
    status_automated_ai_id: int = Field(
        default=-3,
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
    template_project_dir: str = "/Users/stanislav/template-project"
    automation_ci_timeout_sec: int = 900

    def resolve_template_project_dir(self) -> Path:
        return Path(self.template_project_dir)

    def resolve_rag_canon_dir(self, repo_root: Path) -> Path:
        """Vendored RAG inside automator — always read this path at runtime."""
        return repo_root / "docs" / "rag"


@lru_cache
def get_settings() -> Settings:
    return Settings()
