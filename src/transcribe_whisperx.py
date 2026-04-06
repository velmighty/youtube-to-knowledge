import os
import sys
import argparse
import json
import re
import torch
import whisperx
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


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_enriched_transcript(segments: list, has_speakers: bool) -> str:
    lines = []
    for seg in segments:
        start = format_timestamp(seg.get("start", 0))
        end = format_timestamp(seg.get("end", 0))
        header = f"[{start} - {end}]"
        if has_speakers and seg.get("speaker"):
            header += f" [{seg['speaker']}]"
        lines.append(header)
        lines.append(seg["text"].strip())
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="YouTube Transcribe Tool (WhisperX mode)")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Whisper model size (default: small)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for transcription (default: 16)",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        choices=["int8", "float16", "float32"],
        help="Compute type (default: int8, use float16 for GPU)",
    )
    parser.add_argument(
        "--no-diarize",
        action="store_true",
        help="Skip speaker diarization even if HF_TOKEN is set",
    )
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print("Error: could not extract video ID from URL")
        sys.exit(1)

    if is_duplicate(video_id, os.path.join("vault", "processed_videos.md")):
        print(f"SKIPPED_DUPLICATE: {video_id} already in database.")
        sys.exit(0)

    metadata = {"channel": "Unknown_Channel", "title": "Unknown_Title", "id": video_id, "language": "unknown"}
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

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = args.compute_type if device == "cuda" else "int8"

    print(f"Loading WhisperX model '{args.model}' on {device}...")
    model = whisperx.load_model(args.model, device, compute_type=compute)
    try:
        audio = whisperx.load_audio(temp_audio)
        print("Transcribing...")
        result = model.transcribe(audio, batch_size=args.batch_size)
        lang = result.get("language", "unknown")

        # Alignment
        try:
            model_a, metadata_a = whisperx.load_align_model(language_code=lang, device=device)
            result = whisperx.align(result["segments"], model_a, metadata_a, audio, device)
            del model_a
            print("Alignment complete.")
        except Exception as e:
            print(f"Warning: alignment skipped ({e})")

        # Diarization
        has_speakers = False
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token and not args.no_diarize:
            try:
                diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
                diarize_segments = diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                has_speakers = True
                print("Diarization complete.")
            except Exception as e:
                print(f"Warning: diarization skipped ({e})")

        # Plain transcript
        transcript = " ".join([s["text"].strip() for s in result["segments"]])

        # Enriched transcript
        enriched = build_enriched_transcript(result["segments"], has_speakers)

    finally:
        del model
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

    metadata["language"] = lang

    with open(os.path.join(raw_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with open(os.path.join(raw_dir, "transcript_raw.txt"), "w", encoding="utf-8") as f:
        f.write(transcript)

    enriched_path = os.path.join(raw_dir, "transcript_enriched.txt")
    with open(enriched_path, "w", encoding="utf-8") as f:
        f.write(enriched)

    print(f"CHANNEL_DIR:{base_dir}")
    print(f"RAW_FILE:{os.path.join(raw_dir, 'transcript_raw.txt')}")
    print(f"SOURCE_LANG:{lang}")
    print(f"TITLE:{metadata['title']}")
    print(f"ENRICHED_FILE:{enriched_path}")


if __name__ == "__main__":
    main()
