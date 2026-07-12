#!/bin/bash
cd /Users/stanleytan/Downloads
rm -f output.mp4

ffmpeg -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i audioStream_trimmed.mp3 \
  -filter_complex \
  "[0:v]subtitles=filename=chinese.srt:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=28,PrimaryColour=&H00FFFF,Alignment=8'[v1];[v1]subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v2]" \
  -map "[v2]" -map 1:a \
  -shortest output.mp4
