#!/usr/bin/env python3
"""yt_notes.py - YouTube transcript download + note/context pairing.

Two commands:

  download  Re-ports the transcript bookmarklet in Python:
            pulls a video's transcript and saves it raw:
                https://www.youtube.com/watch?v=VIDEO_ID

                [0:00:00]
                caption text...

                [0:00:03]
                more text...

      python3 yt_notes.py download "https://www.youtube.com/watch?v=VIDEO_ID"
      python3 yt_notes.py download VIDEO_ID -o transcript.txt

  pair      Takes the raw transcript plus your timestamped notes and, for
            each note, pulls the transcript window around that timestamp
            (sentence-merged, with clickable t= links) so you can hand the
            result to an AI for rewriting.

      Notes file format (one note per line, timestamp anywhere in the line):
          at 1:30 what is spaced repetition
          [0:05:23] anki connection to the forgetting curve

      python3 yt_notes.py pair transcript.txt notes.txt
      python3 yt_notes.py pair transcript.txt notes.txt -w 40 -o context.md
"""

import argparse
import json
import os
import re
import sys

MARKER_RE = re.compile(r'^\[(\d+):(\d{2}):(\d{2})\]\s*$')
NOTE_TS_RE = re.compile(r'\[?(\d{1,3}):(\d{2})(?::(\d{2}))?\]?')
VID_RE = re.compile(r'(?:v=|youtu\.be/|shorts/)([\w-]{6,})')


def hms(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def video_id(url_or_id):
    m = VID_RE.search(url_or_id)
    return m.group(1) if m else url_or_id.strip()


# ---------------------------------------------------------------- download

def cmd_download(args):
    vid = video_id(args.url)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        sys.exit("youtube-transcript-api not installed: pip3 install youtube-transcript-api")

    try:
        fetched = YouTubeTranscriptApi().fetch(vid)
    except Exception as e:
        sys.exit(f"Could not fetch transcript for {vid}: {e}")

    snippets = fetched.to_raw_data() if hasattr(fetched, 'to_raw_data') else [
        {'text': s.text, 'start': s.start} for s in fetched
    ]
    cleaned = []
    for snip in snippets:
        text = ' '.join(str(snip['text']).split())
        text = re.sub(r'^>+\s*', '', text)  # YouTube speaker-change markers
        if text:
            cleaned.append({'start': int(round(snip['start'])), 'text': text})

    if args.ytn:
        out_dir = os.path.expanduser('~/Documents/technical/github/extensions/yt-notes/transcripts')
        os.makedirs(out_dir, exist_ok=True)
        args.o = os.path.join(out_dir, vid + '.json')

    if args.o and args.o.endswith('.json'):
        # Format the yt-notes extension auto-loads: [{"start": secs, "text": ...}]
        with open(args.o, 'w') as f:
            json.dump(cleaned, f, indent=1)
        print(f"saved {len(cleaned)} segments -> {args.o}")
        return

    out = [f"https://www.youtube.com/watch?v={vid}", ""]
    for snip in cleaned:
        out.append(f"[{hms(snip['start'])}]")
        out.append(snip['text'])
        out.append("")

    text_out = '\n'.join(out)
    if args.o:
        with open(args.o, 'w') as f:
            f.write(text_out)
        print(f"saved {len(cleaned)} segments -> {args.o}")
    else:
        print(text_out)


# ---------------------------------------------------------------- pair

def parse_transcript(path):
    """Return (base_url_or_None, [(seconds, text), ...]) from the raw dump."""
    base = None
    segs = []
    cur_ts = None
    cur_lines = []

    def flush():
        if cur_ts is not None and cur_lines:
            segs.append((cur_ts, ' '.join(cur_lines)))

    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if base is None and ('youtube.com' in line or 'youtu.be' in line):
                vid = video_id(line)
                base = f"https://www.youtube.com/watch?v={vid}"
                continue
            m = MARKER_RE.match(line)
            if m:
                flush()
                cur_ts = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                cur_lines = []
            else:
                cur_lines.append(line)
    flush()
    return base, segs


def parse_note_line(line):
    """Return (display_ts, seconds, note_text) or None if no timestamp."""
    m = NOTE_TS_RE.search(line)
    if not m:
        return None
    if m.group(3) is not None:
        secs = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    else:
        secs = int(m.group(1)) * 60 + int(m.group(2))
    display = m.group(0).strip('[]')
    text = (line[:m.start()] + line[m.end():]).strip()
    text = re.sub(r'^(at|@)\b\s*', '', text, flags=re.I).strip(' -–—:')
    return display, secs, text


SENT_END_RE = re.compile(r'[.?!]["\')\]]?$')


def window_sentences(segs, lo, hi):
    """Sentence-merge segments in [lo, hi]; each sentence keeps its start ts."""
    out = []
    buf, buf_ts = '', None
    for ts, text in segs:
        if ts < lo or ts > hi:
            continue
        if buf_ts is None:
            buf_ts = ts
        buf = f"{buf} {text}".strip()
        if SENT_END_RE.search(buf):
            out.append((buf_ts, buf))
            buf, buf_ts = '', None
    if buf:
        out.append((buf_ts, buf))
    return out


def cmd_pair(args):
    base, segs = parse_transcript(args.transcript)
    if not segs:
        sys.exit(f"No transcript segments found in {args.transcript}")

    notes = []
    with open(args.notes) as f:
        for i, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            parsed = parse_note_line(line)
            if parsed is None:
                print(f"warning: line {i} has no timestamp, skipped: {line}", file=sys.stderr)
                continue
            notes.append(parsed)
    if not notes:
        sys.exit("No timestamped notes found.")

    def link(ts):
        label = hms(ts)
        return f"[{label}]({base}&t={ts}s)" if base else f"[{label}]"

    blocks = []
    for display, secs, text in notes:
        lo, hi = max(0, secs - args.w), secs + args.w
        sents = window_sentences(segs, lo, hi)
        header = f"## {display} — {text}" if text else f"## {display}"
        lines = [header, ""]
        if not sents:
            lines.append(f"(no transcript within {args.w}s of {display})")
        else:
            for ts, sent in sents:
                lines.append(f"{link(ts)} {sent}")
                lines.append("")
        blocks.append('\n'.join(lines).rstrip())

    result = '\n\n'.join(blocks) + '\n'
    if args.o:
        with open(args.o, 'w') as f:
            f.write(result)
        print(f"paired {len(notes)} note(s) -> {args.o}")
    else:
        print(result)


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    d = sub.add_parser('download', help='download a transcript to the raw [H:MM:SS] format')
    d.add_argument('url', help='YouTube URL or video ID')
    d.add_argument('-o', help='output file (default: stdout); .json extension emits extension format')
    d.add_argument('--ytn', action='store_true', help='save as <videoId>.json into the yt-notes extension transcripts folder')
    d.set_defaults(func=cmd_download)

    q = sub.add_parser('pair', help='pair timestamped notes with transcript context')
    q.add_argument('transcript', help='raw transcript file from the download command')
    q.add_argument('notes', help='notes file, one timestamped note per line')
    q.add_argument('-w', type=int, default=25, help='window in seconds around each note (default: 25)')
    q.add_argument('-o', help='output file (default: stdout)')
    q.set_defaults(func=cmd_pair)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
