"""Runtime root resolution for Docker (site-packages) vs editable src layout."""

from __future__ import annotations

from pathlib import Path

from automator.config import Settings, resolve_runtime_root


def test_resolve_runtime_root_finds_repo_templates() -> None:
    root = resolve_runtime_root()
    assert (root / "templates" / "tests-java").is_dir()
    assert (root / "docs" / "rag").is_dir()


def test_resolve_path_absolute_and_relative(tmp_path: Path) -> None:
    settings = Settings(
        allure_api_token="token",
        _env_file=None,
    )
    absolute = settings.resolve_path(str(tmp_path / "abs"), runtime_root=tmp_path)
    assert absolute == (tmp_path / "abs").resolve()

    relative = settings.resolve_path("rel/dir", runtime_root=tmp_path)
    assert relative == (tmp_path / "rel" / "dir").resolve()
