import os
import sys
import argparse
import json
import re
import whisper
from yt_dlp import YoutubeDL


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None


def is_duplicate(video_id: str, db_path: str) -> bool:
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return f"`{video_id}`" in f.read()
    return False


def main():
    parser = argparse.ArgumentParser(description="YouTube Transcribe Tool (Whisper local mode)")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: small)",
    )
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print("Error: could not extract video ID from URL")
        sys.exit(1)

    if is_duplicate(video_id, os.path.join("vault", "processed_videos.md")):
        print(f"SKIPPED_DUPLICATE: {video_id} already in database.")
        sys.exit(0)

    metadata = {"channel": "Unknown_Channel", "title": "Unknown_Title", "id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "language": "unknown"}
    try:
        with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(args.url, download=False)
            metadata["channel"] = info.get("uploader", "Unknown_Channel")
            metadata["title"] = info.get("title", "Unknown_Title")
    except Exception as e:
        print(f"Warning: metadata extraction failed: {e}")

    channel_name = sanitize_filename(metadata["channel"]).replace(" ", "_").lower()
    base_dir = os.path.join("vault", "content", channel_name)
    raw_dir = os.path.join(base_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    temp_audio = f"temp_{video_id}.m4a"
    print("Downloading audio...")
    try:
        with YoutubeDL({"format": "m4a/bestaudio/best", "outtmpl": temp_audio, "quiet": True}) as ydl:
            ydl.download([args.url])
    except Exception as e:
        print(f"Error downloading audio: {e}")
        sys.exit(1)

    print(f"Loading Whisper model '{args.model}'...")
    model = whisper.load_model(args.model)
    print("Transcribing...")
    try:
        result = model.transcribe(temp_audio)
        transcript = result["text"].strip()
        lang = result.get("language", "unknown")
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

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
