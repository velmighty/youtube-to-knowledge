Process a YouTube video into structured knowledge.

**URL:** $ARGUMENTS

Follow these steps exactly:

## Step 1 — Duplicate check
Read `vault/processed_videos.md`. Extract the video ID from the URL. If the ID appears in the file, stop and tell the user the video is already processed.

## Step 2 — Transcription
Run: `python src/transcribe.py $ARGUMENTS`

Parse stdout for:
- `CHANNEL_DIR:<path>`
- `RAW_FILE:<path>`
- `SOURCE_LANG:<lang>`
- `TITLE:<title>`

If the script exits with error code 1 (no transcript found), run instead:
`python src/transcribe_whisper.py $ARGUMENTS`
Parse the same output variables.

## Step 3 — Summary
Read the full transcript from RAW_FILE.

Write a structured summary to `<CHANNEL_DIR>/summary.md`:
- Title and channel at the top
- Key takeaways (5-8 bullet points)
- Main arguments or strategies discussed
- Notable quotes or data points
- Write in the same language as the transcript (use SOURCE_LANG to detect)

## Step 4 — Knowledge graph
Extract 15-20 subject-predicate-object triplets from the transcript.
Focus on: people, companies, tools, concepts, and their relationships.

Save to `<CHANNEL_DIR>/triplets.json`:
```json
[
  {"subject": "Entity A", "predicate": "relation", "object": "Entity B"},
  ...
]
```

Then run: `python src/graph_extractor.py <CHANNEL_DIR> <CHANNEL_DIR>/triplets.json`

## Step 5 — Update database
Run: `python src/generate_video_db.py`

## Step 6 — Report
Tell the user:
- Video title
- Files created (transcript, summary, graph.html path)
- Number of graph nodes and edges
- How to open the graph: open `<CHANNEL_DIR>/graph.html` in a browser
