⏺ Trim the last 6 minutes off (keep first 19 minutes):                          
                                                                                
  ffmpeg -i new1.mp4 -t 1190 -c copy new_trimmed.mp4                 
                                                                                
  19 min 50 sec = 1190 seconds.                                         

  -t 1140 = 19 minutes in seconds. -c copy means no re-encoding so it's instant 
  and no quality loss.
                                                                                
  If you want to cut from a specific start point instead, add -ss before -i:    

  ffmpeg -ss 00:03:00 -i mp4_video.mp4 -t 1140 -c copy mp4_video_trimmed.mp4    
                                                                                
  That would take 19 minutes starting from 3:00. 

3 mins

ffmpeg -i new1.mp4 -t 180 -c copy new_trimmed.mp4

ffmpeg -i output_subtitled.mp4 -t 180 -c copy new_3_mins.mp4