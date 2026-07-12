# English Subtitle on Original Video

## Prerequisites

- `ffmpeg` with libass support (`brew install homebrew-ffmpeg/ffmpeg/ffmpeg`)
- OpenAI API key
- Source file: `mp4_video.mp4`
- Script: `merge_srt.sh` (in the same directory)

## Step 1: Extract audio from video

```bash
ffmpeg -i mp4_video.mp4 -vn -acodec libmp3lame -b:a 128k audioStream.mp3
ffmpeg -i new_trimmed.mp4 -vn -acodec libmp3lame -b:a 128k audioStream.mp3


```

## Step 2: Split audio into 10-minute segments

Splitting improves translation quality — Whisper degrades on long audio.

```bash
ffmpeg -i audioStream.mp3 -f segment -segment_time 600 -c copy segment_%03d.mp3
```

Produces `segment_000.mp3`, `segment_001.mp3`, etc. (each ~10 min).

## Step 3: Generate English SRT per segment

```bash
export OPENAI_API_KEY="sk-..."

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

## Step 4: Merge English SRT segments into a single file

Each segment's SRT timestamps start at 00:00:00. The merge script offsets timestamps based on segment number and combines them.

```bash
bash merge_srt.sh en english.srt
```

Produces `english.srt`.

## Step 5: Burn English subtitles onto video

```bash
ffmpeg -i mp4_video.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2'" \
  -c:a copy output_subtitled.
  
ffmpeg -i new_trimmed.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2'" \
  -c:a copy output_subtitled.mp4
```

Output: `output_subtitled.mp4`

## Font Notes

- **English font:** `Arial Unicode MS` from `/Library/Fonts` (also supports CJK characters)
