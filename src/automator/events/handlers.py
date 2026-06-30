import logging

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.events.detector import TransitionAction
from automator.manual_case import format_manual_test_case_comment
from automator.statuses import format_status_id
from automator.storage.db import StateStore

logger = logging.getLogger(__name__)


class TransitionHandler:
    def __init__(self, settings: Settings, store: StateStore, client: AllureTestOpsClient) -> None:
        self._settings = settings
        self._store = store
        self._client = client

    def handle(
        self,
        project_id: int,
        test_case_id: int,
        test_case_name: str,
        transition_id: int,
        action: TransitionAction,
        from_status_id: int | None,
        to_status_id: int,
        last_modified: int,
    ) -> None:
        url = (
            f"{self._settings.allure_endpoint.rstrip('/')}"
            f"/project/{project_id}/test-cases/{test_case_id}"
        )

        if action == TransitionAction.START_AUTOMATION:
            logger.info(
                "CAUGHT automation trigger | project=%s | #%s %s | status %s → %s | %s",
                project_id,
                test_case_id,
                test_case_name,
                format_status_id(from_status_id),
                format_status_id(to_status_id),
                url,
            )
            if to_status_id != self._settings.status_automate_id:
                logger.info(
                    "Automation trigger for status %s is not handled | #%s",
                    format_status_id(to_status_id),
                    test_case_id,
                )
            elif self._already_automated(project_id, test_case_id):
                logger.info(
                    "Skip automation for #%s — already completed once (re-run not supported yet)",
                    test_case_id,
                )
            else:
                self._store.set_processing(project_id, test_case_id, "idle")
                self._log_manual_test_case(
                    project_id,
                    test_case_id,
                    test_case_name,
                    last_modified,
                )
                self._store.create_job(project_id, test_case_id)
                logger.info("Queued automation job for #%s in project %s", test_case_id, project_id)
        else:
            logger.info(
                "CAUGHT status change | project=%s | #%s %s | status %s → %s | action=%s | %s",
                project_id,
                test_case_id,
                test_case_name,
                format_status_id(from_status_id),
                format_status_id(to_status_id),
                action.value,
                url,
            )

        self._store.mark_transition_handled(transition_id)

    def queue_automation_if_needed(
        self,
        project_id: int,
        test_case_id: int,
        test_case_name: str,
        status_id: int,
        last_modified: int,
    ) -> bool:
        """Pick up cases already sitting in automate status (e.g. after restart)."""
        if status_id != self._settings.status_automate_id:
            return False

        if self._already_automated(project_id, test_case_id):
            return False

        state = self._store.get_state(project_id, test_case_id)
        processing = state.processing if state else "idle"
        if not self._store.should_queue_automation(project_id, test_case_id, processing):
            return False

        self._log_manual_test_case(project_id, test_case_id, test_case_name, last_modified)
        self._store.create_job(project_id, test_case_id)
        logger.info(
            "Backlog: queued automation for #%s (%s) in project %s",
            test_case_id,
            test_case_name,
            project_id,
        )
        return True

    def _already_automated(self, project_id: int, test_case_id: int) -> bool:
        state = self._store.get_state(project_id, test_case_id)
        return state is not None and state.processing == "done"

    def _log_manual_test_case(
        self,
        project_id: int,
        test_case_id: int,
        test_case_name: str,
        last_modified: int,
    ) -> None:
        try:
            test_case = self._client.get_test_case(test_case_id)
            steps_payload = self._client.get_test_case_steps(test_case_id)
            comment_body = format_manual_test_case_comment(test_case, steps_payload)
            comment = self._client.create_test_case_comment(test_case_id, comment_body)
            new_modified = int(test_case.get("lastModifiedDate", last_modified))
            self._store.upsert_state(
                project_id=project_id,
                test_case_id=test_case_id,
                status_id=self._settings.status_automate_id,
                last_modified=new_modified,
                processing="commented",
            )
            logger.info(
                "Manual test case logged | project=%s | #%s %s | comment_id=%s",
                project_id,
                test_case_id,
                test_case_name,
                (comment or {}).get("id", "dry-run"),
            )
        except Exception:
            logger.exception(
                "Failed to log manual test case for #%s (%s) in project %s",
                test_case_id,
                test_case_name,
                project_id,
            )
            self._store.set_processing(project_id, test_case_id, "failed")
