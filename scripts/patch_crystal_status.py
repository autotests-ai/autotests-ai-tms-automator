#!/usr/bin/env python
"""Thin PATCH for TestOps crystal_status. Not GitHub/Java bootstrap.

Reads greedy observe/approve JSON (--from-json) or --testcase + --status.
Never sets from_test_result. Never @Layer(manual).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.testops.crystal_status import (
    VALUES,
    assign_crystal_workflow,
    ensure_crystal_status_values,
    ensure_crystal_workflow,
    patch_crystal_status,
    patch_from_greedy_json,
)


def _with_workflow(client: AllureTestOpsClient, report, test_case_id: int | None, dry_run: bool):
    if not report.ok() or not test_case_id:
        return report
    wf = assign_crystal_workflow(client, test_case_id, dry_run=dry_run)
    report.workflow_id = wf.workflow_id
    report.workflow_name = wf.workflow_name
    report.created_workflow = wf.created_workflow
    report.workflow_assigned = wf.workflow_assigned
    report.errors.extend(wf.errors)
    return report


def _print(report) -> None:
    payload = {
        "ok": report.ok(),
        "from_test_result": report.from_test_result,
        "project_id": report.project_id,
        "test_case_id": report.test_case_id,
        "crystal_status": report.crystal_status,
        "patched": report.patched,
        "created_values": report.created_values,
        "skipped_values": report.skipped_values,
        "errors": report.errors,
        "dry_run": report.dry_run,
        "workflow_id": report.workflow_id,
        "workflow_name": report.workflow_name,
        "created_workflow": report.created_workflow,
        "workflow_assigned": report.workflow_assigned,
    }
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--testcase", type=int, help="TestOps test case id")
    parser.add_argument("--status", choices=VALUES, help="crystal_status value")
    parser.add_argument("--project-id", type=int, help="Ensure field values on this project")
    parser.add_argument("--ensure-values", action="store_true")
    parser.add_argument(
        "--ensure-workflow",
        action="store_true",
        help="Find or create workflow 'greedy.guru crystals' (Active + Outdated only)",
    )
    parser.add_argument("--from-json", type=Path, help="greedy observe/approve JSON file (or - for stdin)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = Settings()
    if args.dry_run:
        settings.dry_run = True
    client = AllureTestOpsClient(settings)
    try:
        if args.ensure_values:
            if not args.project_id:
                print(json.dumps({"ok": False, "error": "--project-id required with --ensure-values"}))
                return 2
            report = ensure_crystal_status_values(client, args.project_id, dry_run=args.dry_run)
            _print(report)
            return 0 if report.ok() else 1
        if args.ensure_workflow:
            if args.testcase:
                report = assign_crystal_workflow(client, args.testcase, dry_run=args.dry_run)
            else:
                report = ensure_crystal_workflow(client, dry_run=args.dry_run)
            _print(report)
            return 0 if report.ok() else 1
        if args.from_json is not None:
            raw = sys.stdin.read() if str(args.from_json) == "-" else args.from_json.read_text(encoding="utf-8")
            payload = json.loads(raw)
            report = patch_from_greedy_json(client, payload, dry_run=args.dry_run)
            report = _with_workflow(client, report, report.test_case_id, args.dry_run)
            _print(report)
            return 0 if report.ok() else 1
        if not args.testcase or not args.status:
            print(json.dumps({"ok": False, "error": "--testcase and --status, or --from-json"}))
            return 2
        report = patch_crystal_status(client, args.testcase, args.status, dry_run=args.dry_run)
        report = _with_workflow(client, report, args.testcase, args.dry_run)
        _print(report)
        return 0 if report.ok() else 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
