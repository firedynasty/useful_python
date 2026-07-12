# Audio to Subtitle Video Workflow

## Prerequisites

- `whisper-cli` (via Homebrew: `brew install whisper-cpp`)
- `ffmpeg` with libass support (via `brew install homebrew-ffmpeg/ffmpeg/ffmpeg`)
- OpenAI API key (for English translation)

## Step 0: Extract audio from video

Source video: `/Users/stanleytan/Downloads/mp4_video.mp4` (recorded via VLC Convert/Stream)

```bash
ffmpeg -i mp4_video.mp4 -vn -acodec libmp3lame -b:a 128k audioStream.mp3
```

## Step 1: Split audio into 10-minute segments

Splitting improves translation quality — Whisper degrades on long audio.

```bash
ffmpeg -i audioStream.mp3 -f segment -segment_time 600 -c copy segment_%03d.mp3
```

This produces `segment_000.mp3`, `segment_001.mp3`, `segment_002.mp3`, etc. (each ~10 min).

## Step 2: Transcribe Chinese (local whisper-cli, full audio)

```bash
/opt/homebrew/bin/whisper-cli \
  -m /opt/homebrew/share/whisper-cpp/ggml-large-v3.bin \
  -f audioStream.mp3 --no-timestamps -otxt -l zh
```

## Step 3: Generate Chinese SRT (OpenAI API)

grab_chinese_transcript.txt

```bash
export OPENAI_API_KEY="sk-..."

# Per segment:
for f in segment_*.mp3; do
  curl https://api.openai.com/v1/audio/transcriptions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: multipart/form-data" \
    -F file="@$f" \
    -F model="whisper-1" \
    -F language="zh" \
    -F response_format="srt" \
    -o "${f%.mp3}_zh.srt"
done
```

Produces `segment_000_zh.srt`, `segment_001_zh.srt`, etc.

## Step 4: Generate English SRT (OpenAI API translation)

grab_audio_transcript_english.txt

```bash
# Per segment:
for f in segment_*.mp3; do
  curl https://api.openai.com/v1/audio/translations \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: multipart/form-data" \
    -F file="@$f" \
    -F model="whisper-1" \
    -F response_format="srt" \
    -F prompt="Translate the following Chinese audio to English." \
    -o "${f%.mp3}_en.srt"
done
```

Produces `segment_000_en.srt`, `segment_001_en.srt`, etc.

## Step 4b: Merge SRT segments into single files

Each segment's SRT starts at 00:00:00. This script offsets timestamps and merges them.

merge_srt_segments.sh

```bash
#!/bin/bash
# Usage: bash merge_srt_segments.sh zh   (or "en")
LANG_SUFFIX="${1:-en}"
SEGMENT_DURATION=600  # 10 minutes in seconds
OUTPUT="merged_${LANG_SUFFIX}.srt"
COUNTER=1

> "$OUTPUT"

for srt in $(ls segment_*_${LANG_SUFFIX}.srt | sort); do
  SEG_NUM=$(echo "$srt" | grep -o '[0-9]\{3\}')
  OFFSET=$((10#$SEG_NUM * SEGMENT_DURATION))

  while IFS= read -r line; do
    if echo "$line" | grep -qE '^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$'; then
      # Parse and offset both timestamps
      START=$(echo "$line" | awk -F' --> ' '{print $1}')
      END=$(echo "$line" | awk -F' --> ' '{print $2}')

      offset_time() {
        local t="$1" off="$2"
        local h=$(echo "$t" | cut -d: -f1)
        local m=$(echo "$t" | cut -d: -f2)
        local s_ms=$(echo "$t" | cut -d: -f3)
        local s=$(echo "$s_ms" | cut -d, -f1)
        local ms=$(echo "$s_ms" | cut -d, -f2)
        local total=$((10#$h*3600 + 10#$m*60 + 10#$s + off))
        printf "%02d:%02d:%02d,%s" $((total/3600)) $(((total%3600)/60)) $((total%60)) "$ms"
      }

      NEW_START=$(offset_time "$START" "$OFFSET")
      NEW_END=$(offset_time "$END" "$OFFSET")
      echo "$NEW_START --> $NEW_END" >> "$OUTPUT"
    elif echo "$line" | grep -qE '^[0-9]+$'; then
      # Re-number subtitle entries
      echo "$COUNTER" >> "$OUTPUT"
      COUNTER=$((COUNTER + 1))
    else
      echo "$line" >> "$OUTPUT"
    fi
  done < "$srt"
done

echo "Merged to $OUTPUT"
```

```bash
bash merge_srt_segments.sh en    # -> merged_en.srt
bash merge_srt_segments.sh zh    # -> merged_zh.srt
```

Then rename for use:
```bash
mv merged_en.srt english.srt
mv merged_zh.srt chinese.srt
```

## Step 5a: Create video with black background + dual subtitles

Chinese (cyan, top) + English (white, bottom) over black background:

create_subtitle_video.sh

```bash
ffmpeg -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i audioStream_trimmed.mp3 \
  -filter_complex \
  "[0:v]subtitles=filename=chinese.srt:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=28,PrimaryColour=&H00FFFF,Alignment=8'[v1];[v1]subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v2]" \
  -map "[v2]" -map 1:a \
  -shortest output.mp4
```

## Step 5b: Add single English subtitle to existing video (recommended)

create_single_subtitle_on_mp4.sh

```bash
ffmpeg -i mp4_video.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2'" \
  -c:a copy output_subtitled.mp4
```

## Font Notes

- **Chinese font:** `STHeiti` from `/System/Library/Fonts`
- **English font:** `Arial Unicode MS` from `/Library/Fonts` (also supports CJK characters)
- macOS restricts fonts in `/System/Library/PrivateFrameworks/` — avoid PingFangUI paths
