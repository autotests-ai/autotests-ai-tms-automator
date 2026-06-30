from typing import Any


def format_manual_test_case_comment(test_case: dict[str, Any], steps_payload: dict[str, Any]) -> str:
    lines = ["## Ручной тест-кейс", ""]

    name = (test_case.get("name") or "").strip()
    if name:
        lines.append(f"**Название:** {name}")

    for field, label in (
        ("precondition", "Предусловия"),
        ("description", "Описание"),
        ("expectedResult", "Ожидаемый результат"),
    ):
        value = (test_case.get(field) or "").strip()
        if value:
            lines.extend(["", f"**{label}:**", value])

    step_lines = _format_scenario_steps(steps_payload)
    if step_lines:
        lines.extend(["", "**Шаги:**", *step_lines])

    return "\n".join(lines)


def _format_scenario_steps(steps_payload: dict[str, Any]) -> list[str]:
    root = steps_payload.get("root") or {}
    scenario_steps = steps_payload.get("scenarioSteps") or {}
    shared_steps = steps_payload.get("sharedSteps") or {}
    shared_step_steps = steps_payload.get("sharedStepScenarioSteps") or {}
    children = root.get("children") or []
    if not children:
        return []
    return _format_step_tree(children, scenario_steps, shared_steps, shared_step_steps)


def _format_step_tree(
    step_ids: list[int],
    scenario_steps: dict[str, Any],
    shared_steps: dict[str, Any],
    shared_step_steps: dict[str, Any],
    indent: int = 0,
) -> list[str]:
    lines: list[str] = []
    prefix = "  " * indent

    for index, raw_step_id in enumerate(step_ids, start=1):
        step = _get_step(raw_step_id, scenario_steps, shared_steps, shared_step_steps)
        if step is None:
            continue

        body = (step.get("body") or "").strip()
        if body:
            marker = f"{index}." if indent == 0 else "-"
            lines.append(f"{prefix}{marker} {body}")

        expected = (step.get("expectedResult") or "").strip()
        if expected:
            lines.append(f"{prefix}   **Ожидаемый результат:** {expected}")

        child_ids = step.get("children") or []
        if child_ids:
            lines.extend(
                _format_step_tree(
                    child_ids,
                    scenario_steps,
                    shared_steps,
                    shared_step_steps,
                    indent + 1,
                )
            )

    return lines


def extract_step_bodies(steps_payload: dict[str, Any]) -> list[str]:
    bodies: list[str] = []
    for line in _format_scenario_steps(steps_payload):
        stripped = line.strip()
        if not stripped or stripped.startswith("**Ожидаемый результат"):
            continue
        if stripped[0].isdigit() and "." in stripped[:4]:
            bodies.append(stripped.split(".", 1)[1].strip())
        elif stripped.startswith("-"):
            bodies.append(stripped[1:].strip())
    return bodies


def _get_step(
    step_id: int,
    scenario_steps: dict[str, Any],
    shared_steps: dict[str, Any],
    shared_step_steps: dict[str, Any],
) -> dict[str, Any] | None:
    step = scenario_steps.get(str(step_id)) or scenario_steps.get(step_id)
    if step is not None:
        return step

    shared_step = shared_steps.get(str(step_id)) or shared_steps.get(step_id)
    if shared_step is None:
        return None

    shared_root = shared_step.get("root") or {}
    shared_children = shared_root.get("children") or []
    if not shared_children:
        shared_name = (shared_step.get("name") or "").strip()
        return {"body": shared_name} if shared_name else None

    shared_lines = _format_step_tree(
        shared_children,
        shared_step_steps,
        shared_steps,
        shared_step_steps,
        indent=0,
    )
    shared_name = (shared_step.get("name") or "Shared step").strip()
    body = shared_name
    if shared_lines:
        body = f"{shared_name}\n" + "\n".join(f"  {line}" for line in shared_lines)
    return {"body": body}
