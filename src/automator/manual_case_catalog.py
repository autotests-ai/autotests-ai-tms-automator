"""Predefined manual scenarios for GitHub CI (one-page-form login only)."""

from __future__ import annotations

from dataclasses import dataclass

_HEADER_STEP_TOKENS = ("шапк", "header", "язык", "lang", "тема", "theme")


@dataclass(frozen=True)
class ManualScenario:
    name: str
    description: str
    steps: list[dict[str, str]]
    avoid_name_tokens: tuple[str, ...] = ()

    def step_bodies(self) -> list[str]:
        return [step["body"] for step in self.steps]


CATALOG: list[ManualScenario] = [
    ManualScenario(
        name="Неуспешный логин с неверным паролем",
        description="Негативный сценарий авторизации: неверный пароль, сообщение об ошибке.",
        steps=[
            {"body": "Открыть login.html?ru", "expected_result": "Отображается форма входа"},
            {"body": "Ввести user1 в поле логина", "expected_result": "Логин заполнен"},
            {"body": "Ввести неверный пароль в поле пароля", "expected_result": "Пароль заполнен"},
            {"body": "Нажать кнопку submit", "expected_result": "Форма отправлена"},
            {
                "body": 'Проверить текст ошибки "Неверный логин или пароль"',
                "expected_result": "Отображается сообщение об ошибке",
            },
        ],
        avoid_name_tokens=("неверный пароль", "неуспешный логин", "wrong password", "невер"),
    ),
    ManualScenario(
        name="Успешная авторизация через login.html",
        description="Happy-path: валидные учётные данные, приветствие после входа.",
        steps=[
            {"body": "Открыть login.html?ru", "expected_result": "Отображается форма входа"},
            {"body": "Ввести user1 в поле логина", "expected_result": "Логин заполнен"},
            {"body": "Ввести password1 в поле пароля", "expected_result": "Пароль заполнен"},
            {"body": "Нажать кнопку submit", "expected_result": "Форма отправлена"},
            {
                "body": 'Проверить приветствие "Добро пожаловать, user1!"',
                "expected_result": "Отображается welcome-message",
            },
        ],
        avoid_name_tokens=("успешная авторизация", "валидными данными", "welcome, user1"),
    ),
]


def _looks_like_header_scenario(scenario: ManualScenario) -> bool:
    combined = " ".join(scenario.step_bodies()).lower()
    return any(token in combined for token in _HEADER_STEP_TOKENS)


def pick_scenario(existing_names: list[str]) -> ManualScenario:
    lowered = [name.lower() for name in existing_names]
    for scenario in CATALOG:
        if _looks_like_header_scenario(scenario):
            continue
        if any(token in name for name in lowered for token in scenario.avoid_name_tokens):
            continue
        if scenario.name.lower() in lowered:
            continue
        return scenario
    for scenario in CATALOG:
        if not _looks_like_header_scenario(scenario):
            return scenario
    raise RuntimeError("manual_case_catalog: no login-only scenarios configured")
