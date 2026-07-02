from pathlib import Path

from automator.github.template import prepare_bootstrap_workdir, should_exclude_consumer_test_file


def test_should_exclude_consumer_test_file():
    assert not should_exclude_consumer_test_file(Path("src/test/java/tests/TestBase.java"))
    assert should_exclude_consumer_test_file(Path("src/test/java/tests/LoginTests.java"))
    assert not should_exclude_consumer_test_file(Path("src/test/java/config/ConfigReaderTest.java"))


def test_prepare_bootstrap_workdir_trims_etalon(tmp_path: Path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"

    (source / "src/test/java/tests").mkdir(parents=True)
    (source / "src/test/java/pages").mkdir(parents=True)
    (source / "src/test/java/tests/component").mkdir(parents=True)
    (source / "src/test/resources/screenshots/login").mkdir(parents=True)
    (source / "src/test/java/config").mkdir(parents=True)
    (source / "build").mkdir()

    (source / "src/test/java/tests/TestBase.java").write_text("class TestBase {}")
    (source / "src/test/java/tests/LoginTests.java").write_text("class LoginTests {}")
    (source / "src/test/java/pages/LoginPage.java").write_text("class LoginPage {}")
    (source / "src/test/java/tests/component/LangToggleTests.java").write_text("class LangToggleTests {}")
    (source / "src/test/java/config/ConfigReaderTest.java").write_text("class ConfigReaderTest {}")
    (source / "src/test/resources/screenshots/login/1280.png").write_bytes(b"png")
    (source / "build/report.html").write_text("skip")
    (source / "history.jsonl").write_text("skip")
    (source / "build.gradle").write_text("plugins {}")

    prepare_bootstrap_workdir(source, dest)

    assert (dest / "src/test/java/tests/TestBase.java").exists()
    assert not (dest / "src/test/java/tests/LoginTests.java").exists()
    assert not (dest / "src/test/java/pages").exists()
    assert not (dest / "src/test/java/tests/component").exists()
    assert not (dest / "src/test/resources/screenshots").exists()
    assert not (dest / "src/test/java/config/ConfigReaderTest.java").exists()
    assert not (dest / "build").exists()
    assert not (dest / "history.jsonl").exists()
    assert (dest / "build.gradle").exists()


def test_prepare_bootstrap_workdir_copies_rag_bundle(tmp_path: Path):
    source = tmp_path / "source"
    rag_source = tmp_path / "rag"
    dest = tmp_path / "dest"

    (source / "src/test/java/tests").mkdir(parents=True)
    (source / "src/test/java/tests/TestBase.java").write_text("class TestBase {}")
    (source / "build.gradle").write_text("plugins {}")

    (rag_source / "e2e").mkdir(parents=True)
    (rag_source / "e2e-header").mkdir(parents=True)
    (rag_source / "e2e/test-taxonomy.md").write_text("taxonomy")
    (rag_source / "manifest.jsonl").write_text('{"id":"test-taxonomy","path":"docs/rag/e2e/test-taxonomy.md"}')
    (rag_source.parent / "adr").mkdir(parents=True)
    (rag_source.parent / "adr" / "002-e2e-canonical-patterns.md").write_text("adr")

    prepare_bootstrap_workdir(source, dest, rag_source=rag_source)

    assert (dest / "docs/rag/e2e/test-taxonomy.md").read_text() == "taxonomy"
    assert (dest / "docs/rag/manifest.jsonl").exists()
    assert (dest / "docs/adr/002-e2e-canonical-patterns.md").read_text() == "adr"
