"""Tests for TestOps layer mapping sync."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from automator.testops.layer_sync import (
    PYRAMID_LAYER_MAPPINGS,
    sync_project_layer_mappings,
)


class LayerSyncTest(unittest.TestCase):
    def test_creates_missing_mappings(self) -> None:
        client = MagicMock()
        client.list_test_layers.return_value = [
            {"id": -1, "name": "Unit Tests"},
            {"id": 3, "name": "Component Tests"},
            {"id": 4, "name": "Integration Tests"},
            {"id": -3, "name": "API Tests"},
            {"id": 6, "name": "E2E Tests"},
            {"id": 5, "name": "Manual Tests"},
            {"id": -2, "name": "UI Tests"},
        ]
        client.list_layer_schemas.return_value = []
        client.list_update_schemas.return_value = []
        client.search_test_cases.return_value = {"totalElements": 0}

        report = sync_project_layer_mappings(client, 5271, dry_run=True)

        self.assertTrue(report.ok())
        self.assertEqual(len(report.created_mappings), len(PYRAMID_LAYER_MAPPINGS))
        self.assertTrue(report.upload_policy_created)

    def test_skips_existing_mapping(self) -> None:
        client = MagicMock()
        client.list_test_layers.return_value = [
            {"id": 6, "name": "E2E Tests"},
            {"id": -1, "name": "Unit Tests"},
            {"id": 3, "name": "Component Tests"},
            {"id": 4, "name": "Integration Tests"},
            {"id": -3, "name": "API Tests"},
            {"id": 5, "name": "Manual Tests"},
        ]
        client.list_layer_schemas.return_value = [
            {
                "id": 1,
                "key": "e2e",
                "testLayer": {"id": 6, "name": "E2E Tests"},
            }
        ]
        client.list_update_schemas.return_value = [{"field": "test_layer", "policy": "from_test_result"}]
        client.search_test_cases.return_value = {"totalElements": 0}

        report = sync_project_layer_mappings(client, 5271, dry_run=True)

        self.assertIn("e2e → E2E Tests", report.skipped_mappings)
        self.assertTrue(report.upload_policy_skipped)


if __name__ == "__main__":
    unittest.main()
