from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    allure_endpoint: str = "https://allure.autotests.cloud"
    allure_api_token: str
    allure_api_prefix: str = "/api/rs"

    workflow_id: int = 4

    status_draft_id: int = -1
    status_review_id: int = -2
    status_automate_id: int = 5
    status_automated_ai_id: int = 13

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
    github_template_dir: str = "templates/project-tests"
    github_projects_dir: str = "projects"
    automation_ci_timeout_sec: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
