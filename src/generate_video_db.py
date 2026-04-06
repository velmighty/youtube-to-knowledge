import json
from pathlib import Path


def build_database(vault_dir: Path, output_file: Path) -> int:
    """Scan vault/content for metadata.json files and rebuild processed_videos.md.

    Returns the number of videos found.
    """
    videos = []

    for item in vault_dir.iterdir():
        if not item.is_dir():
            continue
        metadata_path = item / "raw" / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            videos.append({
                "channel": data.get("channel", "Unknown"),
                "title": data.get("title", "Unknown"),
                "id": data.get("id", ""),
                "language": data.get("language", "unknown"),
            })
        except Exception as e:
            print(f"Warning: could not read {metadata_path}: {e}")

    videos.sort(key=lambda v: v["channel"].lower())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Processed Videos\n\n")
        f.write(
            "Videos processed by youtube-to-knowledge. "
            "Before processing a new video, check if it's already here.\n\n"
        )
        f.write("| Channel | Title | Link | ID |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for v in videos:
            title = v["title"].replace("|", "\\|")
            channel = v["channel"].replace("|", "\\|")
            vid_id = v["id"]
            link = f"[Watch](https://www.youtube.com/watch?v={vid_id})" if vid_id else "—"
            f.write(f"| {channel} | {title} | {link} | `{vid_id}` |\n")

    return len(videos)


if __name__ == "__main__":
    vault_dir = Path("vault/content")
    output_file = Path("vault/processed_videos.md")
    count = build_database(vault_dir, output_file)
    print(f"Database updated: {count} video(s) in {output_file}")
