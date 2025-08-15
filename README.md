# auto-captions

Generate clean, stylized **burned-in captions** for your videos using:
1. Per-word timestamps  
2. An ASS subtitle file you can burn into the final video with FFmpeg

---

## ✨ Features
- **Per-word timing**: ideal for “karaoke” style highlights
- **Stylable captions**: control font, size, outline, margins, pop effect, shadows
- **Burn-in ready**: simple FFmpeg command to embed captions

---

## 🧰 Requirements
- **Python** 3.9+ (3.10/3.11 recommended)
- **FFmpeg** installed and added to PATH  
  - macOS: `brew install ffmpeg`  
  - Linux: `sudo apt-get install ffmpeg`  
  - Windows: Download FFmpeg builds and add `bin` to PATH
- Python packages from `requirements.txt`

---

## 📦 Installation
```bash
git clone https://github.com/nikhil-reddy05/auto-captions.git
cd auto-captions

# (Optional) create a virtual environment
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## 🚀 Usage

> Place your input video in the repo root as `input_video.mp4` (or change the path/arguments accordingly).

### 1) Generate per‑word timestamps (JSON)

```bash
python caption_generator.py
```
This extracts audio, runs transcription, and writes:

```
temp/word_timestamps.json
```

The JSON is a flat list like:

```json
[
  { "word": "hello", "start": 0.32, "end": 0.61 },
  { "word": "world", "start": 0.62, "end": 0.95 }
]
```

---

### 2) Create the ASS subtitle file

```bash
python json_to_ass.py --json temp/word_timestamps.json --out captions.ass
```

Common flags

- `--words-per-cap` – words per caption block (e.g. `3`)  
- `--font` / `--fontsize` – typography (e.g. `Montserrat`, `72`)  
- `--outline` / `--shadow` – readability (e.g. outline `7`, shadow `0`)  
- `--margin-v` / `--margin-lr` – vertical / horizontal margins from frame edge  

List all options:

```bash
python json_to_ass.py -h
```

---

### 3) Burn captions into the video (FFmpeg)

```bash
ffmpeg -y -i input_video.mp4 -vf "ass=captions.ass"   -c:v libx264 -crf 18 -preset medium -c:a copy output_with_captions.mp4
```

If your chosen font doesn’t render, point FFmpeg to a fonts folder:

```bash
ffmpeg -y -i input_video.mp4   -vf "ass=captions.ass:fontsdir=./fonts:shaping=harfbuzz"   -c:v libx264 -crf 18 -preset medium -c:a copy output_with_captions.mp4
```

---

## 📱 Tips for 9:16 / Shorts

- Set ASS `PlayResX=1080` and `PlayResY=1920` (vertical frame).  
- Keep captions above UI bars: try `--margin-v` around `120–180`.  
- For busy backgrounds, use **white text + thick black outline** (`--outline 7–9`).  
- If speech is very fast, slightly reduce `--fontsize` or increase `--words-per-cap`.

---

## 🧷 Troubleshooting

- **Font not found / wrong font:** Install the font system‑wide or use `fontsdir` as shown above. Ensure the ASS style uses the exact family name.  
- **Text looks tiny or misplaced:** Ensure the ASS header’s `PlayResX/PlayResY` matches your target resolution (e.g., 1080×1920).  
- **Transcription is slow on CPU:** Use a smaller Whisper model in `caption_generator.py` (e.g., `base`/`small`).  
- **Captions overlap platform UI:** Increase `--margin-v` or nudge the first word’s `start` to `0.01`.

---

## 📜 License

MIT — see [LICENSE](https://github.com/nikhil-reddy05/auto-captions/blob/main/LICENSE)

---

## Inspiration & Acknowledgments

This project was inspired by the [Captions repository](https://github.com/it-code-lab/Captions), which provided foundational ideas for stylized caption rendering and subtitle formatting. Our version expands on these concepts by integrating:

- Whisper-based per-word timestamp extraction
- Dynamic ASS karaoke-style captions with pop-in animations
- Full customization via CLI arguments (fonts, outlines, animation timings)
