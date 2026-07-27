"""Sync vendored RAG from zero-design-system into this repo."""

from __future__ import annotations

import shutil
from pathlib import Path

_ADR_FILES = (
    "002-e2e-canonical-patterns.md",
    "003-header-smoke-e2e.md",
)


def copy_rag_bundle(rag_source: Path, dest_repo_root: Path) -> None:
    """Copy canonical RAG chunks (+ ADR 002/003) into a consumer repo root."""
    rag_dest = dest_repo_root / "docs" / "rag"
    if rag_dest.exists():
        shutil.rmtree(rag_dest)
    shutil.copytree(rag_source, rag_dest)

    adr_source = rag_source.parent / "adr"
    adr_dest = dest_repo_root / "docs" / "adr"
    adr_dest.mkdir(parents=True, exist_ok=True)
    for filename in _ADR_FILES:
        source = adr_source / filename
        if source.is_file():
            shutil.copy2(source, adr_dest / filename)


def template_rag_source(template_project_dir: Path) -> Path:
    return template_project_dir / "docs" / "rag"


def sync_rag_from_template(template_project_dir: Path, repo_root: Path) -> Path:
    """Refresh vendored docs/rag from zero-design-system SSOT."""
    source = template_rag_source(template_project_dir)
    if not source.is_dir():
        raise FileNotFoundError(f"RAG source missing: {source}")
    copy_rag_bundle(source, repo_root)
    return repo_root / "docs" / "rag"


def _collect_files(root: Path) -> dict[Path, Path]:
    if not root.exists():
        return {}
    return {path.relative_to(root): path for path in root.rglob("*") if path.is_file()}


def rag_bundle_diff(template_project_dir: Path, repo_root: Path) -> list[str]:
    """Return human-readable diff lines; empty list means vendored copy is in sync."""
    source_root = template_rag_source(template_project_dir)
    dest_root = repo_root / "docs" / "rag"
    issues: list[str] = []

    source_files = _collect_files(source_root)
    dest_files = _collect_files(dest_root)

    for rel in sorted(source_files):
        if rel not in dest_files:
            issues.append(f"missing: docs/rag/{rel.as_posix()}")
            continue
        if source_files[rel].read_bytes() != dest_files[rel].read_bytes():
            issues.append(f"changed: docs/rag/{rel.as_posix()}")

    for rel in sorted(dest_files):
        if rel not in source_files:
            issues.append(f"extra: docs/rag/{rel.as_posix()}")

    adr_source = template_project_dir / "docs" / "adr"
    adr_dest = repo_root / "docs" / "adr"
    for filename in _ADR_FILES:
        source = adr_source / filename
        target = adr_dest / filename
        if not source.is_file():
            continue
        if not target.is_file():
            issues.append(f"missing: docs/adr/{filename}")
        elif source.read_bytes() != target.read_bytes():
            issues.append(f"changed: docs/adr/{filename}")

    return issues
