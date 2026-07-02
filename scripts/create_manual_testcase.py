#!/usr/bin/env python
"""Create a manual TestOps test case ready for quick automation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from automator.client.testops import AllureTestOpsClient
from automator.config import get_settings
from automator.links import (
    WORKFLOW_DIAGRAM_FILENAME,
    format_creation_comment,
    format_links_markdown,
    predict_github_code_url,
    predict_test_names,
    resolve_automation_links,
    testops_test_case_url,
)

WORKFLOW_DIAGRAM_PATH = ROOT / "docs/assets/testops-automation-flow-qa.png"
from automator.manual_case import extract_step_bodies
from automator.manual_case_catalog import pick_scenario
from automator.testops.layer_sync import (
    MANUAL_CASE_DEFAULT_LAYER_KEY,
    PYRAMID_LAYER_MAPPINGS,
    mappings_ready,
    resolve_layer_id,
    sync_project_layer_mappings,
)


def _resolve_project_context(project_id: int) -> dict[str, Any]:
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


def _automator_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-fl", "automator.main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _docker_automator_running() -> bool:
    result = subprocess.run(
        ["docker", "compose", "ps", "--status", "running", "--services"],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    return result.returncode == 0 and "automator" in result.stdout


def _ensure_automator(start: bool) -> str:
    if _automator_running():
        return "local python -m automator.main"
    if _docker_automator_running():
        return "docker compose (automator)"
    if not start:
        return "not running (use --start-automator)"
    result = subprocess.run(
        ["docker", "compose", "up", "-d", "--build"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == 0 and _docker_automator_running():
        return "docker compose started"
    return "failed to start — run: docker compose up -d --build"


def _load_steps_file(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("steps"), list):
        return payload["steps"]
    raise SystemExit(f"Invalid steps file: {path}")


def _existing_manual_names(client: AllureTestOpsClient, project_id: int, workflow_id: int) -> list[str]:
    payload = client.search_test_cases(
        project_id,
        f"workflow = {workflow_id}",
        size=100,
    )
    return [str(item.get("name") or "") for item in payload.get("content") or []]


def create_case(
    project_id: int,
    *,
    name: str | None,
    steps: list[dict[str, str]] | None,
    description: str | None,
    precondition: str | None,
    auto_pick: bool,
    start_automator: bool,
    layer_key: str = MANUAL_CASE_DEFAULT_LAYER_KEY,
    ensure_layer_mappings: bool = True,
) -> dict[str, Any]:
    settings = get_settings()
    context = _resolve_project_context(project_id)
    workflow = context["manual_workflow"]
    workflow_id = int(workflow["id"])
    draft_status = workflow["status_ids"].get("draft")
    if draft_status is None:
        raise SystemExit("Could not resolve draft status id from workflow.")

    client = AllureTestOpsClient(settings)
    try:
        if ensure_layer_mappings and not mappings_ready(client, project_id):
            sync_report = sync_project_layer_mappings(
                client,
                project_id,
                dry_run=settings.dry_run,
                migrate_ui_tests=False,
            )
            if not sync_report.ok():
                raise SystemExit("TestOps layer sync failed: " + "; ".join(sync_report.errors))

        if layer_key not in PYRAMID_LAYER_MAPPINGS:
            raise SystemExit(
                f"Unknown --layer {layer_key!r}; expected one of: {', '.join(PYRAMID_LAYER_MAPPINGS)}"
            )
        test_layer_id = resolve_layer_id(client, project_id, key=layer_key)
        test_layer_name = PYRAMID_LAYER_MAPPINGS[layer_key]

        if auto_pick or not name or not steps:
            existing = _existing_manual_names(client, project_id, workflow_id)
            scenario = pick_scenario(existing)
            name = name or scenario.name
            steps = steps or scenario.steps
            description = description or scenario.description

        assert name and steps

        created = client.create_manual_test_case(
            project_id,
            name,
            workflow_id=workflow_id,
            status_id=int(draft_status),
            steps=steps,
            description=description,
            precondition=precondition,
            test_layer_id=test_layer_id,
        )
        test_case_id = int(created["id"])
        step_bodies = [step.get("body") or step.get("name") or "" for step in steps]
        names = predict_test_names(name, step_bodies, test_case_id)
        repo_name = str(context["github"]["repo_name"])
        predicted_code_url = predict_github_code_url(settings, repo_name, names)

        steps_payload = client.get_test_case_steps(test_case_id)
        extracted = extract_step_bodies(steps_payload)

        links = resolve_automation_links(
            settings,
            project_id,
            test_case_id,
            repo_name=repo_name,
            test_case=created,
            step_bodies=extracted or step_bodies,
            projects_dir=ROOT / settings.github_projects_dir,
        )
        if WORKFLOW_DIAGRAM_PATH.is_file():
            uploaded = client.upload_test_case_attachment(
                test_case_id,
                WORKFLOW_DIAGRAM_FILENAME,
                WORKFLOW_DIAGRAM_PATH.read_bytes(),
                content_type="image/png",
            )
            attachment_id = int((uploaded or {}).get("id") or 0) or client.find_test_case_attachment_id(
                test_case_id, WORKFLOW_DIAGRAM_FILENAME
            )
            diagram_path = client.attachment_content_path(attachment_id) if attachment_id else None
        else:
            diagram_path = None
        client.create_test_case_comment(
            test_case_id,
            format_creation_comment(links, attachment_content_path=diagram_path),
        )

        automator_status = _ensure_automator(start_automator)

        return {
            "project_id": project_id,
            "test_case_id": test_case_id,
            "name": name,
            "test_layer_key": layer_key,
            "test_layer_name": test_layer_name,
            "testops_url": testops_test_case_url(settings, project_id, test_case_id),
            "workflow_id": workflow_id,
            "status_id": draft_status,
            "predicted_test": names.qualified_test_name,
            "predicted_github_code_url": predicted_code_url,
            "automator": automator_status,
            "links_markdown": format_links_markdown(links, phase="created"),
            "github": context["github"],
        }
    finally:
        client.close()


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", type=int, nargs="?", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--steps-file", type=Path, default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--precondition", default=None)
    parser.add_argument("--auto", action="store_true", help="pick scenario from catalog")
    parser.add_argument(
        "--layer",
        choices=sorted(PYRAMID_LAYER_MAPPINGS),
        default=MANUAL_CASE_DEFAULT_LAYER_KEY,
        help="TestOps layer key (@Layer canon); default manual → Manual Tests",
    )
    parser.add_argument(
        "--skip-layer-sync",
        action="store_true",
        help="do not auto-run sync_testops_layer_mappings when project mappings are incomplete",
    )
    parser.add_argument("--start-automator", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    project_id = args.project_id if args.project_id is not None else _default_project_id(settings)
    steps = _load_steps_file(args.steps_file) if args.steps_file else None

    payload = create_case(
        project_id,
        name=args.name,
        steps=steps,
        description=args.description,
        precondition=args.precondition,
        auto_pick=args.auto or (args.name is None and steps is None),
        start_automator=args.start_automator,
        layer_key=args.layer,
        ensure_layer_mappings=not args.skip_layer_sync,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Created manual test case #{payload['test_case_id']}: {payload['name']}")
    print(f"Test layer: {payload['test_layer_name']} (@Layer {payload['test_layer_key']})")
    print(payload["links_markdown"])
    print("")
    print(f"Automator: {payload['automator']}")
    print(f"Predicted test: {payload['predicted_test']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
