import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import spacy
from spacy.lang.en import English
from spacy.pipeline import EntityRuler


class EnhancedEntityExtractor:
    """Enhanced entity extraction using spaCy for NER and relationship extraction."""

    def __init__(self, model: str = "en_core_web_sm"):
        """Initialize with spaCy model.

        Args:
            model: spaCy model name (default: en_core_web_sm)
        """
        if not SPACY_AVAILABLE:
            raise ImportError(
                "spaCy is required for enhanced entity extraction. "
                "Install with: pip install spacy && python -m spacy download en_core_web_sm"
            )

        try:
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Model {model} not found. Installing...")
            os.system(f"{sys.executable} -m spacy download {model}")
            self.nlp = spacy.load(model)

        # Add custom entity patterns for common tech/AI terms
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        tech_patterns = [
            {"label": "TECH", "pattern": "Claude"},
            {"label": "TECH", "pattern": "GPT"},
            {"label": "TECH", "pattern": "ChatGPT"},
            {"label": "TECH", "pattern": "OpenAI"},
            {"label": "TECH", "pattern": "Anthropic"},
            {"label": "TECH", "pattern": "Python"},
            {"label": "TECH", "pattern": "JavaScript"},
            {"label": "TECH", "pattern": "API"},
            {"label": "TECH", "pattern": "machine learning"},
            {"label": "TECH", "pattern": "artificial intelligence"},
            {"label": "TECH", "pattern": "neural network"},
            {"label": "ORG", "pattern": "Google"},
            {"label": "ORG", "pattern": "Microsoft"},
            {"label": "ORG", "pattern": "Apple"},
        ]
        ruler.add_patterns(tech_patterns)

        # Sentence segmenter for better processing
        self.sentencizer = English()
        self.sentencizer.add_pipe("sentencizer")

    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities from text using spaCy.

        Returns:
            List of entity dictionaries with text, label, start, end positions
        """
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

        return entities

    def extract_relationships(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """Extract relationships between entities from text.

        Uses pattern matching and dependency parsing to find relationships.

        Returns:
            List of (subject, predicate, object) tuples
        """
        doc = self.nlp(text)
        relationships = []

        # Create entity map for quick lookup
        entity_map = {ent["text"]: ent for ent in entities}

        # Process sentence by sentence
        sentences = list(self.sentencizer(text).sents)

        for sent in sentences:
            sent_doc = self.nlp(sent.text)

            # Find verb relationships
            for token in sent_doc:
                if token.pos_ == "VERB" and token.dep_ in ["ROOT", "conj"]:
                    # Find subject and object of the verb
                    subject = self._find_subject(token)
                    obj = self._find_object(token)

                    if subject and obj and subject in entity_map and obj in entity_map:
                        predicate = self._normalize_predicate(token.lemma_)
                        if predicate:
                            relationships.append((subject, predicate, obj))

            # Find possessive relationships (X's Y)
            for token in sent_doc:
                if token.dep_ == "poss":
                    possessor = token.text
                    possessed = self._find_head_noun(token.head)
                    if possessor in entity_map and possessed and possessed in entity_map:
                        relationships.append((possessor, "has", possessed))

            # Find compound relationships (X Y where X and Y are entities)
            for chunk in sent_doc.noun_chunks:
                entities_in_chunk = [ent for ent in entities
                                   if ent["start"] >= chunk.start_char and ent["end"] <= chunk.end_char]
                if len(entities_in_chunk) >= 2:
                    for i in range(len(entities_in_chunk) - 1):
                        ent1 = entities_in_chunk[i]["text"]
                        ent2 = entities_in_chunk[i + 1]["text"]
                        # Check if they're related (close proximity)
                        if abs(entities_in_chunk[i]["end"] - entities_in_chunk[i + 1]["start"]) < 50:
                            relationships.append((ent1, "related_to", ent2))

        return relationships

    def _find_subject(self, verb_token) -> str:
        """Find the subject of a verb token."""
        for child in verb_token.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                return self._get_full_entity_text(child)
        return None

    def _find_object(self, verb_token) -> str:
        """Find the object of a verb token."""
        for child in verb_token.children:
            if child.dep_ in ["dobj", "pobj", "attr"]:
                return self._get_full_entity_text(child)
        return None

    def _find_head_noun(self, token) -> str:
        """Find the head noun of a token."""
        while token and token.pos_ not in ["NOUN", "PROPN"]:
            token = token.head
        return token.text if token else None

    def _get_full_entity_text(self, token) -> str:
        """Get the full text of an entity including modifiers."""
        text = token.text
        # Include compound nouns
        for child in token.children:
            if child.dep_ == "compound":
                text = child.text + " " + text
        return text

    def _normalize_predicate(self, lemma: str) -> str:
        """Normalize verb lemmas to standard relationship predicates."""
        predicate_map = {
            "create": "created",
            "develop": "developed",
            "build": "built",
            "found": "founded",
            "work": "works_for",
            "use": "uses",
            "recommend": "recommends",
            "compete": "competes_with",
            "own": "owns",
            "lead": "leads",
            "manage": "manages",
            "produce": "produces",
            "provide": "provides",
            "offer": "offers",
            "sell": "sells",
            "buy": "buys",
            "invest": "invests_in",
            "acquire": "acquired",
            "merge": "merged_with",
            "partner": "partners_with",
            "collaborate": "collaborates_with",
        }
        return predicate_map.get(lemma, lemma + "s")

    def extract_triplets(self, text: str, max_triplets: int = 20) -> List[Dict]:
        """Extract triplets from text using enhanced NLP.

        Args:
            text: Input text (transcript)
            max_triplets: Maximum number of triplets to extract

        Returns:
            List of triplet dictionaries
        """
        # Extract entities
        entities = self.extract_entities(text)

        # Extract relationships
        relationships = self.extract_relationships(text, entities)

        # Convert to triplet format
        triplets = []
        seen = set()  # Avoid duplicates

        for subject, predicate, obj in relationships:
            triplet_key = (subject, predicate, obj)
            if triplet_key not in seen and len(triplets) < max_triplets:
                triplets.append({
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj
                })
                seen.add(triplet_key)

        return triplets

    def merge_with_existing(self, new_triplets: List[Dict], existing_file: str = None) -> List[Dict]:
        """Merge new triplets with existing ones, avoiding duplicates."""
        if existing_file and os.path.exists(existing_file):
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_triplets = json.load(f)
        else:
            existing_triplets = []

        # Create set of existing triplet tuples
        existing_set = {(t["subject"], t["predicate"], t["object"]) for t in existing_triplets}

        # Add new triplets that don't exist
        merged = existing_triplets.copy()
        for triplet in new_triplets:
            triplet_tuple = (triplet["subject"], triplet["predicate"], triplet["object"])
            if triplet_tuple not in existing_set:
                merged.append(triplet)

        return merged


def main():
    parser = argparse.ArgumentParser(description="Enhanced Entity Extraction using spaCy")
    parser.add_argument("transcript_file", help="Path to transcript text file")
    parser.add_argument("--output", "-o", help="Output JSON file for triplets")
    parser.add_argument("--max-triplets", type=int, default=20,
                       help="Maximum number of triplets to extract (default: 20)")
    parser.add_argument("--merge", help="Merge with existing triplets file")
    parser.add_argument("--model", default="en_core_web_sm",
                       help="spaCy model to use (default: en_core_web_sm)")

    args = parser.parse_args()

    # Read transcript
    with open(args.transcript_file, 'r', encoding='utf-8') as f:
        transcript = f.read()

    # Initialize extractor
    extractor = EnhancedEntityExtractor(model=args.model)

    # Extract triplets
    triplets = extractor.extract_triplets(transcript, max_triplets=args.max_triplets)

    # Merge with existing if specified
    if args.merge:
        triplets = extractor.merge_with_existing(triplets, args.merge)

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(triplets, f, indent=2, ensure_ascii=False)
        print(f"Extracted {len(triplets)} triplets saved to {args.output}")
    else:
        print(json.dumps(triplets, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()