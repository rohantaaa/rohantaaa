# Bleach TYBW AMV: Orihime vs Yhwach

**Concept: "Rejection vs The Almighty."** Yhwach (ユーハバッハ, *Yūhabahha*) can see every future and rewrite it. Orihime's power rejects events and undoes what already happened. The AMV sets her quiet resolve against his overwhelming presence, ending with her light winning the last frame.

## Files

| File | What it is |
| --- | --- |
| `shots.json` | The storyboard: 56 shots, each timed in beats, with a grade, effects and a note describing the footage to find |
| `build_amv.py` | Cuts your clips to the beat, grades them, adds the effects and title cards, then muxes the song. Needs Python 3 and ffmpeg only |
| `clips/`, `song.mp3`, `out/` | Your footage, music and render. Git ignores them, so no anime footage ends up in the repo |

## Structure (168 beats, about 72 s at 140 BPM)

| Section | Beats | Grade | Cutting |
| --- | --- | --- | --- |
| Intro | 16 | memory | Title card, hairpins, Sora flashback, "ORIHIME vs YHWACH" |
| Threat | 16 | yhwach | Yhwach only: silhouette, Seireitei burning, his eyes, Yamamoto's fall |
| Build | 32 | alternating | 4-beat cuts, then 2-beat Orihime/Yhwach ping-pong into an "I REJECT" card |
| Drop 1 | 32 | clash | 2-beat and 1-beat hits with flashes, shake, impact frames. Santen Kesshun vs his attacks |
| Bridge | 24 | memory | Half-speed memories. Cards: "HE SEES EVERY FUTURE." / "SHE CAN UNDO ANY ONE." |
| Drop 2 | 32 | clash | 8 one-beat cuts, Koten Zanshun, final collision, white-out |
| Outro | 16 | orihime | Calm Orihime, end card "REJECTION // THE ALMIGHTY" |

**Grades:** `orihime` is warm and soft gold. `yhwach` is cold and desaturated, with crushed blacks and a red tint in the mids. `clash` is punchy and saturated. `memory` is a faded flashback look.

**Effects:** `flash` (white flash on the cut), `impact` (2 inverted frames), `punch` (snap zoom), `shake`, `rgb` (chromatic split), `letterbox`, `fade_in`, `fade_out`, `white_out`.

**Song ideas:** the TYBW opening "Scar" (Kitani Tatsuya), a Shiro Sagisu Bleach score track for a cinematic cut, or any track with a clear build and drop. Set `bpm` to match the song. The section lengths assume 4/4 phrasing.

## Making it on your laptop

1. Put your episode clips in `clips/`. For each shot, set `clip` to the file and `in` to its start time (`"mm:ss.ms"`). The `note` says what to look for. I didn't pin exact episode numbers, so pick the moments you like best.
2. Put the song in as `song.mp3`. Set `bpm`, and set `song_start` to where the AMV should begin in the song. To line up the first cut, set it to the time of a downbeat.
3. Run a preview, then the full render:
   ```bash
   python3 build_amv.py --animatic --preview   # timing check with placeholder cards
   python3 build_amv.py --preview              # 960x540 fast render with your clips
   python3 build_amv.py                        # 1080p final -> out/amv.mp4
   ```
   Any shot whose clip is missing renders as a labelled card, so you can fill in footage gradually.

**Tweaking:** to make a cut longer or shorter, change `beats`. Keep each section's total the same to stay on the music. Use `speed` below 1 (e.g. `0.5`) for slow motion. To add or remove shots, just edit the list.
