from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from automator.testops_comments import ci_finished_comment, video_run_comment
from automator.video import find_selenoid_video_url, scan_tree_for_selenoid_video_url


class VideoCommentTests(TestCase):
    def test_ci_finished_comment_includes_selenoid_link(self) -> None:
        body = ci_finished_comment(
            run_url="https://github.com/org/repo/actions/runs/1",
            report_url="https://org.github.io/repo/reports/1/awesome/index.html",
            conclusion="success",
            video_selenoid_url="https://selenoid.autotests.cloud/video/abc-123.mp4",
            video_attachment_name="test-case-45118.mp4",
            video_attachments_tab_url="https://allure.example/project/1/test-cases/45118?tab=attachments",
        )
        self.assertIn("Selenoid", body)
        self.assertIn("https://selenoid.autotests.cloud/video/abc-123.mp4", body)
        self.assertIn("test-case-45118.mp4", body)

    def test_video_run_comment_without_video(self) -> None:
        body = video_run_comment()
        self.assertIn("не найдено", body)

    def test_find_selenoid_video_url_in_html_attach(self) -> None:
        html = (
            "<video><source src='https://selenoid.autotests.cloud/video/dead-beef.mp4'"
            " type='video/mp4'></video>"
        )
        self.assertEqual(
            find_selenoid_video_url(html),
            "https://selenoid.autotests.cloud/video/dead-beef.mp4",
        )

    def test_scan_tree_for_selenoid_video_url(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "allure-results").mkdir()
            (root / "allure-results" / "Video.html").write_text(
                "<source src='https://selenoid.autotests.cloud/video/cafe-babe.mp4'>",
                encoding="utf-8",
            )
            self.assertEqual(
                scan_tree_for_selenoid_video_url(root),
                "https://selenoid.autotests.cloud/video/cafe-babe.mp4",
            )
