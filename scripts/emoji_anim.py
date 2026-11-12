"""Fetch Noto Animated Emoji (fonts.gstatic.com, Apache 2.0) as animated WebP and convert to ProRes 4444 .mov with alpha,
25 fps, looped to >= MIN_S seconds. Usage: python emoji_anim.py name=codepoint [name=codepoint ...]"""
import io, os, subprocess, sys, urllib.request
from PIL import Image, ImageSequence

OUT = "E:/Anan/Assets/PNG/emoji_anim"
SRC = OUT + "/src"
FPS, MIN_S, SIZE = 25, 6.0, 512

for arg in sys.argv[1:]:
    name, cp = arg.split("=")
    mov = f"{OUT}/{name}.mov"
    if os.path.exists(mov):
        print("have", name); continue
    wp = f"{SRC}/{cp}.webp"
    if not os.path.exists(wp):
        try:
            urllib.request.urlretrieve(f"https://fonts.gstatic.com/s/e/notoemoji/latest/{cp}/512.webp", wp)
        except Exception as e:
            print("FAIL", name, cp, e); continue
    im = Image.open(wp)
    frames, durs = [], []
    for fr in ImageSequence.Iterator(im):
        frames.append(fr.convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS))
        durs.append(max(10, fr.info.get("duration", 40)))
    total = sum(durs) / 1000.0
    loops = max(1, int(MIN_S / total + 0.999))
    n_out = int(round(total * loops * FPS))
    starts, acc = [], 0
    for d in durs:
        starts.append(acc); acc += d
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{SIZE}x{SIZE}", "-r", str(FPS),
                            "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", mov], stdin=subprocess.PIPE)
    k = 0
    for f in range(n_out):
        t = (f * 1000.0 / FPS) % acc
        while k + 1 < len(starts) and starts[k + 1] <= t:
            k += 1
        if k > 0 and starts[k] > t:
            k = 0
            while k + 1 < len(starts) and starts[k + 1] <= t:
                k += 1
        enc.stdin.write(frames[k].tobytes())
    enc.stdin.close(); enc.wait()
    print(f"{name}: {len(frames)} frames, {total:.2f}s x{loops} -> {n_out / FPS:.1f}s")
