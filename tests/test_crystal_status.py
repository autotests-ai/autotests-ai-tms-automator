"""Tests for thin crystal_status PATCH (not automator bootstrap)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from automator.testops.crystal_status import (
    FIELD_NAME,
    WORKFLOW_NAME,
    assign_crystal_workflow,
    ensure_crystal_status_values,
    ensure_crystal_workflow,
    patch_crystal_status,
    patch_from_greedy_json,
)


class CrystalStatusTest(unittest.TestCase):
    def test_patch_pending_review_keeps_other_fields(self) -> None:
        client = MagicMock()
        client.get_test_case.return_value = {
            "id": 11,
            "projectId": 7,
            "testLayer": {"id": 6, "name": "E2E Tests"},
            "customFields": [
                {"id": 1, "name": "cm", "customField": {"id": 4, "name": "Component"}},
            ],
        }
        client.list_project_custom_fields.return_value = [{"id": 9, "name": FIELD_NAME}]
        client.list_custom_field_schemas.return_value = []
        client.list_custom_field_values.return_value = [
            {"id": 21, "name": "pending_review"},
            {"id": 22, "name": "live"},
        ]
        client.get_test_case_custom_fields.return_value = [
            {"id": 1, "name": "cm", "customField": {"id": 4, "name": "Component"}},
        ]

        report = patch_crystal_status(client, 11, "pending_review", dry_run=False)

        self.assertTrue(report.ok())
        self.assertFalse(report.from_test_result)
        self.assertTrue(report.patched)
        body = client.patch_test_case.call_args[0][1]
        ids = [item["id"] for item in body["customFields"]]
        self.assertEqual(ids, [1, 21])
        self.assertNotIn("from_test_result", str(body))
        self.assertNotIn(FIELD_NAME, str(body["customFields"]))

    def test_refuses_cfschema_mapping(self) -> None:
        client = MagicMock()
        client.get_test_case.return_value = {"id": 11, "projectId": 7, "testLayer": {"name": "E2E Tests"}}
        client.list_project_custom_fields.return_value = [{"id": 9, "name": FIELD_NAME}]
        client.list_custom_field_schemas.return_value = [
            {"key": "crystal_status", "customField": {"id": 9, "name": FIELD_NAME}},
        ]
        client.list_custom_field_values.return_value = [{"id": 21, "name": "live"}]

        report = patch_crystal_status(client, 11, "live")
        self.assertFalse(report.ok())
        self.assertTrue(any("from_test_result" in e for e in report.errors))
        client.patch_test_case.assert_not_called()

    def test_refuses_manual_layer(self) -> None:
        client = MagicMock()
        client.get_test_case.return_value = {
            "id": 11,
            "projectId": 7,
            "testLayer": {"name": "Manual Tests"},
        }
        report = patch_crystal_status(client, 11, "live")
        self.assertFalse(report.ok())
        self.assertTrue(any("manual" in e for e in report.errors))

    def test_ensure_values_does_not_create_schema_or_policy(self) -> None:
        client = MagicMock()
        client.list_project_custom_fields.return_value = [{"id": 9, "name": FIELD_NAME}]
        client.list_custom_field_schemas.return_value = []
        client.list_custom_field_values.return_value = []

        report = ensure_crystal_status_values(client, 7, dry_run=True)
        self.assertTrue(report.ok())
        self.assertEqual(report.created_values, ["none", "pending_review", "live"])
        client.create_custom_field_schema.assert_not_called()
        client.create_update_schema.assert_not_called()

    def test_from_greedy_json(self) -> None:
        client = MagicMock()
        client.get_test_case.return_value = {"id": 99, "projectId": 7, "testLayer": {"name": "E2E Tests"}}
        client.list_project_custom_fields.return_value = [{"id": 9, "name": FIELD_NAME}]
        client.list_custom_field_schemas.return_value = []
        client.list_custom_field_values.return_value = [{"id": 22, "name": "live"}]
        client.get_test_case_custom_fields.return_value = []

        report = patch_from_greedy_json(
            client,
            {
                "ok": True,
                "crystal_status": "live",
                "from_test_result": False,
                "patch": {"method": "PATCH", "path": "/api/rs/testcase/99"},
            },
            dry_run=True,
        )
        self.assertTrue(report.ok())
        self.assertEqual(report.test_case_id, 99)

    def test_resolves_global_field_when_absent_on_project_list(self) -> None:
        client = MagicMock()
        client.get_test_case.return_value = {"id": 11, "projectId": 7, "testLayer": {"name": "E2E Tests"}}
        client.list_project_custom_fields.return_value = [{"id": -4, "name": "Component"}]
        client.list_global_custom_fields.return_value = [{"id": 6, "name": FIELD_NAME}]
        client.list_custom_field_schemas.return_value = []
        client.list_custom_field_values.return_value = [{"id": 22, "name": "live"}]
        client.get_test_case_custom_fields.return_value = []

        report = patch_crystal_status(client, 11, "live", dry_run=False)
        self.assertTrue(report.ok(), report.errors)
        body = client.patch_test_case.call_args[0][1]
        self.assertEqual(body, {"customFields": [{"id": 22}]})

    def test_rejects_from_test_result_payload(self) -> None:
        report = patch_from_greedy_json(MagicMock(), {"from_test_result": True, "crystal_status": "live"})
        self.assertFalse(report.ok())

    def test_ensure_workflow_reuses_existing(self) -> None:
        client = MagicMock()
        client.list_workflows.return_value = [
            {"id": 5, "name": "Автоматизированные тесты"},
            {"id": 7, "name": WORKFLOW_NAME},
        ]
        report = ensure_crystal_workflow(client, dry_run=False)
        self.assertTrue(report.ok())
        self.assertEqual(report.workflow_id, 7)
        client.create_workflow.assert_not_called()

    def test_ensure_workflow_creates_active_outdated_only(self) -> None:
        client = MagicMock()
        client.list_workflows.return_value = [{"id": 5, "name": "Автоматизированные тесты"}]
        client.create_workflow.return_value = {"id": 7, "name": WORKFLOW_NAME}
        report = ensure_crystal_workflow(client, dry_run=False)
        self.assertTrue(report.ok())
        self.assertTrue(report.created_workflow)
        self.assertEqual(report.workflow_id, 7)
        ids = client.create_workflow.call_args[0][1]
        self.assertEqual(ids, [-3, -4])

    def test_assign_workflow_refuses_manual_layer(self) -> None:
        client = MagicMock()
        client.list_workflows.return_value = [{"id": 7, "name": WORKFLOW_NAME}]
        client.get_test_case.return_value = {"id": 11, "projectId": 7, "testLayer": {"name": "Manual Tests"}}
        report = assign_crystal_workflow(client, 11)
        self.assertFalse(report.ok())
        client.patch_test_case.assert_not_called()

    def test_assign_workflow_patches_ids_only(self) -> None:
        client = MagicMock()
        client.list_workflows.return_value = [{"id": 7, "name": WORKFLOW_NAME}]
        client.get_test_case.return_value = {"id": 11, "projectId": 5366, "testLayer": {"name": "E2E Tests"}}
        report = assign_crystal_workflow(client, 11, dry_run=False)
        self.assertTrue(report.ok(), report.errors)
        self.assertTrue(report.workflow_assigned)
        body = client.patch_test_case.call_args[0][1]
        self.assertEqual(body, {"workflowId": 7, "statusId": -3})
        self.assertNotIn("from_test_result", str(body))


if __name__ == "__main__":
    unittest.main()
