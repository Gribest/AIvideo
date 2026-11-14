"""Cut, tone-map (iPhone HLG -> SDR Rec.709), grade and re-time the raw clip into assets/shots/.
Run from the project root: python3 tools/build_media.py   (raw/IMG_8593.mov is not committed)"""
import subprocess, os
RAW, SHOTS = "raw/IMG_8593.mov", "assets/shots"
os.makedirs(SHOTS, exist_ok=True); os.makedirs("assets/audio", exist_ok=True)

TONEMAP = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
# Overcast street: warm it, lift the pistachio greens, a bit of punch.
GRADE = ("colorbalance=rs=0.01:bs=-0.02:rm=0.02:bm=-0.02:rh=0.02:bh=-0.01,"
         "eq=saturation=1.10:contrast=1.06:gamma=0.98,unsharp=5:5:0.35")

# name, source in, source out, speed (output length = (out-in)/speed)
CUTS = [
    ("s1_hook",    0.50,  2.00, 1.0),
    ("s2_cut",     2.00,  7.00, 2.0),
    ("s3_lift",    7.00,  9.00, 1.0),
    ("s4_layers",  9.50, 11.60, 0.7),
    ("s5_hand",   13.50, 16.50, 1.5),
    ("s6_end",    16.50, 18.75, 0.98),
]

for name, a, b, sp in CUTS:
    vf = f"{TONEMAP},scale=1080:1920:flags=lanczos,{GRADE},setpts=(PTS-STARTPTS)/{sp},fps=30,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", RAW, "-map", "0:v:0",
                    "-vf", vf, "-an", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-g", "15", "-movflags", "+faststart",
                    f"{SHOTS}/{name}.mp4"], check=True)
    print("shot", name, round((b - a) / sp, 3), "s")

# Original street/shop sound, re-timed to match the cuts (pitch preserved), for a quiet ambience bed.
parts, labels = [], []
for i, (name, a, b, sp) in enumerate(CUTS):
    parts.append(f"[0:a:0]atrim={a}:{b},asetpts=PTS-STARTPTS,atempo={sp}[a{i}]"); labels.append(f"[a{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(CUTS)}:v=0:a=1,loudnorm=I=-24:TP=-3[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", RAW, "-filter_complex", fc, "-map", "[out]", "-ar", "44100", "-ac", "2",
                "assets/audio/ambience.wav"], check=True)
print("ambience done")
