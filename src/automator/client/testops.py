import logging
import time
from typing import Any

import httpx

from automator.client.auth import AllureAuth
from automator.config import Settings
from automator.statuses import monitored_status_ids

logger = logging.getLogger(__name__)


class AllureTestOpsClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = f"{settings.allure_endpoint.rstrip('/')}{settings.allure_api_prefix}"
        self._auth = AllureAuth(settings)
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> dict[str, str]:
        token = self._auth.get_token(self._client)
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _get(self, path: str, **params: Any) -> Any:
        response = self._client.get(f"{self._base}{path}", headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def _patch(self, path: str, body: dict[str, Any]) -> Any:
        response = self._client.patch(
            f"{self._base}{path}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=body,
        )
        if response.status_code == 405:
            response = self._client.put(
                f"{self._base}{path}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=body,
            )
        response.raise_for_status()
        return response.json() if response.content else None

    def _post(self, path: str, body: dict[str, Any]) -> Any:
        response = self._client.post(
            f"{self._base}{path}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=body,
        )
        response.raise_for_status()
        return response.json() if response.content else None

    def get_project(self, project_id: int) -> dict[str, Any]:
        return self._get(f"/project/{project_id}")

    def get_workflow(self, workflow_id: int) -> dict[str, Any]:
        return self._get(f"/workflow/{workflow_id}")

    def list_projects(self, page: int = 0, size: int = 100) -> dict[str, Any]:
        return self._get("/project", page=page, size=size)

    def search_test_cases(self, project_id: int, rql: str, page: int = 0, size: int = 100) -> dict[str, Any]:
        return self._get(
            "/testcase/__search",
            projectId=project_id,
            rql=rql,
            page=page,
            size=size,
        )

    def get_test_case(self, test_case_id: int) -> dict[str, Any]:
        return self._get(f"/testcase/{test_case_id}")

    def get_test_case_scenario(self, test_case_id: int) -> dict[str, Any]:
        return self._get(f"/testcase/{test_case_id}/scenario")

    def get_test_case_steps(self, test_case_id: int) -> dict[str, Any]:
        return self._get(f"/testcase/{test_case_id}/step")

    def create_test_case_comment(self, test_case_id: int, body: str) -> Any:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would add comment to test case %s (%s chars)",
                test_case_id,
                len(body),
            )
            return None
        return self._post("/comment", {"testCaseId": test_case_id, "body": body})

    def upload_test_case_attachment(
        self,
        test_case_id: int,
        filename: str,
        content: bytes,
        content_type: str = "video/mp4",
    ) -> dict[str, Any] | None:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would upload attachment %s to test case %s (%s bytes)",
                filename,
                test_case_id,
                len(content),
            )
            return {"name": filename, "dry_run": True}
        files = {"file": (filename, content, content_type)}
        data = {"testCaseId": str(test_case_id)}
        response = self._client.post(
            f"{self._base}/testcase/attachment",
            headers=self._headers(),
            files=files,
            data=data,
        )
        response.raise_for_status()
        if not response.content:
            return {"name": filename}
        payload = response.json()
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            return payload[0]
        return payload if isinstance(payload, dict) else {"name": filename}

    def attachment_content_path(self, attachment_id: int) -> str:
        return f"{self._settings.allure_api_prefix}/testcase/attachment/{attachment_id}/content"

    def find_test_case_attachment_id(self, test_case_id: int, filename: str) -> int | None:
        payload = self._get("/testcase/attachment", testCaseId=test_case_id, size=100)
        matches = [
            item
            for item in payload.get("content", [])
            if str(item.get("name") or "") == filename and item.get("id") is not None
        ]
        if not matches:
            return None
        return int(matches[-1]["id"])

    def test_case_attachments_tab_url(self, project_id: int, test_case_id: int) -> str:
        return (
            f"{self._settings.allure_endpoint.rstrip('/')}"
            f"/project/{project_id}/test-cases/{test_case_id}?tab=attachments"
        )

    def create_manual_test_case(
        self,
        project_id: int,
        name: str,
        *,
        workflow_id: int,
        status_id: int,
        steps: list[dict[str, str]],
        description: str | None = None,
        precondition: str | None = None,
        test_layer_id: int | None = None,
    ) -> dict[str, Any]:
        scenario_steps = [
            {
                "name": step.get("body") or step.get("name") or "",
                "expectedResult": step.get("expected_result") or step.get("expectedResult") or "",
            }
            for step in steps
            if (step.get("body") or step.get("name") or "").strip()
        ]
        payload: dict[str, Any] = {
            "projectId": project_id,
            "name": name.strip(),
            "workflowId": workflow_id,
            "statusId": status_id,
            "scenario": {"steps": scenario_steps},
        }
        if description:
            payload["description"] = description.strip()
        if precondition:
            payload["precondition"] = precondition.strip()
        if test_layer_id is not None:
            payload["testLayerId"] = test_layer_id

        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would create manual test case in project %s: %s (%s steps, layerId=%s)",
                project_id,
                name,
                len(scenario_steps),
                test_layer_id,
            )
            return {
                "id": 0,
                "projectId": project_id,
                "name": name,
                "automated": False,
                "testLayerId": test_layer_id,
                "dry_run": True,
            }
        return self._post("/testcase", payload)

    def set_test_case_status(self, test_case_id: int, status_id: int) -> Any:
        if self._settings.dry_run:
            logger.info("DRY RUN: would set test case %s status to %s", test_case_id, status_id)
            return None
        return self._patch(f"/testcase/{test_case_id}", {"statusId": status_id})

    def mark_automation_failed_status(self, test_case_id: int) -> dict[str, Any] | None:
        """After a failed run: «Сломано AI» if configured, else back to automate trigger."""
        if self._settings.status_ai_failed_id is not None:
            target = self._settings.status_ai_failed_id
        elif self._settings.status_ai_automating_id is not None:
            target = self._settings.status_automate_id
        else:
            return None
        self.set_test_case_status(test_case_id, target)
        return self.get_test_case(test_case_id)

    def revert_to_automate_trigger_status(self, test_case_id: int) -> dict[str, Any] | None:
        return self.mark_automation_failed_status(test_case_id)

    def close_launch(self, launch_id: int) -> bool:
        if self._settings.dry_run:
            logger.info("DRY RUN: would close launch %s", launch_id)
            return True
        response = self._client.post(
            f"{self._base}/launch/{launch_id}/close",
            headers=self._headers(),
        )
        if response.status_code in (200, 204):
            logger.info("Closed TestOps launch %s", launch_id)
            return True
        logger.warning(
            "Failed to close launch %s: HTTP %s %s",
            launch_id,
            response.status_code,
            response.text[:200],
        )
        return False

    def find_open_launch_id_for_test_case(
        self,
        project_id: int,
        test_case_id: int,
    ) -> int | None:
        marker = f"#{test_case_id}"
        page = 0
        while True:
            payload = self._get("/launch", projectId=project_id, page=page, size=50)
            for launch in payload.get("content", []):
                if launch.get("closed"):
                    continue
                name = str(launch.get("name") or "")
                if marker in name:
                    return int(launch["id"])
            if payload.get("last", True):
                break
            page += 1
        return None

    def mark_automation_success_status(self, test_case_id: int) -> dict[str, Any] | None:
        """Move testcase to automated workflow + «Автоматизировано с AI» after passed CI."""
        body: dict[str, Any] = {"statusId": self._settings.status_automated_ai_id}
        if self._settings.automated_workflow_id is not None:
            body["workflowId"] = self._settings.automated_workflow_id
        if self._settings.dry_run:
            logger.info("DRY RUN: would mark test case %s automated success %s", test_case_id, body)
            return {"id": test_case_id, "dry_run": True, **body}
        self._patch(f"/testcase/{test_case_id}", body)
        return self.get_test_case(test_case_id)

    def _is_automation_finalized(self, test_case: dict[str, Any]) -> bool:
        if not bool(test_case.get("automated")):
            return False
        status_id = int((test_case.get("status") or {}).get("id", 0))
        if status_id != self._settings.status_automated_ai_id:
            return False
        workflow_id = self._settings.automated_workflow_id
        if workflow_id is None:
            return True
        return int((test_case.get("workflow") or {}).get("id", 0)) == workflow_id

    def finalize_automation_launch(
        self,
        project_id: int,
        test_case_id: int,
    ) -> dict[str, Any] | None:
        """Close the latest open launch for a test case so TestOps marks it automated."""
        launch_id = self.find_open_launch_id_for_test_case(project_id, test_case_id)
        if launch_id is None:
            logger.info("No open launch found for test case #%s in project %s", test_case_id, project_id)
            test_case = self.get_test_case(test_case_id)
            if self._is_automation_finalized(test_case):
                return {
                    "launch_id": None,
                    "launch_closed": True,
                    "automated": True,
                    "status_id": int((test_case.get("status") or {}).get("id", 0)),
                    "workflow_id": int((test_case.get("workflow") or {}).get("id", 0)),
                }
            return None
        if not self.close_launch(launch_id):
            return None
        return self._wait_for_automation_finalized(launch_id, test_case_id)

    def _wait_for_automation_finalized(
        self,
        launch_id: int,
        test_case_id: int,
        *,
        attempts: int = 10,
        delay_sec: float = 2.0,
    ) -> dict[str, Any] | None:
        test_case: dict[str, Any] = {}
        launch: dict[str, Any] = {}
        for attempt in range(attempts):
            launch = self._get(f"/launch/{launch_id}")
            test_case = self.get_test_case(test_case_id)
            if bool(launch.get("closed")) and self._is_automation_finalized(test_case):
                status = test_case.get("status") or {}
                workflow = test_case.get("workflow") or {}
                return {
                    "launch_id": launch_id,
                    "launch_closed": True,
                    "automated": True,
                    "status_id": int(status.get("id", 0)),
                    "workflow_id": int(workflow.get("id", 0)),
                }
            if attempt + 1 < attempts:
                time.sleep(delay_sec)

        if bool(launch.get("closed")) and bool(test_case.get("automated")):
            try:
                updated = self.mark_automation_success_status(test_case_id)
                if updated and self._is_automation_finalized(updated):
                    status = updated.get("status") or {}
                    workflow = updated.get("workflow") or {}
                    return {
                        "launch_id": launch_id,
                        "launch_closed": True,
                        "automated": True,
                        "status_id": int(status.get("id", 0)),
                        "workflow_id": int(workflow.get("id", 0)),
                    }
            except Exception:
                logger.exception(
                    "Failed to set automated success status for test case #%s",
                    test_case_id,
                )

        logger.warning(
            "Launch %s closed but test case #%s not finalized (automated=%s, workflow=%s, status=%s)",
            launch_id,
            test_case_id,
            test_case.get("automated"),
            (test_case.get("workflow") or {}).get("id"),
            (test_case.get("status") or {}).get("id"),
        )
        return None

    def build_monitor_rql(self) -> str:
        status_ids = ", ".join(
            str(status_id)
            for status_id in monitored_status_ids(
                self._settings.status_ai_automating_id,
                self._settings.status_ai_failed_id,
            )
        )
        return f"workflow = {self._settings.workflow_id} and status in [{status_ids}]"

    def iter_monitored_projects(self) -> list[int]:
        configured = [
            int(value.strip())
            for value in self._settings.monitor_project_ids.split(",")
            if value.strip()
        ]
        if configured:
            return configured

        project_ids: list[int] = []
        page = 0
        while True:
            payload = self.list_projects(page=page, size=self._settings.project_page_size)
            for project in payload.get("content", []):
                project_ids.append(project["id"])
            if payload.get("last", True):
                break
            page += 1
        logger.info("Monitoring all %s accessible projects", len(project_ids))
        return project_ids

    def iter_workflow_test_cases(self, project_id: int) -> list[dict[str, Any]]:
        rql = self.build_monitor_rql()
        cases: list[dict[str, Any]] = []
        page = 0
        while True:
            payload = self.search_test_cases(
                project_id=project_id,
                rql=rql,
                page=page,
                size=self._settings.testcase_page_size,
            )
            cases.extend(payload.get("content", []))
            if payload.get("last", True):
                break
            page += 1
        return cases

    def list_test_layers(self, project_id: int, *, size: int = 100) -> list[dict[str, Any]]:
        payload = self._get("/testlayer", projectId=project_id, size=size)
        return list(payload.get("content", []))

    def list_layer_schemas(self, project_id: int, *, size: int = 100) -> list[dict[str, Any]]:
        payload = self._get("/testlayerschema", projectId=project_id, size=size)
        return list(payload.get("content", []))

    def create_layer_schema(self, project_id: int, key: str, test_layer_id: int) -> dict[str, Any]:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would create layer schema %s → layerId=%s in project %s",
                key,
                test_layer_id,
                project_id,
            )
            return {"key": key, "testLayerId": test_layer_id, "dry_run": True}
        return self._post(
            "/testlayerschema",
            {"projectId": project_id, "key": key, "testLayerId": test_layer_id},
        )

    def patch_layer_schema(self, schema_id: int, test_layer_id: int) -> dict[str, Any] | None:
        if self._settings.dry_run:
            logger.info("DRY RUN: would patch layer schema %s → layerId=%s", schema_id, test_layer_id)
            return None
        return self._patch(f"/testlayerschema/{schema_id}", {"testLayerId": test_layer_id})

    def list_update_schemas(self, project_id: int) -> list[dict[str, Any]]:
        payload = self._get("/testcaseupdateschema", projectId=project_id)
        if isinstance(payload, list):
            return payload
        return list(payload.get("content", []))

    def create_update_schema(
        self,
        project_id: int,
        field: str,
        policy: str,
    ) -> dict[str, Any]:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would create update schema project=%s field=%s policy=%s",
                project_id,
                field,
                policy,
            )
            return {"field": field, "policy": policy, "dry_run": True}
        return self._post(
            "/testcaseupdateschema",
            {"projectId": project_id, "field": field, "policy": policy},
        )

    def bulk_set_test_layer(
        self,
        project_id: int,
        layer_id: int,
        *,
        search: str,
    ) -> None:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would bulk-set layerId=%s search=%r in project %s",
                layer_id,
                search,
                project_id,
            )
            return
        self._post(
            "/testcase/bulk/layer/set",
            {
                "layerId": layer_id,
                "selection": {
                    "projectId": project_id,
                    "search": search,
                },
            },
        )

    def set_test_case_layer(self, test_case_id: int, layer_id: int) -> Any:
        if self._settings.dry_run:
            logger.info("DRY RUN: would set test case %s layerId=%s", test_case_id, layer_id)
            return None
        return self._patch(f"/testcase/{test_case_id}", {"testLayerId": layer_id})

    def list_project_custom_fields(self, project_id: int) -> list[dict[str, Any]]:
        payload = self._get("/cf", projectId=project_id)
        if isinstance(payload, list):
            return payload
        return list(payload.get("content", []))

    def list_custom_field_schemas(self, project_id: int, *, size: int = 100) -> list[dict[str, Any]]:
        payload = self._get("/cfschema", projectId=project_id, size=size)
        return list(payload.get("content", []))

    def create_custom_field_schema(
        self,
        project_id: int,
        key: str,
        custom_field_id: int,
    ) -> dict[str, Any]:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would create cf schema %s → customFieldId=%s in project %s",
                key,
                custom_field_id,
                project_id,
            )
            return {"key": key, "customFieldId": custom_field_id, "dry_run": True}
        return self._post(
            "/cfschema",
            {"projectId": project_id, "key": key, "customFieldId": custom_field_id},
        )

    def patch_custom_field_schema(self, schema_id: int, custom_field_id: int) -> dict[str, Any] | None:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would patch cf schema %s → customFieldId=%s",
                schema_id,
                custom_field_id,
            )
            return None
        return self._patch(f"/cfschema/{schema_id}", {"customFieldId": custom_field_id})

    def list_custom_field_values(
        self,
        custom_field_id: int,
        *,
        project_id: int | None = None,
        size: int = 100,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"customFieldId": custom_field_id, "size": size}
        if project_id is not None:
            params["projectId"] = project_id
        payload = self._get("/cfv", **params)
        return list(payload.get("content", []))

    def create_custom_field_value(self, name: str, custom_field_id: int) -> dict[str, Any]:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would create cf value %r for customFieldId=%s",
                name,
                custom_field_id,
            )
            return {"name": name, "customFieldId": custom_field_id, "dry_run": True}
        return self._post(
            "/cfv",
            {"name": name, "customField": {"id": custom_field_id}},
        )
