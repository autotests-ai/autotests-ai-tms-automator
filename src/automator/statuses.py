"""Workflow and status identifiers for allure.autotests.cloud."""

WORKFLOW_ID = 6

# Workflow 6: «Ручные тесты» (project Automator Sandbox and peers)
STATUS_DRAFT = -1
STATUS_REVIEW = 14
STATUS_AUTOMATE = 5
# Optional in-progress status (create in TestOps workflow UI; set STATUS_AI_AUTOMATING_ID in .env).
STATUS_AI_AUTOMATING: int | None = None
# After successful CI + launch close: workflow 5 «Автоматизированные тесты», status 13.
STATUS_AUTOMATED_DONE = 13
AUTOMATED_WORKFLOW_ID = 5
# Legacy Active id in manual workflow 6; not the AI-automation success target.
STATUS_ACTIVE = -3

MONITORED_STATUS_IDS = (
    STATUS_DRAFT,
    STATUS_REVIEW,
    STATUS_AUTOMATE,
    STATUS_ACTIVE,
)

# Reference only — logic uses IDs above, not these labels.
STATUS_LABELS: dict[int, str] = {
    STATUS_DRAFT: "Draft / Черновик",
    STATUS_REVIEW: "На ревью",
    STATUS_AUTOMATE: "✨ Автоматизировать",
    STATUS_ACTIVE: "Active",
    STATUS_AUTOMATED_DONE: "Автоматизировано с AI",
}
# Populated when STATUS_AI_AUTOMATING_ID is configured.
if STATUS_AI_AUTOMATING is not None:
    STATUS_LABELS[STATUS_AI_AUTOMATING] = "🤖 AI автоматизирует"


def monitored_status_ids(
    ai_automating_id: int | None = None,
    ai_failed_id: int | None = None,
) -> tuple[int, ...]:
    ids = list(MONITORED_STATUS_IDS)
    for extra in (ai_automating_id, ai_failed_id):
        if extra is not None and extra not in ids:
            ids.append(extra)
    return tuple(ids)


def format_status_id(status_id: int | None) -> str:
    if status_id is None:
        return "null"
    return str(status_id)
