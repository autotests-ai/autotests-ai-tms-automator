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
WORKFLOW_NAME = "greedy.guru crystals"
STATUS_ACTIVE_ID = -3
STATUS_OUTDATED_ID = -4


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
    workflow_id: int | None = None
    workflow_name: str = WORKFLOW_NAME
    created_workflow: bool = False
    workflow_assigned: bool = False

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


def _resolve_field(client: AllureTestOpsClient, project_id: int | None) -> int | None:
    if project_id:
        try:
            field_id = _field_id(client.list_project_custom_fields(project_id))
            if field_id is not None:
                return field_id
        except Exception:
            pass
    try:
        return _field_id(client.list_global_custom_fields())
    except Exception:
        return None


def ensure_crystal_status_values(
    client: AllureTestOpsClient,
    project_id: int,
    *,
    dry_run: bool = False,
) -> CrystalStatusReport:
    report = CrystalStatusReport(project_id=project_id, dry_run=dry_run)
    try:
        field_id = _resolve_field(client, project_id)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list custom fields: {exc}")
        return report
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
        field_id = _resolve_field(client, project_id)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list custom fields: {exc}")
        return report
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
    existing_cfv: list[dict[str, Any]] = []
    try:
        existing_cfv = client.get_test_case_custom_fields(test_case_id)
    except Exception:
        existing_cfv = list(test_case.get("customFields") or [])
    ids: list[int] = []
    for item in existing_cfv:
        if not isinstance(item, dict) or item.get("id") is None:
            continue
        cf = item.get("customField") or {}
        if str(cf.get("name")) == FIELD_NAME or int(cf.get("id") or 0) == field_id:
            continue
        ids.append(int(item["id"]))
    if crystal_status != "none" and value_id:
        ids.append(value_id)
    body = {"customFields": [{"id": i} for i in ids]}
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


def ensure_crystal_workflow(
    client: AllureTestOpsClient,
    *,
    dry_run: bool = False,
) -> CrystalStatusReport:
    """Find or create workflow with only Active + Outdated. Not the AI automator workflow."""
    report = CrystalStatusReport(dry_run=dry_run, workflow_name=WORKFLOW_NAME)
    try:
        workflows = client.list_workflows()
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"list_workflows: {exc}")
        return report
    for item in workflows:
        if not isinstance(item, dict):
            continue
        if str(item.get("name")) == WORKFLOW_NAME:
            report.workflow_id = int(item["id"])
            return report
    if dry_run:
        report.created_workflow = True
        report.workflow_id = 0
        return report
    try:
        created = client.create_workflow(WORKFLOW_NAME, [STATUS_ACTIVE_ID, STATUS_OUTDATED_ID])
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"create_workflow: {exc}")
        return report
    report.workflow_id = int(created.get("id") or 0) or None
    report.created_workflow = True
    if report.workflow_id is None:
        report.errors.append("create_workflow returned no id")
    return report


def assign_crystal_workflow(
    client: AllureTestOpsClient,
    test_case_id: int,
    *,
    dry_run: bool = False,
) -> CrystalStatusReport:
    """Move the case onto greedy.guru crystals. Does not change crystal_status."""
    report = ensure_crystal_workflow(client, dry_run=dry_run)
    report.test_case_id = test_case_id
    if not report.ok() or report.workflow_id is None:
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
    report.project_id = int(test_case.get("projectId") or 0) or None
    body = {"workflowId": report.workflow_id, "statusId": STATUS_ACTIVE_ID}
    if dry_run:
        report.workflow_assigned = True
        return report
    try:
        client.patch_test_case(test_case_id, body)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"PATCH workflow: {exc}")
        return report
    report.workflow_assigned = True
    return report
