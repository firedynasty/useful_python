"""
Suggestopedia lesson audio from a dialogue file.

Each turn: Chinese → pause → English → bigger pause → next turn.
Control pacing with your audio player's playback speed.

Sample text: 小西: 你可拉倒吧，这句话我上个月就听你说过了。。Xiǎo Xī: Nǐ kě lā dǎo ba, zhè jù huà wǒ shàng gè yuè jiù tīng nǐ shuō guò le..Xiao Xi: Oh please, I heard you say the exact same thing last month...

小红: 这次不一样！我这次可是下了很大的决心！我还下载了一个减肥APP，它说每天走一万步就能瘦，感觉很容易啊。Xiǎo Hóng: Zhè cì bù yī yàng! Wǒ zhè cì kě shì xià le hěn dà de jué xīn! Wǒ hái xià zǎi le yī gè jiǎn féi APP, tā shuō měi tiān zǒu yī wàn bù jiù néng shòu, gǎn jué hěn róng yì a.Xiao Hong: This time is different! I'm really determined! I even downloaded a weight loss app that says walking 10,000 steps daily will make me slim - seems easy enough! 0:33

小西: 那你今天走了多少步呢？Xiǎo Xī: Nà nǐ jīn tiān zǒu le duō shǎo bù ne?Xiao Xi: So how many steps have you taken today?

小红: 已经走了100步！是我摇手机摇出来的，怎么样我聪明吧！Xiǎo Hóng: Yǐ jīng zǒu le yī bǎi bù!  Shì wǒ yáo shǒu jī yáo chū lái de, zěn me yàng wǒ cōng míng ba!Xiao Hong: Already 100 steps!  I got them by shaking my phone - pretty clever, right?

Usage:
    export ELEVENLABS_API_KEY="your-key"

    python suggestopedia.py -d dialogue.txt
    python suggestopedia.py -d dialogue.txt -o lesson.mp3
    python suggestopedia.py -d dialogue.txt --pause 2000

Dialogue format:
    Works with simple format:
        小红: Chinese text.
         English translation.

    And also with inline pinyin + English all on one line:
        小红: 这次不一样！Xiǎo Hóng: Zhè cì bù yī yàng! Xiao Hong: This time is different! 0:33

    Pinyin (tone marks), pinyin speaker retags, and timestamps are auto-stripped.
"""

import os
import sys
import re
import io
import argparse
from pathlib import Path

from elevenlabs import ElevenLabs
from pydub import AudioSegment


API_KEY = os.environ.get("ELEVENLABS_API_KEY")
MODEL_ID = "eleven_multilingual_v2"

VOICE_POOL = [
    "EXAVITQu4vr4xnSDxMaL",  # Bella  — warm female
    "21m00Tcm4TlvDq8ikWAM",  # Rachel — calm female
    "VR6AewLTigWG4xSOukaG",  # Arnold — male
    "pNInz6obpgDQGcFmaJgB",  # Adam   — male
]

DEFAULT_PAUSE_MS = 1500


# ---------------------------------------------------------------------------
# Dialogue parser
# ---------------------------------------------------------------------------

SPEAKER_RE = re.compile(
    r'^([\u4e00-\u9fffA-Za-z]+[\u4e00-\u9fff\w]*)\s*[:：]\s*', re.UNICODE
)

_TONE_RE = re.compile(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', re.IGNORECASE)
_TIMESTAMP_RE = re.compile(r'\b\d+:\d{2}\b')
_RETAG_RE = re.compile(r'^[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]+\s+[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]+\s*:\s*', re.IGNORECASE)


def _has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def _is_pinyin(text):
    return bool(_TONE_RE.search(text)) and not _has_chinese(text)


def _split_zh_en(text):
    text = _TIMESTAMP_RE.sub("", text)
    zh, en = [], []
    for s in re.split(r'(?<=[。！？.!?])\s*', text):
        s = s.strip()
        if not s:
            continue
        if _has_chinese(s):
            zh.append(s)
        elif _is_pinyin(s):
            pass
        elif re.search(r'[A-Za-z]', s):
            s = _RETAG_RE.sub("", s).strip()
            if s:
                en.append(s)
    return " ".join(zh), " ".join(en)


def parse_dialogue(raw):
    turns = []
    current_speaker = None
    current_lines = []

    def flush():
        if current_speaker and current_lines:
            zh, en = _split_zh_en(" ".join(current_lines).strip())
            if zh or en:
                turns.append((current_speaker, zh, en))

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Only split on Chinese speaker names mid-line (e.g. 小红:).
        # Do NOT split on single Latin words like "Hong:", "Xi:", "plan:" —
        # those are retags or plain text and are handled by _split_zh_en.
        for seg in re.split(r'(?<=[^\s])\s+(?=[\u4e00-\u9fff]+\s*[:：])', line):
            m = SPEAKER_RE.match(seg)
            if m:
                flush()
                current_lines = []
                current_speaker = m.group(1)
                rest = seg[m.end():].strip()
                if rest:
                    current_lines.append(rest)
            else:
                if current_speaker is None:
                    current_speaker = "narrator"
                current_lines.append(seg)

    flush()
    return turns


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

def speak(client, voice_id, text, label=""):
    print(f"  {label:<14} {text[:72]}{'...' if len(text) > 72 else ''}")
    chunks = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
        voice_settings={"stability": 0.45, "similarity_boost": 0.75, "style": 0.4},
    )
    return AudioSegment.from_mp3(io.BytesIO(b"".join(chunks)))


def gap(ms):
    return AudioSegment.silent(duration=ms)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Suggestopedia dialogue TTS")
    parser.add_argument("-d", "--dialogue", required=True, help="Dialogue text file")
    parser.add_argument("-o", "--output",   default="lesson.mp3")
    parser.add_argument("--pause", type=int, default=DEFAULT_PAUSE_MS,
                        help=f"Pause between Chinese and English in ms (default: {DEFAULT_PAUSE_MS})")
    args = parser.parse_args()

    if not API_KEY:
        print("Error: set ELEVENLABS_API_KEY"); sys.exit(1)

    turns = parse_dialogue(Path(args.dialogue).read_text(encoding="utf-8"))
    print(f"Dialogue: {len(turns)} turns\n")

    speaker_voices = {}
    for spk, _, _ in turns:
        if spk not in speaker_voices:
            speaker_voices[spk] = VOICE_POOL[len(speaker_voices) % len(VOICE_POOL)]
            print(f"  {spk} → voice #{len(speaker_voices)}")
    print()

    client = ElevenLabs(api_key=API_KEY)
    audio  = AudioSegment.empty()
    pause  = gap(args.pause)
    between = gap(args.pause * 2)

    for spk, zh, en in turns:
        voice = speaker_voices[spk]
        if zh:
            audio += speak(client, voice, zh, f"[{spk}|ZH]")
            audio += pause
        if en:
            audio += speak(client, voice, en, f"[{spk}|EN]")
            audio += between

    output_path = Path(args.output)
    audio.export(output_path, format="mp3")
    print(f"\nSaved: {output_path}  ({len(audio)/1000:.0f}s)")


if __name__ == "__main__":
    main()
