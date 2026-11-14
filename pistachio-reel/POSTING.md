# Pistachio slice reel: posting kit

Master: `output/tres-leches-reel.mp4` (1080x1920, 30 fps, SDR, 19.2 s, original audio at about -14 LUFS).

## Instagram caption options
1. We waited outside in the cold for THIS 😭💚 Amsterdam's viral pistachio tres leches… worth the hype? 👇
2. The whole squad lined up for ONE slice 🫣 Viral tres leches in Amsterdam, would you try it? 🇳🇱
3. Tag the friend you'd wait in the cold with for this 👇💚 Viral tres leches, Amsterdam edition

Hashtags (pick 5): #tresleches #amsterdamfood #amsterdam #viralfood #dessert
Extras to rotate in: #pistachio #foodreels #amsterdameats #foodie #netherlands

## To help it go viral
- Post the no-music version and add a sound that's trending right now (tap the ↗ arrow next to sounds in Reels). Trending audio gets a big reach boost.
- Cover: frame 0 (squad + hook box). Leave "Show in grid" on.
- Tag the shop and the location, and collab-tag the friends in the video (Collab invite = their followers see it too).
- Post in your audience's evening (around 6–9 pm) and reply to every comment in the first hour.

## Rebuilding
1. Put the source clip at `raw/IMG_8593.mov`.
2. `python3 tools/build_media.py` → tone-mapped, graded, re-timed shots + ambience.
4. `npx hyperframes check`, then `npx hyperframes render --sdr --output output/pistachio-reel.mp4`.
