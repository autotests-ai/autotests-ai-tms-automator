#!/usr/bin/env python
"""Probe which TestOps test-case UI blocks update live while the page stays open.

Run:
  cd autotests-ai-tms-automator
  PYTHONPATH=src pytest scripts/testops_live_ui_probe.py -v \\
    --alluredir=build/allure-results/testops-live-ui
  allure generate build/allure-results/testops-live-ui \\
    -o build/allure-report/testops-live-ui --clean
  allure open build/allure-report/testops-live-ui
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import allure
import httpx
import pytest
from playwright.sync_api import Page, sync_playwright

from automator.client.auth import AllureAuth
from automator.config import Settings, get_settings

SCREENSHOTS = Path("build/testops-live-ui-screenshots")
POLL_SEC = 8
VIEWPORT = {"width": 1600, "height": 1000}


@dataclass(frozen=True)
class LiveProbeResult:
    block: str
    tab: str
    api: str
    selector: str
    live: bool
    live_sec: int | None
    visible_after_reload: bool
    recommendation: str


@pytest.fixture(scope="module")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="module")
def probe_context(settings: Settings):
    auth = AllureAuth(settings)
    client = httpx.Client(timeout=60.0)
    token = auth.get_token(client)
    endpoint = settings.allure_endpoint.rstrip("/")
    api_base = f"{endpoint}{settings.allure_api_prefix}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    project_id = int(settings.monitor_project_ids.split(",")[0].strip() or "5269")
    test_case_id = 45340
    page_url = f"{endpoint}/project/{project_id}/test-cases/{test_case_id}"
    run_id = uuid.uuid4().hex[:8]
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()

    def inject_auth(route, request) -> None:
        route.continue_(headers={**request.headers, "authorization": f"Bearer {token}"})

    page.route("**/*", inject_auth)
    page.goto(page_url, wait_until="domcontentloaded", timeout=90_000)
    time.sleep(3)

    yield {
        "settings": settings,
        "client": client,
        "token": token,
        "endpoint": endpoint,
        "api_base": api_base,
        "headers": headers,
        "project_id": project_id,
        "test_case_id": test_case_id,
        "page_url": page_url,
        "run_id": run_id,
        "page": page,
        "browser": browser,
        "playwright": playwright,
    }

    browser.close()
    playwright.stop()
    client.close()


def _shot(page: Page, name: str) -> Path:
    path = SCREENSHOTS / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    return path


def _wait_live(check: Callable[[], bool], seconds: int = POLL_SEC) -> int | None:
    for index in range(seconds):
        time.sleep(1)
        if check():
            return index + 1
    return None


def _norm(text: str) -> str:
    return text.casefold()


def _open_tab(page: Page, label: str) -> None:
    page.locator('[data-testid="list-view__item"]').filter(has_text=label).first.click()
    time.sleep(1)


def _scroll_comments_into_view(page: Page) -> None:
    page.evaluate(
        """() => {
          const sec = [...document.querySelectorAll('section')]
            .find(s => (s.innerText || '').startsWith('Комментарии'));
          if (sec) sec.scrollIntoView({ block: 'center' });
        }"""
    )
    time.sleep(0.5)


def _comments_visible(page: Page, marker: str) -> bool:
    _scroll_comments_into_view(page)
    body = page.inner_text("body")
    return _norm(marker) in _norm(body)


def _run_probe(
    page: Page,
    *,
    block: str,
    tab: str,
    api: str,
    selector: str,
    marker: str,
    apply_change: Callable[[str], None],
    read_visible: Callable[[str], bool],
    cleanup: Callable[[str], None] | None = None,
) -> LiveProbeResult:
    slug = block.lower().replace(" ", "-")
    with allure.step(f"Open tab: {tab}"):
        if tab != "current":
            _open_tab(page, tab)
        before = _shot(page, f"{slug}-before")
        allure.attach.file(str(before), name=f"{slug}-before", attachment_type=allure.attachment_type.PNG)

    with allure.step(f"API: {api}"):
        apply_change(marker)

    with allure.step(f"Poll UI ({POLL_SEC}s) without reload"):
        live_sec = _wait_live(lambda: read_visible(marker))
        live = live_sec is not None
        after = _shot(page, f"{slug}-after-poll")
        allure.attach.file(str(after), name=f"{slug}-after-poll", attachment_type=allure.attachment_type.PNG)

    visible_after_reload = live
    if not live:
        with allure.step("Reload page and re-check"):
            page.reload(wait_until="domcontentloaded")
            time.sleep(5)
            if tab != "current":
                _open_tab(page, tab)
            visible_after_reload = read_visible(marker)
            reloaded = _shot(page, f"{slug}-after-reload")
            allure.attach.file(
                str(reloaded),
                name=f"{slug}-after-reload",
                attachment_type=allure.attachment_type.PNG,
            )

    if cleanup is not None:
        with allure.step("Cleanup API state"):
            cleanup(marker)

    if live:
        recommendation = "Подходит для live-прогресса автоматизации без F5."
    elif visible_after_reload:
        recommendation = "API работает; UI обновляется только после reload / повторного открытия кейса."
    else:
        recommendation = "Проверить селектор или формат API — в UI маркер не найден даже после reload."

    result = LiveProbeResult(
        block=block,
        tab=tab,
        api=api,
        selector=selector,
        live=live,
        live_sec=live_sec,
        visible_after_reload=visible_after_reload,
        recommendation=recommendation,
    )
    allure.attach(
        "\n".join(
            [
                f"block={result.block}",
                f"tab={result.tab}",
                f"api={result.api}",
                f"selector={result.selector}",
                f"live={result.live}",
                f"live_sec={result.live_sec}",
                f"visible_after_reload={result.visible_after_reload}",
                f"recommendation={result.recommendation}",
            ]
        ),
        name="probe-result",
        attachment_type=allure.attachment_type.TEXT,
    )
    return result


@allure.epic("TestOps UI")
@allure.feature("Live updates on test case page")
@allure.story("API patch while user keeps the page open")
class TestTestOpsLiveUiProbe:
    def test_comment_section_updates_live(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        run_id: str = probe_context["run_id"]

        result = _run_probe(
            page,
            block="Comments",
            tab="Обзор",
            api="POST /comment",
            selector="Overview › Комментарии feed",
            marker=f"LIVE_COMMENT_{run_id}",
            apply_change=lambda marker: client.post(
                f"{api_base}/comment",
                headers=headers,
                json={"testCaseId": test_case_id, "body": f"## automation probe\n\n{marker}"},
            ),
            read_visible=lambda marker: _comments_visible(page, marker),
        )
        assert result.visible_after_reload, "Comment must persist in API/UI after reload"

    def test_description_requires_reload(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        run_id: str = probe_context["run_id"]

        def description_text() -> str:
            return page.locator('[data-testid="section__description"]').inner_text()

        result = _run_probe(
            page,
            block="Description",
            tab="Обзор",
            api="PATCH /testcase/{id} description",
            selector='[data-testid="section__description"]',
            marker=f"LIVE_DESC_{run_id}",
            apply_change=lambda marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"description": marker},
            ),
            read_visible=lambda marker: _norm(marker) in _norm(description_text()),
            cleanup=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"description": ""},
            ),
        )
        assert result.visible_after_reload

    def test_title_header_requires_reload(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        run_id: str = probe_context["run_id"]
        original_name = client.get(f"{api_base}/testcase/{test_case_id}", headers=headers).json()["name"]

        def header_text() -> str:
            return page.locator("h2").nth(1).inner_text()

        result = _run_probe(
            page,
            block="Title header",
            tab="Обзор",
            api="PATCH /testcase/{id} name",
            selector="h2 case header",
            marker=f"TITLE_{run_id}",
            apply_change=lambda marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"name": f"Probe workflow {marker}"},
            ),
            read_visible=lambda marker: _norm(marker) in _norm(header_text()),
            cleanup=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"name": original_name},
            ),
        )
        assert result.visible_after_reload

    def test_status_badge_in_header_requires_reload(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        workflow = client.get(f"{api_base}/workflow/6", headers=headers).json()
        statuses = {str(st.get("name", "")).casefold(): int(st["id"]) for st in workflow.get("statuses", [])}
        review_id = statuses.get("ревью") or statuses.get("review") or 14
        draft_id = statuses.get("черновик") or statuses.get("draft") or -1

        def header_text() -> str:
            return page.locator("h2").nth(1).inner_text().casefold()

        result = _run_probe(
            page,
            block="Status badge (header)",
            tab="Обзор",
            api="PATCH /testcase/{id} statusId",
            selector="h2 status chip",
            marker=f"STATUS_{probe_context['run_id']}",
            apply_change=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"statusId": review_id},
            ),
            read_visible=lambda _marker: "ревью" in header_text() or "review" in header_text(),
            cleanup=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"statusId": draft_id},
            ),
        )
        assert result.visible_after_reload

    def test_status_in_tree_updates_live(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        workflow = client.get(f"{api_base}/workflow/6", headers=headers).json()
        statuses = {str(st.get("name", "")).casefold(): int(st["id"]) for st in workflow.get("statuses", [])}
        review_id = statuses.get("ревью") or statuses.get("review") or 14
        draft_id = statuses.get("черновик") or statuses.get("draft") or -1

        page.goto(probe_context["page_url"], wait_until="domcontentloaded")
        time.sleep(3)

        def tree_row_text() -> str:
            return page.locator(f'a:has-text("#{test_case_id}")').first.inner_text().casefold()

        result = _run_probe(
            page,
            block="Status in left tree",
            tab="current",
            api="PATCH /testcase/{id} statusId",
            selector=f'tree row "#{test_case_id}"',
            marker=f"TREE_{probe_context['run_id']}",
            apply_change=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"statusId": review_id},
            ),
            read_visible=lambda _marker: "ревью" in tree_row_text() or "review" in tree_row_text(),
            cleanup=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"statusId": draft_id},
            ),
        )
        assert result.visible_after_reload

    def test_tags_section_requires_reload(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        run_id: str = probe_context["run_id"]
        tag_name = f"LIVE_TAG_{run_id}"

        def tags_text() -> str:
            return page.locator('[data-testid="section__tags"]').inner_text()

        result = _run_probe(
            page,
            block="Tags",
            tab="Обзор",
            api="PATCH /testcase/{id} tags",
            selector='[data-testid="section__tags"]',
            marker=tag_name,
            apply_change=lambda marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"tags": [{"name": marker}]},
            ),
            read_visible=lambda marker: _norm(marker) in _norm(tags_text()),
            cleanup=lambda _marker: client.patch(
                f"{api_base}/testcase/{test_case_id}",
                headers=headers,
                json={"tags": []},
            ),
        )
        assert result.visible_after_reload

    def test_attachments_tab_requires_reload(self, probe_context) -> None:
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        token: str = probe_context["token"]
        test_case_id: int = probe_context["test_case_id"]
        run_id: str = probe_context["run_id"]
        filename = f"probe-{run_id}.txt"

        def attachments_text() -> str:
            return page.locator("body").inner_text()

        result = _run_probe(
            page,
            block="Attachments",
            tab="Вложения",
            api="POST /testcase/attachment",
            selector="Attachments tab list",
            marker=filename,
            apply_change=lambda marker: client.post(
                f"{api_base}/testcase/attachment",
                headers={"Authorization": f"Bearer {token}"},
                data={"testCaseId": str(test_case_id)},
                files={"file": (marker, f"probe {marker}".encode(), "text/plain")},
            ),
            read_visible=lambda marker: _norm(marker) in _norm(attachments_text()),
        )
        assert result.visible_after_reload

    def test_automation_comment_stream(self, probe_context) -> None:
        """Simulate automator stages: several comments while page stays on Overview."""
        page: Page = probe_context["page"]
        client: httpx.Client = probe_context["client"]
        api_base: str = probe_context["api_base"]
        headers: dict = probe_context["headers"]
        test_case_id: int = probe_context["test_case_id"]
        run_id: str = probe_context["run_id"]
        _open_tab(page, "Обзор")

        stages = [
            "🚀 Репозиторий создан",
            "📝 Автотест сгенерирован",
            "⚙️ GitHub Actions запущен",
            "✅ Прогон завершён",
        ]
        live_hits = 0
        for index, title in enumerate(stages, start=1):
            marker = f"STAGE{index}_{run_id}"
            with allure.step(f"Stage comment {index}: {title}"):
                client.post(
                    f"{api_base}/comment",
                    headers=headers,
                    json={"testCaseId": test_case_id, "body": f"## {title}\n\n{marker}"},
                )
                live_sec = _wait_live(lambda marker=marker: _comments_visible(page, marker), seconds=5)
                shot = _shot(page, f"stream-stage-{index}")
                allure.attach.file(
                    str(shot),
                    name=f"stream-stage-{index}",
                    attachment_type=allure.attachment_type.PNG,
                )
                if live_sec is not None:
                    live_hits += 1

        allure.attach(
            f"live_stages={live_hits}/{len(stages)}",
            name="automation-stream-summary",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert live_hits >= 1, "At least one automation-stage comment should appear live"
