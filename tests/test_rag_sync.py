from pathlib import Path

from automator.rag.sync import rag_bundle_diff, sync_rag_from_template


def test_sync_rag_from_template(tmp_path: Path):
    template = tmp_path / "zero-design-system"
    repo = tmp_path / "automator"

    rag_source = template / "docs" / "rag"
    (rag_source / "testing").mkdir(parents=True)
    (rag_source / "testing" / "test-taxonomy.md").write_text("taxonomy")
    (rag_source / "manifest.jsonl").write_text('{"id":"test-taxonomy"}')
    adr_dir = template / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "002-e2e-canonical-patterns.md").write_text("adr")

    target = sync_rag_from_template(template, repo)

    assert (target / "testing" / "test-taxonomy.md").read_text() == "taxonomy"
    assert (repo / "docs" / "adr" / "002-e2e-canonical-patterns.md").read_text() == "adr"
    assert rag_bundle_diff(template, repo) == []


def test_rag_bundle_diff_detects_changes(tmp_path: Path):
    template = tmp_path / "zero-design-system"
    repo = tmp_path / "automator"

    rag_source = template / "docs" / "rag"
    (rag_source / "testing").mkdir(parents=True)
    (rag_source / "testing" / "test-taxonomy.md").write_text("new")
    (rag_source / "manifest.jsonl").write_text("{}")

    (repo / "docs" / "rag" / "testing").mkdir(parents=True)
    (repo / "docs" / "rag" / "testing" / "test-taxonomy.md").write_text("old")

    issues = rag_bundle_diff(template, repo)
    assert any("changed: docs/rag/testing/test-taxonomy.md" in issue for issue in issues)
