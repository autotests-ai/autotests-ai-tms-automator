from dataclasses import dataclass
from enum import Enum

from automator.config import Settings


class TransitionAction(str, Enum):
    NONE = "none"
    START_AUTOMATION = "start_automation"
    LOG_ONLY = "log_only"


@dataclass
class DetectedTransition:
    action: TransitionAction
    from_status_id: int | None
    to_status_id: int


class TransitionDetector:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def detect(self, previous_status_id: int | None, new_status_id: int) -> DetectedTransition:
        if previous_status_id == new_status_id:
            return DetectedTransition(
                action=TransitionAction.NONE,
                from_status_id=previous_status_id,
                to_status_id=new_status_id,
            )

        action = self._resolve_action(previous_status_id, new_status_id)
        return DetectedTransition(
            action=action,
            from_status_id=previous_status_id,
            to_status_id=new_status_id,
        )

    def _resolve_action(self, from_status_id: int | None, to_status_id: int) -> TransitionAction:
        s = self._settings

        if to_status_id == s.status_automate_id and from_status_id != s.status_automate_id:
            return TransitionAction.START_AUTOMATION

        return TransitionAction.LOG_ONLY
