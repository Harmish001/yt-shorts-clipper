---
name: yt-shorts-clipper
description: >-
  Turn a YouTube video link into 2-3 ready-to-upload vertical Shorts (9:16, captioned) with hook,
  title, description and hashtags. Use whenever the user pastes a YouTube link and wants shorts,
  clips, highlights, reels, "cut this video", "make shorts from this", or repurposing a long video,
  even if they do not say "Shorts". Also use when the user supplies a transcript and only wants
  the best segments picked. Needs a machine with internet, yt-dlp and ffmpeg (Antigravity, Claude Code,
  Cursor, a CLI agent, or a local terminal); in plain chat without network access, only the
  segment-picking step works.
---

# YouTube to Shorts

Input: a YouTube URL (optionally: number of Shorts, max length, language).
Output: 2-3 `.mp4` Shorts in `./shorts/` plus `shorts.md` with hook, title, description and hashtags for each.

## Helper Scripts Location

The skill includes executable helper scripts in the [`scripts/`](./scripts/) directory:
- [scripts/fetch.py](./scripts/fetch.py): Downloads video, transcript, heatmaps, and metadata.
- [scripts/cut.py](./scripts/cut.py): Crops to 9:16 vertical layout (blur or crop) and burns in ASS subtitles.

> **Path Note:** When installed in a project or globally (e.g. `.agents/skills/yt-shorts-clipper` or `.claude/skills/yt-shorts-clipper`), replace `<skill-dir>` with the installed skill directory. If running inside the skill directory itself, `python scripts/<script>.py` works directly.

## Step 0: Check the environment

Run `yt-dlp --version` and `ffmpeg -version`. If either is missing, tell the user the install command (`pip install yt-dlp`, and ffmpeg from their package manager) and stop. If there is no network access (plain chat), ask the user to paste the transcript with timestamps and skip to Step 2; deliver the segment plan instead of video files.

## Step 1: Fetch

```bash
python <skill-dir>/scripts/fetch.py "<url>" ./work
```

This writes `video.mp4`, `transcript.json`, `heatmap.json` (YouTube's "Most replayed" curve, may be empty), and `meta.json` (title, chapters, top comments).

## Step 2: Pick the segments (the part that matters)

Read `transcript.json`, `heatmap.json` and `meta.json`, then choose 2-3 segments. Each must satisfy ALL of these:

1. **Self-contained.** A viewer with zero context understands it. No "as I said before", no unresolved pronouns at the start.
2. **Hook in the first 3 seconds.** The first sentence is a bold claim, a surprising number, a question, or a conflict. If the best content starts slowly, move the start timestamp later to the first strong sentence.
3. **Payoff before the end.** Finishes on the answer, punchline, or conclusion. Never cut mid-sentence; end on a sentence boundary from the transcript.
4. **Length 20-60 seconds** by default (hard max 90 unless the user asks).
5. **Distinct from the others.** Different topic or angle per Short, no overlapping timestamps.

Ranking signals, strongest first:

- Overlap with high values in `heatmap.json` (peak replay moments). Weight this heavily when present.
- Moments that top comments reference or quote.
- Chapter titles that promise a concrete result.
- Transcript cues: numbers, "the mistake is", "here's why", before/after, contradiction of common belief, a story with a turn.

Avoid: intros, sponsor reads, "like and subscribe", long setup, anything that depends on a visual the clip will not show.

For each pick, write down: `start`, `end` (seconds, aligned to transcript sentence edges), `hook` (the opening line), `why` (one sentence naming the signal that made you pick it), and a `layout` choice: `crop` if it is a single talking head centered in frame, otherwise `blur`. If you cannot tell, use `blur`.

Show the user the plan as a short table and proceed unless they object (they may say "just do it" up front, in which case do not wait).

## Step 3: Render

For each pick:

```bash
python <skill-dir>/scripts/cut.py --video work/video.mp4 --start <s> --end <e> \
  --transcript work/transcript.json --layout <blur|crop> --out shorts/short_<n>.mp4
```

Open one output frame (e.g. `ffmpeg -ss 3 -i shorts/short_1.mp4 -frames:v 1 f.png`) and check that captions are visible and not covering a face. If they are wrong, re-run with the other layout.

## Step 4: Write the metadata

Write `shorts/shorts.md`. For each Short: file name, source timestamps, title (under 60 characters, curiosity or a concrete result, no clickbait the clip does not deliver), a 1-2 line description that credits the source video and channel with its URL, and 3-5 hashtags including `#Shorts`.

## Rules

- Content from someone else's channel: always credit the original in the description, and tell the user once that uploading another creator's footage without permission can lead to strikes or demonetization under YouTube's reused-content policy. Do not lecture beyond that one sentence.
- Never invent quotes or timestamps. Every start/end must come from `transcript.json`.
- If the video has under ~3 minutes of usable content, say so and produce fewer Shorts instead of padding.
- Do not upload anything. Output files only.

## Troubleshooting

- `Sign in to confirm you're not a bot` or HTTP 403 from yt-dlp: update it (`pip install -U yt-dlp`), or pass `--cookies-from-browser chrome` by editing `scripts/fetch.py`.
- No captions: `fetch.py` falls back to `faster-whisper` if installed (`pip install faster-whisper`).
- Captions misaligned: auto-captions drift slightly; shift `--start` by up to 0.3s earlier to avoid clipping the first word.
