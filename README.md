# YouTube Shorts Clipper (Agent Skill)

Turn any YouTube video into 2–3 high-retention, ready-to-upload vertical Shorts (9:16, burned-in captions, hook scoring, titles, descriptions, and hashtags).

Compatible with **Google Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, **GitHub Copilot**, **Codex**, and any agent supporting the open [Skills standard](https://skills.sh).

---

## ⚡ Installation

Install into your current project:
```bash
npx skills add Harmish001/yt-shorts-clipper
```

Install globally across all projects:
```bash
npx skills add -g Harmish001/yt-shorts-clipper
```

Install to specific agents:
```bash
npx skills add Harmish001/yt-shorts-clipper --agent antigravity cursor claude-code
```

---

## 🛠️ Prerequisites

This skill uses standard CLI tools to download and render video clips:

1. **Python 3.8+**
2. **yt-dlp**:
   ```bash
   pip install -U yt-dlp
   ```
3. **FFmpeg** (with `libass` enabled, standard in homebrew, winget, and official builds):
   - **Windows**: `winget install Gyan.FFmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
4. *(Optional fallback for videos without subtitles)*:
   ```bash
   pip install faster-whisper
   ```

---

## 🚀 How to Use

Once installed, just ask your agent:

> *"Cut 2-3 shorts from this video: https://www.youtube.com/watch?v=..."*  
> *"Turn this podcast into vertical clips with captions."*  
> *"Extract the most viral highlights from this YouTube URL."*

### What the Skill Does

1. **Signal-Driven Fetching (`fetch.py`)**:
   - Downloads the best video stream up to 1080p and merges audio.
   - Extracts YouTube auto-captions or manual transcript.
   - Pulls YouTube's **Most Replayed Heatmap** curve to pinpoint peak viral retention points.
   - Collects top-voted comments and chapter markers.

2. **Hook-First Segment Selection**:
   - Identifies 20–60 second self-contained clips.
   - Requires a punchy hook in the first 3 seconds (bold claim, question gap, number shock).
   - Weighted by heatmap retention peaks and audience quotes.

3. **Vertical Video Rendering (`cut.py`)**:
   - Layout options:
     - `blur`: Centers 16:9 frame over an organically blurred backdrop (great for screen recordings, multi-person shots).
     - `crop`: Dynamic 9:16 center crop (best for talking heads).
   - Burned-in ASS captions styled for readability.

4. **SEO & Metadata (`shorts/shorts.md`)**:
   - High-CTR curiosity titles (<60 characters).
   - Source attribution & creator credit.
   - Curated hashtags including `#Shorts`.

---

## 📁 Repository Structure

```text
yt-shorts-clipper/
├── SKILL.md                 # Agent instructions & triggers
├── scripts/
│   ├── fetch.py             # yt-dlp downloader + signal extractor
│   └── cut.py               # ffmpeg 9:16 vertical renderer + ASS captions
└── README.md
```

## 📄 License

MIT
