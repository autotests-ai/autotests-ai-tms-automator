from unittest import TestCase
from unittest.mock import MagicMock, patch

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.events.handlers import TransitionHandler
from automator.statuses import monitored_status_ids
from automator.storage.db import StateStore


class MonitoredStatusIdsTests(TestCase):
    def test_includes_ai_automating_when_configured(self) -> None:
        ids = monitored_status_ids(11)
        self.assertIn(11, ids)
        self.assertIn(5, ids)

    def test_unchanged_without_ai_automating(self) -> None:
        ids = monitored_status_ids(None)
        self.assertNotIn(11, ids)


class BuildMonitorRqlTests(TestCase):
    def test_rql_includes_ai_status(self) -> None:
        settings = Settings(allure_api_token="token", status_ai_automating_id=11)
        client = AllureTestOpsClient(settings)
        rql = client.build_monitor_rql()
        self.assertIn("11", rql)
        self.assertIn("workflow = 6", rql)

    def test_rql_includes_failed_status(self) -> None:
        settings = Settings(allure_api_token="token", status_ai_failed_id=16)
        client = AllureTestOpsClient(settings)
        rql = client.build_monitor_rql()
        self.assertIn("16", rql)


class RevertToAutomateTriggerTests(TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            allure_api_token="token",
            status_ai_automating_id=11,
            status_ai_failed_id=None,
        )
        self.client = AllureTestOpsClient(self.settings)

    @patch.object(AllureTestOpsClient, "set_test_case_status")
    @patch.object(AllureTestOpsClient, "get_test_case")
    def test_revert_sets_automate_trigger_when_only_in_progress_enabled(
        self,
        get_test_case: MagicMock,
        set_status: MagicMock,
    ) -> None:
        get_test_case.return_value = {"lastModifiedDate": 123, "status": {"id": 5}}
        result = self.client.mark_automation_failed_status(45118)
        self.assertIsNotNone(result)
        set_status.assert_called_once_with(45118, 5)

    @patch.object(AllureTestOpsClient, "set_test_case_status")
    @patch.object(AllureTestOpsClient, "get_test_case")
    def test_failed_status_takes_priority(
        self,
        get_test_case: MagicMock,
        set_status: MagicMock,
    ) -> None:
        client = AllureTestOpsClient(
            Settings(allure_api_token="token", status_ai_automating_id=11, status_ai_failed_id=16)
        )
        get_test_case.return_value = {"lastModifiedDate": 123, "status": {"id": 16}}
        result = client.mark_automation_failed_status(45118)
        self.assertIsNotNone(result)
        set_status.assert_called_once_with(45118, 16)

    def test_revert_skipped_when_no_failure_or_in_progress_status(self) -> None:
        client = AllureTestOpsClient(
            Settings(
                allure_api_token="token",
                status_ai_automating_id=None,
                status_ai_failed_id=None,
            )
        )
        self.assertIsNone(client.mark_automation_failed_status(45118))


class MarkAiAutomatingHandlerTests(TestCase):
    def setUp(self) -> None:
        self.settings = Settings(allure_api_token="token", status_ai_automating_id=11)
        self.store = StateStore(":memory:")
        self.client = MagicMock()
        self.handler = TransitionHandler(self.settings, self.store, self.client)

    def tearDown(self) -> None:
        self.store.close()

    def test_mark_ai_automating_updates_testops_and_store(self) -> None:
        self.client.get_test_case.return_value = {"lastModifiedDate": 999}
        self.handler._mark_ai_automating(5267, 45118)
        self.client.set_test_case_status.assert_called_once_with(45118, 11)
        state = self.store.get_state(5267, 45118)
        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.status_id, 11)
