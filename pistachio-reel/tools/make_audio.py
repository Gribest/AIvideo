"""Synthesises an original, royalty-free 120 BPM bed + SFX into assets/audio/.
python3 tools/make_audio.py   (cuts sit on the 0.5 s beat grid)"""
import numpy as np, wave
SR = 44100; OUT = "assets/audio"; rng = np.random.default_rng(11)
def save(name, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
def t_(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.005, r=0.3): t = t_(d); return np.minimum(1, t / a) * np.exp(-t / r)
def note(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, k):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
    return y

BPM = 120; beat = 0.5; DUR = 13.3; N = int(DUR * SR)
L = np.zeros(N); R = np.zeros(N)
def add(start, sig, gl, gr=None):
    i = int(round(start * SR)); j = min(N, i + len(sig))
    if 0 <= i < N: L[i:j] += sig[:j-i] * gl; R[i:j] += sig[:j-i] * (gl if gr is None else gr)

prog = [[62, 65, 69, 72], [58, 62, 65, 69], [60, 64, 67, 70], [57, 61, 64, 67]]  # Dm7 Bbmaj7 C7 A7
bass = [38, 34, 36, 33]
DROP = 6.0  # the layers reveal
for b in range(int(DUR / 2) + 1):
    t0 = b * 2.0; ch = prog[b % 4]
    for k in range(16):  # 16th pluck arp
        n = ch[[0,2,1,3,2,0,3,1][k % 8]] + 12; d = 0.25
        s = (np.sin(2*np.pi*note(n)*t_(d)) + 0.5*np.sign(np.sin(2*np.pi*note(n)*t_(d)))*0.3) * env(d, 0.002, 0.06)
        add(t0 + k * 0.125, s, 0.05 if k % 2 else 0.035, 0.035 if k % 2 else 0.05)
    for k in range(4):  # bass: off-beat pumping
        tt = t_(0.24); s = np.tanh(2.5*np.sin(2*np.pi*note(bass[b % 4])*tt)) * env(0.24, 0.005, 0.12)
        add(t0 + k*beat + 0.25, s, 0.13)
    for k in range(4):
        tk = t0 + k * beat
        if 5.5 <= tk < DROP: continue  # one-beat gap right before the drop
        tt = t_(0.4); f = 140*np.exp(-tt*22) + 45
        add(tk, np.sin(2*np.pi*np.cumsum(f)/SR) * env(0.4, 0.001, 0.13), 0.34)
        hat = np.diff(rng.standard_normal(int(0.05*SR)), prepend=0) * env(0.05, 0.001, 0.012)
        add(tk + 0.25, hat, 0.05, 0.065)
        if tk >= 1.5 and k in (1, 3):
            cl = lp(rng.standard_normal(int(0.22*SR)), 0.55) * env(0.22, 0.002, 0.06)
            add(tk, cl, 0.12, 0.11)
# riser into the drop
d = 1.0; tt = t_(d); nz = rng.standard_normal(len(tt))
add(DROP - d, lp(nz, 0.08) * (tt/d)**2 * 0.25 + np.sin(2*np.pi*np.cumsum(300 + 900*(tt/d)**2)/SR) * (tt/d)**3 * 0.08, 1.0)
mix = np.stack([L, R], 1); tt = np.arange(N)/SR
mix *= (np.minimum(1, (DUR - tt)/0.25) * np.minimum(1, tt/0.01))[:, None]
mix /= np.abs(mix).max() / 0.85
save("music_bed", mix)

# whoosh
d = 0.4; tt = t_(d); n = rng.standard_normal(len(tt)); sw = np.empty_like(n); a1 = a2 = 0.0
for i, v in enumerate(n):
    k = 0.02 + 0.3*(tt[i]/d)**1.5; a1 += k*(v-a1); a2 += k*(a1-a2); sw[i] = a1 - a2
w = sw * np.sin(np.pi*np.clip(tt/d, 0, 1))**2; w /= np.abs(w).max()
save("whoosh", np.stack([w*0.6, np.roll(w, 300)*0.6], 1))
# pop for captions
d = 0.12; tt = t_(d); f = 900*np.exp(-tt*40) + 300
save("pop", np.sin(2*np.pi*np.cumsum(f)/SR) * env(d, 0.001, 0.03) * 0.6)
# impact for the drop
d = 1.0; tt = t_(d); f = 150*np.exp(-tt*8) + 40
h = np.sin(2*np.pi*np.cumsum(f)/SR)*env(d, 0.002, 0.35)*0.9 + lp(rng.standard_normal(len(tt)), 0.35)*env(d, 0.001, 0.04)*0.5
save("hit", h / np.abs(h).max() * 0.85)
print("audio done")
