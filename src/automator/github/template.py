"""Prepare consumer GitHub repos from the tests-java etalon."""

from __future__ import annotations

import shutil
from pathlib import Path

from automator.rag.sync import copy_rag_bundle

# Local-only artifacts in templates/tests-java/
_COPY_IGNORE = shutil.ignore_patterns(
    "build",
    ".gradle",
    "bin",
    "history.jsonl",
    "app-path-local",
    "app-path-local.example",
)

_TESTS_DIR = Path("src/test/java/tests")
_PAGES_DIR = Path("src/test/java/pages")
_COMPONENT_DIR = _TESTS_DIR / "component"
_SCREENSHOTS_DIR = Path("src/test/resources/screenshots")
_TEST_BASE = _TESTS_DIR / "TestBase.java"


def _trim_test_base_for_consumer(test_base_path: Path) -> None:
    """Consumer bootstrap has no pages/ — drop PO fields from TestBase."""
    if not test_base_path.is_file():
        return
    lines = [
        line
        for line in test_base_path.read_text(encoding="utf-8").splitlines(keepends=True)
        if "import pages." not in line
        and "LoginPage loginPage" not in line
        and "LoggedInPage loggedInPage" not in line
    ]
    test_base_path.write_text("".join(lines), encoding="utf-8")


def should_exclude_consumer_test_file(path: Path) -> bool:
    """Return True for e2e/integration test classes excluded from bootstrap."""
    if path.suffix != ".java":
        return False
    if path.parent.name != "tests":
        return False
    return path.name != "TestBase.java"


def prepare_bootstrap_workdir(
    source: Path,
    dest: Path,
    *,
    rag_source: Path | None = None,
) -> None:
    """Copy tests-java etalon into a trimmed consumer project workdir."""
    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(source, dest, ignore=_COPY_IGNORE, dirs_exist_ok=False)

    pages = dest / _PAGES_DIR
    if pages.exists():
        shutil.rmtree(pages)

    component = dest / _COMPONENT_DIR
    if component.exists():
        shutil.rmtree(component)

    screenshots = dest / _SCREENSHOTS_DIR
    if screenshots.exists():
        shutil.rmtree(screenshots)

    tests_dir = dest / _TESTS_DIR
    if tests_dir.exists():
        for test_file in tests_dir.glob("*.java"):
            if should_exclude_consumer_test_file(test_file):
                test_file.unlink()

    _trim_test_base_for_consumer(dest / _TEST_BASE)

    for pattern in ("helpers/*Test.java", "config/*Test.java"):
        for test_file in (dest / "src/test/java").glob(pattern):
            test_file.unlink(missing_ok=True)

    if rag_source is not None and rag_source.is_dir():
        copy_rag_bundle(rag_source, dest)
