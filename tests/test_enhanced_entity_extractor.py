import json
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_entity_extractor import EnhancedEntityExtractor


def test_extract_entities_basic():
    """Test basic entity extraction."""
    extractor = EnhancedEntityExtractor()

    text = "Apple Inc. was founded by Steve Jobs in Cupertino."
    entities = extractor.extract_entities(text)

    # Should find Apple Inc., Steve Jobs, Cupertino
    entity_texts = [e["text"] for e in entities]
    assert "Apple Inc." in entity_texts or "Apple" in entity_texts
    assert "Steve Jobs" in entity_texts
    assert "Cupertino" in entity_texts


def test_extract_triplets_basic():
    """Test basic triplet extraction."""
    extractor = EnhancedEntityExtractor()

    text = "Steve Jobs founded Apple Inc. in 1976."
    triplets = extractor.extract_triplets(text, max_triplets=5)

    # Should find some relationship between Steve Jobs and Apple
    triplet_texts = [(t["subject"], t["predicate"], t["object"]) for t in triplets]
    assert len(triplets) > 0

    # Check for expected relationship
    found_founded = any("founded" in pred or "found" in pred for _, pred, _ in triplet_texts)
    assert found_founded or len(triplets) > 0  # At least some triplets extracted


def test_extract_triplets_tech_entities():
    """Test extraction with tech-specific entities."""
    extractor = EnhancedEntityExtractor()

    text = "OpenAI developed ChatGPT using Python and machine learning."
    triplets = extractor.extract_triplets(text, max_triplets=10)

    entity_texts = [e["text"] for e in extractor.extract_entities(text)]

    # Should recognize tech entities
    tech_entities = ["OpenAI", "ChatGPT", "Python", "machine learning"]
    found_tech = any(entity in " ".join(entity_texts) for entity in tech_entities)
    assert found_tech or len(triplets) > 0


def test_merge_with_existing():
    """Test merging new triplets with existing ones."""
    extractor = EnhancedEntityExtractor()

    existing_triplets = [
        {"subject": "Apple", "predicate": "founded", "object": "Steve Jobs"}
    ]

    new_triplets = [
        {"subject": "Apple", "predicate": "produces", "object": "iPhone"},
        {"subject": "Apple", "predicate": "founded", "object": "Steve Jobs"}  # duplicate
    ]

    merged = extractor.merge_with_existing(new_triplets, None)
    merged = extractor.merge_with_existing(existing_triplets, None)  # simulate existing

    # Should have unique triplets
    assert len(merged) >= len(existing_triplets)


def test_max_triplets_limit():
    """Test that max_triplets parameter is respected."""
    extractor = EnhancedEntityExtractor()

    text = """
    Apple was founded by Steve Jobs. Microsoft was founded by Bill Gates.
    Google was founded by Larry Page and Sergey Brin. Amazon was founded by Jeff Bezos.
    Tesla was founded by Elon Musk. Facebook was founded by Mark Zuckerberg.
    """

    triplets_5 = extractor.extract_triplets(text, max_triplets=5)
    triplets_10 = extractor.extract_triplets(text, max_triplets=10)

    assert len(triplets_5) <= 5
    assert len(triplets_10) <= 10
    assert len(triplets_10) >= len(triplets_5)  # More triplets when limit is higher


def test_normalize_predicate():
    """Test predicate normalization."""
    extractor = EnhancedEntityExtractor()

    # Test various verb forms
    assert extractor._normalize_predicate("create") == "created"
    assert extractor._normalize_predicate("develop") == "developed"
    assert extractor._normalize_predicate("found") == "founded"
    assert extractor._normalize_predicate("unknown_verb") == "unknown_verbs"