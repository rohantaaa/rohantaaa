#!/usr/bin/env python3
"""Build the Orihime vs Yhwach AMV from shots.json.

Every shot is timed in beats, so cuts land on the music. Shots whose clip is
missing are rendered as labelled placeholder cards, which turns the same file
into an animatic you can check before collecting footage.

Needs only Python 3 and ffmpeg on PATH.

    python3 build_amv.py                  # full render -> out/amv.mp4
    python3 build_amv.py --animatic       # placeholders + click track, no clips needed
    python3 build_amv.py --preview        # 960x540 fast render
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

GRADES = {
    # Warm, soft, slightly lifted: Orihime's healing light.
    "orihime": "eq=brightness=0.03:saturation=1.12:gamma=1.04,"
               "colorbalance=rs=0.05:gs=0.02:bs=-0.06:rh=0.06:gh=0.03:bh=-0.05",
    # Cold, desaturated, crushed blacks with a little red in the mids: Yhwach.
    "yhwach": "eq=contrast=1.25:saturation=0.55:brightness=-0.04,"
              "colorbalance=rs=-0.05:bs=0.09:rm=0.07:bm=-0.02,vignette=PI/4.5",
    # Punchy and saturated for the fight drops.
    "clash": "eq=contrast=1.32:saturation=1.28,colorbalance=rh=0.04:bs=0.05",
    # Faded flashback look.
    "memory": "eq=saturation=0.35:brightness=0.03:contrast=0.92,"
              "colorbalance=rs=0.08:bs=-0.07,vignette=PI/4",
    "none": "",
}

# Placeholder card colours per grade, so the animatic shows the colour story.
CARD_COLORS = {
    "orihime": "0xE8A35C", "yhwach": "0x1B1F2A", "clash": "0x8E1B2B",
    "memory": "0x7A6F63", "none": "0x333333",
}


def fx_filters(fx, dur, w, h, fps):
    out = []
    for name in fx:
        if name == "flash":
            out.append("fade=in:st=0:d=0.12:color=white")
        elif name == "fade_in":
            out.append(f"fade=in:st=0:d={min(0.6, dur / 2):.3f}")
        elif name == "fade_out":
            d = min(0.6, dur / 2)
            out.append(f"fade=out:st={dur - d:.3f}:d={d:.3f}")
        elif name == "white_out":
            d = min(1.2, dur)
            out.append(f"fade=out:st={dur - d:.3f}:d={d:.3f}:color=white")
        elif name == "punch":
            # Starts 12% zoomed in and settles back over ~6 frames.
            out.append(f"zoompan=z='1.12-0.12*min(on/6\\,1)':d=1:"
                       f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}")
        elif name == "shake":
            out.append(f"scale={int(w * 1.06)}:{int(h * 1.06)},"
                       f"crop={w}:{h}:x='(iw-ow)/2+10*sin(t*61)':y='(ih-oh)/2+7*cos(t*47)'")
        elif name == "rgb":
            out.append("rgbashift=rh=-7:bh=7")
        elif name == "impact":
            # Two inverted frames on the hit.
            out.append(f"negate=enable='lt(t\\,{2 / fps:.4f})'")
        elif name == "letterbox":
            bar = int(h * 0.12)
            out.append(f"drawbox=y=0:w=iw:h={bar}:color=black:t=fill,"
                       f"drawbox=y=ih-{bar}:w=iw:h={bar}:color=black:t=fill")
        else:
            sys.exit(f"unknown fx '{name}'")
    return out


def parse_time(value):
    if isinstance(value, (int, float)):
        return float(value)
    secs = 0.0
    for part in str(value).split(":"):
        secs = secs * 60 + float(part)
    return secs


def run(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stderr[-3000:])
        sys.exit(f"ffmpeg failed: {' '.join(cmd[:6])} ...")


def render_shot(i, shot, cfg, args, tmp, font):
    w, h, fps = args.w, args.h, cfg["fps"]
    dur = shot["beats"] * 60.0 / cfg["bpm"]
    grade = shot.get("grade", "none")
    clip = os.path.join(HERE, shot["clip"]) if shot.get("clip") else None
    use_clip = clip and os.path.exists(clip) and not args.animatic
    out = os.path.join(tmp, f"shot_{i:03d}.mp4")

    vf = []
    if use_clip:
        speed = float(shot.get("speed", 1.0))
        inputs = ["-ss", f"{parse_time(shot.get('in', 0)):.3f}",
                  "-t", f"{dur * speed + 0.5:.3f}", "-i", clip]
        if speed != 1.0:
            vf.append(f"setpts=PTS/{speed}")
        vf += [f"fps={fps}",
               f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"]
        if GRADES.get(grade):
            vf.append(GRADES[grade])
    else:
        color = "black" if shot.get("text") else CARD_COLORS.get(grade, "0x333333")
        inputs = ["-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}:r={fps}:d={dur:.3f}"]

    label = shot.get("text") or (f"#{i + 1}  {shot.get('section', '')}  "
                                 f"[{grade}]  {shot['beats']} beats\n\n{shot.get('note', '')}")
    if shot.get("text") or not use_clip:
        txt = os.path.join(tmp, f"text_{i:03d}.txt")
        with open(txt, "w") as f:
            f.write(label)
        size = int(h / 14) if shot.get("text") else int(h / 30)
        vf.append(f"drawtext=fontfile='{font}':textfile='{txt}':fontcolor=white:"
                  f"fontsize={size}:line_spacing={size // 2}:"
                  f"x=(w-text_w)/2:y=(h-text_h)/2")

    vf += fx_filters(shot.get("fx", []), dur, w, h, fps)
    vf.append("format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-vf", ",".join(vf),
         "-t", f"{dur:.3f}", "-r", str(fps), "-an",
         "-c:v", "libx264", "-preset", args.x264_preset, "-crf", "18", out])
    return out, dur


def find_font():
    try:
        path = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"],
                              capture_output=True, text=True).stdout.strip()
        if path:
            return path
    except FileNotFoundError:
        pass
    for p in ("C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial Bold.ttf"):
        if os.path.exists(p):
            return p
    sys.exit("no font found for title cards; set \"font\" in shots.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.path.join(HERE, "shots.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out", "amv.mp4"))
    ap.add_argument("--animatic", action="store_true",
                    help="ignore clips, render placeholder cards (click track if no song)")
    ap.add_argument("--preview", action="store_true", help="960x540, fast encode")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    with open(args.config) as f:
        cfg = json.load(f)
    args.w, args.h = (960, 540) if args.preview else cfg.get("resolution", [1920, 1080])
    args.x264_preset = "veryfast" if (args.preview or args.animatic) else "medium"
    font = cfg.get("font") or find_font()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="amv_")
    try:
        parts, total, missing = [], 0.0, 0
        for i, shot in enumerate(cfg["shots"]):
            if shot.get("clip") and not os.path.exists(os.path.join(HERE, shot["clip"])):
                missing += 1
            path, dur = render_shot(i, shot, cfg, args, tmp, font)
            parts.append(path)
            total += dur
            print(f"[{i + 1:>2}/{len(cfg['shots'])}] {total:6.2f}s  {shot.get('note') or shot.get('text', '')}"[:100])

        listing = os.path.join(tmp, "list.txt")
        with open(listing, "w") as f:
            f.writelines(f"file '{p}'\n" for p in parts)
        video = os.path.join(tmp, "video.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", listing, "-c", "copy", video])

        song = os.path.join(HERE, cfg["song"]) if cfg.get("song") else None
        fade = min(2.0, total / 4)
        if song and os.path.exists(song):
            audio = ["-ss", f"{parse_time(cfg.get('song_start', 0)):.3f}", "-i", song]
        else:
            # Click track on every beat, accented on the downbeat of each bar.
            b, first = 60.0 / cfg["bpm"], parse_time(cfg.get("first_beat", 0))
            expr = (f"0.5*sin(2*PI*(1000+600*lt(mod(t-{first}\\,{4 * b})\\,0.04))*t)"
                    f"*lt(mod(t-{first}\\,{b})\\,0.035)")
            audio = ["-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d={total:.3f}"]
            print("no song found: using a click track")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, *audio,
             "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-af", f"afade=out:st={total - fade:.3f}:d={fade:.3f}",
             "-c:a", "aac", "-b:a", "256k", "-t", f"{total:.3f}", "-movflags", "+faststart",
             args.out])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nwrote {args.out}  ({total:.1f}s, {len(parts)} shots"
          + (f", {missing} placeholder" if missing and not args.animatic else "") + ")")


if __name__ == "__main__":
    main()
