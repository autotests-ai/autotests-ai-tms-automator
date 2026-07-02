"""Sync Allure TestOps layer key mappings with qa-guru testing pyramid."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from automator.client.testops import AllureTestOpsClient

# @Layer value in Java → TestOps Test Layer display name (admin /admin/testlayer).
PYRAMID_LAYER_MAPPINGS: dict[str, str] = {
    "unit": "Unit Tests",
    "component": "Component Tests",
    "integration": "Integration Tests",
    "api": "API Tests",
    "e2e": "E2E Tests",
    "manual": "Manual Tests",
}

# Default Test Layer for manual workflow cases (give-manual-testcase, create_manual_testcase.py).
MANUAL_CASE_DEFAULT_LAYER_KEY = "manual"

# Allure default layer — do not assign to qa-guru cases; migrate to E2E Tests if found.
DEPRECATED_TESTOPS_LAYER = "UI Tests"
MIGRATE_UI_TO_LAYER = "E2E Tests"


def resolve_layer_id(
    client: AllureTestOpsClient,
    project_id: int,
    *,
    key: str | None = None,
    layer_name: str | None = None,
) -> int:
    if key is None and layer_name is None:
        raise ValueError("key or layer_name required")
    if key is not None and key not in PYRAMID_LAYER_MAPPINGS:
        raise KeyError(f"Unknown layer key: {key}")
    resolved_name = layer_name or PYRAMID_LAYER_MAPPINGS[str(key)]
    layers = client.list_test_layers(project_id)
    layer_ids = _layer_name_index(layers)
    if resolved_name not in layer_ids:
        raise KeyError(f"TestOps layer not found: {resolved_name}")
    return layer_ids[resolved_name]


def mappings_ready(client: AllureTestOpsClient, project_id: int) -> bool:
    schemas = client.list_layer_schemas(project_id)
    keys = {str(item["key"]) for item in schemas}
    return set(PYRAMID_LAYER_MAPPINGS) <= keys


@dataclass
class LayerSyncReport:
    project_id: int
    created_mappings: list[str] = field(default_factory=list)
    updated_mappings: list[str] = field(default_factory=list)
    skipped_mappings: list[str] = field(default_factory=list)
    upload_policy_created: bool = False
    upload_policy_skipped: bool = False
    migrated_ui_cases: int = 0
    errors: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors


def _layer_name_index(layers: list[dict[str, Any]]) -> dict[str, int]:
    return {str(layer["name"]): int(layer["id"]) for layer in layers}


def sync_project_layer_mappings(
    client: AllureTestOpsClient,
    project_id: int,
    *,
    dry_run: bool = False,
    migrate_ui_tests: bool = True,
) -> LayerSyncReport:
    report = LayerSyncReport(project_id=project_id)

    try:
        layers = client.list_test_layers(project_id)
        layer_ids = _layer_name_index(layers)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_test_layers: {exc}")
        return report

    missing_layers = [
        name for name in PYRAMID_LAYER_MAPPINGS.values() if name not in layer_ids
    ]
    if missing_layers:
        report.errors.append(
            "Missing TestOps layers in admin: "
            + ", ".join(missing_layers)
            + " — create at /admin/testlayer"
        )
        return report

    try:
        existing = {
            str(item["key"]): item
            for item in client.list_layer_schemas(project_id)
        }
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_layer_schemas: {exc}")
        return report

    for key, layer_name in PYRAMID_LAYER_MAPPINGS.items():
        target_id = layer_ids[layer_name]
        current = existing.get(key)
        if current is None:
            if not dry_run:
                try:
                    client.create_layer_schema(project_id, key, target_id)
                except Exception as exc:  # noqa: BLE001
                    report.errors.append(f"create {key}: {exc}")
                    continue
            report.created_mappings.append(f"{key} → {layer_name}")
            continue

        current_layer = current.get("testLayer") or {}
        current_id = int(current_layer.get("id", 0))
        if current_id == target_id:
            report.skipped_mappings.append(f"{key} → {layer_name}")
            continue

        if not dry_run:
            try:
                client.patch_layer_schema(int(current["id"]), target_id)
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"patch {key}: {exc}")
                continue
        report.updated_mappings.append(
            f"{key}: {current_layer.get('name', current_id)} → {layer_name}"
        )

    try:
        policies = client.list_update_schemas(project_id)
        has_layer_policy = any(item.get("field") == "test_layer" for item in policies)
        if has_layer_policy:
            report.upload_policy_skipped = True
        elif not dry_run:
            client.create_update_schema(project_id, "test_layer", "from_test_result")
            report.upload_policy_created = True
        else:
            report.upload_policy_created = True
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"upload_policy: {exc}")

    if migrate_ui_tests and DEPRECATED_TESTOPS_LAYER in layer_ids and MIGRATE_UI_TO_LAYER in layer_ids:
        search = f'layer = "{DEPRECATED_TESTOPS_LAYER}"'
        try:
            ui_cases = client.search_test_cases(project_id, search, size=1)
            total = int(ui_cases.get("totalElements", 0))
            if total > 0 and not dry_run:
                client.bulk_set_test_layer(
                    project_id,
                    layer_ids[MIGRATE_UI_TO_LAYER],
                    search=search,
                )
            report.migrated_ui_cases = total
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"migrate_ui_tests: {exc}")

    return report
