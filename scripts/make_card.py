"""Bake a B-roll "card" (white border + rounded corners, transparent outside) as ProRes 4444.

  python make_card.py src.mp4 out.mov [--ss 0] [--t 3] [--w 1500] [--aspect 16:9] [--r 56] [--b 16]
  python make_card.py photo.jpg out.mov --t 2          (stills work too)
  python make_card.py src.mp4 out.mov --circle --w 760  (circle headshot / PiP, white ring)

Use it when Impact "Stroke" + "Rounded Crop" can't be applied by script (or for still images).
In Premiere the card still gets the editor's entry move: Motion Scale ~50% of final -> 100% over
0.25-0.8 s with Opacity 0 -> 100 in ~0.2 s (place it at its final size; animate scale, not crop).
Output is 25 fps, centre-cropped to the aspect; size = --w wide (incl. border).
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw


def arg(n, d, cast=str):
    return cast(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d


def mask(w, h, r, path, circle=False):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    (d.ellipse if circle else d.rounded_rectangle)([0, 0, w - 1, h - 1], **({} if circle else {"radius": r}), fill=255)
    m.save(path)


def main():
    src, out = sys.argv[1], sys.argv[2]
    circle = "--circle" in sys.argv
    W = arg("--w", 760 if circle else 1500, int)
    a, b = (1, 1) if circle else map(int, arg("--aspect", "16:9").split(":"))
    H = round(W * b / a / 2) * 2
    r, bw = arg("--r", 56, int), arg("--b", 16 if not circle else 14, int)
    ss, t = arg("--ss", "0"), arg("--t", "3")
    iw, ih = W - 2 * bw, H - 2 * bw
    tmp = tempfile.mkdtemp(prefix="card_")
    outer, inner = os.path.join(tmp, "outer.png"), os.path.join(tmp, "inner.png")
    mask(W, H, r, outer, circle)
    mask(iw, ih, max(r - bw, 4), inner, circle)
    still = src.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    vin = ["-loop", "1", "-t", t, "-i", src] if still else ["-ss", ss, "-t", t, "-i", src]
    fc = (f"[0:v]fps=25,scale={iw}:{ih}:force_original_aspect_ratio=increase,crop={iw}:{ih},format=rgba[v];"
          f"[2:v]format=gray,loop=-1:1:0[im];[v][im]alphamerge[vm];"
          f"color=white:s={W}x{H}:r=25:d={t},format=rgba[bg];"
          f"[1:v]format=gray,loop=-1:1:0[om];[bg][om]alphamerge[card];"
          f"[card][vm]overlay={bw}:{bw}:shortest=1,format=yuva444p10le[o]")
    cmd = ["ffmpeg", "-v", "error", "-y", *vin, "-i", outer, "-i", inner, "-filter_complex", fc,
           "-map", "[o]", "-t", t, "-an", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", out]
    subprocess.run(cmd, check=True)
    print(out, f"{W}x{H}", t + "s")


if __name__ == "__main__":
    main()
