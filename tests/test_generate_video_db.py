import json
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generate_video_db import build_database


def _make_video(tmp_path, channel_dir: str, metadata: dict):
    """Helper: create vault/content/<channel>/raw/metadata.json"""
    raw = tmp_path / channel_dir / "raw"
    raw.mkdir(parents=True)
    with open(raw / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f)


def test_empty_vault_creates_header_only(tmp_path):
    vault = tmp_path / "content"
    vault.mkdir()
    output = tmp_path / "processed_videos.md"
    count = build_database(vault, output)
    assert count == 0
    text = output.read_text(encoding="utf-8")
    assert "# Processed Videos" in text


def test_single_video_appears_in_table(tmp_path):
    vault = tmp_path / "content"
    vault.mkdir()
    _make_video(tmp_path / "content", "test_channel", {
        "channel": "Test Channel",
        "title": "Test Video",
        "id": "abc123",
        "language": "en"
    })
    output = tmp_path / "processed_videos.md"
    count = build_database(vault, output)
    assert count == 1
    text = output.read_text(encoding="utf-8")
    assert "Test Channel" in text
    assert "Test Video" in text
    assert "abc123" in text


def test_pipe_chars_in_title_are_escaped(tmp_path):
    vault = tmp_path / "content"
    vault.mkdir()
    _make_video(tmp_path / "content", "ch", {
        "channel": "Chan",
        "title": "A | B",
        "id": "xyz",
        "language": "en"
    })
    output = tmp_path / "processed_videos.md"
    build_database(vault, output)
    text = output.read_text(encoding="utf-8")
    assert "A \\| B" in text
