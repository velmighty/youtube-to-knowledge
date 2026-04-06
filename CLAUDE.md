# youtube-to-knowledge

A Claude Code tool that converts YouTube videos into structured knowledge: transcript, summary, and interactive knowledge graph.

## Quick start

```
/process https://www.youtube.com/watch?v=VIDEO_ID
```

That's it. Claude handles the rest.

## What happens

1. Transcript is fetched (fast mode via YouTube API, or local Whisper as fallback)
2. A structured summary is generated in the video's language
3. A knowledge graph is built from entities and relationships
4. Everything is saved to `vault/content/<channel_name>/`

## Skills

This project includes two custom skills:

- **video_specialist** — for deep-dive questions about a specific video's content
- **kg_navigator** — for exploring connections between entities across videos

Claude loads these automatically when relevant questions are asked.

## Output structure

```
vault/content/<channel>/
  raw/
    transcript_raw.txt
    metadata.json
  summary.md
  triplets.json
  graph.json
  graph.html          ← open in browser
```

## Two transcription modes

| Mode | When | Command |
|------|------|---------|
| Fast | Video has subtitles | `python src/transcribe.py <url>` |
| Whisper | No subtitles / better accuracy | `python src/transcribe_whisper.py <url>` |

The `/process` command tries fast mode first and falls back to Whisper automatically.
