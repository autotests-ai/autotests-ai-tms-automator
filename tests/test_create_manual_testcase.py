import unittest
from unittest.mock import MagicMock, patch

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.manual_case_catalog import pick_scenario
from automator.testops.layer_sync import PYRAMID_LAYER_MAPPINGS, resolve_layer_id


class CreateManualTestCaseTests(unittest.TestCase):
    def test_dry_run_create_payload_with_layer(self) -> None:
        settings = Settings(allure_api_token="token", dry_run=True)
        client = AllureTestOpsClient(settings)
        try:
            result = client.create_manual_test_case(
                5267,
                "Probe case",
                workflow_id=6,
                status_id=-1,
                steps=[{"body": "Открыть login.html?ru", "expected_result": "Форма видна"}],
                description="desc",
                test_layer_id=5,
            )
        finally:
            client.close()
        self.assertTrue(result.get("dry_run"))
        self.assertEqual(result["name"], "Probe case")
        self.assertEqual(result["testLayerId"], 5)

    def test_resolve_layer_id_by_key(self) -> None:
        client = MagicMock()
        client.list_test_layers.return_value = [
            {"id": 5, "name": "Manual Tests"},
            {"id": 6, "name": "E2E Tests"},
        ]
        self.assertEqual(resolve_layer_id(client, 5267, key="manual"), 5)
        self.assertEqual(resolve_layer_id(client, 5267, key="e2e"), 6)

    def test_create_case_sets_manual_layer(self) -> None:
        import sys
        from pathlib import Path

        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        sys.path.insert(0, str(scripts_dir))
        import importlib

        module = importlib.import_module("create_manual_testcase")

        resolve_ctx = {
            "manual_workflow": {"id": 6, "status_ids": {"draft": -1}},
            "github": {"repo_name": "qa_guru_automator_ethalon-5267"},
        }
        client = MagicMock()
        client.list_test_layers.return_value = [
            {"id": layer_id, "name": name}
            for name, layer_id in [
                ("Unit Tests", -1),
                ("Component Tests", 3),
                ("Integration Tests", 4),
                ("API Tests", -3),
                ("E2E Tests", 6),
                ("Manual Tests", 5),
            ]
        ]
        client.create_manual_test_case.return_value = {"id": 42, "name": "Case"}
        client.get_test_case_steps.return_value = {"steps": []}
        client.search_test_cases.return_value = {"content": []}

        with (
            patch.object(module, "sync_project_layer_mappings"),
            patch.object(module, "mappings_ready", return_value=True),
            patch.object(module, "_resolve_project_context", return_value=resolve_ctx),
            patch.object(module, "AllureTestOpsClient", return_value=client),
            patch.object(module, "get_settings") as get_settings,
            patch.object(module, "resolve_automation_links", return_value={}),
            patch.object(module, "format_creation_comment", return_value="comment"),
            patch.object(module, "format_links_markdown", return_value="links"),
            patch.object(module, "WORKFLOW_DIAGRAM_PATH", module.ROOT / "docs/assets/missing.png"),
            patch.object(module, "_ensure_automator", return_value="idle"),
        ):
            get_settings.return_value = Settings(allure_api_token="token", dry_run=True)
            payload = module.create_case(
                5267,
                name="Case",
                steps=[{"body": "step", "expected_result": "ok"}],
                description=None,
                precondition=None,
                auto_pick=False,
                start_automator=False,
                layer_key="manual",
            )

        client.create_manual_test_case.assert_called_once()
        call_kwargs = client.create_manual_test_case.call_args.kwargs
        self.assertEqual(call_kwargs["test_layer_id"], 5)
        self.assertEqual(payload["test_layer_name"], "Manual Tests")

    def test_pick_scenario_skips_duplicates(self) -> None:
        existing = ["Неуспешный логин с неверным паролем", "Успешная авторизация"]
        scenario = pick_scenario(existing)
        self.assertNotIn("неверный пароль", scenario.name.lower())


if __name__ == "__main__":
    unittest.main()
