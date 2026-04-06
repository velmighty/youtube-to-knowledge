import json
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_extractor import GraphExtractor


def test_add_triplet_creates_edge(tmp_path):
    g = GraphExtractor(str(tmp_path))
    g.add_triplet("Claude", "made_by", "Anthropic")
    assert g.graph.has_edge("Claude", "Anthropic")
    assert g.graph["Claude"]["Anthropic"]["label"] == "made_by"


def test_add_multiple_triplets(tmp_path):
    g = GraphExtractor(str(tmp_path))
    g.add_triplet("A", "rel1", "B")
    g.add_triplet("B", "rel2", "C")
    assert g.graph.number_of_nodes() == 3
    assert g.graph.number_of_edges() == 2


def test_save_and_load_json(tmp_path):
    g = GraphExtractor(str(tmp_path))
    g.add_triplet("X", "has", "Y")
    g.save_json()

    g2 = GraphExtractor(str(tmp_path))
    loaded = g2.load_json()
    assert loaded is True
    assert g2.graph.has_edge("X", "Y")


def test_load_json_returns_false_when_missing(tmp_path):
    g = GraphExtractor(str(tmp_path))
    assert g.load_json() is False


def test_save_json_format(tmp_path):
    g = GraphExtractor(str(tmp_path))
    g.add_triplet("Node1", "connects", "Node2")
    g.save_json()

    with open(tmp_path / "graph.json", encoding="utf-8") as f:
        data = json.load(f)
    assert "nodes" in data
    assert "links" in data
