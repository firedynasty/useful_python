# Dual Chinese + English Subtitles (Black Background)

## Prerequisites

- `ffmpeg` with libass support (`brew install homebrew-ffmpeg/ffmpeg/ffmpeg`)
- OpenAI API key
- Source file: `mp4_video.mp4`
- Script: `merge_srt.sh` (in the same directory)

## Step 1: Extract audio from video

```bash
ffmpeg -i mp4_video.mp4 -vn -acodec libmp3lame -b:a 128k audioStream.mp3
```

## Step 2: Split audio into 10-minute segments

Splitting improves translation quality — Whisper degrades on long audio.

```bash
ffmpeg -i audioStream.mp3 -f segment -segment_time 600 -c copy segment_%03d.mp3
```

Produces `segment_000.mp3`, `segment_001.mp3`, etc. (each ~10 min).

## Step 3: Generate Chinese SRT per segment

```bash
export OPENAI_API_KEY="sk-..."

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

## Step 4: Generate English SRT per segment

```bash
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

## Step 5: Merge SRT segments into single files

Each segment's SRT timestamps start at 00:00:00. The merge script offsets timestamps based on segment number and combines them.

```bash
bash merge_srt.sh en english.srt
bash merge_srt.sh zh chinese.srt
```

Produces `english.srt` and `chinese.srt`.

## Step 6: Create video with black background + dual subtitles

Chinese (cyan, top) + English (white, bottom):

```bash
ffmpeg -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i audioStream.mp3 \
  -filter_complex \
  "[0:v]subtitles=filename=chinese.srt:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=28,PrimaryColour=&H00FFFF,Alignment=8'[v1];[v1]subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v2]" \
  -map "[v2]" -map 1:a \
  -shortest output.mp4
```

Output: `output.mp4`

## Font Notes

- **Chinese font:** `STHeiti` from `/System/Library/Fonts`
- **English font:** `Arial Unicode MS` from `/Library/Fonts` (also supports CJK characters)
- macOS restricts fonts in `/System/Library/PrivateFrameworks/` — avoid PingFangUI paths
