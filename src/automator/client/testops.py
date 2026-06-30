import logging
from typing import Any

import httpx

from automator.client.auth import AllureAuth
from automator.config import Settings
from automator.statuses import MONITORED_STATUS_IDS

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
    ) -> Any:
        if self._settings.dry_run:
            logger.info(
                "DRY RUN: would upload attachment %s to test case %s (%s bytes)",
                filename,
                test_case_id,
                len(content),
            )
            return None
        files = {"file": (filename, content, content_type)}
        data = {"testCaseId": str(test_case_id)}
        response = self._client.post(
            f"{self._base}/testcase/attachment",
            headers=self._headers(),
            files=files,
            data=data,
        )
        response.raise_for_status()
        return response.json() if response.content else None

    def set_test_case_status(self, test_case_id: int, status_id: int) -> Any:
        if self._settings.dry_run:
            logger.info("DRY RUN: would set test case %s status to %s", test_case_id, status_id)
            return None
        return self._patch(f"/testcase/{test_case_id}", {"statusId": status_id})

    def build_monitor_rql(self) -> str:
        status_ids = ", ".join(str(status_id) for status_id in MONITORED_STATUS_IDS)
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
