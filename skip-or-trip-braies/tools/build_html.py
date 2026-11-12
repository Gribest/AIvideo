"""Writes index.html from the edit tables below. Edit the tables, re-run:
python3 tools/build_html.py"""
import html, re

DUR = 33.5
# id, type, src, start, duration
SHOTS = [
    ("hook",    "img", "assets/stills/p8_family_boat.jpg", 0.0, 2.0),
    ("dock",    "vid", "assets/shots/s02_dock.mp4",        2.0, 1.4),
    ("tilt",    "vid", "assets/shots/s03_tilt.mp4",        3.4, 2.0),
    ("lake",    "vid", "assets/shots/s04_lake.mp4",        5.4, 2.6),
    ("boats",   "img", "assets/stills/p1_boats.jpg",       8.0, 1.5),
    ("bench",   "vid", "assets/shots/s06_bench.mp4",       9.5, 2.5),
    ("rowing",  "img", "assets/stills/p2_rowing.jpg",     12.0, 1.5),
    ("water",   "vid", "assets/shots/s08_water.mp4",      13.5, 2.5),
    ("larches", "img", "assets/stills/p6_larches.jpg",    16.0, 1.5),
    ("smile",   "vid", "assets/shots/s10_smile.mp4",      17.5, 0.8),
    ("us",      "img", "assets/stills/p3_us.jpg",         18.3, 1.7),
    ("crowd",   "img", "assets/stills/p5_dock.jpg",       20.0, 2.5),
    ("shore",   "img", "assets/stills/p4_shore.jpg",      22.5, 2.0),
    ("forest",  "vid", "assets/shots/s14_forest.mp4",     24.5, 3.0),
    ("back",    "vid", "assets/shots/s15_back.mp4",       27.5, 2.0),
    ("cliffs",  "vid", "assets/shots/s16_cliffs.mp4",     29.5, 1.5),
    ("loop",    "img", "assets/stills/p8_family_boat.jpg",31.0, 2.5),
]
# id, start, end, text (*yellow keyword*, | = line break), centre y in px
CAPS = [
    ("c01",  2.10,  3.35, "Dolomites, *Italy*", 560),
    ("c02",  3.50,  5.35, "~1,500 m *up*", 560),
    ("c03",  5.50,  7.95, "Rowboat: *€55*|for 40 min", 560),
    ("c04",  8.10,  9.45, "Classic *wooden* boats", 520),
    ("c05",  9.60, 11.95, "Row right under|*the peaks*", 470),
    ("c06", 13.60, 15.95, "*Glass*-clear water", 560),
    ("c07", 16.10, 17.45, "Larches turning *gold*", 560),
    ("c08", 18.40, 19.95, "Family *approved*", 560),
    ("c09", 21.05, 22.45, "Crowds at the *dock*", 640),
    ("c10", 22.60, 24.45, "Autumn = *low water*", 560),
    ("c11", 24.60, 25.85, "*P4* parking = pricey", 560),
    ("c12", 25.90, 27.45, "Park at *P3 or P2*", 560),
]
BUT = (20.0, 21.0)
VERDICT = ("TRIP", 27.8, 31.0)          # "SKIP" turns the card red
HOOK_TEXT = ("Lago di Braies:", "Skip or Trip?")
HOOK_WINDOWS = [("hookbox", 0.0, 2.0), ("hookbox2", 32.65, DUR - 32.65)]

def cap_html(t):
    out = []
    for line in t.split("|"):
        parts = re.split(r"(\*[^*]+\*)", line)
        out.append("".join(f'<span class="key">{html.escape(p[1:-1])}</span>' if p.startswith("*") else html.escape(p) for p in parts))
    return "<br>".join(out)

# SFX cues: (file, time, volume)
cuts = [s[3] for s in SHOTS[1:]]
sfx = []
for i, c in enumerate(cuts):
    if c in (BUT[0], VERDICT[1] - 0.3): continue
    if i % 2 == 0 or c in (2.0, 8.0, 31.0): sfx.append(("whoosh", c - 0.2, 0.55))
for cid, a, b, t, y in CAPS: sfx.append(("tick", a, 0.5))
sfx.append(("hit", BUT[0], 0.9))
sfx.append(("stamp", VERDICT[1], 0.9))

z = 1; body = []
for sid, kind, src, a, d in SHOTS:
    if kind == "vid":
        body.append(f'<video id="{sid}" class="clip shot" src="{src}" data-start="{a}" data-duration="{d}" data-track-index="0" muted playsinline style="z-index:{z}"></video>')
    else:
        body.append(f'<img id="{sid}" class="clip shot" src="{src}" data-start="{a}" data-duration="{d}" data-track-index="0" alt="" style="z-index:{z}">')
z = 50
for hid, a, d in HOOK_WINDOWS:
    body.append(f'<div id="{hid}" class="clip hook" data-start="{a}" data-duration="{round(d,3)}" data-track-index="1" style="z-index:{z}"><div class="hookin">{HOOK_TEXT[0]}<br>{HOOK_TEXT[1]}</div></div>')
for cid, a, b, t, y in CAPS:
    body.append(f'<div id="{cid}" class="clip cap" data-start="{a}" data-duration="{round(b-a,3)}" data-track-index="2" style="top:{y-160}px;z-index:{z}"><div class="capin">{cap_html(t)}</div></div>')
body.append(f'<div id="but" class="clip big" data-start="{BUT[0]}" data-duration="{BUT[1]-BUT[0]}" data-track-index="3" style="z-index:{z}"><div class="butin">BUT</div></div>')
vcol = "var(--trip)" if VERDICT[0] == "TRIP" else "var(--skip)"
body.append(f'<div id="verdict" class="clip verdict" data-start="{VERDICT[1]}" data-duration="{round(VERDICT[2]-VERDICT[1],3)}" data-track-index="4" style="z-index:{z+1}"><div class="vin"><div class="vlabel">VERDICT</div><div class="vcard" style="background:{vcol}">{VERDICT[0]}</div></div></div>')
body.append(f'<audio id="music" class="clip" src="assets/audio/music_bed.wav" data-start="0" data-duration="{DUR}" data-track-index="10" data-volume="0.5"></audio>')
SFX_LEN = {"whoosh": 0.45, "tick": 0.06, "hit": 1.0, "stamp": 1.4}
SFX_TRACK = {"whoosh": 11, "tick": 12, "hit": 13, "stamp": 13}
for i, (f, t, v) in enumerate(sorted(sfx, key=lambda x: x[1])):
    body.append(f'<audio id="sfx{i:02d}" class="clip" src="assets/audio/{f}.wav" data-start="{round(max(0,t),3)}" data-duration="{SFX_LEN[f]}" data-track-index="{SFX_TRACK[f]}" data-volume="{v}"></audio>')

# animation script
js = []
for sid, kind, src, a, d in SHOTS:
    if sid == "hook":
        js.append(f'tl.fromTo("#hook",{{scale:1}},{{scale:1.07,duration:{d},ease:"none"}},{a});')
    elif sid == "loop":   # lands exactly on frame 1's framing for a seamless replay
        js.append(f'tl.fromTo("#loop",{{scale:1.12}},{{scale:1,duration:{d},ease:"power2.out"}},{a});')
    elif kind == "img":
        js.append(f'tl.fromTo("#{sid}",{{scale:1.0}},{{scale:1.09,duration:{d},ease:"none"}},{a});')
    else:
        js.append(f'tl.fromTo("#{sid}",{{scale:1.08}},{{scale:1.0,duration:0.35,ease:"power3.out"}},{a});')
js.append('tl.fromTo("#hookbox .hookin",{scale:1},{scale:1.04,duration:0.25,yoyo:true,repeat:3,ease:"sine.inOut"},0.4);')
js.append('tl.fromTo("#hookbox2 .hookin",{scale:0.6,opacity:0},{scale:1,opacity:1,duration:0.25,ease:"back.out(2)"},32.65);')
for cid, a, b, t, y in CAPS:
    js.append(f'tl.fromTo("#{cid} .capin",{{scale:0.55,opacity:0,y:30}},{{scale:1,opacity:1,y:0,duration:0.2,ease:"back.out(2.2)"}},{a});')
    js.append(f'tl.to("#{cid} .capin",{{opacity:0,scale:0.95,duration:0.12,ease:"power2.in"}},{round(b-0.12,3)});')
a, b = BUT
js.append(f'tl.fromTo("#but .butin",{{scale:3.2,opacity:0}},{{scale:1,opacity:1,duration:0.18,ease:"power4.in"}},{a});')
js.append(f'tl.fromTo("#crowd",{{x:0}},{{x:14,duration:0.05,yoyo:true,repeat:5,ease:"none"}},{a+0.18});')
js.append(f'tl.to("#but .butin",{{opacity:0,scale:1.15,duration:0.12}},{b-0.12});')
v, a, b = VERDICT
js.append(f'tl.fromTo("#verdict .vcard",{{scale:3.5,opacity:0,rotation:-18}},{{scale:1,opacity:1,rotation:-6,duration:0.22,ease:"power4.in"}},{a});')
js.append(f'tl.fromTo("#verdict .vlabel",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.2,ease:"back.out(2)"}},{a+0.25});')
js.append(f'tl.fromTo("#back",{{x:0}},{{x:16,duration:0.05,yoyo:true,repeat:5,ease:"none"}},{a+0.22});')
js.append(f'tl.to("#verdict .vcard",{{scale:1.05,duration:0.5,yoyo:true,repeat:3,ease:"sine.inOut"}},{a+0.6});')
js.append(f'tl.to("#verdict .vin",{{opacity:0,scale:0.9,duration:0.15,ease:"power2.in"}},{round(b-0.15,3)});')

doc = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Lago di Braies: Skip or Trip?</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{ --yellow:#FFD60A; --ink:#ffffff; --trip:#16A34A; --skip:#DC2626; --font:"Inter", sans-serif; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:#0b0b0b; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; font-family:var(--font); background:#0b0b0b; }}
      .shot {{ position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; transform-origin:50% 45%; }}
      /* text lives left of the right-hand button rail and above the bottom 20% */
      .cap {{ position:absolute; left:40px; width:920px; height:320px; display:flex; align-items:center; justify-content:center; text-align:center; overflow:visible; }}
      .capin {{ font-weight:900; font-size:84px; line-height:1.08; letter-spacing:-0.01em; color:var(--ink);
        -webkit-text-stroke:10px rgba(0,0,0,0.85); paint-order:stroke fill; text-shadow:0 6px 18px rgba(0,0,0,0.45); }}
      .key {{ color:var(--yellow); }}
      .hook {{ position:absolute; left:40px; width:920px; top:250px; height:300px; display:flex; align-items:center; justify-content:center; }}
      .hookin {{ background:var(--yellow); color:#0b0b0b; font-weight:900; font-size:80px; line-height:1.05; text-align:center;
        padding:22px 40px 26px; border-radius:22px; box-shadow:0 10px 30px rgba(0,0,0,0.35); letter-spacing:-0.015em; }}
      .big {{ position:absolute; left:0; width:1000px; top:560px; height:400px; display:flex; align-items:center; justify-content:center; }}
      .butin {{ font-weight:900; font-size:300px; color:#fff; letter-spacing:-0.03em; -webkit-text-stroke:14px #0b0b0b; paint-order:stroke fill; text-shadow:0 14px 40px rgba(0,0,0,0.55); }}
      .verdict {{ position:absolute; left:0; width:1000px; top:170px; height:470px; display:flex; align-items:center; justify-content:center; }}
      .vin {{ display:flex; flex-direction:column; align-items:center; gap:22px; }}
      .vlabel {{ background:#fff; color:#0b0b0b; font-weight:900; font-size:46px; letter-spacing:0.18em; padding:10px 28px 12px; border-radius:999px; }}
      .vcard {{ color:#fff; font-weight:900; font-size:190px; line-height:1; padding:26px 60px 36px; border:12px solid #fff; border-radius:40px;
        letter-spacing:-0.02em; box-shadow:0 18px 50px rgba(0,0,0,0.45); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
      {chr(10).join("      " + l for l in body).strip()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + l for l in js).strip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open("index.html", "w").write(doc)
print("index.html written:", len(SHOTS), "shots,", len(CAPS), "captions,", len(sfx), "sfx")
