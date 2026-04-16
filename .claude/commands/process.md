Process one or more YouTube videos (or a playlist) into structured knowledge.

**Arguments:** $ARGUMENTS

Parse `$ARGUMENTS` to extract:
- **URLs**: All arguments that start with `http` or look like YouTube video IDs. There may be one or many.
- **Playlist**: If a URL contains `playlist?list=`, it is a playlist — expand it first (see Step 0).
- **--depth**: `light` | `standard` | `deep` (default: `standard`).
- **--engine**: `whisperx` | `whisper` (default: `whisper`).
- **--obsidian**: flag (no value). If present, export entities as Obsidian markdown notes.

Examples:
- `/process https://youtube.com/watch?v=xyz`
- `/process https://youtube.com/watch?v=abc https://youtube.com/watch?v=def`
- `/process https://www.youtube.com/playlist?list=PLxxx`
- `/process --depth deep https://youtube.com/watch?v=xyz`
- `/process --obsidian https://youtube.com/watch?v=xyz`

Follow these steps exactly:

## Step 0 — Expand playlist (only if a playlist URL was given)
Run: `python src/playlist_extractor.py <playlist_url>`

Each line of stdout is a video URL. Replace the playlist URL in your working list with these individual URLs. Proceed to Step 1 for each video sequentially.

## Step 1 — Duplicate check
**If processing multiple videos:** announce "Processing X videos" before starting.

Read `vault/processed_videos.md`. Extract the video ID from the URL. If the ID appears in the file, skip this video (print "SKIPPED: already processed") and move to the next one.

## Step 2 — Transcription
Run: `python src/transcribe.py <URL>`

Parse stdout for:
- `CHANNEL_DIR:<path>`
- `RAW_FILE:<path>`
- `SOURCE_LANG:<lang>`
- `TITLE:<title>`
- `ENRICHED_FILE:<path>` (optional, only from WhisperX)

If the script exits with error code 1 (no transcript found):
- If engine is `whisper` (default): run `python src/transcribe_whisper.py <URL>`
- If engine is `whisperx`: run `python src/transcribe_whisperx.py <URL>`
- If the chosen engine also fails, try the other as a last resort.

Parse the same output variables from whichever script succeeds.

## Step 3 — Summary
Read the transcript. **If ENRICHED_FILE was provided, read it instead of RAW_FILE** for richer context (timestamps, speaker labels). Otherwise read RAW_FILE.

Write a structured summary to `<CHANNEL_DIR>/summary_<video_id>.md`:
- Title and channel at the top.
- Write in the same language as the transcript (use SOURCE_LANG to detect).

**If depth = light:**
- 3-5 key takeaways (concise bullet points).
- One paragraph overview.

**If depth = standard (default):**
- 5-8 key takeaways.
- Main arguments or strategies discussed.
- Notable quotes or data points.

**If depth = deep:**
- 8-12 key takeaways.
- Comprehensive argument breakdown with supporting evidence.
- All notable quotes with timestamps (if available from enriched transcript).
- Data points and statistics mentioned.
- Counterarguments or caveats raised by the speaker.
- Connections to other topics in the vault (check existing summaries).

## Step 4 — Knowledge graph
Extract triplets from the transcript (prefer enriched transcript if available).

**Entity resolution (all depths):**
- Use full canonical names. Check metadata.json for speaker/channel.
- Predicates must be specific verbs: "founded", "recommends", "competes_with". Never "is related to".
- Before adding entities, check existing `<CHANNEL_DIR>/graph.json` for equivalent nodes.

**If depth = light:**
Extract 8-12 triplets. Primary entities and direct relationships only.

**If depth = standard (default):**
Extract 15-20 triplets. People, companies, tools, concepts, and their relationships.

**If depth = deep:**
Extract 25-35 triplets. Include:
- Primary relationships (people, companies, tools, concepts)
- Causal chains ("X leads to Y" = separate triplets)
- Temporal relationships ("X preceded Y", "X replaced Y")
- Attributed claims (use speaker name if from diarized transcript)
- Quantitative relationships ("X grew by 300%")

Save to `<CHANNEL_DIR>/triplets_<video_id>.json`:
```json
[
  {"subject": "Entity A", "predicate": "relation", "object": "Entity B"},
  ...
]
```

Then run: `python src/graph_extractor.py <CHANNEL_DIR> <CHANNEL_DIR>/triplets_<video_id>.json`

## Step 5 — Update database
Run: `python src/generate_video_db.py`

## Step 5.5 — Obsidian export (only if --obsidian flag was set)

Read `<CHANNEL_DIR>/raw/metadata.json`.

Run:
```
python src/obsidian_exporter.py <CHANNEL_DIR>/triplets_<video_id>.json <CHANNEL_DIR>/obsidian --metadata <CHANNEL_DIR>/raw/metadata_<video_id>.json
```

This creates one `.md` file per entity in `<CHANNEL_DIR>/obsidian/`, with `[[wikilinks]]` between related entities.

## Step 6 — Report
**If a single video was processed:**
- Video title
- Depth level used
- Files created (transcript, summary, graph.html path)
- Whether enriched transcript was available
- Number of graph nodes and edges
- How to open the graph: open `<CHANNEL_DIR>/graph.html` in a browser
- If --obsidian was set: number of Obsidian notes created and path to `<CHANNEL_DIR>/obsidian/`

**If multiple videos were processed:**
- Summary table: one row per video with title, channel, status (processed / skipped)
- Total processed vs skipped
- List of graph.html paths to open
