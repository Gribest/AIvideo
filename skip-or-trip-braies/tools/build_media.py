"""Cut, crop, grade and privacy-blur the raw clips/photos into assets/.
Run from the project root: python3 tools/build_media.py
Raw files live in raw/ (not committed)."""
import subprocess, os
from PIL import Image, ImageDraw, ImageFilter

RAW, SHOTS, STILLS = "raw", "assets/shots", "assets/stills"
os.makedirs(SHOTS, exist_ok=True); os.makedirs(STILLS, exist_ok=True)

# Light warm grade, natural skin. "strong" for the flat, overcast Nov-6 clips.
# iPhone clips are HLG HDR: tone-map to SDR Rec.709 so the master plays right on Reels/Shorts.
TONEMAP = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
GRADE = {
    "light":  "colorbalance=rm=0.03:bm=-0.03:rh=0.02:bh=-0.02,eq=saturation=1.06:contrast=1.02",
    "strong": "colorbalance=rs=0.02:bs=-0.03:rm=0.045:gm=0.01:bm=-0.045:rh=0.03:bh=-0.03,eq=saturation=1.05:contrast=1.03",
}

def ellipse_mask(size, blobs, feather=6):
    m = Image.new("L", size, 0); d = ImageDraw.Draw(m)
    for cx, cy, r in blobs:
        d.ellipse([cx - r, cy - r * 1.25, cx + r, cy + r * 1.25], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))

# ---- video shots -------------------------------------------------------
# name, src, start, dur, crop ("full" 9:16 portrait | x-centre fraction for landscape), grade, speed, blur blobs (source px, after rotation)
# Horizontal camera drift of the dock clip, measured by phase correlation (source px; blobs were placed at t=0.7s).
PAN = {"s02_dock": "-174+248*t"}
C4_BLOBS = [(49,3112,55),(472,3080,55),(373,3182,55),(130,3269,55),(799,3139,55),(956,3058,55),
            (1048,3101,60),(1922,3042,55),(2003,3047,55),(2122,3042,55),(1900,3060,50),(2080,3060,50),
            (0,3112,60),(-70,3112,60),(-140,3112,60)]  # left rower drifts left as he rows
VIDEOS = [
    ("s02_dock",   "IMG_2700.mov", 0.0, 1.43, "full", "strong", 1.0, C4_BLOBS),
    ("s03_tilt",   "IMG_2698.mov", 1.0, 2.0,  "full", "strong", 1.0, []),
    ("s04_lake",   "IMG_2694.mov", 0.0, 2.6,  0.55,   "strong", 1.0, []),
    ("s06_bench",  "IMG_2727.MOV", 0.0, 2.5,  "full", "light",  1.0, []),
    ("s08_water",  "IMG_2699.mov", 3.5, 2.5,  "full", "strong", 1.0, []),
    ("s10_smile",  "IMG_2726.MOV", 0.0, 0.83, "full", "light",  1.0, []),
    ("s14_forest", "IMG_2694.mov", 3.8, 3.0,  0.45,   "strong", 1.0, []),
    ("s15_back",   "IMG_2728.MOV", 0.0, 1.23, "full", "light",  0.615, []),
    ("s16_cliffs", "IMG_2698.mov", 6.0, 1.5,  "full", "strong", 1.0, []),
]

def build_video(name, src, ss, dur, crop, grade, speed, blobs):
    out = f"{SHOTS}/{name}.mp4"
    chain = []
    if crop != "full":
        chain.append(f"crop=ih*9/16:ih:(iw-ih*9/16)*{crop}:0")
    inputs = ["-ss", str(ss), "-t", str(dur), "-i", f"{RAW}/{src}"]
    if blobs:
        # Mask drawn on a padded canvas, then cropped per frame so the blur follows the camera pan.
        PAD = 400
        mask = f"/tmp/{name}_mask.png"
        ellipse_mask((2160 + 2 * PAD, 3840), [(x + PAD, y, r) for x, y, r in blobs], 8).save(mask)
        dx = PAN.get(name, "0")
        inputs += ["-loop", "1", "-i", mask]
        fc = (f"[0:v]{TONEMAP},split[a][b];[b]gblur=sigma=28[bl];[1:v]format=gray,crop=2160:3840:x='{PAD}-({dx})':y=0[m];"
              "[bl][m]alphamerge[blm];[a][blm]overlay=shortest=1[v0];[v0]")
    else:
        fc = f"[0:v]{TONEMAP},"
    chain += ["scale=1080:1920:flags=lanczos", GRADE[grade]]
    if speed != 1.0:
        chain.append(f"setpts=PTS/{speed}")
    chain += ["fps=30", "format=yuv420p"]
    fc += ",".join(chain) + "[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-an",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-g", "15", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("video", out)

# ---- stills ------------------------------------------------------------
# Strangers only (P5 dock, P3 background rowers). The woman in black is with the family: not blurred.
STILL_LIST = {
    "p8_family_boat": ("P8.jpg", "light",  []),
    "p1_boats":       ("P1.jpg", "light",  []),
    "p2_rowing":      ("P2.jpg", "light",  []),
    "p6_larches":     ("P6.jpg", "light",  []),
    "p3_us":          ("P3.jpg", "light",  [(130,990,22),(190,995,22),(160,985,30),(222,990,26),(240,1000,24)]),
    "p5_dock":        ("P5.jpg", "strong", [(55,2052,24),(105,2050,24),(348,2040,24),(507,2068,24),(285,2120,26),
                                            (180,2152,28),(627,2030,24),(663,2075,24),(690,2068,24),(1132,2015,22),
                                            (1152,2015,22),(1197,2018,22),(1246,2010,22),(1365,2460,42)]),
    "p4_shore":       ("P4.jpg", "strong", []),
}

def build_still(name, src, grade, blobs):
    im = Image.open(f"{RAW}/{src}").convert("RGB")
    if blobs:
        r = max(b[2] for b in blobs)
        blurred = im.filter(ImageFilter.GaussianBlur(max(10, r // 2)))
        im = Image.composite(blurred, im, ellipse_mask(im.size, blobs, 4))
    # cover 1080x1920 at 1.25x so slow zooms stay sharp
    W, H = 1350, 2400
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (im.width - W) // 2; y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    tmp = f"/tmp/{name}.png"; im.save(tmp)
    out = f"{STILLS}/{name}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-vf", GRADE[grade], "-q:v", "2", out], check=True)
    print("still", out)

if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    for v in VIDEOS:
        if not only or v[0] in only: build_video(*v)
    if only and not any(o.startswith("p") for o in only): raise SystemExit
    for k, (src, g, b) in STILL_LIST.items(): build_still(k, src, g, b)
