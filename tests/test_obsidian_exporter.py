import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_exporter import ObsidianExporter, slugify, _build_filename_map


SAMPLE_TRIPLETS = [
    {"subject": "Claude", "predicate": "made_by", "object": "Anthropic"},
    {"subject": "Claude", "predicate": "competes_with", "object": "GPT-4"},
    {"subject": "Anthropic", "predicate": "founded_by", "object": "Dario Amodei"},
    {"subject": "GPT-4", "predicate": "made_by", "object": "OpenAI"},
]


def test_creates_one_file_per_entity(tmp_path):
    exporter = ObsidianExporter(str(tmp_path))
    created = exporter.export(SAMPLE_TRIPLETS)
    entities = {"Claude", "Anthropic", "GPT-4", "Dario Amodei", "OpenAI"}
    assert len(created) == len(entities)


def test_wikilinks_in_outgoing(tmp_path):
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert "[[Anthropic]]" in content
    assert "[[GPT-4]]" in content


def test_incoming_relations_referenced_by(tmp_path):
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS)
    content = (tmp_path / "Anthropic.md").read_text(encoding="utf-8")
    assert "Referenced by" in content
    assert "[[Claude]] → made_by" in content


def test_metadata_source_section(tmp_path):
    metadata = {"title": "Test Video", "url": "https://youtube.com/watch?v=abc123", "channel": "Test Channel"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert "Test Video" in content
    assert "https://youtube.com/watch?v=abc123" in content
    assert 'author: "Test Channel"' in content
    assert "tags:" in content
    assert "type: entity" in content
    assert content.startswith("---")


def test_skips_incomplete_triplets(tmp_path):
    bad_triplets = [
        {"subject": "A", "predicate": "rel", "object": "B"},
        {"subject": "", "predicate": "rel", "object": "C"},
        {"subject": "D", "predicate": "", "object": "E"},
        {"subject": "F", "predicate": "rel", "object": ""},
    ]
    exporter = ObsidianExporter(str(tmp_path))
    created = exporter.export(bad_triplets)
    assert len(created) == 2  # only A and B


def test_slugify_removes_bad_chars():
    assert slugify('Entity: "Test"') == "Entity_ _Test_"
    assert slugify("Normal Name") == "Normal Name"
    assert slugify("Path/To/Thing") == "Path_To_Thing"


def test_slugify_strips_trailing_dot():
    assert slugify("Version 1.0.") == "Version 1.0"
    assert slugify("name.") == "name"


def test_slugify_strips_tab():
    assert slugify("Entity\tName") == "Entity_Name"


def test_output_dir_created(tmp_path):
    nested = tmp_path / "deep" / "nested"
    exporter = ObsidianExporter(str(nested))
    exporter.export(SAMPLE_TRIPLETS)
    assert nested.exists()


def test_frontmatter_without_metadata(tmp_path):
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "type: entity" in content
    assert "youtube-to-knowledge" in content
    assert "source_title" not in content
    assert "author" not in content


def test_yaml_safe_with_quotes_in_title(tmp_path):
    metadata = {"title": 'He said "hello" to AI', "url": "https://youtube.com/watch?v=abc", "channel": 'Channel "Official"'}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert 'source_title: "He said \\"hello\\" to AI"' in content
    assert 'author: "Channel \\"Official\\""' in content


def test_yaml_safe_with_url_fragment(tmp_path):
    metadata = {"title": "Video", "url": "https://youtube.com/watch?v=abc#t=30"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert 'source_url: "https://youtube.com/watch?v=abc#t=30"' in content


def test_webpage_url_fallback(tmp_path):
    metadata = {"title": "Video", "webpage_url": "https://youtube.com/watch?v=xyz"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert "xyz" in content


def test_id_url_fallback(tmp_path):
    metadata = {"title": "Video", "id": "abc123def45"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert "https://www.youtube.com/watch?v=abc123def45" in content


def test_non_ascii_channel_tag_omitted(tmp_path):
    # Channel name that slugifies to empty string must not emit an empty tag
    metadata = {"title": "Video", "channel": "日本語チャンネル"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    # Tags block must not contain a bare "  - " with nothing after it
    for line in content.splitlines():
        if line.startswith("  - "):
            assert line.strip() != "-", f"Empty tag found: {repr(line)}"


def test_filename_collision_resolved(tmp_path):
    # "A:B" and "A/B" both slugify to "A_B" — must produce two distinct files
    colliding_triplets = [
        {"subject": "A:B", "predicate": "rel", "object": "X"},
        {"subject": "A/B", "predicate": "rel", "object": "X"},
    ]
    exporter = ObsidianExporter(str(tmp_path))
    created = exporter.export(colliding_triplets)
    filenames = [Path(p).name for p in created]
    assert len(filenames) == len(set(filenames)), "Filename collision: two entities wrote the same file"


def test_wikilink_uses_aliased_format_for_special_chars(tmp_path):
    # Entity with ":" in name — wikilink must point to slugified filename, not raw name
    triplets = [
        {"subject": "Tool", "predicate": "uses", "object": "React: v18"},
    ]
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(triplets)
    content = (tmp_path / "Tool.md").read_text(encoding="utf-8")
    # Must use aliased wikilink [[slug|display]] so Obsidian resolves the file
    assert "[[React_ v18|React: v18]]" in content


def test_duplicate_triplets_deduplicated(tmp_path):
    # Same triplet twice must appear only once in output
    triplets = [
        {"subject": "Claude", "predicate": "made_by", "object": "Anthropic"},
        {"subject": "Claude", "predicate": "made_by", "object": "Anthropic"},
    ]
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(triplets)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert content.count("made_by: [[Anthropic]]") == 1


def test_empty_triplets_returns_empty_list(tmp_path):
    exporter = ObsidianExporter(str(tmp_path))
    created = exporter.export([])
    assert created == []


def test_markdown_safe_title_in_source_link(tmp_path):
    # Title with ] breaks Markdown link syntax — must be escaped
    metadata = {"title": "[Tutorial] React 18", "url": "https://youtube.com/watch?v=abc"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert "[\\[Tutorial\\] React 18](https://youtube.com/watch?v=abc)" in content
