#!/usr/bin/env python3
"""Download a YouTube video plus the signals needed to pick Shorts.

Usage: python fetch.py <youtube_url> <workdir>

Writes to <workdir>:
  video.mp4        the video (<=1080p)
  transcript.json  [{"start": sec, "end": sec, "text": str}, ...]
  heatmap.json     [{"start": sec, "end": sec, "value": 0..1}, ...]  ("Most replayed"; may be empty)
  meta.json        title, channel, duration, description, chapters, top comments (if available)

Requires: pip install yt-dlp   (and ffmpeg on PATH)
Optional fallback when a video has no captions: pip install faster-whisper
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp is missing. Run: pip install yt-dlp")


def parse_json3(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs).replace("\n", " ").strip()
        if not text:
            continue
        start = ev["tStartMs"] / 1000
        end = start + ev.get("dDurationMs", 0) / 1000
        out.append({"start": round(start, 2), "end": round(end, 2), "text": text})
    # auto-captions repeat rolling text; drop exact consecutive duplicates
    dedup = []
    for seg in out:
        if dedup and dedup[-1]["text"] == seg["text"]:
            dedup[-1]["end"] = seg["end"]
        else:
            dedup.append(seg)
    return dedup


def whisper_fallback(video: Path):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("No captions found and faster-whisper is not installed. Run: pip install faster-whisper")
    model = WhisperModel("small", compute_type="int8")
    segments, _ = model.transcribe(str(video), vad_filter=True)
    return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    url, workdir = sys.argv[1], Path(sys.argv[2])
    workdir.mkdir(parents=True, exist_ok=True)

    opts = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(workdir / "video.%(ext)s"),
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en.*", "en", "en-US", "en-orig"],
        "subtitlesformat": "json3",
        "ignoreerrors": "only_download",
        "getcomments": True,
        "extractor_args": {"youtube": {"max_comments": ["20", "0", "0", "0"], "comment_sort": ["top"]}},
        "quiet": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # transcript
    subs = sorted(workdir.glob("video.*.json3"))
    transcript = parse_json3(subs[0]) if subs else whisper_fallback(workdir / "video.mp4")
    (workdir / "transcript.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=1), encoding="utf-8")

    # most-replayed heatmap (yt-dlp exposes it when YouTube provides it)
    heat = [
        {"start": h["start_time"], "end": h["end_time"], "value": round(h["value"], 3)}
        for h in (info.get("heatmap") or [])
    ]
    (workdir / "heatmap.json").write_text(json.dumps(heat, indent=1), encoding="utf-8")

    comments = sorted(info.get("comments") or [], key=lambda c: c.get("like_count") or 0, reverse=True)[:15]
    meta = {
        "title": info.get("title"),
        "channel": info.get("channel"),
        "url": info.get("webpage_url"),
        "duration": info.get("duration"),
        "description": (info.get("description") or "")[:1500],
        "chapters": info.get("chapters") or [],
        "top_comments": [{"text": c.get("text"), "likes": c.get("like_count")} for c in comments],
    }
    (workdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"OK  transcript segments: {len(transcript)}  heatmap points: {len(heat)}  workdir: {workdir}")


if __name__ == "__main__":
    main()