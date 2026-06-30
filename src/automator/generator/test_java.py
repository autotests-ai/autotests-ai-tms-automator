import re
from dataclasses import dataclass
from typing import Any

from automator.generator.naming import TestNames, build_test_names


@dataclass(frozen=True)
class GeneratedTest:
    names: TestNames
    method_source: str
    page_path: str
    test_case_name: str
    test_case_id: int
    tag: str
    step_bodies: list[str]

    @property
    def qualified_class_name(self) -> str:
        return self.names.qualified_class_name

    @property
    def qualified_test_name(self) -> str:
        return self.names.qualified_test_name


def _extract_page_path(steps: list[str]) -> str:
    for step in steps:
        match = re.search(r"one-page-form/([^\s\"']+)", step)
        if match:
            path = match.group(1)
            if path == "login.html":
                return "login.html?ru"
            return path
        match = re.search(r"([\w-]+\.html(?:\?\w+)?)", step)
        if match:
            path = match.group(1)
            if path == "login.html":
                return "login.html?ru"
            return path
    return "login.html?ru"


def _normalize_expected_text(text: str, page_path: str) -> str:
    if "?ru" not in page_path:
        return text
    translations = {
        "Wrong login or password": "Неверный логин или пароль",
        "Welcome, user1!": "Добро пожаловать, user1!",
    }
    return translations.get(text, text)


def _build_step_blocks(step_bodies: list[str], page_constant: str, page_path: str) -> str:
    step_blocks: list[str] = []
    for index, body in enumerate(step_bodies, start=1):
        escaped = body.replace('"', '\\"')
        if index == 1 and "открыть" in body.lower():
            step_blocks.append(
                f'        step("{escaped}", () ->\n                open({page_constant}));'
            )
        elif "ввести" in body.lower() and "логин" in body.lower():
            step_blocks.append(
                f'        step("{escaped}", () ->\n                $("[data-testid=login-input]").setValue("user1"));'
            )
        elif "парол" in body.lower() and "ввести" in body.lower():
            password = "password1"
            if "wrong" in body.lower() or "невер" in body.lower():
                password = "wrongpassword"
            step_blocks.append(
                f'        step("{escaped}", () ->\n                $("[data-testid=password-input]").setValue("{password}"));'
            )
        elif "submit" in body.lower() or "кнопку" in body.lower():
            step_blocks.append(
                f'        step("{escaped}", () ->\n                $("[data-testid=submit-button]").click());'
            )
        elif "провер" in body.lower():
            expected_match = re.search(r'"([^"]+)"', body)
            expected = expected_match.group(1) if expected_match else "..."
            expected = _normalize_expected_text(expected, page_path)
            selector = "welcome-message" if "привет" in body.lower() or "welcome" in body.lower() else "error-message"
            step_blocks.append(
                f'        step("{escaped}", () ->\n                $("[data-testid={selector}]").shouldHave(text("{expected}")));'
            )
        else:
            step_blocks.append(
                f'        step("{escaped}", () ->\n                fail("Шаг не распознан генератором — добавьте правило в automator или реализуйте вручную"));'
            )
    return "\n\n".join(step_blocks)


def build_test_method(
    names: TestNames,
    test_case_id: int,
    test_case_name: str,
    step_bodies: list[str],
    page_path: str,
    tag: str,
    page_constant: str | None = None,
) -> str:
    constant = page_constant or names.page_constant
    steps_joined = _build_step_blocks(step_bodies, constant, page_path)
    return f"""    @Test
    @AllureId("{test_case_id}")
    @Tag("{tag}")
    @DisplayName("{test_case_name}")
    void {names.method_name}() {{
{steps_joined}
    }}"""


def build_test_class_file(
    names: TestNames,
    test_case_id: int,
    test_case_name: str,
    step_bodies: list[str],
    page_path: str,
    tag: str,
) -> str:
    method_source = build_test_method(names, test_case_id, test_case_name, step_bodies, page_path, tag)
    return f"""package tests;

import annotations.Layer;
import io.qameta.allure.AllureId;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.fail;
import static com.codeborne.selenide.Selenide.open;
import static io.qameta.allure.Allure.step;

@Layer("e2e")
@Epic("{names.epic}")
@Feature("{names.feature}")
@DisplayName("{names.class_display_name}")
public class {names.class_name} extends TestBase {{

    private static final String {names.page_constant} = "{page_path}";

{method_source}
}}
"""


def generate_test_java(
    test_case_id: int,
    test_case: dict[str, Any],
    step_bodies: list[str],
) -> GeneratedTest:
    name = (test_case.get("name") or f"Test case {test_case_id}").strip()
    names = build_test_names(name, step_bodies, test_case_id)
    page_path = _extract_page_path(step_bodies)
    tag = "negative" if any(word in name.lower() for word in ("неусп", "невер", "wrong", "fail")) else "positive"
    method_source = build_test_method(names, test_case_id, name, step_bodies, page_path, tag)

    return GeneratedTest(
        names=names,
        method_source=method_source,
        page_path=page_path,
        test_case_name=name,
        test_case_id=test_case_id,
        tag=tag,
        step_bodies=step_bodies,
    )
