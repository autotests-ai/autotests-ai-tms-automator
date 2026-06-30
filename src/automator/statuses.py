"""Workflow and status identifiers for allure.autotests.cloud."""

WORKFLOW_ID = 4

# Workflow 4: «Автоматизация ручных тестов с ИИ»
STATUS_DRAFT = -1
STATUS_REVIEW = -2
STATUS_AUTOMATE = 5
STATUS_AUTOMATED_AI = 13
# STATUS_REGENERATE = 12  # reserved: re-run automation (not implemented yet)

MONITORED_STATUS_IDS = (
    STATUS_DRAFT,
    STATUS_REVIEW,
    STATUS_AUTOMATE,
    STATUS_AUTOMATED_AI,
)

# Reference only — logic uses IDs above, not these labels.
STATUS_LABELS: dict[int, str] = {
    STATUS_DRAFT: "Draft / Черновик",
    STATUS_REVIEW: "Review / На ревью",
    STATUS_AUTOMATE: "✨ Автоматизировать",
    STATUS_AUTOMATED_AI: "Автоматизировано с ИИ",
}


def format_status_id(status_id: int | None) -> str:
    if status_id is None:
        return "null"
    return str(status_id)
