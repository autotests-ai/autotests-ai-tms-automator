"""Sync Allure TestOps Component custom field with selenoid-home service repos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from automator.client.testops import AllureTestOpsClient

# Allure label `component` → TestOps custom field "Component".
COMPONENT_LABEL_KEY = "component"
COMPONENT_FIELD_NAME = "Component"

SELENOID_COMPONENTS: tuple[str, ...] = (
    "cm",
    "selenoid",
    "selenoid-ui",
    "playwright-image",
    "webdriver-image",
)


@dataclass
class ComponentSyncReport:
    project_id: int
    created_values: list[str] = field(default_factory=list)
    skipped_values: list[str] = field(default_factory=list)
    created_mapping: bool = False
    skipped_mapping: bool = False
    upload_policy_created: bool = False
    upload_policy_skipped: bool = False
    errors: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors


def _component_field_id(fields: list[dict[str, Any]]) -> int | None:
    for item in fields:
        if str(item.get("name")) == COMPONENT_FIELD_NAME:
            return int(item["id"])
    return None


def sync_project_component_mappings(
    client: AllureTestOpsClient,
    project_id: int,
    *,
    dry_run: bool = False,
) -> ComponentSyncReport:
    report = ComponentSyncReport(project_id=project_id)

    try:
        fields = client.list_project_custom_fields(project_id)
        component_field_id = _component_field_id(fields)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_project_custom_fields: {exc}")
        return report

    if component_field_id is None:
        report.errors.append(
            f'Custom field "{COMPONENT_FIELD_NAME}" not found — add it in TestOps project settings'
        )
        return report

    try:
        existing_values = {
            str(item["name"])
            for item in client.list_custom_field_values(component_field_id)
        }
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_custom_field_values: {exc}")
        return report

    for name in SELENOID_COMPONENTS:
        if name in existing_values:
            report.skipped_values.append(name)
            continue
        if not dry_run:
            try:
                client.create_custom_field_value(name, component_field_id)
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"create value {name}: {exc}")
                continue
        report.created_values.append(name)

    try:
        schemas = {
            str(item["key"]): item
            for item in client.list_custom_field_schemas(project_id)
        }
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_custom_field_schemas: {exc}")
        return report

    current = schemas.get(COMPONENT_LABEL_KEY)
    if current is None:
        if not dry_run:
            try:
                client.create_custom_field_schema(
                    project_id,
                    COMPONENT_LABEL_KEY,
                    component_field_id,
                )
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"create mapping {COMPONENT_LABEL_KEY}: {exc}")
                return report
        report.created_mapping = True
    else:
        current_field = (current.get("customField") or {}).get("id")
        if int(current_field or 0) == component_field_id:
            report.skipped_mapping = True
        elif not dry_run:
            try:
                client.patch_custom_field_schema(
                    int(current["id"]),
                    component_field_id,
                )
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"patch mapping {COMPONENT_LABEL_KEY}: {exc}")
                return report
            report.created_mapping = True
        else:
            report.created_mapping = True

    try:
        policies = client.list_update_schemas(project_id)
        has_custom_field_policy = any(
            item.get("field") == "custom_field" for item in policies
        )
        if has_custom_field_policy:
            report.upload_policy_skipped = True
        elif not dry_run:
            client.create_update_schema(project_id, "custom_field", "from_test_result")
            report.upload_policy_created = True
        else:
            report.upload_policy_created = True
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"upload_policy: {exc}")

    return report
