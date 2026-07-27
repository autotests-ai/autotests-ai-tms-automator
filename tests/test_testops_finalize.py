from unittest import TestCase
from unittest.mock import MagicMock, patch

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings


class FinalizeAutomationLaunchTests(TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            allure_api_token="token",
            status_automated_ai_id=13,
            automated_workflow_id=5,
            status_ai_failed_id=None,
            status_ai_automating_id=None,
        )
        self.client = AllureTestOpsClient(self.settings)

    @patch.object(AllureTestOpsClient, "mark_automation_success_status")
    @patch.object(AllureTestOpsClient, "find_launch_id_for_test_case", return_value=54021)
    @patch.object(AllureTestOpsClient, "close_launch", return_value=True)
    @patch.object(AllureTestOpsClient, "_get")
    @patch.object(AllureTestOpsClient, "get_test_case")
    def test_finalize_closes_open_launch_then_sets_status(
        self,
        get_test_case: MagicMock,
        get_launch: MagicMock,
        close_launch: MagicMock,
        find_launch: MagicMock,
        mark_success: MagicMock,
    ) -> None:
        get_test_case.side_effect = [
            {"automated": False, "workflow": {"id": 6}, "status": {"id": 17}},
            {"automated": True, "workflow": {"id": 5}, "status": {"id": -3}},
            {"automated": True, "workflow": {"id": 5}, "status": {"id": 13}},
        ]
        get_launch.side_effect = [
            {"closed": False},  # initial check
            {"closed": True},  # wait loop
        ]
        mark_success.return_value = {
            "automated": True,
            "workflow": {"id": 5},
            "status": {"id": 13},
        }

        with patch("automator.client.testops.time.sleep"):
            result = self.client.finalize_automation_launch(5269, 45341)

        close_launch.assert_called_once_with(54021)
        mark_success.assert_called_with(45341, test_layer_id=None)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["status_id"], 13)
        self.assertEqual(result["workflow_id"], 5)
        self.assertTrue(result["automated"])

    @patch.object(AllureTestOpsClient, "mark_automation_success_status")
    @patch.object(AllureTestOpsClient, "find_launch_id_for_test_case", return_value=54021)
    @patch.object(AllureTestOpsClient, "close_launch")
    @patch.object(AllureTestOpsClient, "_get")
    @patch.object(AllureTestOpsClient, "get_test_case")
    def test_finalize_does_not_reclose_already_closed_launch(
        self,
        get_test_case: MagicMock,
        get_launch: MagicMock,
        close_launch: MagicMock,
        find_launch: MagicMock,
        mark_success: MagicMock,
    ) -> None:
        get_test_case.side_effect = [
            {"automated": False, "workflow": {"id": 6}, "status": {"id": 17}},
            {"automated": True, "workflow": {"id": 5}, "status": {"id": -3}},
        ]
        get_launch.return_value = {"closed": True}
        mark_success.return_value = {
            "automated": True,
            "workflow": {"id": 5},
            "status": {"id": 13},
        }

        with patch("automator.client.testops.time.sleep"):
            result = self.client.finalize_automation_launch(5269, 45341)

        close_launch.assert_not_called()
        mark_success.assert_called_with(45341, test_layer_id=None)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["status_id"], 13)

    @patch.object(AllureTestOpsClient, "get_test_case")
    def test_finalize_accepts_already_automated_case(
        self,
        get_test_case: MagicMock,
    ) -> None:
        get_test_case.return_value = {
            "automated": True,
            "workflow": {"id": 5},
            "status": {"id": 13},
        }

        result = self.client.finalize_automation_launch(5269, 45341)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["launch_id"], None)
        self.assertEqual(result["status_id"], 13)

    @patch.object(AllureTestOpsClient, "mark_automation_success_status")
    @patch.object(AllureTestOpsClient, "find_launch_id_for_test_case", return_value=None)
    @patch.object(AllureTestOpsClient, "get_test_case")
    def test_finalize_marks_success_when_no_launch_found(
        self,
        get_test_case: MagicMock,
        find_launch: MagicMock,
        mark_success: MagicMock,
    ) -> None:
        get_test_case.return_value = {
            "automated": False,
            "workflow": {"id": 6},
            "status": {"id": 17},
        }
        mark_success.return_value = {
            "automated": True,
            "workflow": {"id": 5},
            "status": {"id": 13},
        }

        result = self.client.finalize_automation_launch(5269, 47322)

        mark_success.assert_called_with(47322, test_layer_id=None)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["status_id"], 13)
        self.assertTrue(result["automated"])
