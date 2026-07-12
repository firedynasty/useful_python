ffmpeg -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i audioStream.mp3 \
  -filter_complex \
  "[0:v]subtitles=filename=english.srt:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v]" \
  -map "[v]" -map 1:a \
  -shortest output.mp4


# Add subtitles to an existing video file:

ffmpeg -i your_video.mp4 \
  -filter_complex \
  "[0:v]subtitles=filename=english.srt:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v]" \
  -map "[v]" -map 0:a \
  -shortest output.mp4





ffmpeg -i shema_israel.mp4 \
  -filter_complex \
  "[0:v]subtitles=filename=new_english.srt:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v]" \
  -map "[v]" -map 0:a \
  -shortest shema_israel_output.mp4





<video src="/Users/stanleytan/Documents/technical/python/create_subtitles/shema_israel.mp4" controls=""></video>
