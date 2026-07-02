from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from automator.generator.naming import canonical_class_name, equivalent_class_names


@dataclass(frozen=True)
class ExistingTestClass:
    file_path: Path
    class_name: str
    content: str
    method_names: frozenset[str]
    allure_ids: frozenset[str]
    page_constant: str | None


def _parse_class_name(content: str) -> str | None:
    match = re.search(r"public class (\w+) extends TestBase", content)
    return match.group(1) if match else None


def _parse_method_names(content: str) -> frozenset[str]:
    return frozenset(re.findall(r"void (\w+)\(\)", content))


def _parse_allure_ids(content: str) -> frozenset[str]:
    return frozenset(re.findall(r'@AllureId\("(\d+)"\)', content))


def _parse_page_constant(content: str) -> str | None:
    match = re.search(r"private static final String (\w+) = ", content)
    return match.group(1) if match else None


def load_existing_test_classes(tests_dir: Path) -> list[ExistingTestClass]:
    if not tests_dir.is_dir():
        return []

    classes: list[ExistingTestClass] = []
    for path in sorted(tests_dir.glob("*.java")):
        if path.name == "TestBase.java":
            continue
        content = path.read_text(encoding="utf-8")
        class_name = _parse_class_name(content)
        if not class_name:
            continue
        classes.append(
            ExistingTestClass(
                file_path=path,
                class_name=class_name,
                content=content,
                method_names=_parse_method_names(content),
                allure_ids=_parse_allure_ids(content),
                page_constant=_parse_page_constant(content),
            )
        )
    return classes


def find_equivalent_class(existing: list[ExistingTestClass], target_class_name: str) -> ExistingTestClass | None:
    equivalents = equivalent_class_names(target_class_name)
    for item in existing:
        if item.class_name in equivalents:
            return item
    return None


def has_allure_id(existing: ExistingTestClass, test_case_id: int) -> bool:
    return str(test_case_id) in existing.allure_ids


def rename_class(content: str, new_class_name: str) -> str:
    return re.sub(
        r"public class \w+ extends TestBase",
        f"public class {new_class_name} extends TestBase",
        content,
        count=1,
    )


def append_method(content: str, method_block: str) -> str:
    trimmed = content.rstrip()
    if not trimmed.endswith("}"):
        raise ValueError("Invalid Java test class: missing closing brace")
    return f"{trimmed[:-1]}\n\n{method_block}\n}}\n"


_STATIC_IMPORTS_BY_NEEDLE: tuple[tuple[str, str], ...] = (
    ("fail(", "import static com.codeborne.selenide.Selenide.fail;"),
    ("not(cssClass", "import static com.codeborne.selenide.Condition.not;"),
    ("cssClass(", "import static com.codeborne.selenide.Condition.cssClass;"),
)


def ensure_static_imports(content: str, *sources: str) -> str:
    combined = "".join(sources)
    missing = [
        import_line
        for needle, import_line in _STATIC_IMPORTS_BY_NEEDLE
        if needle in combined and import_line not in content
    ]
    if not missing:
        return content

    lines = content.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("import static"):
            insert_at = index + 1
        elif line.startswith("@") or line.startswith("public class"):
            break
    for import_line in missing:
        lines.insert(insert_at, f"{import_line}\n")
        insert_at += 1
    return "".join(lines)


def resolve_target_class(
    existing: list[ExistingTestClass],
    names: TestNames,
) -> tuple[ExistingTestClass | None, str]:
    match = find_equivalent_class(existing, names.class_name)
    if match:
        canonical = canonical_class_name(names.class_name)
        return match, canonical
    return None, names.class_name


def resolve_method_name(existing: ExistingTestClass | None, names: TestNames, test_case_id: int) -> TestNames:
    if existing is None or names.method_name not in existing.method_names:
        return names
    return names.with_method_suffix(test_case_id)


def normalize_class_file(content: str, canonical_class_name: str) -> str:
    current = _parse_class_name(content)
    if current and current != canonical_class_name:
        return rename_class(content, canonical_class_name)
    return content
