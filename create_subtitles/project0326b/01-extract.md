# Extract a Segment from an MP4

Use `ffmpeg` to clip a portion of a video by specifying a start time and duration (or end time).

## Basic Command

```bash
ffmpeg -ss 00:11:00 -i input.mp4 -t 2340 -c copy output.mp4
```

- `-ss 00:11:00` — start time
- `-t 2340` — duration in seconds (e.g., 50:00 - 11:00 = 39 min = 2340 sec)
- `-c copy` — no re-encoding (fast, no quality loss)

## Using End Time Instead of Duration

Use `-to` to specify the end time directly (no math needed):

```bash
ffmpeg -ss 00:11:00 -i input.mp4 -to 00:50:00 -c copy output.mp4
```

## Examples

| Clip | Command |
|---|---|
| 11:00 to 50:00 (39 min) | `ffmpeg -ss 00:11:00 -i input.mp4 -t 2340 -c copy output.mp4` |
| 20:00 to 54:00 (34 min) | `ffmpeg -ss 00:20:00 -i input.mp4 -t 2040 -c copy output.mp4` |
| Keep first 19 min | `ffmpeg -i input.mp4 -t 1140 -c copy output.mp4` |
| Keep first 3 min | `ffmpeg -i input.mp4 -t 180 -c copy output.mp4` |

running to grab 
mp4

first commmand is to grab the mp3 from shortened video

ffmpeg -i streetTalkEp1.mp4 -vn -acodec libmp3lame -b:a 128k audioStream.mp3

third is to divide them 

ffmpeg -i audioStream.mp3 -f segment -segment_time 600 -c copy segment_%03d.mp3

get the API key then 

ENGLISH VERSION

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

CHINESE VERSION

for f in segment_*.mp3; do
  curl https://api.openai.com/v1/audio/transcriptions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: multipart/form-data" \
    -F file="@$f" \
    -F model="whisper-1" \
    -F response_format="srt" \
    -F language="zh" \
    -o "${f%.mp3}_zh.srt"
done



Merge everything

bash merge_srt.sh en english.srt


Copy the english.srt to the video

ffmpeg -i streetTalkEp1.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2'" \
  -c:a copy output_subtitled.mp4

#burning the English but to the top instead of over the Chinese

ffmpeg -i streetTalkEp1.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=6,MarginV=80'" \
  -c:a copy output_subtitled.mp4

#burning over the Chinese Subtitles, if not good enough higher 150, 180
ffmpeg -i streetTalkEp1.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2,MarginV=120'" \
  -c:a copy output_subtitled.mp4



probably next time need to be at 80 because 120 is too high

ffmpeg -i streetTalkEp1.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2,MarginV=60'" \
  -c:a copy output_subtitled.mp4 



`MarginV=60` will drop it closer to the bottom. If it still overlaps the Chinese, nudge up to `80`. The sweet spot is likely somewhere between `60–90` for this video.



python translate_srt.py -c chinese.srt -o english_chinese.txt  

