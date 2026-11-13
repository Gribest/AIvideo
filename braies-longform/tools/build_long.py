"""Builds the long-form "Lago di Braies: Instagram vs Reality" from the approved storyboard.
Run from braies-longform/:  python3 tools/build_long.py [--plates]
 - reads the shot list S from ../skip-or-trip-braies/tools/storyboard.py (the storyboard is the source of truth)
 - narration timings from assets/vo/vo.json (tools/make_vo.py, tools/make_vo_extra.py)
 - --plates renders every cut to assets/plates/ (crops, framed portraits, splits; strangers' faces blurred)
 - writes timeline.json and index.html"""
import os, re, sys, json, html, hashlib, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
import pillow_heif; pillow_heif.register_heif_opener()

RAW = "../skip-or-trip-braies/raw/drive"
PREP, PLATES = "assets/prep", "assets/plates"
os.makedirs(PREP, exist_ok=True); os.makedirs(PLATES, exist_ok=True)
W, H, FPS = 1920, 1080, 30
MP4 = "3e1893c5-4458-4077-9694-2f5686c837de.mp4"
TONEMAP = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
GRADE = "colorbalance=rm=0.025:bm=-0.025:rh=0.02:bh=-0.02,eq=saturation=1.07:contrast=1.03"
# strangers only; family and friend are never blurred
BLUR = {"IMG_2671.MOV", "IMG_2700.MOV"}  # stranger faces in crowd clips; stills only show distant people (Haar misfires on rock)

# ---- shot list from the storyboard ---------------------------------------
src = open("../skip-or-trip-braies/tools/storyboard.py").read()
block = src[src.index("\nS = [") + 1: src.index("\n]\n", src.index("\nS = [")) + 2]
ns = {"MP4": MP4}; exec(block, ns); S = ns["S"]

# extra cuts inside long frames (frame number -> [(file, t, layout, y)])
EXTRA = {
 4: [("IMG_2731.MOV", 5, "crop", .55)],
 6: [("IMG_2683.MOV", .5, "crop", .62)],
 7: [("IMG_2705.heic", 0, "crop", .62)],
 9: [("IMG_2674.heic", 0, "crop", .55)],
 10: [("IMG_2710.heic", 0, "frame", .5)],
 11: [("IMG_2699.MOV", 3, "crop", .66), ("IMG_2686.heic", 0, "crop", .72)],
 12: [("IMG_2695.heic", 0, "crop", .5)],
 13: [("IMG_2654.MOV", 0, "crop", .6)],
 14: [("IMG_2690.jpg", 0, "crop", .5)],
 15: [("IMG_2711.heic", 0, "crop", .7)],
 17: [("IMG_2737.MOV", 7, "frame", .5)],
 18: [("IMG_2731.MOV", 34, "crop", .55)],
 20: [("IMG_2732.MOV", 20, "crop", .45)],
 24: [("IMG_2700.MOV", 0, "crop", .62)],
 25: [("IMG_2687.heic", 0, "crop", .75)],
 26: [("IMG_2731.MOV", 44, "crop", .55)],
 27: [("IMG_2747.MOV", 4, "crop", .40), ("IMG_2675.heic", 0, "crop", .55)],
 28: [("IMG_2696.MOV", 6, "crop", .5)],
 29: [("IMG_2749.HEIC", 0, "crop", .62)],
}
NAT = {13: ("IMG_2657.MOV", 2, .55), 14: (MP4, 3, .5), 17: ("IMG_2742.MOV", 1.5, .45), 18: ("IMG_2731.MOV", 22, .8),
       19: ("IMG_2734.MOV", 8, .8), 3: ("IMG_2671.MOV", 4, .45), 24: ("IMG_2671.MOV", 8, .35)}

vo = json.load(open("assets/vo/vo.json"))

# ---- timeline: each frame lasts its planned length, or longer if its narration needs it ----
frames, t = [], 0.0
for i, (act, title, st, en, srcs, mode, y, ovs, text, reads, sound, note) in enumerate(S, 1):
    lead = 0.6 if i == 1 else 0.35
    v = vo.get(str(i)); need = 0
    if v:
        need = lead + v["dur"] + (0.5 + v["extra"]["dur"] if "extra" in v else 0) + 0.9
    dur = round(max(en - st, need), 2)
    cuts = [(srcs, mode, y)] + [([(f, ts)], m, yy) for f, ts, m, yy in EXTRA.get(i, [])]
    frames.append(dict(n=i, act=act, title=title, start=round(t, 2), dur=dur, cuts=cuts, ovs=ovs, vo=v, lead=lead))
    t += dur
TOTAL = round(t, 2)

def is_video(f): return f.lower().endswith((".mov", ".mp4"))
def probe(f, entries):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries, "-of", "csv=p=0", f],
                          capture_output=True, text=True).stdout.strip()

# ---- face blur (strangers) ---------------------------------------------------
import cv2
CASC = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")]
def faces(bgr):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY); g = cv2.equalizeHist(g); out = []
    for c in CASC:
        for flip in (False, True):
            gg = cv2.flip(g, 1) if flip else g
            for (x, y, w, h) in c.detectMultiScale(gg, 1.08, 4, minSize=(12, 12)):
                if flip: x = g.shape[1] - x - w
                out.append((x, y, w, h))
    return out
def blur_boxes(bgr, boxes):
    if not boxes: return bgr
    bl = cv2.GaussianBlur(bgr, (0, 0), 14); m = np.zeros(bgr.shape[:2], np.uint8)
    for (x, y, w, h) in boxes:
        cv2.ellipse(m, (int(x + w / 2), int(y + h / 2)), (int(w * .8), int(h)), 0, 0, 360, 255, -1)
    m = cv2.GaussianBlur(m, (0, 0), 3)[..., None] / 255.0
    return (bgr * (1 - m) + bl * m).astype(np.uint8)

# ---- source prep ---------------------------------------------------------------
def prep_image(f):
    out = f"{PREP}/{hashlib.md5(f.encode()).hexdigest()[:10]}.png"
    if not os.path.exists(out):
        im = ImageOps.exif_transpose(Image.open(f"{RAW}/{f}")).convert("RGB")
        s = 2400 / max(im.size)
        if s < 1: im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        im = ImageEnhance.Color(im).enhance(1.06)
        if f in BLUR:
            bgr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR); bgr = blur_boxes(bgr, faces(bgr))
            im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        im.save(out)
    return out

def prep_video(f, ts, dur):
    """SDR, graded, 30 fps clip of exactly `dur` seconds from `ts` (slowed to at most 0.6x, then held)."""
    key = hashlib.md5(f"{f}|{ts}|{dur}".encode()).hexdigest()[:10]; out = f"{PREP}/{key}.mp4"
    if os.path.exists(out): return out
    p = f"{RAW}/{f}"
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
    ts = min(ts, max(0, total - 0.5)); avail = total - ts
    speed = 1.0 if avail >= dur else max(0.6, avail / dur)
    hdr = probe(p, "stream=color_transfer") == "arib-std-b67"
    vf = ["scale='if(gt(iw,ih),-2,1920)':'if(gt(iw,ih),1080,-2)'"] + ([TONEMAP] if hdr else []) + [GRADE]
    if speed < 1: vf.append(f"setpts=PTS/{speed:.3f}")
    vf += [f"fps={FPS}", f"tpad=stop_mode=clone:stop_duration={dur}", f"trim=duration={dur}", "format=yuv420p"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ts), "-i", p, "-vf", ",".join(vf), "-an",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "15", out], check=True)
    if f in BLUR:
        cap = cv2.VideoCapture(out); w = int(cap.get(3)); h = int(cap.get(4)); tmp = out + ".blur.mp4"
        wr = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h)); hist = []
        while True:
            ok, fr = cap.read()
            if not ok: break
            small = cv2.resize(fr, (w * 2 // 3, h * 2 // 3)) if w > 1400 else fr
            sc = fr.shape[1] / small.shape[1]
            b = [(x * sc, y * sc, ww * sc, hh * sc) for x, y, ww, hh in faces(small)]
            hist = (hist + [b])[-8:]  # hold detections for 8 frames to stop flicker
            wr.write(blur_boxes(fr, [bx for hb in hist for bx in hb]))
        wr.release(); cap.release()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", out + ".x.mp4"], check=True)
        os.replace(out + ".x.mp4", out); os.remove(tmp)
    return out

# ---- plates ------------------------------------------------------------------
def mask(w, h, r=34):
    p = f"{PREP}/mask_{w}x{h}.png"
    if not os.path.exists(p):
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); m.save(p)
    return p

def geometry(mode, n):
    if mode == "crop": return [(0, 0, W, H)]
    if mode == "frame": ph = H - 80; pw = round(ph * 9 / 16); return [((W - pw) // 2, 40, pw, ph)]
    if mode == "compare": return [(0, 0, W // 2, H), (W // 2, 0, W // 2, H)]
    gap = 28; pw = (W - 120 - gap * (n - 1)) // n; ph = min(H - 90, round(pw * 16 / 9))
    return [(60 + i * (pw + gap), (H - ph) // 2, pw, ph) for i in range(n)]

def build_plate(name, srcs, mode, y, dur):
    vids = any(is_video(f) for f, _ in srcs); ext = "mp4" if vids else "jpg"; out = f"{PLATES}/{name}.{ext}"
    if os.path.exists(out): return out
    geo = geometry(mode, len(srcs))
    if not vids:  # all stills: compose in PIL
        ims = [Image.open(prep_image(f)) for f, _ in srcs]
        def cover(im, w, h, yy):
            s = max(w / im.width, h / im.height); im2 = im.resize((round(im.width * s) + 1, round(im.height * s) + 1), Image.LANCZOS)
            l = (im2.width - w) // 2; tp = round((im2.height - h) * yy); return im2.crop((l, tp, l + w, tp + h))
        bg = cover(ims[0], W, H, .5).filter(ImageFilter.GaussianBlur(40)); bg = ImageEnhance.Brightness(bg).enhance(.5)
        for im, (x, yy0, w, h) in zip(ims, geo):
            p = cover(im, w, h, y if len(geo) == 1 or mode == "compare" else .5)
            bg.paste(p, (x, yy0), None if mode in ("crop", "compare") else Image.open(mask(w, h)))
        bg.save(out, quality=92); return out
    # any video: compose in ffmpeg
    inputs, fc, k = [], [], 0
    for f, ts in srcs:
        if is_video(f): inputs += ["-i", prep_video(f, ts, dur)]
        else: inputs += ["-loop", "1", "-framerate", str(FPS), "-t", str(dur), "-i", prep_image(f)]
    def cover_f(i, w, h, yy):
        return (f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h}:(iw-{w})/2:(ih-{h})*{yy},setsar=1")
    fc.append(cover_f(0, W, H, .5) + ",gblur=sigma=40,eq=brightness=-0.22[bg]"); last = "bg"
    for idx, (x, yy0, w, h) in enumerate(geo):
        yy = y if len(geo) == 1 or mode == "compare" else .5
        fc.append(cover_f(idx, w, h, yy) + f",format=rgba[p{idx}]")
        if mode not in ("crop", "compare"):
            inputs += ["-loop", "1", "-i", mask(w, h)]; mi = len(srcs) + idx
            fc.append(f"[{mi}:v]format=gray,scale={w}:{h}[m{idx}];[p{idx}][m{idx}]alphamerge[q{idx}]"); pin = f"q{idx}"
        else: pin = f"p{idx}"
        fc.append(f"[{last}][{pin}]overlay={x}:{yy0}:shortest=0[o{idx}]"); last = f"o{idx}"
    fc.append(f"[{last}]trim=duration={dur},fps={FPS},format=yuv420p[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[out]", "-t", str(dur), "-an",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "30", "-movflags", "+faststart", out], check=True)
    return out

cutlist = []
for fr in frames:
    n = len(fr["cuts"]); first = fr["dur"] if n == 1 else round(fr["dur"] * 0.5, 2)
    rest = 0 if n == 1 else round((fr["dur"] - first) / (n - 1), 2); t0 = fr["start"]
    for j, (srcs, mode, y) in enumerate(fr["cuts"]):
        d = first if j == 0 else (round(fr["start"] + fr["dur"] - t0, 2) if j == n - 1 else rest)
        cutlist.append(dict(id=f"s{fr['n']:02d}{chr(97 + j)}", frame=fr["n"], start=round(t0, 2), dur=d, srcs=srcs, mode=mode, y=y)); t0 += d

if "--plates" in sys.argv:
    for c in cutlist:
        c["file"] = build_plate(f"{c['id']}_{hashlib.md5(json.dumps([c['srcs'], c['mode'], c['y'], c['dur']]).encode()).hexdigest()[:6]}", c["srcs"], c["mode"], c["y"], c["dur"])
        print("plate", c["id"], c["file"], flush=True)
    # natural sound beds
    for n, (f, ts, vol) in NAT.items():
        fr = frames[n - 1]; out = f"assets/nat/f{n:02d}.wav"; os.makedirs("assets/nat", exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ts), "-i", f"{RAW}/{f}", "-t", str(fr["dur"]), "-vn", "-ac", "2", "-ar", "48000",
                        "-af", f"afade=t=in:d=0.4,afade=t=out:st={max(0, fr['dur'] - 0.6)}:d=0.6", out], check=True)
    json.dump(dict(total=TOTAL, frames=frames, cuts=cutlist), open("timeline.json", "w"), indent=1)
    sys.exit()

tl = json.load(open("timeline.json")); cutlist = tl["cuts"]
print("total", TOTAL, "s", len(cutlist), "cuts")

# ==== composition ===========================================================
frames = tl["frames"]; TOTAL = tl["total"]
def esc(s): return html.escape(s)
def rich(t):  # *keyword* -> yellow span
    return "".join(f'<span class="key">{esc(p)}</span>' if i % 2 else esc(p) for i, p in enumerate(t.split("*")))

body, js, audio = [], [], []
# -- plates
for c in cutlist:
    f = c["file"]; a, d = c["start"], c["dur"]
    if f.endswith(".mp4"):
        body.append(f'<video id="{c["id"]}" class="clip shot" src="{f}" data-start="{a}" data-duration="{d}" data-track-index="0" muted playsinline></video>')
    else:
        body.append(f'<img id="{c["id"]}" class="clip shot" src="{f}" data-start="{a}" data-duration="{d}" data-track-index="0" alt="">')
    fr = frames[c["frame"] - 1]
    if c["mode"] == "crop" and not f.endswith(".mp4"):
        js.append(f'tl.fromTo("#{c["id"]}",{{scale:1}},{{scale:1.07,duration:{d},ease:"none"}},{a});')
    elif c["mode"] == "crop":
        js.append(f'tl.fromTo("#{c["id"]}",{{scale:1.06}},{{scale:1.0,duration:{d},ease:"power1.out"}},{a});')
    else:
        js.append(f'tl.fromTo("#{c["id"]}",{{scale:1.0}},{{scale:1.025,duration:{d},ease:"none"}},{a});')

# -- overlays per frame
for fr in frames:
    n, a, d = fr["n"], fr["start"], fr["dur"]
    for k, ov in enumerate(fr["ovs"]):
        oid = f"o{n:02d}{k}"; kind = ov[0]
        if kind == "chapter":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="chapter">{esc(ov[1])}</div></div>')
            js.append(f'tl.fromTo("#{oid} .chapter",{{x:-40,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power3.out"}},{a+.3});')
            js.append(f'tl.to("#{oid} .chapter",{{opacity:0,duration:.3}},{a+d-.35});')
        elif kind == "lower":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="lower"><div class="l1">{esc(ov[1])}</div><div class="l2">{esc(ov[2])}</div></div></div>')
            js.append(f'tl.fromTo("#{oid} .lower",{{x:-60,opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power3.out"}},{a+.8});')
            js.append(f'tl.to("#{oid} .lower",{{x:-30,opacity:0,duration:.35,ease:"power2.in"}},{min(a+d, a+9)-.4});')
        elif kind == "card":
            rows = "".join(f'<div class="row">{esc(r)}</div>' for r in ov[2])
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="card"><div class="head">{esc(ov[1])}</div>{rows}</div></div>')
            js.append(f'tl.fromTo("#{oid} .card",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power3.out"}},{a+.5});')
            for r in range(len(ov[2])):
                js.append(f'tl.fromTo("#{oid} .row:nth-of-type({r+2})",{{x:-20,opacity:0}},{{x:0,opacity:1,duration:.3,ease:"power2.out"}},{a+1.0+r*.6});')
                audio.append(("tick", a + 1.0 + r * .6, .35))
            js.append(f'tl.to("#{oid} .card",{{opacity:0,duration:.35}},{a+d-.4});')
        elif kind == "big":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="big">{esc(ov[1])}</div></div>')
            js.append(f'tl.fromTo("#{oid} .big",{{scale:2.6,opacity:0}},{{scale:1,opacity:1,duration:.2,ease:"power4.in"}},{a+.15});')
            js.append(f'tl.to("#{oid} .big",{{opacity:0,scale:1.1,duration:.25}},{a+min(d,3.6)-.3});')
            audio.append(("hit", a + .15, .7))
        elif kind == "title":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="title"><div class="t1">{esc(ov[1])}</div><div class="t2">{esc(ov[2])}</div></div></div>')
            js.append(f'tl.fromTo("#{oid} .t1",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.6,ease:"power3.out"}},{a+.4});')
            js.append(f'tl.fromTo("#{oid} .t2",{{y:30,opacity:0}},{{y:0,opacity:1,duration:.6,ease:"power3.out"}},{a+.9});')
            js.append(f'tl.to("#{oid} .title",{{opacity:0,duration:.4}},{a+d-.45});')
            audio.append(("whoosh", a + .25, .5))
        elif kind == "labels":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="divider"></div><div class="lab insta">INSTAGRAM</div><div class="lab real">REALITY</div></div>')
            js.append(f'tl.fromTo("#{oid} .divider",{{scaleY:0}},{{scaleY:1,duration:.5,ease:"power3.out"}},{a});')
            js.append(f'tl.fromTo("#{oid} .lab",{{y:-30,opacity:0}},{{y:0,opacity:1,duration:.4,stagger:.3,ease:"back.out(2)"}},{a+.5});')
            audio.append(("whoosh", a, .5))
        elif kind == "hearts":
            hs = "".join(f'<div class="heart h{j}">♥ 48.2k</div>' for j in range(3))
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2">{hs}</div>')
            for j in range(3):
                js.append(f'tl.fromTo("#{oid} .h{j}",{{scale:.4,opacity:0}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2.5)"}},{a+.5+j*.7});')
                audio.append(("tick", a + .5 + j * .7, .5))
        elif kind == "stamp":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="stamp"><div class="vl">VERDICT</div><div class="vc">{esc(ov[1])}</div></div></div>')
            js.append(f'tl.fromTo("#{oid} .vc",{{scale:3.2,opacity:0,rotation:-16}},{{scale:1,opacity:1,rotation:-6,duration:.25,ease:"power4.in"}},{a+.3});')
            js.append(f'tl.fromTo("#{oid} .vl",{{y:30,opacity:0}},{{y:0,opacity:1,duration:.3,ease:"back.out(2)"}},{a+.6});')
            audio.append(("stamp", a + .3, .8))
        elif kind == "endscreen":
            body.append(f'<div id="{oid}" class="clip ov" data-start="{a}" data-duration="{d}" data-track-index="2"><div class="es es1">Watch next</div><div class="es es2">Watch next</div><div class="sub">SUBSCRIBE</div></div>')
            js.append(f'tl.fromTo("#{oid} .es",{{y:30,opacity:0}},{{y:0,opacity:1,duration:.5,stagger:.2,ease:"power3.out"}},{a+.5});')
            js.append(f'tl.fromTo("#{oid} .sub",{{scale:.5,opacity:0}},{{scale:1,opacity:1,duration:.4,ease:"back.out(2)"}},{a+1.2});')
    # narration + captions
    v = fr["vo"]
    if v:
        lines = [(v["text"], v["dur"], f"assets/vo/f{n:02d}.wav", a + fr["lead"])]
        if "extra" in v:
            lines.append((v["extra"]["text"], v["extra"]["dur"], f"assets/vo/f{n:02d}b.wav", a + fr["lead"] + v["dur"] + .5))
        for li, (text, dur, wav, st) in enumerate(lines):
            audio.append(("vo", st, dur, wav, f"vo{n:02d}{li}"))
            words, key = [], False   # (word, is_key)
            for tok in text.split():
                k0 = tok.startswith("*") or key; clean = tok.replace("*", "")
                if tok.startswith("*"): key = True
                words.append((clean, k0))
                if tok.rstrip(".,?!:;").endswith("*") or (tok.endswith("*") ): key = False
            groups, cur = [], []
            for w in words:
                cur.append(w)
                if len(cur) >= 5 or w[0][-1] in ".?!:,": groups.append(cur); cur = []
            if cur: groups.append(cur)
            # merge 1-word tail groups into the previous one
            g2 = []
            for g in groups:
                if g2 and len(g) == 1 and len(g2[-1]) < 6: g2[-1] += g
                else: g2.append(g)
            chars = [sum(len(w) + 1 for w, _ in g) for g in g2]; speak = dur - .16; t0 = st + .08
            for gi, g in enumerate(g2):
                gd = speak * chars[gi] / sum(chars); cid = f"c{n:02d}{li}{gi}"
                inner = " ".join(f'<span class="key">{esc(w)}</span>' if k else esc(w) for w, k in g)
                ga, gb = round(t0, 2), round(t0 + gd + (0.15 if gi == len(g2) - 1 else 0), 2)
                body.append(f'<div id="{cid}" class="clip cap" data-start="{ga}" data-duration="{round(gb-ga,2)}" data-track-index="3"><div class="capin">{inner}</div></div>')
                js.append(f'tl.fromTo("#{cid} .capin",{{y:14,opacity:0}},{{y:0,opacity:1,duration:.18,ease:"power2.out"}},{ga});')
                js.append(f'tl.to("#{cid} .capin",{{opacity:0,duration:.1,ease:"power2.in"}},{round(gb-.1,2)});')
                t0 += gd

# -- whooshes on act changes
prev = None
for fr in frames:
    if prev and fr["act"] != prev and fr["n"] not in (22,): audio.append(("whoosh", fr["start"] - .2, .4))
    prev = fr["act"]

# -- audio tags
SFXLEN = {"whoosh": .45, "tick": .06, "hit": 1.0, "stamp": 1.4}
for i, a in enumerate(sorted(audio, key=lambda x: x[1])):
    if a[0] == "vo":
        _, st, dur, wav, aid = a
        body.append(f'<audio id="{aid}" class="clip" src="{wav}" data-start="{round(st,2)}" data-duration="{dur}" data-track-index="10" data-volume="1.0"></audio>')
    else:
        f, st, vol = a
        body.append(f'<audio id="fx{i:03d}" class="clip" src="assets/audio/{f}.wav" data-start="{round(max(0,st),2)}" data-duration="{SFXLEN[f]}" data-track-index="12" data-volume="{vol}"></audio>')
for f in sorted(os.listdir("assets/nat")):
    n = int(f[1:3]); fr = frames[n - 1]; vol = NAT[n][2]
    body.append(f'<audio id="nat{n:02d}" class="clip" src="assets/nat/{f}" data-start="{fr["start"]}" data-duration="{fr["dur"]}" data-track-index="11" data-volume="{vol}"></audio>')
body.append(f'<audio id="music" class="clip" src="assets/audio/music_long.wav" data-start="0" data-duration="{TOTAL}" data-track-index="13" data-volume="1.0"></audio>')

doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<title>Lago di Braies: Instagram vs Reality</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
:root {{ --yellow:#FFD60A; --ink:#ffffff; --trip:#16A34A; --insta:#E1306C; --scrim:rgba(8,12,12,.78); --font:"Inter", sans-serif; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1920px; height:1080px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1920px; height:1080px; overflow:hidden; font-family:var(--font); background:#000; }}
.shot {{ position:absolute; inset:0; width:1920px; height:1080px; object-fit:cover; z-index:1; }}
.ov {{ position:absolute; inset:0; z-index:20; }}
.cap {{ position:absolute; left:0; right:0; bottom:96px; height:120px; z-index:40; display:flex; align-items:center; justify-content:center; text-align:center; overflow:visible; }}
.capin {{ font-weight:900; font-size:54px; line-height:1.1; color:var(--ink); max-width:1500px;
  -webkit-text-stroke:9px rgba(0,0,0,.85); paint-order:stroke fill; text-shadow:0 4px 16px rgba(0,0,0,.5); }}
.key {{ color:var(--yellow); }}
.chapter {{ position:absolute; left:110px; top:84px; font-weight:900; font-size:36px; letter-spacing:.06em; color:var(--yellow);
  -webkit-text-stroke:7px rgba(0,0,0,.85); paint-order:stroke fill; text-transform:uppercase; }}
.lower {{ position:absolute; left:110px; bottom:250px; padding:22px 36px 22px 40px; background:var(--scrim); border-left:10px solid var(--yellow); border-radius:16px; }}
.l1 {{ font-weight:900; font-size:58px; color:var(--ink); }}
.l2 {{ font-weight:700; font-size:34px; color:#e6ecec; margin-top:6px; }}
.card {{ position:absolute; left:110px; top:110px; width:760px; padding:40px 48px; background:var(--scrim); border-radius:28px; }}
.head {{ font-weight:900; font-size:56px; color:var(--yellow); margin-bottom:18px; }}
.row {{ font-weight:700; font-size:44px; color:var(--ink); line-height:1.6; }}
.big {{ position:absolute; left:0; right:0; top:330px; text-align:center; font-weight:900; font-size:230px; color:var(--yellow);
  -webkit-text-stroke:20px #000; paint-order:stroke fill; text-shadow:0 10px 30px rgba(0,0,0,.5); }}
.title {{ position:absolute; left:0; right:0; top:330px; text-align:center; }}
.t1 {{ font-weight:900; font-size:150px; color:var(--yellow); -webkit-text-stroke:16px #000; paint-order:stroke fill; }}
.t2 {{ font-weight:900; font-size:88px; color:var(--ink); -webkit-text-stroke:12px #000; paint-order:stroke fill; margin-top:10px; }}
.divider {{ position:absolute; left:955px; top:0; width:10px; height:1080px; background:#fff; transform-origin:50% 0; }}
.lab {{ position:absolute; top:70px; width:600px; text-align:center; font-weight:900; font-size:64px; color:#fff; padding:12px 0; border-radius:20px; }}
.insta {{ left:180px; background:var(--insta); }} .real {{ left:1140px; background:#222; }}
.heart {{ position:absolute; top:850px; width:300px; text-align:center; font-weight:900; font-size:40px; color:var(--insta); background:#fff; border-radius:40px; padding:10px 0; }}
.h0 {{ left:185px; }} .h1 {{ left:810px; }} .h2 {{ left:1435px; }}
.stamp {{ position:absolute; left:1240px; top:330px; width:560px; text-align:center; }}
.vl {{ font-weight:900; font-size:64px; color:#fff; -webkit-text-stroke:8px #000; paint-order:stroke fill; margin-bottom:20px; }}
.vc {{ display:inline-block; background:var(--trip); color:#fff; font-weight:900; font-size:170px; padding:10px 60px; border-radius:36px; box-shadow:0 18px 50px rgba(0,0,0,.45); }}
.es {{ position:absolute; top:220px; width:700px; height:394px; border:6px solid #fff; border-radius:24px; background:rgba(0,0,0,.35);
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:44px; color:#fff; }}
.es1 {{ left:180px; }} .es2 {{ left:1040px; }}
.sub {{ position:absolute; left:810px; top:700px; width:300px; height:96px; border-radius:48px; background:#E02424; color:#fff; font-weight:900; font-size:40px; display:flex; align-items:center; justify-content:center; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{chr(10).join(body)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
open("index.html", "w").write(doc)
print("index.html:", len(cutlist), "cuts,", sum(1 for b in body if 'class="clip cap"' in b), "caption groups, total", TOTAL)
