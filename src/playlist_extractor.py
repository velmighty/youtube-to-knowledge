import sys
from yt_dlp import YoutubeDL


def main():
    if len(sys.argv) < 2:
        print("Usage: python playlist_extractor.py <playlist_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            for entry in info.get("entries", []):
                vid_id = entry.get("id")
                if vid_id:
                    print(f"https://www.youtube.com/watch?v={vid_id}")
        else:
            vid_id = info.get("id")
            if vid_id:
                print(f"https://www.youtube.com/watch?v={vid_id}")


if __name__ == "__main__":
    main()
