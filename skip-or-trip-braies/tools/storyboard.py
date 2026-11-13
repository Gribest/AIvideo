"""Long-form storyboard: "Lago di Braies: Instagram vs Reality" (16:9, ~6 min).
One shot list drives the stills (boards/stills), STORYBOARD.md and boards/storyboard.html.
Run from the project root: python3 tools/storyboard.py   (raw footage in raw/drive/, not committed)"""
import os, subprocess, html, io
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance
import pillow_heif; pillow_heif.register_heif_opener()

RAW, OUT = "raw/drive", "boards/stills"
os.makedirs(OUT, exist_ok=True)
W, H = 1280, 720
YEL, TRIP = (255, 214, 10), (22, 163, 74)
F = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(F + {"black": "Inter-Black.otf", "bold": "Inter-Bold.otf", "med": "Inter-Medium.otf"}[w], s)
TONEMAP = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
MP4 = "3e1893c5-4458-4077-9694-2f5686c837de.mp4"

def grab(src, t=0.0):
    p = f"{RAW}/{src}"
    if src.lower().endswith((".mov", ".mp4")):
        hdr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                              "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() == "arib-std-b67"
        vf = (TONEMAP + "," if hdr else "") + "format=rgb24"
        png = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", p, "-frames:v", "1", "-vf", vf, "-f", "image2pipe",
                              "-vcodec", "png", "-"], capture_output=True, check=True).stdout
        im = Image.open(io.BytesIO(png))
    else:
        im = ImageOps.exif_transpose(Image.open(p))
    im = im.convert("RGB")
    return ImageEnhance.Color(im).enhance(1.06)

def cover(im, w, h, y=0.5, x=0.5):
    s = max(w / im.width, h / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l = round((im.width - w) * x); t = round((im.height - h) * y)
    return im.crop((l, t, l + w, t + h))

def rounded(im, r=22):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, *im.size], r, fill=255); return m

def base_frame(srcs, mode, y):
    ims = [grab(s, t) for s, t in srcs]
    if mode == "crop":
        return cover(ims[0], W, H, y)
    bg = cover(ims[0], W, H, 0.5).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    if mode == "frame":
        ph = H - 60; pw = round(ph * 9 / 16); p = cover(ims[0], pw, ph, y)
        bg.paste(p, ((W - pw) // 2, 30), rounded(p)); return bg
    if mode == "split":
        n = len(ims); gap = 18; pw = (W - 80 - gap * (n - 1)) // n; ph = min(H - 60, round(pw * 16 / 9))
        for i, im in enumerate(ims):
            p = cover(im, pw, ph, 0.5); bg.paste(p, (40 + i * (pw + gap), (H - ph) // 2), rounded(p))
        return bg
    if mode == "compare":  # left: Instagram photo, right: reality frame, hard split
        a = cover(ims[0], W // 2, H, 0.55); b = cover(ims[1], W // 2, H, 0.55)
        bg.paste(a, (0, 0)); bg.paste(b, (W // 2, 0)); return bg

def text_box(d, xy, txt, f, fill=(255, 255, 255), stroke=7, anchor="mm"):
    d.text(xy, txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0), anchor=anchor)

def caption(d, txt):  # narration caption, bottom-centre, *keyword* in yellow
    f = font("black", 34); parts = []
    for i, seg in enumerate(txt.split("*")): parts.append((seg, YEL if i % 2 else (255, 255, 255)))
    total = sum(d.textlength(s, font=f) for s, _ in parts); x = (W - total) / 2; y = H - 78
    for s, c in parts:
        d.text((x, y), s, font=f, fill=c, stroke_width=5, stroke_fill=(0, 0, 0), anchor="ls"); x += d.textlength(s, font=f)

def overlay(im, ov):
    d = ImageDraw.Draw(im, "RGBA"); kind = ov[0]
    if kind == "title":
        _, a, b = ov
        text_box(d, (W / 2, H * 0.40), a, font("black", 92), YEL, 10)
        text_box(d, (W / 2, H * 0.55), b, font("black", 64), (255, 255, 255), 8)
    elif kind == "big":
        text_box(d, (W / 2, H * 0.42), ov[1], font("black", 150), YEL if len(ov) < 3 else ov[2], 14)
    elif kind == "lower":  # lower third
        _, a, b = ov; d.rounded_rectangle([48, H - 300, 48 + max(d.textlength(a, font=font("black", 40)), d.textlength(b, font=font("med", 26))) + 48, H - 192], 14, fill=(0, 0, 0, 170))
        d.rectangle([48, H - 300, 56, H - 192], fill=YEL)
        d.text((76, H - 282), a, font=font("black", 40), fill=(255, 255, 255)); d.text((76, H - 232), b, font=font("med", 26), fill=(230, 230, 230))
    elif kind == "card":  # info card, left side
        _, head, rows = ov; x0, y0, w = 56, 70, 520; h = 96 + 62 * len(rows)
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 22, fill=(12, 12, 12, 205))
        d.text((x0 + 32, y0 + 26), head, font=font("black", 40), fill=YEL)
        for i, r in enumerate(rows): d.text((x0 + 32, y0 + 92 + 62 * i), r, font=font("bold", 30), fill=(255, 255, 255))
    elif kind == "labels":  # compare labels
        for x, t, c in ((W * 0.25, "INSTAGRAM", (225, 48, 108)), (W * 0.75, "REALITY", (40, 40, 40))):
            tw = d.textlength(t, font=font("black", 44)); d.rounded_rectangle([x - tw / 2 - 22, 40, x + tw / 2 + 22, 104], 14, fill=c + (235,))
            d.text((x, 72), t, font=font("black", 44), fill=(255, 255, 255), anchor="mm")
        d.rectangle([W // 2 - 3, 0, W // 2 + 3, H], fill=(255, 255, 255))
    elif kind == "stamp":
        lab = font("black", 40); text_box(d, (W * 0.80, H * 0.30), "VERDICT", lab, (255, 255, 255), 6)
        card = Image.new("RGBA", (420, 170), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, 419, 169], 26, fill=TRIP + (255,)); cd.text((210, 88), ov[1], font=font("black", 120), fill=(255, 255, 255), anchor="mm")
        card = card.rotate(6, expand=True, resample=Image.BICUBIC); im.paste(card, (int(W * 0.80) - card.width // 2, int(H * 0.36)), card)
    elif kind == "endscreen":
        for x in (150, 690):
            d.rounded_rectangle([x, 170, x + 440, 418], 18, fill=(0, 0, 0, 120), outline=(255, 255, 255), width=4)
            d.text((x + 220, 294), "next video", font=font("bold", 30), fill=(255, 255, 255), anchor="mm")
        d.ellipse([W / 2 - 70, 450, W / 2 + 70, 590], fill=(220, 30, 30)); d.text((W / 2, 520), "SUBSCRIBE", font=font("black", 22), fill=(255, 255, 255), anchor="mm")
    elif kind == "chapter":
        d.text((48, 48), ov[1].upper(), font=font("black", 30), fill=YEL, stroke_width=5, stroke_fill=(0, 0, 0))
    elif kind == "hearts":
        for x in (W * 0.18, W * 0.5, W * 0.82):
            d.rounded_rectangle([x - 95, H - 170, x + 95, H - 116], 27, fill=(255, 255, 255, 235))
            d.text((x, H - 143), "♥ 48.2k", font=font("black", 28), fill=(225, 48, 108), anchor="mm")

# act, title, start, end, sources [(file, t)], layout, y, overlays, voiceover, reads, sound, note
S = [
 ("1 · Hook", "The postcard", 0, 7, [("IMG_2747.MOV", 3)], "crop", .40, [("chapter", "The Instagram version")],
  "This is the shot everyone comes to *Lago di Braies* for.", "rows of wooden boats under the snowy peak (0-3s); chapter tag (1-7s)",
  "music enters soft; water lapping", "Best opening shot in the set: 18 s handheld drift, cropped full-screen."),
 ("1 · Hook", "Instagram dream", 7, 14, [("e301100b-d690-4a43-af25-b27216893da6.jpg", 0), ("3c93faea-94d7-41fa-8f7d-9c40801c79b2.jpg", 0), ("ecb0ccc4-42af-40f2-8bab-fd769a2f6f7a.jpg", 0)], "split", .5, [("hearts",)],
  "Turquoise water. *Wooden boats.* Not another soul around.", "three perfect posed photos pop in one by one with like counters",
  "pop on each photo; music lifts", "Your bright, edited-looking photos sell the 'Instagram' promise."),
 ("1 · Hook", "Reality check", 14, 18, [("IMG_2749.HEIC", 0)], "crop", .66, [("big", "REALITY")],
  "And this is what it actually looks like when you *get there.*", "music cuts (14.0s); REALITY slams in (14.3-17.5s)",
  "record-scratch; music drops out; dock chatter (natural sound)", "Dock crowd clip; strangers' faces blurred as in the Short."),
 ("1 · Hook", "The promise", 18, 27, [("IMG_2737.MOV", 4)], "frame", .5, [],
  "We spent a whole day here with our *little one*: the boats, the shore, and the honest truth.", "Dad rowing, laughing, cliffs behind",
  "natural oar sound; music back in, lighter", ""),
 ("1 · Hook", "Title", 27, 35, [("IMG_2682.HEIC", 0)], "crop", .40, [("title", "LAGO DI BRAIES", "Instagram vs Reality")],
  "Here's our honest *family guide*.", "title lands (27.5s), subtitle (28.2s)", "whoosh + hit on the title", ""),

 ("2 · Getting there", "Arrival", 35, 48, [("IMG_2694.MOV", 4.5)], "crop", .5, [("lower", "Lago di Braies", "South Tyrol, Italy  ·  1,496 m")],
  "Lago di Braies sits at almost *1,500 metres* in the Dolomites of South Tyrol.", "pan from forest to the lakeside chapel; lower third (36-44s)",
  "music bed; footsteps on gravel", "Only true landscape clip: full-screen, no crop needed."),
 ("2 · Getting there", "Parking tip", 48, 62, [("IMG_2701.HEIC", 0)], "crop", .55, [("card", "PARKING", ["P4  ·  closest, priciest", "P3 / P2  ·  cheaper", "short walk to the lake"])],
  "Parking tip: *P4* is closest but pricey. *P3 or P2* save you money.", "card slides in (48.5s), rows tick in one by one",
  "tick per row", "Info card over the dock overview photo."),
 ("2 · Getting there", "Snack stop", 62, 72, [("IMG_2707.HEIC", 0), ("IMG_2712.HEIC", 0)], "split", .5, [],
  "First, a *snack stop* for the smallest member of the crew.", "two selfies side by side", "light, playful music phrase", ""),
 ("2 · Getting there", "First view", 72, 80, [("IMG_2641.HEIC", 0)], "crop", .42, [],
  "Then you round the corner, and *there it is.*", "slow push-in on the boats under the peak", "music swells", ""),

 ("3 · The beauty", "The cliffs", 80, 92, [("IMG_2698.MOV", 5)], "crop", .30, [("lower", "Seekofel", "2,810 m above the lake")],
  "Above the lake rises the *Seekofel*, almost 2,800 metres high.", "tilt up the rock face; lower third", "music bed only", "Height to be double-checked before narration is recorded."),
 ("3 · The beauty", "Clear water", 92, 102, [("IMG_2699.MOV", 3)], "crop", .66, [],
  "The water is so clear you can count the *pebbles.*", "ripples over the stones", "water lapping up", ""),
 ("3 · The beauty", "Golden larches", 102, 114, [("IMG_2746.HEIC", 0), ("31151498-b7bf-4639-a980-09955fa3f875.jpg", 0), ("ba61cc35-afea-4ea3-90e2-d30361413d5a.jpg", 0)], "split", .5, [],
  "In autumn, the larches turn *gold.*", "three panels slide in left to right", "soft whoosh per panel", ""),
 ("3 · The beauty", "Sunny beach", 114, 128, [("IMG_2657.MOV", 2)], "frame", .5, [],
  "And when the sun broke through at the *sandy end*, the colours changed completely.", "you and your daughter in the sun", "natural sound up (laughing)", "Sunny clip, same visit."),
 ("3 · The beauty", "Shore play", 128, 145, [(MP4, 3), ("63A1ED87-3BC1-48FA-9B19-797269672309.jpg", 0), ("B564B181-53C0-409D-93C2-D1EAF6590576.jpg", 0)], "split", .5, [],
  "Plenty of pebble beach for *little legs.*", "laughing clip + two lift photos", "laughter (clip audio)", "The laughing clip only exists as a small 850p export: kept as one panel. Have the original?"),

 ("4 · The boat", "Boathouse", 145, 157, [("IMG_2749.HEIC", 0)], "crop", .58, [("card", "ROWBOAT", ["€55  ·  40 minutes", "pay at the boathouse", "life jackets for kids"])],
  "The famous wooden rowboats: *€55* for 40 minutes.", "card over the dock", "tick per row", "'life jackets for kids': confirm we can say this."),
 ("4 · The boat", "All aboard", 157, 167, [("IMG_2727.MOV", 1)], "frame", .5, [],
  "Little one on the bench...", "you and your daughter settling in", "creak of the boat", ""),
 ("4 · The boat", "Captain Dad", 167, 180, [("IMG_2742.MOV", 1.5)], "frame", .5, [("chapter", "Captain Dad")],
  "...and *Dad* on the oars.", "close on Dad rowing", "oar splash on each stroke", ""),
 ("4 · The boat", "On the water", 180, 196, [("IMG_2731.MOV", 22)], "crop", .55, [],
  "(no narration: let it breathe)", "family on the bench, peaks behind", "natural sound up, music low", "From the 50 s clip."),
 ("4 · The boat", "Selfie", 196, 209, [("IMG_2734.MOV", 8)], "frame", .5, [],
  "(no narration)", "selfie with your daughter and friend", "natural sound", ""),
 ("4 · The boat", "Under the cliffs", 209, 222, [("IMG_2732.MOV", 3)], "crop", .40, [],
  "From inside the boat, it's forty minutes of *pure calm.*", "boat turns toward the cliffs", "music back up", "From the 67 s clip."),
 ("4 · The boat", "From the shore", 222, 232, [("c1ad2572-b66a-4181-aea5-425a8cfabda3.jpg", 0), ("ba61cc35-afea-4ea3-90e2-d30361413d5a.jpg", 0)], "split", .5, [],
  "From the shore, you *are* the postcard.", "your boat seen from the shore, two angles", "music", ""),

 ("5 · The reality", "BUT", 232, 240, [("IMG_2701.HEIC", 0)], "crop", .78, [("big", "BUT...")],
  "Now, the *honest part.*", "BUT punches in; frame shakes", "hit; music stops", ""),
 ("5 · The reality", "Insta vs real", 240, 256, [("e301100b-d690-4a43-af25-b27216893da6.jpg", 0), ("IMG_2747.MOV", 9)], "compare", .5, [("labels",)],
  "Most photos online are shot at *sunrise* and edited. On a normal day it's greyer, flatter, and busier.", "split slides open from the centre; labels (241s)",
  "swoosh on the split", "The comparison frame: your edited photo vs the raw overcast clip."),
 ("5 · The reality", "Crowds", 256, 268, [("IMG_2749.HEIC", 0)], "crop", .74, [],
  "Even on a grey autumn day, there are people at every viewpoint and *boats in every shot.*", "slow zoom into the dock", "crowd murmur", "Your footage shows a busy-ish dock, not a packed one, so the line stays honest. Have a real crowd clip? It would hit harder here. Strangers blurred."),
 ("5 · The reality", "Low water", 268, 278, [("IMG_2682.HEIC", 0)], "crop", .92, [("chapter", "Autumn = low water")],
  "In autumn the water drops, and the shore turns to *gravel.*", "gravel shore + chapter tag", "music low", ""),
 ("5 · The reality", "Toddler time", 278, 290, [("IMG_2732.MOV", 45)], "crop", .55, [],
  "And with a toddler? Forty minutes was *exactly enough.*", "daughter wriggling in the boat", "light laugh in the music", ""),

 ("6 · Tips", "Tip 1: timing", 290, 308, [("IMG_2747.MOV", 14)], "crop", .55, [("card", "TIP 1", ["Go at sunset", "or after the boats close", "= empty lake, no crowds"])],
  "Want the Instagram shot? Come at *sunset*, or after the boats close, when the lake goes quiet.", "boats tied up in rows; card", "music warm", "Your tip from yesterday's brief."),
 ("6 · Tips", "Tip 2: how long", 308, 324, [("IMG_2694.MOV", 1)], "crop", .5, [("card", "TIP 2 · HOW LONG", ["Boat  ·  40 min", "Lakeside loop  ·  ~1 h", "Snack + photos  ·  ~1 h", "Plan 2 to 3 hours"])],
  "Plan *two to three hours*: the boat, the loop walk round the lake, and a snack.", "rows tick in", "tick per row", "Loop walk time to be double-checked."),
 ("6 · Tips", "Tip 3: parking", 324, 338, [("IMG_2641.HEIC", 0)], "crop", .7, [("card", "TIP 3", ["Skip P4, park at P3 / P2", "Summer: check if the road", "needs a booking"])],
  "Skip P4, park at *P3 or P2*, and in summer check whether the road needs booking.", "card", "tick per row", "Summer road rule to be double-checked."),

 ("7 · Verdict", "Was it worth it?", 338, 350, [("835738B4-4F17-4766-8EBC-D9CC861CC08B.jpg", 0), (MP4, 6), ("63A1ED87-3BC1-48FA-9B19-797269672309.jpg", 0)], "split", .5, [],
  "So, Instagram or reality? Honestly... *both.*", "family moments, three panels", "music builds", ""),
 ("7 · Verdict", "TRIP", 350, 360, [("3c93faea-94d7-41fa-8f7d-9c40801c79b2.jpg", 0)], "frame", .5, [("stamp", "TRIP")],
  "Lago di Braies is a *TRIP.* Just go early, or go late.", "stamp slams (350.3s); VERDICT label", "stamp hit", "Same verdict card as the Short."),
 ("7 · Verdict", "End screen", 360, 380, [("IMG_2747.MOV", 16)], "crop", .55, [("endscreen",)],
  "Subscribe for more *family travel*: skip or trip?", "two end-screen slots + subscribe", "music outro", "YouTube end-screen area: 20 s."),
]

def mmss(s): return f"{int(s)//60}:{int(s)%60:02d}"

cards, md = [], ["---", "format: 1920x1080", f"duration: {mmss(S[-1][3])}",
  'message: "Lago di Braies is worth it, if you know what the Instagram photos don\'t show"',
  "arc: Postcard → Reality → Arrival → Beauty → The boat → The honest part → Tips → Verdict",
  "audience: families planning a Dolomites trip (YouTube long-form)", "---", "",
  "# Lago di Braies: Instagram vs Reality — storyboard", "",
  "Narration: AI voice (warm, female or male: your choice). Captions: narration word by word, bottom centre, keywords in yellow (like the Short). Music: original bed, natural clip sound under the voice.", ""]
act = None
for i, (a, title, st, en, srcs, mode, y, ovs, vo, reads, sound, note) in enumerate(S, 1):
    im = base_frame(srcs, mode, y)
    for ov in ovs: overlay(im, ov)
    if not vo.startswith("("): caption(ImageDraw.Draw(im), vo if len(vo) < 62 else vo[:vo.rfind(" ", 0, 60)] + "...")
    fn = f"frame-{i:02d}.jpg"; im.save(f"{OUT}/{fn}", quality=84)
    files = ", ".join(s for s, _ in srcs)
    if a != act: cards.append(f'<section class="act">Act {html.escape(a)}</section>'); md += [f"# Act {a}", ""]; act = a
    cards.append(f'''<div class="frame"><img src="stills/{fn}" alt="" loading="lazy"><div class="body">
<div class="title">{i:02d}: {html.escape(title)}</div><div class="time">{mmss(st)} to {mmss(en)} · {en-st}s</div>
<p class="words vo">“{html.escape(vo.replace("*", ""))}”</p>
<p class="meta"><b>Shot</b> {html.escape(files)} <i>({mode})</i></p><p class="meta"><b>Sound</b> {html.escape(sound)}</p>
{f'<p class="note">{html.escape(note)}</p>' if note else ""}</div></div>''')
    md += [f"## Frame {i}: {title} ({mmss(st)}-{mmss(en)})", f"- act: {a}", "- status: outline", f"- duration: {en-st}s",
           f"- scene: {files} ({mode})", f"- voiceover: {vo.replace('*', '')}", f"- reads: {reads}", f"- sound: {sound}", "", note, ""]

open("STORYBOARD.md", "w").write("\n".join(md))
print(len(S), "frames, total", mmss(S[-1][3]))

# ---- board page --------------------------------------------------------
chapters, seen = [], set()
for a, title, st, *_ in S:
    if a not in seen: seen.add(a); chapters.append(f"<li><span class='ts'>{mmss(st)}</span> {html.escape(a.split(' · ')[1])}</li>")
QUESTIONS = [
 "Narrator voice: female or male, and any accent you prefer? (Or record it yourself and I'll cut to it.)",
 "Facts I'll double-check before the voice is recorded: lake at 1,496 m, Seekofel at 2,810 m, the loop walk taking about an hour, and whether the summer road needs booking.",
 "The laughing-on-the-shore clip only exists as a small 850p export. Is there an original in your camera roll?",
 "Do you have any clip of a really busy dock or queue? Frames 03, 22 and 24 would hit harder with one.",
 "Strangers' faces get blurred as in the Short; your family friend stays unblurred. Still right?",
]
page = f'''<title>Braies Long-Form Storyboard</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap">
<style>
/* layout: header with run-time + chapters, then frames as cards in a 2-col grid grouped by act */
:root {{ --bg:#f3f6f6; --card:#ffffff; --fg:#14201f; --muted:#5b6b69; --line:#d9e2e1; --accent:#0e7c7b; --mark:#ffd60a;
  --display:"Space Grotesk", "Inter", system-ui, sans-serif; --body:"Inter", system-ui, sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#0f1716; --card:#172221; --fg:#e6eeed; --muted:#9db0ae; --line:#2a3a38; --accent:#4fc2bf; color-scheme:dark; }} }}
:root[data-theme="dark"] {{ --bg:#0f1716; --card:#172221; --fg:#e6eeed; --muted:#9db0ae; --line:#2a3a38; --accent:#4fc2bf; color-scheme:dark; }}
body {{ background:var(--bg); color:var(--fg); font-family:var(--body); font-size:15px; line-height:1.5; }}
.wrap {{ max-width:1180px; margin:0 auto; padding-block:32px 64px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); display:grid; gap:28px; }}
h1 {{ font-family:var(--display); font-size:clamp(28px, 4.5vw, 44px); line-height:1.1; margin:0; text-wrap:balance; }}
.kicker {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); font-weight:600; }}
.lede {{ color:var(--muted); max-width:68ch; margin:0; }}
.facts {{ display:flex; flex-wrap:wrap; gap:8px 20px; font-size:14px; }} .facts b {{ font-variant-numeric:tabular-nums; }}
.top {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.panel {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px 20px; min-width:0; }}
.panel h2 {{ font-family:var(--display); font-size:18px; margin:0 0 10px; }}
.panel ol, .panel ul {{ margin:0; padding-left:20px; display:grid; gap:6px; }}
.ts {{ font-variant-numeric:tabular-nums; font-weight:600; color:var(--accent); margin-right:6px; }}
.act {{ font-family:var(--display); font-size:22px; font-weight:700; padding-top:14px; border-top:1px solid var(--line); }}
.grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:20px; }}
.frame {{ background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; display:flex; flex-direction:column; }}
.frame img {{ display:block; width:100%; aspect-ratio:16/9; object-fit:cover; background:#000; }}
.body {{ padding:14px 18px 18px; display:grid; gap:6px; }}
.title {{ font-family:var(--display); font-weight:700; font-size:18px; }}
.time {{ font-size:13px; color:var(--accent); font-weight:600; font-variant-numeric:tabular-nums; }}
.vo {{ margin:2px 0; font-size:15px; }}
.meta {{ margin:0; font-size:13px; color:var(--muted); overflow-wrap:anywhere; }} .meta b {{ color:var(--fg); font-weight:600; margin-right:4px; }}
.note {{ margin:4px 0 0; font-size:13px; padding:8px 10px; border-radius:8px; background:color-mix(in srgb, var(--mark) 22%, var(--card)); }}
@media (max-width:760px) {{ .top, .grid {{ grid-template-columns:1fr; }} }}
</style>
<div class="wrap">
<header style="display:grid;gap:10px">
  <div class="kicker">YouTube long-form · storyboard for feedback</div>
  <h1>Lago di Braies: Instagram vs Reality</h1>
  <p class="lede">A family day at the lake, told as the gap between the postcard and the real visit. Every still below is a real frame from your footage, laid out as it will sit in the 16:9 video, with the narration caption drawn in. Comment on any frame by its number.</p>
  <div class="facts"><span>Length <b>{mmss(S[-1][3])}</b></span><span>Frames <b>{len(S)}</b></span><span>Format <b>1920×1080, 30 fps</b></span><span>Footage used <b>14 clips, 22 photos</b></span></div>
</header>
<div class="top">
  <section class="panel"><h2>YouTube chapters</h2><ol style="list-style:none;padding:0">{"".join(chapters)}</ol></section>
  <section class="panel"><h2>Questions before I build</h2><ol>{"".join(f"<li>{html.escape(q)}</li>" for q in QUESTIONS)}</ol></section>
</div>
'''
out, grid = [], []
for c in cards:
    if c.startswith('<section class="act">'):
        if grid: out.append('<div class="grid">' + "".join(grid) + "</div>"); grid = []
        out.append(c)
    else: grid.append(c)
out.append('<div class="grid">' + "".join(grid) + "</div>")
open("boards/storyboard.html", "w").write(page + "\n".join(out) + "\n</div>\n")
print("board written")
