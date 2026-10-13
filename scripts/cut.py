#!/usr/bin/env python3
"""Cut one Short (9:16, 1080x1920) from a video with burned-in captions.

Usage:
  python cut.py --video video.mp4 --start 125.0 --end 171.5 --out short1.mp4 \
                [--transcript transcript.json] [--layout blur|crop]

Layouts:
  blur  full frame centered over a blurred copy of itself (safe for screen recordings / wide shots)
  crop  center crop to 9:16 (best for talking heads framed in the middle)

Requires ffmpeg built with libass (standard builds have it).
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def ass_time(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(segments, start, end, path: Path):
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,"
        "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV\n"
        "Style: Cap,Arial,64,&H00FFFFFF,&H00000000,&H64000000,1,1,5,1,2,80,80,520\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Text\n"
    )
    lines = []
    for seg in segments:
        if seg["end"] <= start or seg["start"] >= end:
            continue
        s = max(seg["start"], start) - start
        e = min(seg["end"], end) - start
        if e - s < 0.2:
            continue
        text = seg["text"].replace("{", "(").replace("}", ")").strip()
        # wrap long captions onto two lines
        words = text.split()
        if len(words) > 6:
            mid = len(words) // 2
            text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
        lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,{text}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--transcript")
    ap.add_argument("--layout", choices=["blur", "crop"], default="blur")
    a = ap.parse_args()

    if a.end <= a.start:
        sys.exit("--end must be greater than --start")
    if a.end - a.start > 180:
        print("warning: Shorts can be up to 3 minutes, but 20-60s usually performs best", file=sys.stderr)

    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp())
    ass_path = tmp / "cap.ass"
    have_caps = False
    try:
        if a.transcript:
            build_ass(json.loads(Path(a.transcript).read_text(encoding="utf-8")), a.start, a.end, ass_path)
            have_caps = True

        if a.layout == "crop":
            base = "crop=ih*9/16:ih,scale=1080:1920,setsar=1[v0]"
            graph = f"[0:v]{base}"
        else:
            graph = (
                "[0:v]split=2[a][b];"
                "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
                "[b]scale=1080:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v0]"
            )
        if have_caps:
            # ffmpeg filter paths need escaping of ':' and '\'
            esc = str(ass_path).replace("\\", "/").replace(":", "\\:")
            graph += f";[v0]ass='{esc}'[v]"
        else:
            graph += ";[v0]null[v]"

        cmd = [
            "ffmpeg", "-y", "-ss", str(a.start), "-t", str(a.end - a.start), "-i", a.video,
            "-filter_complex", graph, "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(r.stderr[-1500:])
        print(f"OK  {out_path}  ({a.end - a.start:.1f}s)")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()