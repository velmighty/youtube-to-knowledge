import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_exporter import ObsidianExporter, slugify


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
    assert "[[Claude]]" in content


def test_metadata_source_section(tmp_path):
    metadata = {"title": "Test Video", "url": "https://youtube.com/watch?v=abc123"}
    exporter = ObsidianExporter(str(tmp_path))
    exporter.export(SAMPLE_TRIPLETS, metadata)
    content = (tmp_path / "Claude.md").read_text(encoding="utf-8")
    assert "Test Video" in content
    assert "https://youtube.com/watch?v=abc123" in content


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


def test_output_dir_created(tmp_path):
    nested = tmp_path / "deep" / "nested"
    exporter = ObsidianExporter(str(nested))
    exporter.export(SAMPLE_TRIPLETS)
    assert nested.exists()
