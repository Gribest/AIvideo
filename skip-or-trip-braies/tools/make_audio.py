"""Synthesises an original (royalty-free) music bed and the SFX into assets/audio/.
python3 tools/make_audio.py"""
import numpy as np, wave, os
SR = 44100; OUT = "assets/audio"; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

def save(name, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def t_(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.005, r=0.3):
    t = t_(d); e = np.minimum(1, t / a) * np.exp(-t / r); return e
def note(f): return 440 * 2 ** ((f - 69) / 12)

def lp(x, k):  # one-pole low-pass
    y = np.empty_like(x); acc = 0.0; a = k
    for i, v in enumerate(x): acc += a * (v - acc); y[i] = acc
    return y

# ---------------- music bed -------------------------------------------
BPM = 112; beat = 60 / BPM; DUR = 33.5
N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N)
def add(buf, start, sig, gain=1.0):
    i = int(start * SR); j = min(N, i + len(sig))
    if i < N: buf[i:j] += sig[: j - i] * gain

# Cmaj7 - Am7 - Fmaj7 - G6, one bar each, MIDI notes
prog = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 64]]
bass = [36, 33, 29, 31]
bars = int(DUR / (beat * 4)) + 1
BUT_T, TRIP_T = 20.0, 27.8
for b in range(bars):
    t0 = b * beat * 4; ch = prog[b % 4]
    # warm pad
    d = beat * 4
    pad = sum(np.sin(2 * np.pi * note(n) * t_(d)) + 0.3 * np.sin(2 * np.pi * note(n) * 2.003 * t_(d)) for n in ch)
    pe = np.minimum(1, t_(d) / 0.4) * np.minimum(1, (d - t_(d)) / 0.3)
    add(L, t0, pad * pe, 0.035); add(R, t0, pad * pe, 0.035)
    # plucked arpeggio, 8ths
    for k in range(8):
        n = ch[[0, 1, 2, 3, 2, 1, 2, 3][k]] + 12
        tt = t_(0.5)
        s = (np.sin(2 * np.pi * note(n) * tt) + 0.4 * np.sin(4 * np.pi * note(n) * tt)) * env(0.5, 0.003, 0.12)
        pan = 0.35 if k % 2 else -0.35
        add(L, t0 + k * beat / 2, s, 0.07 * (1 - pan)); add(R, t0 + k * beat / 2, s, 0.07 * (1 + pan))
    # bass on 1 and 3
    for k in (0, 2):
        tt = t_(beat * 1.8)
        s = np.sin(2 * np.pi * note(bass[b % 4]) * tt) * env(beat * 1.8, 0.01, 0.5)
        add(L, t0 + k * beat, s, 0.16); add(R, t0 + k * beat, s, 0.16)
    if t0 < 1.9: continue  # drums enter after the hook
    for k in range(4):
        tk = t0 + k * beat
        if BUT_T - 0.05 <= tk < BUT_T + 1.0: continue  # drop out on "BUT"
        tt = t_(0.35); f = 110 * np.exp(-tt * 18) + 45
        kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.35, 0.002, 0.12)
        add(L, tk, kick, 0.28); add(R, tk, kick, 0.28)
        hat = np.diff(rng.standard_normal(int(0.06 * SR)), prepend=0) * env(0.06, 0.001, 0.015)
        add(L, tk + beat / 2, hat, 0.05); add(R, tk + beat / 2, hat, 0.06)
        if k in (1, 3):  # soft clap
            cl = lp(rng.standard_normal(int(0.2 * SR)), 0.5) * env(0.2, 0.002, 0.05)
            add(L, tk, cl, 0.08); add(R, tk, cl, 0.08)

mix = np.stack([L, R], 1)
# duck the bed under "BUT", fade the very end so the loop restarts clean
tt = np.arange(N) / SR
duck = 1 - 0.6 * np.exp(-((tt - (BUT_T + 0.5)) / 0.6) ** 2)
fade = np.minimum(1, (DUR - tt) / 0.6) * np.minimum(1, tt / 0.05)
mix *= (duck * fade)[:, None]
mix /= np.abs(mix).max() / 0.8
save("music_bed", mix)

# ---------------- sfx -------------------------------------------------
# whoosh: band-passed noise sweeping up
d = 0.45; tt = t_(d); n = rng.standard_normal(len(tt))
sweep = np.empty_like(n); acc = 0; acc2 = 0
for i, v in enumerate(n):
    k = 0.02 + 0.25 * (tt[i] / d) ** 1.5
    acc += k * (v - acc); acc2 += k * (acc - acc2); sweep[i] = acc - acc2
e = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
w = sweep * e; w /= np.abs(w).max()
save("whoosh", np.stack([w * 0.6, np.roll(w, 300) * 0.6], 1))
# tick
d = 0.06; tt = t_(d)
tick = (np.sin(2 * np.pi * 2400 * tt) + 0.5 * np.sin(2 * np.pi * 3600 * tt)) * env(d, 0.0005, 0.008)
save("tick", tick * 0.5)
# hit: low boom + noise crack (BUT / verdict)
d = 1.0; tt = t_(d); f = 160 * np.exp(-tt * 9) + 38
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.002, 0.35)
crack = lp(rng.standard_normal(len(tt)), 0.35) * env(d, 0.001, 0.04)
hit = boom * 0.9 + crack * 0.5; hit /= np.abs(hit).max()
save("hit", hit * 0.85)
# stamp: hit + bright chime for the verdict
d = 1.4; tt = t_(d)
chime = sum(np.sin(2 * np.pi * note(n) * tt) for n in (84, 88, 91)) * env(d, 0.003, 0.5) / 3
st = np.concatenate([hit, np.zeros(len(tt) - len(hit))]) * 0.8 + chime * 0.45
save("stamp", st / np.abs(st).max() * 0.85)
print("audio done")
