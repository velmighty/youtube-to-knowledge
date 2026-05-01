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

### Install spaCy (for enhanced entity extraction)

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

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

Process multiple videos at once:

```
/process https://youtube.com/watch?v=abc https://youtube.com/watch?v=def
```

Process an entire playlist:

```
/process https://www.youtube.com/playlist?list=PLxxx
```
Use enhanced NLP-based entity extraction (faster, no API calls):

```
/process --enhanced https://www.youtube.com/watch?v=VIDEO_ID
```
Already-processed videos are skipped automatically.

Additional commands:

- `/video_specialist` — deep-dive questions about what was said in a processed video
- `/kg_navigator` — explore entity connections across videos

## Output

Files are saved to `vault/content/<channel_name>/`:

```
raw/
  transcript_<video_id>.txt    raw transcript
  metadata_<video_id>.json     title, channel, video ID, language
summary_<video_id>.md          structured summary
triplets_<video_id>.json       knowledge graph source data (per video)
graph.json                     cumulative graph in node-link format
graph.html                     open in browser — interactive visualization
```

Each file is named after the video ID, so multiple videos from the same channel are stored without overwriting each other.

## Transcription modes

| Mode | Speed | Requirement |
|------|-------|-------------|
| Fast (default) | Seconds | Video must have subtitles |
| Whisper (local) | Minutes | Any video, no subtitles needed |
| WhisperX (opt-in) | Minutes | `pip install -r requirements-whisperx.txt` |

The `/process` command tries fast mode first and falls back to Whisper automatically. To force Whisper:

```bash
python src/transcribe_whisper.py https://www.youtube.com/watch?v=VIDEO_ID
```

### WhisperX mode

WhisperX provides word-level timestamps, speaker diarization, and faster transcription via faster-whisper. Install the extra dependencies:

```bash
pip install -r requirements-whisperx.txt
```

Then use the `--engine` flag:

```
/process --engine whisperx https://www.youtube.com/watch?v=VIDEO_ID
```

Speaker diarization requires a [HuggingFace token](https://huggingface.co/settings/tokens) set as `HF_TOKEN` in your environment. Without it, WhisperX still produces timestamped segments but without speaker labels.

## Obsidian integration

Add `--obsidian` to export the knowledge graph directly into your Obsidian vault.

```
/process --obsidian https://www.youtube.com/watch?v=VIDEO_ID
```

This generates one `.md` file per extracted entity in `vault/content/<channel_name>/obsidian/`. Each file contains:

- **YAML frontmatter** — tags, source title, URL, channel
- **Relations** — outgoing links to other entities: `- made_by: [[Anthropic]]`
- **Referenced by** — incoming links: `- [[Claude]] → made_by`

Wikilinks use Obsidian's `[[filename|display]]` aliasing, so they resolve correctly even when entity names contain special characters.

To connect the exported notes to your main vault, point Obsidian at the `vault/` folder or copy the `obsidian/` directory into your existing vault.

You can also run the exporter directly:

```bash
python src/obsidian_exporter.py vault/content/<channel>/triplets_<video_id>.json /path/to/output \
  --metadata vault/content/<channel>/raw/metadata_<video_id>.json
```

## Options

```
/process [--depth light|standard|deep] [--engine whisperx|whisper] [--obsidian] <URL> [<URL2> ...]
```

| Flag | Values | Default | Effect |
|------|--------|---------|--------|
| `--depth` | `light`, `standard`, `deep` | `standard` | Controls triplet count and summary detail |
| `--engine` | `whisper`, `whisperx` | `whisper` | Selects transcription engine for fallback |
| `--obsidian` | — | off | Exports entity notes to `obsidian/` subfolder |

Flags apply to all videos in a batch.

Examples:

```
/process https://www.youtube.com/watch?v=VIDEO_ID
/process https://youtube.com/watch?v=abc https://youtube.com/watch?v=def
/process https://www.youtube.com/playlist?list=PLxxx
/process --depth deep https://www.youtube.com/watch?v=VIDEO_ID
/process --engine whisperx --depth light https://www.youtube.com/watch?v=VIDEO_ID
/process --obsidian https://www.youtube.com/watch?v=VIDEO_ID
/process --obsidian --depth deep https://www.youtube.com/watch?v=VIDEO_ID
```

## License

[MIT](LICENSE)
