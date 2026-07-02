#!/usr/bin/env python
"""Resolve TestOps + GitHub + CI links for an automated test case."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from automator.client.testops import AllureTestOpsClient
from automator.config import get_settings
from automator.links import format_links_markdown, resolve_automation_links
from automator.manual_case import extract_step_bodies


def _resolve_project_context(project_id: int) -> dict[str, Any]:
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/resolve_testops_project.py"), str(project_id), "--json"],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout or "resolve_testops_project failed")
    return json.loads(result.stdout)


def _default_project_id(settings) -> int:
    configured = [value.strip() for value in settings.monitor_project_ids.split(",") if value.strip()]
    if not configured:
        raise SystemExit("MONITOR_PROJECT_IDS is empty — pass project_id explicitly.")
    return int(configured[0])


def fetch_links(project_id: int, test_case_id: int) -> dict[str, Any]:
    settings = get_settings()
    context = _resolve_project_context(project_id)
    repo_name = str(context["github"]["repo_name"])

    client = AllureTestOpsClient(settings)
    try:
        test_case = client.get_test_case(test_case_id)
        steps_payload = client.get_test_case_steps(test_case_id)
        step_bodies = extract_step_bodies(steps_payload)
    finally:
        client.close()

    links = resolve_automation_links(
        settings,
        project_id,
        test_case_id,
        repo_name=repo_name,
        test_case=test_case,
        step_bodies=step_bodies,
        projects_dir=ROOT / settings.github_projects_dir,
    )
    payload = links.as_dict()
    payload["links_markdown"] = format_links_markdown(links, phase="final")
    payload["ready"] = bool(links.github_code_url and links.ci_run_url)
    return payload


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", type=int, nargs="?", default=None)
    parser.add_argument("test_case_id", type=int)
    parser.add_argument("--watch", action="store_true", help="poll until code + CI run appear")
    parser.add_argument("--timeout-sec", type=int, default=900)
    parser.add_argument("--interval-sec", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    project_id = args.project_id if args.project_id is not None else _default_project_id(settings)
    deadline = time.monotonic() + args.timeout_sec

    while True:
        payload = fetch_links(project_id, args.test_case_id)
        if payload["ready"] or not args.watch or time.monotonic() >= deadline:
            break
        time.sleep(args.interval_sec)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(payload["links_markdown"])
    if args.watch and not payload["ready"]:
        print("")
        print("Timeout: не все ссылки найдены — проверьте automator и CI.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
