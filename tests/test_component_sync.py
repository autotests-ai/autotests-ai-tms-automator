"""Tests for TestOps Component custom field sync."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from automator.testops.component_sync import (
    SELENOID_COMPONENTS,
    sync_project_component_mappings,
)


class ComponentSyncTest(unittest.TestCase):
    def test_creates_values_mapping_and_policy(self) -> None:
        client = MagicMock()
        client.list_project_custom_fields.return_value = [
            {"id": -4, "name": "Component"},
        ]
        client.list_custom_field_values.return_value = []
        client.list_custom_field_schemas.return_value = []
        client.list_update_schemas.return_value = []

        report = sync_project_component_mappings(client, 5271, dry_run=True)

        self.assertTrue(report.ok())
        self.assertEqual(len(report.created_values), len(SELENOID_COMPONENTS))
        self.assertTrue(report.created_mapping)
        self.assertTrue(report.upload_policy_created)

    def test_skips_existing_values_and_mapping(self) -> None:
        client = MagicMock()
        client.list_project_custom_fields.return_value = [
            {"id": -4, "name": "Component"},
        ]
        client.list_custom_field_values.return_value = [
            {"name": name} for name in SELENOID_COMPONENTS
        ]
        client.list_custom_field_schemas.return_value = [
            {
                "id": 1,
                "key": "component",
                "customField": {"id": -4, "name": "Component"},
            }
        ]
        client.list_update_schemas.return_value = [
            {"field": "custom_field", "policy": "from_test_result"},
        ]

        report = sync_project_component_mappings(client, 5271, dry_run=True)

        self.assertEqual(len(report.skipped_values), len(SELENOID_COMPONENTS))
        self.assertTrue(report.skipped_mapping)
        self.assertTrue(report.upload_policy_skipped)


if __name__ == "__main__":
    unittest.main()
