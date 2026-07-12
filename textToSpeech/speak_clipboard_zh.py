import os
import pyperclip
import sounddevice as sd
from kokoro_onnx import Kokoro
from misaki.zh import ZHG2P

VOICE = "zf_xiaoxiao"  # Mandarin voices: zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
SPEED = 1.0

_dir = os.path.dirname(os.path.abspath(__file__))
kokoro = Kokoro(os.path.join(_dir, "kokoro-v1.0.onnx"), os.path.join(_dir, "voices-v1.0.bin"))
g2p = ZHG2P()

text = pyperclip.paste().strip()
if not text:
    print("Clipboard is empty.")
    raise SystemExit

print(f"Speaking {len(text)} chars with {VOICE}…")

# Convert Chinese text to phonemes using misaki
phonemes, _ = g2p(text)

# Pass phonemes directly to kokoro (bypass espeak)
stream = kokoro.create_stream(phonemes, voice=VOICE, speed=SPEED, is_phonemes=True)

import asyncio
async def play():
    async for samples, sr in stream:
        sd.play(samples, sr)
        sd.wait()

asyncio.run(play())
