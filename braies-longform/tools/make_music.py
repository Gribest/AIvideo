"""Original, royalty-free, soothing music bed for the whole film, ducked under the narration.
Reads timeline.json + assets/vo/vo.json.  python3 tools/make_music.py -> assets/audio/music_long.wav"""
import json, wave, numpy as np
SR = 44100
tl = json.load(open("timeline.json")); vo = json.load(open("assets/vo/vo.json"))
TOTAL = tl["total"]; N = int(TOTAL * SR) + SR
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(3)
def note(m): return 440 * 2 ** ((m - 69) / 12)
def t_(d): return np.arange(int(d * SR)) / SR
def add(buf, start, sig, g):
    i = int(start * SR); j = min(N, i + len(sig))
    if 0 <= i < N: buf[i:j] += sig[: j - i] * g

fr = {f["n"]: f for f in tl["frames"]}
BUT = fr[22]["start"]; REAL = fr[3]["start"]; TRIP = fr[31]["start"]; BOAT = fr[15]["start"]; BOAT_END = fr[22]["start"]
BPM = 72; beat = 60 / BPM; bar = beat * 4
# Dmaj9 - Bm7 - Gmaj7 - A6sus
prog = [[62, 66, 69, 73, 76], [59, 62, 66, 69, 73], [55, 59, 62, 66, 69], [57, 62, 64, 66, 69]]
bass = [38, 35, 31, 33]
nb = int(TOTAL / bar) + 2
for b in range(nb):
    t0 = b * bar; ch = prog[b % 4]
    if REAL <= t0 < REAL + 3.5 or BUT - bar < t0 < BUT + 2.0:  # music drops for "Reality" and "BUT"
        continue
    tt = t_(bar + 0.8)
    env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (bar + 0.8 - tt)) / 0.9)
    pad = sum(np.sin(2 * np.pi * note(m) * tt + k) * (0.6 if k else 1) + 0.25 * np.sin(2 * np.pi * note(m) * 1.004 * tt)
              for k, m in enumerate(ch[:4]))
    add(L, t0, pad * env, 0.022); add(R, t0, pad * env, 0.022)
    # soft bell/piano arpeggio, quarter notes (eighths in the boat section)
    step = beat / 2 if BOAT <= t0 < BOAT_END else beat
    k = 0; tt2 = t_(2.2)
    while k * step < bar - 1e-6:
        m = ch[[0, 2, 4, 3, 1, 3, 2, 4][k % 8]] + 12
        s = (np.sin(2 * np.pi * note(m) * tt2) + 0.25 * np.sin(4 * np.pi * note(m) * tt2) + 0.08 * np.sin(6 * np.pi * note(m) * tt2)) \
            * np.minimum(1, tt2 / 0.006) * np.exp(-tt2 / 0.7)
        pan = [-0.3, 0.2, -0.1, 0.3][k % 4]
        add(L, t0 + k * step, s, 0.05 * (1 - pan)); add(R, t0 + k * step, s, 0.05 * (1 + pan)); k += 1
    # warm bass, whole notes
    tb = t_(bar)
    s = np.sin(2 * np.pi * note(bass[b % 4]) * tb) * np.minimum(1, tb / 0.05) * np.exp(-tb / 2.2)
    add(L, t0, s, 0.12); add(R, t0, s, 0.12)
    # light shaker pulse in the boat section and the verdict
    if BOAT <= t0 < BOAT_END or t0 >= TRIP:
        for q in range(8):
            n_ = rng.standard_normal(int(0.05 * SR)) * np.exp(-t_(0.05) / 0.012)
            add(L, t0 + q * beat / 2, n_, 0.012); add(R, t0 + q * beat / 2, n_, 0.014)

mix = np.stack([L, R], 1)
# simple room: two short delays
for d, g in ((0.11, 0.25), (0.23, 0.15)):
    k = int(d * SR); mix[k:, 0] += mix[:-k, 1] * g; mix[k:, 1] += mix[:-k, 0] * g
# duck under narration (-10 dB, 0.3 s ramps)
tt = np.arange(N) / SR; gain = np.ones(N)
for f in tl["frames"]:
    v = vo.get(str(f["n"]))
    if not v: continue
    a = f["start"] + f["lead"]; b = a + v["dur"] + (0.5 + v["extra"]["dur"] if "extra" in v else 0)
    gain = np.minimum(gain, 1 - 0.68 * np.clip(np.minimum((tt - (a - 0.3)) / 0.3, ((b + 0.4) - tt) / 0.4), 0, 1))
fade = np.minimum(1, tt / 1.5) * np.clip((TOTAL - tt) / 4.0, 0, 1)
mix *= (gain * fade)[:, None]
mix = mix[: int(TOTAL * SR)]
mix /= np.abs(mix).max() / 0.6
with wave.open("assets/audio/music_long.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("music", round(TOTAL, 1), "s")
