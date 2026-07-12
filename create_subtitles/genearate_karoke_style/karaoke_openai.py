"""
Karaoke-style video generator using OpenAI TTS + Whisper API.

Step 1: Generate AI voiceover with OpenAI TTS
Step 2: Transcribe it back with OpenAI Whisper API (whisper-1) to get word-level timestamps
Step 3: Render video with text and an underline indicator showing the current word

Requirements:
    pip install openai moviepy pillow numpy

Usage:
    python karaoke_openai.py --text sample_text.md --output output.mp4

Optional:
    --voice alloy             OpenAI TTS voice (alloy, echo, fable, onyx, nova, shimmer)
    --model tts-1             OpenAI TTS model (tts-1 or tts-1-hd)
    --video background.mp4    Optional background video (otherwise uses dark background)
    --width 1080              Video width (default: 1080)
    --height 1920             Video height (default: 1920, vertical format)
    --words-per-line 6        Words shown per line (default: 6)
"""

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    VideoClip,
    VideoFileClip,
    ColorClip,
)


def generate_openai_tts(text, voice="alloy", model="tts-1", api_key=None):
    """Generate speech audio using OpenAI TTS API."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    # OpenAI TTS has a 4096 character limit per request, so chunk if needed
    max_chars = 4096
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        cut = remaining[:max_chars].rfind(". ")
        if cut == -1:
            cut = remaining[:max_chars].rfind(" ")
        if cut == -1:
            cut = max_chars
        else:
            cut += 1
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    print(f"  Split text into {len(chunks)} chunk(s) for TTS")

    audio_parts = []
    for i, chunk in enumerate(chunks):
        print(f"  Generating audio chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)...")
        part_path = tempfile.mktemp(suffix=f"_part{i}.mp3")
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=chunk,
            response_format="mp3",
        ) as response:
            response.stream_to_file(part_path)
        audio_parts.append(part_path)

    if len(audio_parts) == 1:
        return audio_parts[0]

    output_path = tempfile.mktemp(suffix=".mp3")
    concat_list = tempfile.mktemp(suffix=".txt")
    with open(concat_list, "w") as f:
        for part in audio_parts:
            f.write(f"file '{part}'\n")

    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_path],
        capture_output=True,
    )

    os.unlink(concat_list)
    for part in audio_parts:
        os.unlink(part)

    return output_path


def transcribe_with_whisper_api(audio_path, api_key=None):
    """Transcribe audio with OpenAI Whisper API (whisper-1) to get word-level timestamps."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    print("  Transcribing audio via OpenAI Whisper API...")
    with open(audio_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    word_timestamps = []
    for word_info in result.words:
        word_timestamps.append({
            "word": word_info.word.strip(),
            "start": word_info.start,
            "end": word_info.end,
        })

    return word_timestamps


def get_font(size):
    """Get a font, trying common macOS paths."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def create_karaoke_frame_generator(word_timestamps, video_size, words_per_line=6):
    """Create a function that generates frames with an underline on the active word."""
    width, height = video_size
    font = get_font(44)
    text_color = (255, 255, 255, 255)
    underline_color = (255, 210, 0, 255)
    shadow_color = (0, 0, 0, 180)
    margin = 60

    # Group words into lines
    lines = []
    for i in range(0, len(word_timestamps), words_per_line):
        lines.append(word_timestamps[i:i + words_per_line])

    def make_frame(t):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Find which word is active at time t
        active_word_idx = -1
        for i, w in enumerate(word_timestamps):
            if w["start"] <= t <= w["end"]:
                active_word_idx = i
                break
        # If between words, highlight the next upcoming word
        if active_word_idx == -1:
            for i, w in enumerate(word_timestamps):
                if w["start"] > t:
                    # Only highlight if we're close (within 0.3s)
                    if i > 0 and t > word_timestamps[i - 1]["end"]:
                        active_word_idx = i - 1  # stay on previous word
                    break

        # Which line is active
        active_line_idx = 0
        if active_word_idx >= 0:
            active_line_idx = active_word_idx // words_per_line
        else:
            # Find line for next upcoming word
            for i, w in enumerate(word_timestamps):
                if w["start"] > t:
                    active_line_idx = i // words_per_line
                    break
            else:
                active_line_idx = len(lines) - 1

        # Show a window of lines centered on the active line
        visible_lines = 6
        display_start = max(0, active_line_idx - visible_lines // 2)
        display_end = min(len(lines), display_start + visible_lines)
        display_start = max(0, display_end - visible_lines)

        line_height = 70
        total_display_height = (display_end - display_start) * line_height
        start_y = (height - total_display_height) // 2

        for line_num in range(display_start, display_end):
            line_words = lines[line_num]
            y = start_y + (line_num - display_start) * line_height

            # Build the line text and measure each word for positioning
            word_positions = []
            total_line_width = 0
            for w in line_words:
                text = w["word"] + " "
                bbox = font.getbbox(text)
                word_w = bbox[2] - bbox[0]
                word_positions.append(word_w)
                total_line_width += word_w

            # Clamp line to fit within margins
            x = max(margin, (width - total_line_width) // 2)

            for idx, w in enumerate(line_words):
                global_idx = line_num * words_per_line + idx
                is_active = (global_idx == active_word_idx)
                text = w["word"] + " "
                word_w = word_positions[idx]

                # Shadow
                draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)
                # Text (all same color and size)
                draw.text((x, y), text, font=font, fill=text_color)

                # Draw underline under active word
                if is_active:
                    word_only = w["word"]
                    word_only_bbox = font.getbbox(word_only)
                    word_only_w = word_only_bbox[2] - word_only_bbox[0]
                    underline_y = y + font.getbbox("Ay")[3] + 4
                    # Yellow underline, 3px thick
                    draw.line(
                        [(x, underline_y), (x + word_only_w, underline_y)],
                        fill=underline_color, width=3,
                    )

                x += word_w

        return np.array(img)

    return make_frame


def main():
    parser = argparse.ArgumentParser(description="Generate karaoke-style video with OpenAI TTS + Whisper")
    parser.add_argument("--text", required=True, help="Path to text file")
    parser.add_argument("--output", default="output.mp4", help="Output video path")
    parser.add_argument("--voice", default="onyx",
                        help="OpenAI TTS voice: alloy, echo, fable, onyx, nova, shimmer (default: onyx)")
    parser.add_argument("--model", default="tts-1", help="OpenAI TTS model: tts-1 or tts-1-hd (default: tts-1)")
    parser.add_argument("--audio", default=None, help="Pre-generated audio file (skips TTS step)")
    parser.add_argument("--video", default=None, help="Background video (optional)")
    parser.add_argument("--width", type=int, default=1280, help="Video width")
    parser.add_argument("--height", type=int, default=720, help="Video height")
    parser.add_argument("--words-per-line", type=int, default=6, help="Words per line")
    parser.add_argument("--api-key", default=None, help="OpenAI API key (or set OPENAI_API_KEY env var)")
    args = parser.parse_args()

    # Read text
    text = Path(args.text).read_text().strip()
    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)
    clean_text = re.sub(r'[#\-]', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    print(f"Text length: {len(clean_text)} characters")
    print(f"First 100 chars: {clean_text[:100]}...")
    print()

    # Step 1: Generate audio with OpenAI TTS (or use pre-generated)
    if args.audio:
        audio_path = args.audio
        print(f"Step 1: Skipped — using existing audio: {audio_path}")
    else:
        print("Step 1: Generating OpenAI TTS audio...")
        audio_path = generate_openai_tts(
            clean_text, voice=args.voice, model=args.model, api_key=args.api_key
        )
        print(f"Audio saved to: {audio_path}")

    # Step 2: Transcribe with Whisper API for word timestamps
    print("\nStep 2: Getting word timestamps with Whisper API...")
    word_timestamps = transcribe_with_whisper_api(audio_path, api_key=args.api_key)
    print(f"Got {len(word_timestamps)} word timestamps")

    # Save timestamps for debugging
    timestamps_path = Path(args.output).with_suffix(".timestamps.json")
    with open(timestamps_path, "w") as f:
        json.dump(word_timestamps, f, indent=2)
    print(f"Timestamps saved to: {timestamps_path}")

    # Load audio to get duration
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    print(f"Audio duration: {duration:.2f}s")

    # Create background
    video_size = (args.width, args.height)
    if args.video:
        bg_clip = VideoFileClip(args.video).resized(video_size).with_duration(duration)
    else:
        bg_clip = ColorClip(size=video_size, color=(20, 20, 30), duration=duration)

    # Step 3: Create text overlay
    print("\nStep 3: Rendering karaoke text overlay...")
    frame_generator = create_karaoke_frame_generator(
        word_timestamps, video_size, words_per_line=args.words_per_line
    )
    text_clip = VideoClip(frame_generator, duration=duration)

    # Composite
    final = CompositeVideoClip([bg_clip, text_clip])
    final = final.with_audio(audio_clip)

    # Export
    print(f"\nWriting video to {args.output}...")
    final.write_videofile(
        args.output,
        fps=15,
        codec="libx264",
        audio_codec="aac",
        threads=4,
    )

    # Cleanup temp audio (only if we generated it)
    if not args.audio:
        os.unlink(audio_path)
    print("Done!")


if __name__ == "__main__":
    main()
