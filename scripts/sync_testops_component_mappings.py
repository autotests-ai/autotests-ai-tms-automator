#!/usr/bin/env python
"""Apply selenoid-home Component custom field mappings to Allure TestOps projects."""

from __future__ import annotations

import argparse
import sys

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.testops.component_sync import (
    COMPONENT_LABEL_KEY,
    SELENOID_COMPONENTS,
    sync_project_component_mappings,
)


def _parse_project_ids(raw: str | None, settings: Settings, client: AllureTestOpsClient) -> list[int]:
    if raw:
        return [int(value.strip()) for value in raw.split(",") if value.strip()]
    return client.iter_monitored_projects()


def _print_report(report) -> None:
    print(f"\nProject {report.project_id}")
    if report.created_values:
        print("  values created:", ", ".join(report.created_values))
    if report.skipped_values:
        print("  values skipped:", ", ".join(report.skipped_values))
    if report.created_mapping:
        print(f"  mapping: {COMPONENT_LABEL_KEY} → Component (created/updated)")
    if report.skipped_mapping:
        print(f"  mapping: {COMPONENT_LABEL_KEY} → Component (already set)")
    if report.upload_policy_created:
        print("  upload policy: custom_field ← from_test_result (created)")
    if report.upload_policy_skipped:
        print("  upload policy: custom_field (already set)")
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
        "--list-components",
        action="store_true",
        help="Print canonical component values and exit",
    )
    args = parser.parse_args()

    if args.list_components:
        for name in SELENOID_COMPONENTS:
            print(name)
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
            report = sync_project_component_mappings(
                client,
                project_id,
                dry_run=args.dry_run,
            )
            _print_report(report)
            if not report.ok():
                exit_code = 1
    finally:
        client.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
