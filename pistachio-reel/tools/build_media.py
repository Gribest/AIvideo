"""Tone-map the full iPhone HLG clip to SDR Rec.709 with a light grade, and pull out the original audio.
Run from the project root: python3 tools/build_media.py   (raw/IMG_8593.mov is not committed)"""
import subprocess, os
RAW = "raw/IMG_8593.mov"
os.makedirs("assets/shots", exist_ok=True); os.makedirs("assets/audio", exist_ok=True)
TONEMAP = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
GRADE = ("colorbalance=rs=0.01:bs=-0.02:rm=0.02:bm=-0.02:rh=0.02:bh=-0.01,"
         "eq=saturation=1.10:contrast=1.06:gamma=0.98,unsharp=5:5:0.35")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", RAW, "-map", "0:v:0",
                "-vf", f"{TONEMAP},scale=1080:1920:flags=lanczos,{GRADE},fps=30,format=yuv420p", "-an",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-g", "15", "-movflags", "+faststart",
                "assets/shots/full.mp4"], check=True)
# Original sound, untouched except for loudness (-14 LUFS, Reels level).
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", RAW, "-map", "0:a:0", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-ar", "48000", "-ac", "2", "assets/audio/original.wav"], check=True)
print("done")
