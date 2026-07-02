#!/usr/bin/env python
"""Apply qa-guru pyramid layer mappings to Allure TestOps projects."""

from __future__ import annotations

import argparse
import sys

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.testops.layer_sync import (
    PYRAMID_LAYER_MAPPINGS,
    sync_project_layer_mappings,
)


def _parse_project_ids(raw: str | None, settings: Settings, client: AllureTestOpsClient) -> list[int]:
    if raw:
        return [int(value.strip()) for value in raw.split(",") if value.strip()]
    return client.iter_monitored_projects()


def _print_report(report) -> None:
    print(f"\nProject {report.project_id}")
    if report.created_mappings:
        print("  created:", ", ".join(report.created_mappings))
    if report.updated_mappings:
        print("  updated:", ", ".join(report.updated_mappings))
    if report.skipped_mappings:
        print("  skipped:", ", ".join(report.skipped_mappings))
    if report.upload_policy_created:
        print("  upload policy: test_layer ← from_test_result (created)")
    if report.upload_policy_skipped:
        print("  upload policy: test_layer (already set)")
    if report.migrated_ui_cases:
        print(f"  migrated UI Tests → E2E Tests: {report.migrated_ui_cases} case(s)")
    for error in report.errors:
        print(f"  ERROR: {error}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-id",
        help="Comma-separated TestOps project IDs (default: MONITOR_PROJECT_IDS or all accessible)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without API writes")
    parser.add_argument(
        "--no-migrate-ui",
        action="store_true",
        help="Do not bulk-migrate cases from UI Tests to E2E Tests",
    )
    parser.add_argument("--list-mapping", action="store_true", help="Print canonical key → layer table and exit")
    args = parser.parse_args()

    if args.list_mapping:
        for key, layer_name in PYRAMID_LAYER_MAPPINGS.items():
            print(f"{key:12} → {layer_name}")
        print(f"{'(deprecated)':12}   UI Tests — do not assign")
        return 0

    settings = Settings()
    if args.dry_run:
        settings.dry_run = True

    client = AllureTestOpsClient(settings)
    exit_code = 0
    try:
        project_ids = _parse_project_ids(args.project_id, settings, client)
        if not project_ids:
            print("No project IDs resolved.", file=sys.stderr)
            return 1

        for project_id in project_ids:
            report = sync_project_layer_mappings(
                client,
                project_id,
                dry_run=args.dry_run,
                migrate_ui_tests=not args.no_migrate_ui,
            )
            _print_report(report)
            if not report.ok():
                exit_code = 1
    finally:
        client.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
