# youtube-to-knowledge

Turn any YouTube video into a transcript, summary, and knowledge graph — powered by Claude Code.

Paste a link. Get structured knowledge.

## How it works

1. Fetches the transcript (YouTube API or local Whisper)
2. Generates a structured summary in the video's language
3. Extracts entities and relationships → builds an interactive knowledge graph

## Requirements

- Python 3.10+
- [Claude Code](https://claude.ai/code)
- ffmpeg (required for Whisper mode)

### Install ffmpeg

| OS | Command |
|----|---------|
| macOS | `brew install ffmpeg` |
| Ubuntu / Debian | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg` |
| Windows | `winget install ffmpeg` |

## Setup

```bash
git clone https://github.com/velmighty/youtube-to-knowledge
cd youtube-to-knowledge
pip install -r requirements.txt
```

Open the folder in Claude Code.

## Usage

```
/process https://www.youtube.com/watch?v=VIDEO_ID
```

## Output

Files are saved to `vault/content/<channel_name>/`:

```
raw/
  transcript_raw.txt    raw transcript
  metadata.json         title, channel, video ID, language
summary.md              structured summary
triplets.json           knowledge graph source data
graph.json              graph in node-link format
graph.html              open in browser — interactive visualization
```

## Transcription modes

| Mode | Speed | Requirement |
|------|-------|-------------|
| Fast (default) | Seconds | Video must have subtitles |
| Whisper (local) | Minutes | Any video, no subtitles needed |

The `/process` command tries fast mode first and falls back to Whisper automatically. To force Whisper:

```bash
python src/transcribe_whisper.py https://www.youtube.com/watch?v=VIDEO_ID
```

## License

MIT
