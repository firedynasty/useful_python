#!/bin/bash
# Usage: bash merge_srt.sh <lang_suffix> <output_filename>
# Example: bash merge_srt.sh en english.srt
#          bash merge_srt.sh zh chinese.srt

LANG_SUFFIX="$1"
OUTPUT="$2"
SEGMENT_DURATION=600
COUNTER=1

if [ -z "$LANG_SUFFIX" ] || [ -z "$OUTPUT" ]; then
  echo "Usage: bash merge_srt.sh <lang_suffix> <output_filename>"
  echo "  e.g. bash merge_srt.sh en english.srt"
  exit 1
fi

> "$OUTPUT"

for srt in $(ls segment_*_${LANG_SUFFIX}.srt | sort); do
  SEG_NUM=$(echo "$srt" | grep -o '[0-9]\{3\}')
  OFFSET=$((10#$SEG_NUM * SEGMENT_DURATION))

  while IFS= read -r line; do
    if echo "$line" | grep -qE '^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$'; then
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
      echo "$COUNTER" >> "$OUTPUT"
      COUNTER=$((COUNTER + 1))
    else
      echo "$line" >> "$OUTPUT"
    fi
  done < "$srt"
done

echo "Merged to $OUTPUT"
