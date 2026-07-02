#!/usr/bin/env python
"""Sync vendored docs/rag from template-project (SSOT maintainer)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from automator.config import get_settings
from automator.rag.sync import rag_bundle_diff, sync_rag_from_template


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if vendored docs/rag differs from template-project",
    )
    parser.add_argument(
        "--template-project-dir",
        type=Path,
        default=None,
        help="Override TEMPLATE_PROJECT_DIR (default: from .env or built-in)",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    template_dir = args.template_project_dir or settings.resolve_template_project_dir()
    root = repo_root()

    if args.check:
        issues = rag_bundle_diff(template_dir, root)
        if issues:
            print("Vendored RAG is out of sync with template-project:", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
            print("\nRun: python scripts/sync_rag_from_template_project.py", file=sys.stderr)
            return 1
        print("Vendored RAG is in sync.")
        return 0

    target = sync_rag_from_template(template_dir, root)
    print(f"Synced {template_dir / 'docs/rag'} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
