"""Load RAG chunks for e2e pattern retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RagChunk:
    id: str
    path: Path
    domain: str
    phase: str
    tags: tuple[str, ...]
    content: str


def load_manifest(rag_dir: Path) -> list[dict[str, object]]:
    manifest_path = rag_dir / "manifest.jsonl"
    if not manifest_path.is_file():
        return []

    entries: list[dict[str, object]] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def _chunk_path(rag_dir: Path, entry: dict[str, object]) -> Path:
    rel = str(entry.get("path", ""))
    if rel.startswith("docs/rag/"):
        rel = rel.removeprefix("docs/rag/")
    return rag_dir / rel


def _read_chunk(rag_dir: Path, entry: dict[str, object]) -> RagChunk | None:
    chunk_path = _chunk_path(rag_dir, entry)
    if not chunk_path.is_file():
        return None
    tags = entry.get("tags") or []
    return RagChunk(
        id=str(entry["id"]),
        path=chunk_path,
        domain=str(entry.get("domain", "")),
        phase=str(entry.get("phase", "")),
        tags=tuple(str(tag) for tag in tags),
        content=chunk_path.read_text(encoding="utf-8"),
    )


def resolve_chunks_by_ids(rag_dir: Path, chunk_ids: list[str]) -> list[RagChunk]:
    wanted = set(chunk_ids)
    chunks: list[RagChunk] = []
    for entry in load_manifest(rag_dir):
        chunk_id = str(entry.get("id", ""))
        if chunk_id not in wanted:
            continue
        chunk = _read_chunk(rag_dir, entry)
        if chunk is not None:
            chunks.append(chunk)
    return chunks


def resolve_chunks_by_tags(rag_dir: Path, tags: list[str]) -> list[RagChunk]:
    wanted = set(tags)
    chunks: list[RagChunk] = []
    for entry in load_manifest(rag_dir):
        entry_tags = {str(tag) for tag in (entry.get("tags") or [])}
        if not wanted.intersection(entry_tags):
            continue
        chunk = _read_chunk(rag_dir, entry)
        if chunk is not None:
            chunks.append(chunk)
    return chunks


def bootstrap_chunk_ids() -> list[str]:
    """Minimum RAG set before generating or bootstrapping a project repo."""
    return [
        "e2e-config-keys",
        "test-taxonomy",
        "test-style-ladder",
        "po-locators",
        "po-step",
        "base-lifecycle",
        "cfg-env-profile",
        "gen-python-policy",
    ]


def load_bootstrap_context(rag_dir: Path) -> list[RagChunk]:
    return resolve_chunks_by_ids(rag_dir, bootstrap_chunk_ids())


def load_generator_chunk_ids(rag_dir: Path) -> list[str]:
    """Chunk ids required by the Python test generator."""
    from automator.rag.policy import generator_policy_chunk_id

    return [generator_policy_chunk_id()] + [
        chunk_id
        for chunk_id in bootstrap_chunk_ids()
        if chunk_id != generator_policy_chunk_id()
    ]
