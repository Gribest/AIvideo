"""Second narration lines for the longest scenes (story, no new facts). -> assets/vo/fNNb.wav, merged into vo.json"""
import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
C = "/root/.cache/hyperframes/tts/"
k = Kokoro(C + "models/kokoro-v1.0.onnx", C + "voices/voices-v1.0.bin")
EXTRA = {
 6: "We arrived with our little one, a camera, and a bag full of *snacks.*",
 10: "Every few minutes, the light shifts across that *rock face.*",
 12: "Green, gold, and that *turquoise* water. It hardly looks real.",
 13: "Our daughter headed straight for the *sand.*",
 14: "She could have stayed here *all day.*",
 20: "The only sounds are the oars, and the odd *happy squeal.*",
 24: "Everyone is chasing the same photo, from the *same spot.*",
 26: "Bring snacks, a warm layer, and a *toy* for the boat.",
 27: "Golden light, still water, and the boats lined up at the *dock.*",
 30: "It's busy, and it's not quite the postcard. But in that boat, with our daughter, under those mountains, we didn't mind *at all.*",
}
vo = json.load(open("assets/vo/vo.json"))
for n, text in EXTRA.items():
    audio, sr = k.create(text.replace("*", ""), voice="af_heart", speed=0.9, lang="en-us")
    pad = np.zeros(int(0.08 * sr)); audio = np.concatenate([pad, audio, pad]); audio = audio / np.abs(audio).max() * 0.7
    sf.write(f"assets/vo/f{n:02d}b.wav", audio, sr)
    vo[str(n)]["extra"] = {"text": text, "dur": round(len(audio) / sr, 2)}
    print(n, vo[str(n)]["extra"]["dur"])
json.dump(vo, open("assets/vo/vo.json", "w"), indent=1)
