#!/usr/bin/env python
"""Resolve TestOps + GitHub context for a project id (do not guess status/workflow ids)."""

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
from automator.github.naming import build_repo_name


def _match_status_id(statuses: list[dict[str, Any]], *needles: str) -> int | None:
    lowered = [(int(st["id"]), str(st.get("name") or "").lower()) for st in statuses]
    for needle in needles:
        token = needle.lower()
        for status_id, name in lowered:
            if token in name:
                return status_id
    return None


def _match_ai_automating_status(
    statuses: list[dict[str, Any]],
    *,
    trigger_id: int | None = None,
) -> int | None:
    skip = ("сломан", "broken", "готов", "active", "draft", "ревью", "outdated", "новый")
    for st in statuses:
        status_id = int(st["id"])
        if trigger_id is not None and status_id == trigger_id:
            continue
        name = str(st.get("name") or "").lower()
        if any(token in name for token in skip):
            continue
        if "ai automating" in name or "ai автоматиз" in name or "🤖" in name:
            return status_id
        if "автоматизир" in name and " ai" in name:
            return status_id
        if name.startswith("ai автоматизир") or " ai автоматизир" in name:
            return status_id
    return None


def _resolve_manual_workflow(client: AllureTestOpsClient, project_id: int) -> dict[str, Any]:
    configured = client._settings.workflow_id
    for rql in (
        f"workflow = {configured}",
        "status in [5, -1, 14, 11]",
    ):
        payload = client.search_test_cases(project_id, rql, size=1)
        content = payload.get("content") or []
        if not content:
            continue
        workflow = content[0].get("workflow") or {}
        if workflow.get("id") is not None:
            return {
                "workflow_id": int(workflow["id"]),
                "workflow_name": workflow.get("name"),
                "source": f"search:{rql}",
            }
    return {
        "workflow_id": configured,
        "workflow_name": None,
        "source": "settings.workflow_id (fallback — verify in TestOps UI)",
    }


def _resolve_automated_done(client: AllureTestOpsClient, settings) -> dict[str, Any]:
    workflow_id = settings.automated_workflow_id
    workflow = client.get_workflow(workflow_id)
    statuses = workflow.get("statuses") or []
    done_id = _match_status_id(
        statuses,
        "автоматизировано с ai",
        "автоматизировано",
        "automated with ai",
        "active",
    )
    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.get("name"),
        "status_id": done_id,
        "statuses": [{"id": st["id"], "name": st.get("name")} for st in statuses],
    }


def _workflow_payload(client: AllureTestOpsClient, workflow_info: dict[str, Any]) -> dict[str, Any]:
    workflow_id = int(workflow_info["workflow_id"])
    workflow = client.get_workflow(workflow_id)
    statuses = workflow.get("statuses") or []
    automate_trigger = _match_status_id(
        statuses, "✨", "автоматизировать", "automate", "готов к автомат"
    )
    return {
        "id": workflow_id,
        "name": workflow.get("name") or workflow_info.get("workflow_name"),
        "resolved_from": workflow_info["source"],
        "statuses": [{"id": st["id"], "name": st.get("name")} for st in statuses],
        "status_ids": {
            "draft": _match_status_id(statuses, "draft", "черновик", "новый"),
            "review": _match_status_id(statuses, "ревью", "review"),
            "automate_trigger": automate_trigger,
            "ai_automating": _match_ai_automating_status(statuses, trigger_id=automate_trigger),
            "ai_failed": _match_status_id(statuses, "сломан", "broken", "не удал"),
        },
    }


def _github_repo_exists(repo_full: str) -> bool:
    result = subprocess.run(
        ["gh", "repo", "view", repo_full, "--json", "name"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _github_vars(repo_full: str) -> dict[str, str]:
    result = subprocess.run(
        ["gh", "variable", "list", "-R", repo_full, "--json", "name,value"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {}
    return {item["name"]: item["value"] for item in json.loads(result.stdout)}


def resolve(project_id: int, test_case_id: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    client = AllureTestOpsClient(settings)
    try:
        project = client.get_project(project_id)
        project_name = str(project.get("name") or f"project-{project_id}")
        repo_name = build_repo_name(project_name, project_id)
        repo_full = f"{settings.github_org}/{repo_name}"

        manual_workflow = _workflow_payload(
            client, _resolve_manual_workflow(client, project_id)
        )
        automated_workflow = _resolve_automated_done(client, settings)

        test_case_snapshot = None
        if test_case_id is not None:
            test_case = client.get_test_case(test_case_id)
            tc_workflow = test_case.get("workflow") or {}
            tc_status = test_case.get("status") or {}
            test_case_snapshot = {
                "id": test_case_id,
                "name": test_case.get("name"),
                "automated": bool(test_case.get("automated")),
                "workflow_id": tc_workflow.get("id"),
                "workflow_name": tc_workflow.get("name"),
                "status_id": tc_status.get("id"),
                "status_name": tc_status.get("name"),
            }

        gh_exists = _github_repo_exists(repo_full)
        gh_vars = _github_vars(repo_full) if gh_exists else {}

        return {
            "project_id": project_id,
            "project_name": project_name,
            "testops_url": f"{settings.allure_endpoint.rstrip('/')}/project/{project_id}",
            "manual_workflow": manual_workflow,
            "automated_workflow": automated_workflow,
            "test_case": test_case_snapshot,
            "github": {
                "org": settings.github_org,
                "repo_name": repo_name,
                "repo_full": repo_full,
                "repo_url": f"https://github.com/{repo_full}",
                "exists": gh_exists,
                "allure_project_id": gh_vars.get("ALLURE_PROJECT_ID"),
                "allure_endpoint": gh_vars.get("ALLURE_ENDPOINT"),
            },
            "env_drift": {
                "workflow_id": manual_workflow["id"] != settings.workflow_id,
                "settings_workflow_id": settings.workflow_id,
                "settings_automate_id": settings.status_automate_id,
                "settings_ai_automating_id": settings.status_ai_automating_id,
                "settings_ai_failed_id": settings.status_ai_failed_id,
                "settings_automated_done_id": settings.status_automated_ai_id,
                "settings_automated_workflow_id": settings.automated_workflow_id,
            },
            "notes": [
                "Do not copy status ids from README or another project.",
                "automate_trigger is the status to set when starting automation (manual workflow).",
                "ai_automating is in-progress status in manual workflow.",
                "ai_failed is failure status in manual workflow.",
                "automated_done is status 13 «Автоматизировано с AI» in workflow 5 after success.",
            ],
        }
    finally:
        client.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", type=int)
    parser.add_argument("--test-case-id", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    payload = resolve(args.project_id, args.test_case_id)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    wf = payload["manual_workflow"]
    awf = payload["automated_workflow"]
    st = wf["status_ids"]
    gh = payload["github"]
    print(f"Project {payload['project_id']}: {payload['project_name']}")
    print(f"  TestOps: {payload['testops_url']}")
    print(f"  Manual workflow {wf['id']} ({wf['name']}) ← {wf['resolved_from']}")
    print("  Statuses:")
    for item in wf["statuses"]:
        print(f"    {item['id']:4} {item['name']}")
    print("  Resolved roles (manual, use these — not README):")
    for role, value in st.items():
        print(f"    {role}: {value}")
    print(
        f"  Automated workflow {awf['workflow_id']} ({awf['workflow_name']}): "
        f"automated_done={awf['status_id']}"
    )
    if payload.get("test_case"):
        tc = payload["test_case"]
        print(
            f"  Test case #{tc['id']}: workflow {tc['workflow_id']} ({tc['workflow_name']}), "
            f"status {tc['status_id']} ({tc['status_name']}), automated={tc['automated']}"
        )
    print(f"  GitHub: {gh['repo_url']} ({'exists' if gh['exists'] else 'missing'})")
    if gh.get("allure_project_id"):
        match = gh["allure_project_id"] == str(payload["project_id"])
        print(f"  ALLURE_PROJECT_ID={gh['allure_project_id']} ({'ok' if match else 'MISMATCH'})")
    drift = payload["env_drift"]
    if drift["workflow_id"]:
        print(
            "  WARNING: .env WORKFLOW_ID="
            f"{drift['settings_workflow_id']} differs from project workflow {wf['id']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
