import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.events.detector import TransitionDetector
from automator.events.handlers import TransitionHandler
from automator.storage.db import StateStore

logger = logging.getLogger(__name__)


class StatusWatcher:
    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        client: AllureTestOpsClient,
        detector: TransitionDetector,
        handler: TransitionHandler,
    ) -> None:
        self._settings = settings
        self._store = store
        self._client = client
        self._detector = detector
        self._handler = handler

    def poll_once(self) -> int:
        project_ids = self._client.iter_monitored_projects()
        transitions = 0

        with ThreadPoolExecutor(max_workers=self._settings.max_concurrent_project_requests) as pool:
            futures = {pool.submit(self._poll_project, project_id): project_id for project_id in project_ids}
            for future in as_completed(futures):
                project_id = futures[future]
                try:
                    transitions += future.result()
                except Exception:
                    logger.exception("Failed polling project %s", project_id)

        return transitions

    def _poll_project(self, project_id: int) -> int:
        transitions = 0
        for test_case in self._client.iter_workflow_test_cases(project_id):
            status = test_case.get("status") or {}
            status_id = int(status.get("id", 0))
            test_case_id = int(test_case["id"])
            last_modified = int(test_case.get("lastModifiedDate", 0))
            test_case_name = str(test_case.get("name", ""))

            previous = self._store.get_state(project_id, test_case_id)
            previous_status_id = previous.status_id if previous else None

            if previous is not None and previous.status_id != status_id:
                detected = self._detector.detect(previous_status_id, status_id)
                transition_id = self._store.record_transition(
                    project_id=project_id,
                    test_case_id=test_case_id,
                    test_case_name=test_case_name,
                    from_status_id=previous_status_id,
                    to_status_id=status_id,
                )
                transitions += 1
                self._handler.handle(
                    project_id,
                    test_case_id,
                    test_case_name,
                    transition_id,
                    detected.action,
                    previous_status_id,
                    status_id,
                    last_modified,
                )

            processing = previous.processing if previous and previous.status_id == status_id else None
            if processing is None and previous:
                processing = previous.processing
            self._store.upsert_state(
                project_id=project_id,
                test_case_id=test_case_id,
                status_id=status_id,
                last_modified=last_modified,
                processing=processing or "idle",
            )

            if self._handler.queue_automation_if_needed(
                project_id,
                test_case_id,
                test_case_name,
                status_id,
                last_modified,
            ):
                transitions += 1

        return transitions
