# News cards (11-11-2026): crop outlet bar + headline from the headless-Edge captures, upscale, then a yellow marker
# sweeps over the key words (multiply) -> 1920-wide H.264 clips in E:/Anan/Assets/news/. Opaque white card; build_reel
# rounds the corners. 0.4 s plain, then each highlight span sweeps in 0.32 s, hold to 6 s.
import os, subprocess, sys
from PIL import Image, ImageOps, ImageChops, ImageDraw, ImageFilter, ImageEnhance

N = "E:/Anan/Assets/news/"
OUT_W, PAD, FPS, DUR = 1920, 70, 25, 6.0
YEL = (255, 222, 60)

CARDS = {
    # name: (source, [crop boxes stacked top->bottom], [highlight boxes in SOURCE coords], invert, brighten)
    "card_cnn_affair": ("nv_cnn.png", [(90, 278, 238, 314), (40, 515, 1000, 685)],
                        [(604, 526, 890, 572), (840, 580, 994, 628), (44, 634, 276, 680)], False, 1.0),
    "card_cnbc_2days": ("nv_cnbc.png", [(55, 4, 175, 46), (55, 288, 790, 420)],
                        [(402, 292, 618, 334), (582, 336, 782, 376), (58, 377, 276, 418)], False, None),
    "card_forbes_half": ("nv_yahoo_divorce.png", [(85, 560, 150, 588), (85, 598, 725, 712)],
                         [(484, 637, 720, 676), (86, 676, 530, 712)], True, 1.0),
    "card_rtv_470": ("nv_470_rtv.png", [(16, 255, 705, 665), (8, 684, 610, 772)],
                     [(188, 689, 520, 734)], False, 1.0),
}


def build(name, src, boxes, hls, invert, bright):
    im = Image.open(N + src).convert("RGB")
    if bright is None:  # cookie modal darkened the page: divide it back out (white measured -> 253)
        g = im.getpixel((950, 300))[0]
        im = im.point(lambda v: min(255, int(v * 253 / max(1, g))))
    if invert:  # dark-theme page: greyscale first, or the inverted blue-grey turns cream
        im = ImageOps.invert(ImageOps.grayscale(im).convert("RGB"))
    im = im.point(lambda v: 255 if v > 228 else v)  # page tints (grey / off-white) -> clean white card
    parts, offs, y = [], [], 0
    for b in boxes:
        parts.append(im.crop(b)); offs.append((b, y)); y += (b[3] - b[1]) + 18
    inner_w = max(p.size[0] for p in parts)
    sc = (OUT_W - 2 * PAD) / inner_w
    H = int((y - 18) * sc) + 2 * PAD
    H += H % 2
    base = Image.new("RGB", (OUT_W, H), (255, 255, 255))
    for p, (b, yy) in zip(parts, offs):
        q = p.resize((int(p.size[0] * sc), int(p.size[1] * sc)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
        base.paste(q, (PAD, PAD + int(yy * sc)))
    # map highlight boxes (source coords) into card coords via the crop they sit in
    rects = []
    for hx0, hy0, hx1, hy1 in hls:
        for b, yy in offs:
            if b[0] <= hx0 and b[1] <= hy0 and hy1 <= b[3] + 4:
                X0 = PAD + (hx0 - b[0]) * sc; X1 = PAD + (hx1 - b[0]) * sc
                Y0 = PAD + (yy + hy0 - b[1]) * sc; Y1 = PAD + (yy + hy1 - b[1]) * sc
                rects.append((X0, Y0, X1, Y1)); break
    d = f"{N}{name}_frames"
    os.makedirs(d, exist_ok=True)
    nf, t_start, sweep = int(DUR * FPS), 0.4, 0.32
    for f in range(nf):
        t = f / FPS
        hl = Image.new("RGB", base.size, (255, 255, 255))
        dr = ImageDraw.Draw(hl)
        for k, (X0, Y0, X1, Y1) in enumerate(rects):
            a = (t - t_start - k * sweep) / sweep
            if a <= 0:
                continue
            a = min(1.0, a); a = 1 - (1 - a) ** 3
            pad = (Y1 - Y0) * 0.12
            dr.rounded_rectangle((X0 - 10, Y0 - pad, X0 - 10 + (X1 - X0 + 20) * a, Y1 + pad * 0.6), radius=12, fill=YEL)
        ImageChops.multiply(base, hl).save(f"{d}/f{f:04d}.png")
    out = f"{N}{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{d}/f%04d.png", "-c:v", "libx264", "-crf", "12",
                    "-pix_fmt", "yuv420p", out], check=True)
    ImageChops.multiply(base, hl).save(f"{N}{name}_final.png")
    print(name, base.size, len(rects), "highlights ->", out)


for k, v in CARDS.items():
    if len(sys.argv) < 2 or k in sys.argv[1:]:
        build(k, *v)
