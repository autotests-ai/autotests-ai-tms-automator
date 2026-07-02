import logging
import tempfile
from pathlib import Path

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.errors import AutomationError
from automator.generator.test_java import generate_test_java
from automator.github.client import GitHubClient
from automator.manual_case import extract_step_bodies
from automator.project_repo import ProjectRepositoryService
from automator.storage.db import StateStore
from automator.testops_comments import (
    ci_finished_comment,
    ci_started_comment,
    repo_created_comment,
    test_pushed_comment,
    video_run_comment,
)

logger = logging.getLogger(__name__)


class AutomationWorker:
    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        client: AllureTestOpsClient,
        project_repo: ProjectRepositoryService,
        github: GitHubClient,
        rag_dir: Path,
    ) -> None:
        self._settings = settings
        self._store = store
        self._client = client
        self._project_repo = project_repo
        self._github = github
        self._rag_dir = rag_dir

    def process_pending(self, limit: int = 5) -> int:
        processed = 0
        for job in self._store.fetch_pending_jobs(limit=limit):
            self._run_job(int(job["id"]), int(job["project_id"]), int(job["test_case_id"]))
            processed += 1
        return processed

    def _comment(self, test_case_id: int, body: str) -> None:
        self._client.create_test_case_comment(test_case_id, body)

    def _comment_repo_created(
        self,
        test_case_id: int,
        project_id: int,
        repo_name: str,
        repo_url: str,
    ) -> None:
        self._comment(
            test_case_id,
            repo_created_comment(
                repo_url=repo_url,
                repo_name=repo_name,
                testops_project_url=self._project_repo.testops_project_url(project_id),
            ),
        )

    def _fail_job(self, job_id: int, project_id: int, test_case_id: int, message: str, comment: str) -> None:
        self._store.set_processing(project_id, test_case_id, "failed")
        self._store.finish_job(job_id, "failed", message)
        self._comment(test_case_id, comment)
        try:
            test_case = self._client.mark_automation_failed_status(test_case_id)
            if test_case is not None:
                status = test_case.get("status") or {}
                self._store.upsert_state(
                    project_id=project_id,
                    test_case_id=test_case_id,
                    status_id=int(status.get("id", self._settings.status_automate_id)),
                    last_modified=int(test_case.get("lastModifiedDate", 0)),
                    processing="failed",
                )
        except Exception:
            logger.exception("Failed to mark #%s as automation failed in TestOps", test_case_id)

    def _run_job(self, job_id: int, project_id: int, test_case_id: int) -> None:
        self._store.set_processing(project_id, test_case_id, "running")
        logger.info("Starting automation for test case #%s (project %s)", test_case_id, project_id)

        try:
            test_case = self._client.get_test_case(test_case_id)
            steps_payload = self._client.get_test_case_steps(test_case_id)
            step_bodies = extract_step_bodies(steps_payload)

            repo_info = self._project_repo.ensure_repository(project_id)
            repo_name = str(repo_info["repo_name"])
            repo_url = str(repo_info["repo_url"])

            if repo_info.get("created"):
                self._comment_repo_created(test_case_id, project_id, repo_name, repo_url)

            generated = generate_test_java(
                test_case_id,
                test_case,
                step_bodies,
                rag_dir=self._rag_dir,
            )
            class_name, created_repo_info = self._project_repo.push_generated_test(
                project_id,
                repo_name,
                test_case_id,
                generated,
            )
            if created_repo_info:
                repo_name = str(created_repo_info["repo_name"])
                repo_url = str(created_repo_info["repo_url"])
                self._comment_repo_created(test_case_id, project_id, repo_name, repo_url)
            self._comment(
                test_case_id,
                test_pushed_comment(
                    repo_url=repo_url,
                    class_name=class_name,
                    test_case_url=self._project_repo.testops_test_case_url(project_id, test_case_id),
                ),
            )

            run = self._github.dispatch_workflow(
                repo_name,
                test_class=class_name,
                test_case_id=test_case_id,
            )
            report_hint = f"https://{self._settings.github_org}.github.io/{repo_name}/reports/"
            self._comment(
                test_case_id,
                ci_started_comment(run_url=run.run_url, report_url_hint=report_hint),
            )

            finished = self._github.wait_for_run(
                repo_name,
                run.run_id,
                timeout_sec=self._settings.automation_ci_timeout_sec,
            )

            video_attachment_name: str | None = None
            video_selenoid_url: str | None = None
            with tempfile.TemporaryDirectory() as tmp:
                video_path = Path(tmp) / f"test-case-{test_case_id}.mp4"
                capture = self._github.download_video_artifact(repo_name, run.run_id, video_path)
                video_selenoid_url = capture.selenoid_url
                if capture.path and capture.path.exists():
                    uploaded = self._client.upload_test_case_attachment(
                        test_case_id=test_case_id,
                        filename=f"test-case-{test_case_id}.mp4",
                        content=capture.path.read_bytes(),
                        content_type="video/mp4",
                    )
                    video_attachment_name = (
                        str((uploaded or {}).get("name") or f"test-case-{test_case_id}.mp4")
                    )

            attachments_tab_url = self._client.test_case_attachments_tab_url(project_id, test_case_id)
            if video_selenoid_url or video_attachment_name:
                self._comment(
                    test_case_id,
                    video_run_comment(
                        video_selenoid_url=video_selenoid_url,
                        video_attachment_name=video_attachment_name,
                        video_attachments_tab_url=attachments_tab_url,
                    ),
                )

            self._comment(
                test_case_id,
                ci_finished_comment(
                    run_url=finished.run_url,
                    report_url=finished.report_url,
                    conclusion=finished.conclusion,
                    video_selenoid_url=video_selenoid_url,
                    video_attachment_name=video_attachment_name,
                    video_attachments_tab_url=attachments_tab_url,
                ),
            )

            if finished.conclusion == "success":
                processing = "failed"
                try:
                    finalized = self._client.finalize_automation_launch(project_id, test_case_id)
                    if finalized:
                        logger.info(
                            "TestOps finalized for #%s: launch=%s automated=%s status=%s",
                            test_case_id,
                            finalized.get("launch_id"),
                            finalized.get("automated"),
                            finalized.get("status_id"),
                        )
                        processing = "done"
                    else:
                        logger.warning(
                            "CI succeeded for #%s but TestOps launch was not finalized",
                            test_case_id,
                        )
                except Exception:
                    logger.exception("Failed to finalize TestOps launch for #%s", test_case_id)
            else:
                processing = "failed"
                try:
                    test_case = self._client.mark_automation_failed_status(test_case_id)
                    if test_case is not None:
                        status = test_case.get("status") or {}
                        self._store.upsert_state(
                            project_id=project_id,
                            test_case_id=test_case_id,
                            status_id=int(status.get("id", self._settings.status_automate_id)),
                            last_modified=int(test_case.get("lastModifiedDate", 0)),
                            processing="failed",
                        )
                except Exception:
                    logger.exception("Failed to mark #%s as automation failed after CI failure", test_case_id)

            test_case_after = self._client.get_test_case(test_case_id)
            self._store.upsert_state(
                project_id=project_id,
                test_case_id=test_case_id,
                status_id=int(
                    test_case_after.get("status", {}).get("id", self._settings.status_automate_id)
                ),
                last_modified=int(test_case_after.get("lastModifiedDate", 0)),
                processing=processing,
            )
            self._store.finish_job(job_id, "completed" if processing == "done" else "failed")
            logger.info("Automation finished for #%s with status %s", test_case_id, processing)
        except AutomationError as exc:
            logger.error("Automation failed for #%s: %s", test_case_id, exc)
            self._fail_job(
                job_id,
                project_id,
                test_case_id,
                str(exc),
                f"## ❌ Ошибка автоматизации\n\n`{exc}`",
            )
        except Exception:
            logger.exception("Automation failed for #%s", test_case_id)
            self._fail_job(
                job_id,
                project_id,
                test_case_id,
                "unexpected error",
                "## ❌ Ошибка автоматизации\n\nНепредвиденная ошибка, см. логи automator.",
            )
