import logging
import time
from pathlib import Path

from automator.client.testops import AllureTestOpsClient
from automator.config import get_settings, resolve_runtime_root
from automator.statuses import STATUS_LABELS
from automator.events.detector import TransitionDetector
from automator.events.handlers import TransitionHandler
from automator.github.client import GitHubClient
from automator.poller.watcher import StatusWatcher
from automator.project_repo import ProjectRepositoryService
from automator.storage.db import StateStore
from automator.worker.automator import AutomationWorker


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    logger = logging.getLogger("automator")
    store = StateStore(settings.database_path)
    client = AllureTestOpsClient(settings)

    try:
        workflow = client.get_workflow(settings.workflow_id)
        status_chain = " → ".join(
            f"{status['id']}" for status in workflow.get("statuses", [])
        )
        logger.info("Workflow id=%s statuses: %s", settings.workflow_id, status_chain)
        for status_id, label in sorted(STATUS_LABELS.items()):
            logger.info("  status id=%s | %s", status_id, label)

        detector = TransitionDetector(settings)
        handler = TransitionHandler(settings, store, client)
        watcher = StatusWatcher(settings, store, client, detector, handler)

        runtime_root = resolve_runtime_root(Path(__file__))
        projects_dir = settings.resolve_path(settings.github_projects_dir, runtime_root=runtime_root)
        rag_canon_dir = settings.resolve_rag_canon_dir(runtime_root)
        runtime_workflow = settings.resolve_path(
            str(Path(settings.github_template_dir) / ".github/workflows/selenoid-qa-guru_github.yml"),
            runtime_root=runtime_root,
        )
        if not rag_canon_dir.is_dir():
            raise SystemExit(
                f"RAG canon dir not found: {rag_canon_dir} (runtime_root={runtime_root})"
            )
        if not runtime_workflow.is_file():
            raise SystemExit(f"runtime workflow not found: {runtime_workflow}")
        projects_dir.mkdir(parents=True, exist_ok=True)
        github = GitHubClient(
            settings.github_org,
            repo_public=settings.github_repo_public,
            template_repo=settings.github_template,
            runtime_workflow=runtime_workflow,
        )
        project_repo = ProjectRepositoryService(
            settings, store, client, github, projects_dir, rag_canon_dir
        )
        worker = AutomationWorker(settings, store, client, project_repo, github, rag_canon_dir)

        logger.info(
            "Watcher started. Poll interval=%ss, projects=%s, dry_run=%s, github_org=%s, "
            "github_template=%s, runtime_root=%s",
            settings.poll_interval_sec,
            settings.monitor_project_ids or "ALL",
            settings.dry_run,
            settings.github_org,
            settings.github_template,
            runtime_root,
        )

        while True:
            transitions = watcher.poll_once()
            if transitions:
                logger.info("Poll cycle: caught %s transition(s)", transitions)
            processed = worker.process_pending()
            if processed:
                logger.info("Processed %s automation job(s)", processed)
            time.sleep(settings.poll_interval_sec)
    finally:
        client.close()
        store.close()


if __name__ == "__main__":
    main()
