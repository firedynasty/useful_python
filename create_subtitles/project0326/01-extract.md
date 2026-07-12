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

first command is to shorten the video
ffmpeg -ss 00:20:00 -i lchsMandarin.mp4 -to 00:54:00 -c copy lchsMandarinshortened.mp4

second commmand is to grab the mp3 from shortened video

ffmpeg -i lchsMandarinshortened.mp4 -vn -acodec libmp3lame -b:a 128k audioStream.mp3

third is to divide them 

ffmpeg -i audioStream.mp3 -f segment -segment_time 600 -c copy segment_%03d.mp3

get the API key then 

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


Merge everything

bash merge_srt.sh en english.srt


Copy the english.srt to the video

ffmpeg -i lchsMandarinshortened.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2'" \
  -c:a copy output_subtitled.mp4

  

