import argparse
import json
import os
import re
import sys
from collections import defaultdict


def slugify(name: str) -> str:
    """Convert entity name to a safe filename.

    Strips characters illegal on Windows/macOS/Linux and in Obsidian,
    including tabs, trailing dots, and trailing spaces.
    """
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', "_", name).strip().rstrip(".")
    return name or "_"


def _build_filename_map(entities: set[str]) -> dict[str, str]:
    """Assign a unique filename slug to each entity, handling collisions."""
    slug_count: dict[str, int] = {}
    filename_map: dict[str, str] = {}
    for entity in sorted(entities):
        slug = slugify(entity)
        if slug not in slug_count:
            slug_count[slug] = 0
            filename_map[entity] = slug
        else:
            slug_count[slug] += 1
            filename_map[entity] = f"{slug}_{slug_count[slug]}"
    return filename_map


class ObsidianExporter:
    """Exports triplets.json to Obsidian-compatible markdown files with [[wikilinks]]."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, triplets: list[dict], metadata: dict | None = None) -> list[str]:
        """Generate one .md file per entity from a list of triplets.

        Each file contains:
        - YAML frontmatter (tags, type, source metadata)
        - outgoing relations: what this entity does / is / has
        - incoming relations: what other entities say about this one
        - [[wikilinks]] to all related entities (aliased to resolve correctly)

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

        filename_map = _build_filename_map(all_entities)

        created: list[str] = []
        for entity in sorted(all_entities):
            path = self._write_entity_file(
                entity, filename_map, outgoing[entity], incoming[entity], metadata
            )
            created.append(path)

        return created

    def _write_entity_file(
        self,
        entity: str,
        filename_map: dict[str, str],
        out_rels: list[tuple[str, str]],
        in_rels: list[tuple[str, str]],
        metadata: dict | None,
    ) -> str:
        filename = filename_map[entity] + ".md"
        path = os.path.join(self.output_dir, filename)

        source_title = ""
        source_url = ""
        channel = ""
        if metadata:
            source_title = metadata.get("title", "") or ""
            source_url = (
                metadata.get("url", "")
                or metadata.get("webpage_url", "")
                or (f"https://www.youtube.com/watch?v={metadata['id']}" if metadata.get("id") else "")
            )
            channel = metadata.get("channel", "") or ""

        lines: list[str] = []

        # YAML frontmatter
        lines.append("---\n")
        lines.append("tags:\n")
        lines.append("  - youtube-to-knowledge\n")
        if channel:
            channel_tag = re.sub(r"\s+", "-", channel.strip().lower())
            channel_tag = re.sub(r"[^a-z0-9\-_]", "", channel_tag)
            if channel_tag:
                lines.append(f"  - {channel_tag}\n")
        lines.append("type: entity\n")
        if source_title:
            escaped = source_title.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'source_title: "{escaped}"\n')
        if source_url:
            escaped = source_url.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'source_url: "{escaped}"\n')
        if channel:
            escaped = channel.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'author: "{escaped}"\n')
        lines.append("---\n")
        lines.append("\n")

        lines.append(f"# {entity}\n")

        if source_title or source_url:
            lines.append("\n## Source\n\n")
            if source_title and source_url:
                safe_title = source_title.replace("[", "\\[").replace("]", "\\]")
                lines.append(f"- [{safe_title}]({source_url})\n")
            elif source_title:
                lines.append(f"- {source_title}\n")
            else:
                lines.append(f"- {source_url}\n")

        if out_rels:
            lines.append("\n## Relations\n\n")
            for pred, obj in sorted(set(out_rels)):
                target = filename_map.get(obj, slugify(obj))
                link = f"[[{target}|{obj}]]" if target != obj else f"[[{obj}]]"
                lines.append(f"- {pred}: {link}\n")

        if in_rels:
            lines.append("\n## Referenced by\n\n")
            for pred, subj in sorted(set(in_rels)):
                target = filename_map.get(subj, slugify(subj))
                link = f"[[{target}|{subj}]]" if target != subj else f"[[{subj}]]"
                lines.append(f"- {link} → {pred}\n")

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return path


def main():
    parser = argparse.ArgumentParser(
        description="Export triplets.json to Obsidian markdown files"
    )
    parser.add_argument("triplets_json", help="Path to triplets.json")
    parser.add_argument("output_dir", help="Directory to write .md files into")
    parser.add_argument("--metadata", help="Path to metadata.json (optional)", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.triplets_json):
        print(f"Error: file not found: {args.triplets_json}")
        sys.exit(1)

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
