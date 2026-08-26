"""Thin TestOps PATCH for greedy.guru crystal_status. Not GitHub bootstrap."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from automator.client.testops import AllureTestOpsClient

FIELD_NAME = "crystal_status"
VALUES = ("none", "pending_review", "live")
ELIGIBILITY_TAG = "crystal"
FORBIDDEN_POLICY = "from_test_result"
FORBIDDEN_LAYER = "manual"


@dataclass
class CrystalStatusReport:
    project_id: int | None = None
    test_case_id: int | None = None
    crystal_status: str = ""
    from_test_result: bool = False
    dry_run: bool = False
    field_id: int | None = None
    value_id: int | None = None
    patched: bool = False
    created_values: list[str] = field(default_factory=list)
    skipped_values: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors


def _field_id(fields: list[dict[str, Any]]) -> int | None:
    for item in fields:
        if str(item.get("name")) == FIELD_NAME:
            return int(item["id"])
    return None


def _refuse_schema(client: AllureTestOpsClient, project_id: int, field_id: int) -> str | None:
    for item in client.list_custom_field_schemas(project_id):
        mapped = (item.get("customField") or {}).get("id")
        key = str(item.get("key") or "")
        if key == FIELD_NAME or int(mapped or 0) == field_id:
            return (
                f"cfschema maps {key!r} → {FIELD_NAME}; "
                f"upload would treat it as {FORBIDDEN_POLICY}. Remove the mapping."
            )
    return None


def _refuse_manual_layer(test_case: dict[str, Any]) -> str | None:
    layer = test_case.get("testLayer") or {}
    name = str(layer.get("name") or "").lower()
    if name in {"manual tests", "manual"}:
        return f"crystal is not @Layer({FORBIDDEN_LAYER!r})"
    return None


def ensure_crystal_status_values(
    client: AllureTestOpsClient,
    project_id: int,
    *,
    dry_run: bool = False,
) -> CrystalStatusReport:
    report = CrystalStatusReport(project_id=project_id, dry_run=dry_run)
    try:
        fields = client.list_project_custom_fields(project_id)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_project_custom_fields: {exc}")
        return report
    field_id = _field_id(fields)
    if field_id is None:
        report.errors.append(f'Custom field "{FIELD_NAME}" not found — add it in TestOps (not from_test_result)')
        return report
    report.field_id = field_id
    schema_err = _refuse_schema(client, project_id, field_id)
    if schema_err:
        report.errors.append(schema_err)
        return report
    try:
        existing = {str(item["name"]) for item in client.list_custom_field_values(field_id)}
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_custom_field_values: {exc}")
        return report
    for name in VALUES:
        if name in existing:
            report.skipped_values.append(name)
            continue
        if not dry_run:
            try:
                client.create_custom_field_value(name, field_id)
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"create value {name}: {exc}")
                continue
        report.created_values.append(name)
    return report


def patch_crystal_status(
    client: AllureTestOpsClient,
    test_case_id: int,
    crystal_status: str,
    *,
    dry_run: bool = False,
) -> CrystalStatusReport:
    report = CrystalStatusReport(
        test_case_id=test_case_id,
        crystal_status=crystal_status,
        dry_run=dry_run,
    )
    if crystal_status not in VALUES:
        report.errors.append(f"unknown crystal_status {crystal_status!r}")
        return report
    try:
        test_case = client.get_test_case(test_case_id)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"get_test_case: {exc}")
        return report
    manual = _refuse_manual_layer(test_case)
    if manual:
        report.errors.append(manual)
        return report
    project_id = int(test_case.get("projectId") or 0)
    report.project_id = project_id
    try:
        fields = client.list_project_custom_fields(project_id)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_project_custom_fields: {exc}")
        return report
    field_id = _field_id(fields)
    if field_id is None:
        report.errors.append(f'Custom field "{FIELD_NAME}" not found')
        return report
    report.field_id = field_id
    schema_err = _refuse_schema(client, project_id, field_id)
    if schema_err:
        report.errors.append(schema_err)
        return report
    try:
        values = client.list_custom_field_values(field_id)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_custom_field_values: {exc}")
        return report
    value_id = 0
    for item in values:
        if str(item.get("name")) == crystal_status:
            value_id = int(item["id"])
            break
    if crystal_status != "none" and value_id == 0:
        report.errors.append(f"value {crystal_status!r} missing — run --ensure-values")
        return report
    report.value_id = value_id or None
    merged: list[dict[str, Any]] = []
    for item in test_case.get("customFields") or []:
        if not isinstance(item, dict):
            continue
        cf = item.get("customField") or {}
        if str(cf.get("name")) == FIELD_NAME or int(cf.get("id") or 0) == field_id:
            continue
        merged.append(item)
    if crystal_status != "none" and value_id:
        merged.append(
            {
                "id": value_id,
                "name": crystal_status,
                "customField": {"id": field_id, "name": FIELD_NAME},
            }
        )
    body = {"customFields": merged}
    if FORBIDDEN_POLICY in str(body):
        report.errors.append(f"{FORBIDDEN_POLICY} forbidden on crystal_status PATCH")
        return report
    if dry_run:
        report.patched = True
        return report
    try:
        client.patch_test_case(test_case_id, body)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"PATCH: {exc}")
        return report
    report.patched = True
    return report


def patch_from_greedy_json(
    client: AllureTestOpsClient,
    payload: dict[str, Any],
    *,
    dry_run: bool = False,
) -> CrystalStatusReport:
    """Apply greedy observe/approve stdout. Does not bootstrap a repo."""
    if payload.get("from_test_result") is True:
        report = CrystalStatusReport(errors=[f"{FORBIDDEN_POLICY} in greedy payload"])
        return report
    test_case_id = int(payload.get("testcase") or payload.get("test_case_id") or 0)
    patch = payload.get("patch") or {}
    path = str(patch.get("path") or "")
    if test_case_id <= 0 and "/testcase/" in path:
        tail = path.rsplit("/testcase/", 1)[-1]
        if tail.isdigit():
            test_case_id = int(tail)
    crystal_status = str(payload.get("crystal_status") or "")
    if test_case_id <= 0:
        return CrystalStatusReport(errors=["testcase id required"])
    return patch_crystal_status(client, test_case_id, crystal_status, dry_run=dry_run)
