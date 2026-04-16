import os
import sys
import argparse
import json
import re
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None


def get_metadata(url: str) -> dict:
    metadata = {"channel": "Unknown_Channel", "title": "Unknown_Title", "language": "unknown"}
    try:
        with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            metadata["channel"] = info.get("uploader", "Unknown_Channel")
            metadata["title"] = info.get("title", "Unknown_Title")
            metadata["language"] = info.get("language") or "unknown"
    except Exception as e:
        print(f"Warning: metadata extraction failed: {e}")
    return metadata


def fetch_transcript(video_id: str, raw_dir: str) -> tuple[str, str]:
    """Try YouTube Transcript API first, fall back to yt-dlp subtitles.

    Returns (transcript_text, language_code).
    """
    # Method 1: YouTube Transcript API
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, ["pl", "en"])
        text = " ".join([t.text for t in fetched])
        if text.strip():
            lang = getattr(fetched, "language_code", "en") or "en"
            return text, lang
    except Exception as e:
        print(f"Warning: YouTubeTranscriptApi failed: {e}")

    # Method 2: yt-dlp subtitle download
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writeautomaticsub": True,
        "writesubtitles": True,
        "subtitleslangs": ["pl", "en"],
        "outtmpl": f"{raw_dir}/subs",
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        for lang in ["pl", "en"]:
            sub_file = f"{raw_dir}/subs.{lang}.json3"
            if os.path.exists(sub_file):
                with open(sub_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                lines = [
                    seg.get("utf8", "")
                    for event in data.get("events", [])
                    for seg in event.get("segs", [])
                ]
                text = "".join(lines)
                if text.strip():
                    return text, lang
    except Exception as e:
        print(f"Warning: yt-dlp subtitle extraction failed: {e}")

    return "", "unknown"


def is_duplicate(video_id: str, db_path: str) -> bool:
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return f"`{video_id}`" in f.read()
    return False


def main():
    parser = argparse.ArgumentParser(description="YouTube Transcribe Tool (fast mode)")
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print("Error: could not extract video ID from URL")
        sys.exit(1)

    if is_duplicate(video_id, os.path.join("vault", "processed_videos.md")):
        print(f"SKIPPED_DUPLICATE: {video_id} already in database.")
        sys.exit(0)

    metadata = get_metadata(args.url)
    metadata["id"] = video_id
    metadata["url"] = f"https://www.youtube.com/watch?v={video_id}"

    channel_name = sanitize_filename(metadata["channel"]).replace(" ", "_").lower()
    base_dir = os.path.join("vault", "content", channel_name)
    raw_dir = os.path.join(base_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    transcript, lang = fetch_transcript(video_id, raw_dir)

    if not transcript.strip():
        print("Error: no transcript found. Try transcribe_whisper.py instead.")
        sys.exit(1)

    metadata["language"] = lang

    with open(os.path.join(raw_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    raw_filename = f"transcript_{video_id}.txt"
    with open(os.path.join(raw_dir, raw_filename), "w", encoding="utf-8") as f:
        f.write(transcript)

    print(f"CHANNEL_DIR:{base_dir}")
    print(f"RAW_FILE:{os.path.join(raw_dir, raw_filename)}")
    print(f"SOURCE_LANG:{lang}")
    print(f"TITLE:{metadata['title']}")


if __name__ == "__main__":
    main()
