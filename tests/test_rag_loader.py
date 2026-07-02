from pathlib import Path

from automator.rag.loader import bootstrap_chunk_ids, load_bootstrap_context, resolve_chunks_by_ids


def test_bootstrap_chunk_ids_are_stable():
    assert "test-taxonomy" in bootstrap_chunk_ids()
    assert "po-locators" in bootstrap_chunk_ids()


def test_load_bootstrap_context_from_fixture(tmp_path: Path):
    rag_dir = tmp_path / "docs" / "rag"
    (rag_dir / "e2e").mkdir(parents=True)
    (rag_dir / "e2e" / "test-taxonomy.md").write_text("---\nid: test-taxonomy\n---\n# Taxonomy")
    (rag_dir / "manifest.jsonl").write_text(
        '{"id":"test-taxonomy","path":"docs/rag/e2e/test-taxonomy.md","domain":"e2e","phase":"4a","tags":["pattern"]}\n'
    )

    chunks = resolve_chunks_by_ids(rag_dir, ["test-taxonomy"])
    assert len(chunks) == 1
    assert chunks[0].id == "test-taxonomy"
    assert "Taxonomy" in chunks[0].content

    bootstrap = load_bootstrap_context(rag_dir)
    assert any(chunk.id == "test-taxonomy" for chunk in bootstrap)
