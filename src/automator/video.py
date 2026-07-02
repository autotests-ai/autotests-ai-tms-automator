"""Helpers for Selenoid / CI video artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SELENOID_VIDEO_URL = re.compile(r"https://[^\s\"'<>]+/video/[a-f0-9-]+\.mp4", re.IGNORECASE)


@dataclass(frozen=True)
class VideoCapture:
    path: Path | None
    selenoid_url: str | None = None
    attachment_name: str | None = None


def find_selenoid_video_url(text: str) -> str | None:
    match = SELENOID_VIDEO_URL.search(text)
    return match.group(0) if match else None


def scan_tree_for_selenoid_video_url(root: Path) -> str | None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".json", ".txt", ".xml", ".log"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        url = find_selenoid_video_url(content)
        if url:
            return url
    return None
