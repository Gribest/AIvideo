# Lago di Braies: Skip or Trip? (posting kit)

Master: `output/lago-di-braies-skip-or-trip.mp4` (1080x1920, 30 fps, SDR, 33.5 s, -14 LUFS). Same file for Reels and Shorts.

## Title options (under 60 characters)
1. Lago di Braies: Skip or Trip? 🇮🇹
2. Italy's Most Famous Lake: Skip or Trip?
3. Rowing Lago di Braies with a Toddler: Skip or Trip?

## Instagram caption
Lago di Braies: Skip or Trip? 🛶
Turquoise water, wooden rowboats, golden larches… but there's a catch.
Tip: skip P4 parking, P3 or P2 is way cheaper.
#lagodibraies #dolomites #southtyrol #italytravel #familytravel

## YouTube Shorts
Title: Lago di Braies: Skip or Trip? #Shorts
Description: Rowing Italy's most famous Dolomites lake with our little one. Worth it or overrated? Boat about €50 for 45 min, and don't park at P4 (P3 or P2 is much cheaper). Verdict at the end! #Shorts #LagoDiBraies #Dolomites #Italy #TravelTips

## Cover frame
Frame 0: boat #20 under the mountain with the yellow "Lago di Braies: Skip or Trip?" box in the top third.

## Rebuilding
1. Put the raw clips/photos in `raw/` (see `tools/build_media.py` for names).
2. `python3 tools/build_media.py` → graded, tone-mapped, blurred shots in `assets/`.
3. `python3 tools/make_audio.py` → original music bed + SFX (royalty-free, synthesised).
4. `python3 tools/build_html.py` → `index.html` (edit the SHOTS / CAPS tables to change the edit).
5. `npx hyperframes check`, then `npx hyperframes render --sdr --output output/master-hq.mp4`.
