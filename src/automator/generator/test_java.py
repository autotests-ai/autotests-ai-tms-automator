import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from automator.generator.naming import TestNames, build_test_names
from automator.rag.policy import GeneratorPolicy, load_generator_policy


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


def _extract_page_path(steps: list[str], policy: GeneratorPolicy) -> str:
    for step in steps:
        match = re.search(r"one-page-form/([^\s\"']+)", step)
        if match:
            return policy.normalize_page_path(match.group(1))
        match = re.search(r"([\w-]+\.html(?:\?\w+)?)", step)
        if match:
            return policy.normalize_page_path(match.group(1))
    return policy.default_page_path


def _build_step_blocks(
    step_bodies: list[str],
    page_constant: str,
    page_path: str,
    policy: GeneratorPolicy,
) -> str:
    step_blocks: list[str] = []
    login_testid = policy.locator("login_input")
    password_testid = policy.locator("password_input")
    submit_testid = policy.locator("submit_button")

    for index, body in enumerate(step_bodies, start=1):
        escaped = body.replace('"', '\\"')
        lowered = body.lower()
        if index == 1 and "открыть" in lowered:
            step_blocks.append(
                f'        step("{escaped}", () ->\n                open("{page_path}"));'
            )
        elif login_testid in body or f"data-testid={login_testid}" in lowered or (
            "ввести" in lowered and "логин" in lowered
        ):
            user = policy.credential("valid_user")
            step_blocks.append(
                f'        step("{escaped}", () ->\n'
                f'                $("[data-testid={login_testid}]").setValue("{user}"));'
            )
        elif password_testid in body or f"data-testid={password_testid}" in lowered or (
            "парол" in lowered and "ввести" in lowered
        ):
            password = policy.credential("valid_password")
            if "wrong" in lowered or "невер" in lowered:
                password = policy.credential("wrong_password")
            step_blocks.append(
                f'        step("{escaped}", () ->\n'
                f'                $("[data-testid={password_testid}]").setValue("{password}"));'
            )
        elif "login-link" in body or f"data-testid=login-link" in lowered:
            step_blocks.append(
                f'        step("{escaped}", () ->\n'
                f'                $("[data-testid=login-link]").click());'
            )
        elif submit_testid in body or f"data-testid={submit_testid}" in lowered or "кнопку" in lowered:
            step_blocks.append(
                f'        step("{escaped}", () ->\n'
                f'                $("[data-testid={submit_testid}]").click());'
            )
        elif "провер" in lowered:
            expected_match = re.search(r'"([^"]+)"', body)
            if not expected_match:
                expected_match = re.search(
                    r"((?:Welcome|Добро пожаловать)[^!\n\"]*!|Wrong login or password|Неверный логин или пароль)",
                    body,
                    re.IGNORECASE,
                )
            expected = expected_match.group(1).strip() if expected_match else "..."
            expected = policy.translate_expected(expected, page_path)
            selector = policy.resolve_assert_testid(body)
            step_blocks.append(
                f'        step("{escaped}", () ->\n'
                f'                $("[data-testid={selector}]").shouldHave(text("{expected}")));'
            )
        else:
            step_blocks.append(
                f'        step("{escaped}", () ->\n'
                f'                fail("Шаг не распознан генератором — добавьте правило в '
                f'gen-python-policy.json или реализуйте вручную"));'
            )
    return "\n\n".join(step_blocks)


def build_test_method(
    names: TestNames,
    test_case_id: int,
    test_case_name: str,
    step_bodies: list[str],
    page_path: str,
    tag: str,
    policy: GeneratorPolicy,
    page_constant: str | None = None,
) -> str:
    constant = page_constant or names.page_constant
    steps_joined = _build_step_blocks(step_bodies, constant, page_path, policy)
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
    policy: GeneratorPolicy,
) -> str:
    method_source = build_test_method(
        names, test_case_id, test_case_name, step_bodies, page_path, tag, policy
    )
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

@Layer("{policy.layer}")
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
    *,
    rag_dir: Path | None = None,
    policy: GeneratorPolicy | None = None,
) -> GeneratedTest:
    resolved_policy = policy or load_generator_policy(rag_dir)
    name = (test_case.get("name") or f"Test case {test_case_id}").strip()
    names = build_test_names(name, step_bodies, test_case_id)
    if names.epic != resolved_policy.default_epic:
        names = replace(names, epic=resolved_policy.default_epic)
    page_path = _extract_page_path(step_bodies, resolved_policy)
    tag = resolved_policy.infer_tag(name)
    method_source = build_test_method(
        names, test_case_id, name, step_bodies, page_path, tag, resolved_policy
    )

    return GeneratedTest(
        names=names,
        method_source=method_source,
        page_path=page_path,
        test_case_name=name,
        test_case_id=test_case_id,
        tag=tag,
        step_bodies=step_bodies,
    )
