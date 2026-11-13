"""Narration: Kokoro-82M, voice af_heart (soft female), slowed slightly. Reads ../skip-or-trip-braies/STORYBOARD.md.
python3 tools/make_vo.py  -> assets/vo/fNN.wav + assets/vo/vo.json (durations)"""
import re, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
C = "/root/.cache/hyperframes/tts/"
k = Kokoro(C + "models/kokoro-v1.0.onnx", C + "voices/voices-v1.0.bin")
md = open("../skip-or-trip-braies/STORYBOARD.md").read()
lines = re.findall(r"## Frame (\d+): .*\n(?:- .*\n)*?- voiceover: (.*)\n", md)
# pronunciation help for the TTS only (captions keep the real spelling)
SAY = {"Lago di Braies": "Lahgo dee Bry-es", "Seekofel": "Zay-ko-fel", "€55": "fifty-five euros", "P4": "P four",
       "P3 or P2": "P three or P two", "P3": "P three", "1,500": "fifteen hundred", "2,800": "twenty-eight hundred", "TRIP": "trip"}
out = {}
for num, text in lines:
    if text.startswith("("): continue
    say = text
    for a, b in SAY.items(): say = say.replace(a, b)
    audio, sr = k.create(say, voice="af_heart", speed=0.9, lang="en-us")
    pad = np.zeros(int(0.08 * sr)); audio = np.concatenate([pad, audio, pad])
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.7
    sf.write(f"assets/vo/f{int(num):02d}.wav", audio, sr)
    out[int(num)] = {"text": text, "dur": round(len(audio) / sr, 2)}
    print(num, out[int(num)]["dur"], text[:60])
json.dump(out, open("assets/vo/vo.json", "w"), indent=1)
