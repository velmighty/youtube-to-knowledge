import json
import os
import re
from collections import defaultdict


def slugify(name: str) -> str:
    """Convert entity name to a safe filename (preserve case, replace bad chars)."""
    return re.sub(r'[<>:"/\\|?*\n\r]', "_", name).strip()


class ObsidianExporter:
    """Exports triplets.json to Obsidian-compatible markdown files with [[wikilinks]]."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, triplets: list[dict], metadata: dict | None = None) -> list[str]:
        """Generate one .md file per entity from a list of triplets.

        Each file contains:
        - outgoing relations: what this entity does / is / has
        - incoming relations: what other entities say about this one
        - [[wikilinks]] to all related entities

        Returns list of created file paths.
        """
        outgoing: dict[str, list[tuple[str, str]]] = defaultdict(list)
        incoming: dict[str, list[tuple[str, str]]] = defaultdict(list)
        all_entities: set[str] = set()

        for t in triplets:
            subj = t.get("subject", "").strip()
            pred = t.get("predicate", "").strip()
            obj = t.get("object", "").strip()
            if not (subj and pred and obj):
                continue
            outgoing[subj].append((pred, obj))
            incoming[obj].append((pred, subj))
            all_entities.update([subj, obj])

        created: list[str] = []
        for entity in sorted(all_entities):
            path = self._write_entity_file(entity, outgoing[entity], incoming[entity], metadata)
            created.append(path)

        return created

    def _write_entity_file(
        self,
        entity: str,
        out_rels: list[tuple[str, str]],
        in_rels: list[tuple[str, str]],
        metadata: dict | None,
    ) -> str:
        filename = slugify(entity) + ".md"
        path = os.path.join(self.output_dir, filename)

        lines: list[str] = []
        lines.append(f"# {entity}\n")

        if metadata:
            source_title = metadata.get("title", "")
            source_url = metadata.get("url", "")
            if source_title or source_url:
                lines.append("## Source\n")
                if source_title and source_url:
                    lines.append(f"- [{source_title}]({source_url})\n")
                elif source_title:
                    lines.append(f"- {source_title}\n")
                elif source_url:
                    lines.append(f"- {source_url}\n")
                lines.append("")

        if out_rels:
            lines.append("## Relations\n")
            for pred, obj in sorted(out_rels):
                lines.append(f"- {pred}: [[{obj}]]\n")
            lines.append("")

        if in_rels:
            lines.append("## Referenced by\n")
            for pred, subj in sorted(in_rels):
                lines.append(f"- [[{subj}]] {pred} this\n")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return path


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Export triplets.json to Obsidian markdown files"
    )
    parser.add_argument("triplets_json", help="Path to triplets.json")
    parser.add_argument("output_dir", help="Directory to write .md files into")
    parser.add_argument("--metadata", help="Path to metadata.json (optional)", default=None)
    args = parser.parse_args()

    with open(args.triplets_json, "r", encoding="utf-8") as f:
        triplets = json.load(f)

    metadata = None
    if args.metadata and os.path.exists(args.metadata):
        with open(args.metadata, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    exporter = ObsidianExporter(args.output_dir)
    created = exporter.export(triplets, metadata)

    print(f"Created {len(created)} Obsidian notes in {args.output_dir}")
    for path in created:
        print(f"  {path}")


if __name__ == "__main__":
    main()
