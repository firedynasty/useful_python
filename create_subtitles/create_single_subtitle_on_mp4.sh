#!/bin/bash
cd /Users/stanleytan/Downloads

ffmpeg -i mp4_video.mp4 \
  -vf "subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=24,PrimaryColour=&HFFFFFF,Alignment=2'" \
  -c:a copy output_subtitled.mp4
