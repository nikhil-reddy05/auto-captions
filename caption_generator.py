#!/usr/bin/env python3
"""
Extract audio from a video, transcribe with Whisper (per-word), and write
temp/word_timestamps.json in your original schema.

Usage examples:
  python captions_prep.py
  python captions_prep.py -i myvideo.mp4 -o temp/word_timestamps.json
  python captions_prep.py -i input.mp4 -a tmp/audio.wav -o tmp/words.json -m small -l en --no-lowercase
"""

from pathlib import Path
from typing import Dict, List, Any, Optional

from moviepy.editor import VideoFileClip
import whisper
import json
import argparse
import sys

def extract_audio(video_path: str, audio_path: str) -> None:
    """Extract audio track from video to a WAV file."""
    Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
    with VideoFileClip(video_path) as clip:
        if clip.audio is None:
            raise ValueError("No audio track found in the input video.")
        clip.audio.write_audiofile(audio_path, logger=None)


def transcribe_audio_to_segments(
    audio_path: str,
    model_name: str = "small",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load Whisper model and transcribe audio with per-word timestamps.
    Returns the raw Whisper result dict (with 'segments').
    """
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, word_timestamps=True, language=language)
    return result


def build_word_timestamps(
    captions_data: Dict[str, Any],
    lowercase: bool = True,
    init_start: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Flatten Whisper segments into:
    [{"word": "...", "start": 0.0, "end": 0.0, }, ...]
    """
    word_timestamps: List[Dict[str, Any]] = []

    for segment in captions_data.get("segments", []):
        for word_data in segment.get("words", []) or []:
            token = str(word_data.get("word", ""))
            token = token.lower() if lowercase else token
            word_timestamps.append({
                "word": token,
                "start": float(word_data.get("start", 0.0)),
                "end": float(word_data.get("end", 0.0))
            })
    # Only bump the very first word’s start to init_start
    if word_timestamps and word_timestamps[0]["start"] < init_start:
        word_timestamps[0]["start"] = init_start

    return word_timestamps


def save_word_timestamps_json(word_timestamps: List[Dict[str, Any]], output_path: str) -> None:
    """Write the word timestamps list to JSON."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(word_timestamps, f, ensure_ascii=False, indent=4)

def prepare_json_words_with_timestamps(
    input_video_path: str = "input_video.mp4",
    audio_path: str = "audio.wav",
    output_json_path: str = "temp/word_timestamps.json",
    model_name: str = "small",
    language: Optional[str] = None,
    lowercase: bool = True,
    init_start_ts: float = 0.0
) -> None:
    """
    1) Extract audio from the video
    2) Transcribe with Whisper (per-word)
    3) Build the word_timestamps array
    4) Save to output_json_path
    """
    try:
        extract_audio(input_video_path, audio_path)
        print("Audio extracted successfully!")
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return

    captions_data = transcribe_audio_to_segments(audio_path, model_name=model_name, language=language)
    word_timestamps = build_word_timestamps(captions_data, lowercase=lowercase, init_start=init_start_ts)
    save_word_timestamps_json(word_timestamps, output_json_path)

    print(f"Extracted captions saved to {output_json_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate per-word timestamps JSON from a video using Whisper.")
    p.add_argument("-i", "--input-video", default="input_video.mp4", help="Path to input video file.")
    p.add_argument("-a", "--audio-out", default="audio.wav", help="Temporary/output audio WAV path.")
    p.add_argument("-o", "--output-json", default="temp/word_timestamps.json", help="Output JSON path.")
    p.add_argument("-m", "--model", default="small", help="Whisper model size (tiny/base/small/medium/large...).")
    p.add_argument("-l", "--language", default="en", help="Language code (e.g., en). Omit to auto-detect.")
    p.add_argument("--no-lowercase", action="store_true", help="Keep original word casing (default lowercases).")
    p.add_argument("-s", "--init-start", default=0.0, help="Set initial start time, 0.0 otherwise")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        prepare_json_words_with_timestamps(
            input_video_path=args.input_video,
            audio_path=args.audio_out,
            output_json_path=args.output_json,
            model_name=args.model,
            language=args.language,
            lowercase=not args.no_lowercase,
            init_start_ts=args.init_start
        )
        return 0
    except KeyboardInterrupt:
        print("Aborted.")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
