"""Build the 100-piece PNG pack: 70 commonly used emojis (Google Noto Emoji, Apache-2.0, 512 px)
+ 30 editor overlays drawn here (arrows, rings, X / check, banners, bubbles, bursts, frames, vignette...).

    python fetch_png_pack.py                     # -> D:/TarZo/Edits/Assets/PNG/emoji_pack + PNG/editor
    python fetch_png_pack.py --out D:/X/PNG

Everything is transparent PNG. Writes <out>/pack_index.json (name -> file, kind, use-for).
Emoji: https://github.com/googlefonts/noto-emoji (png/512). Editor PNGs are drawn at 4x and downsampled (clean edges).
"""
import argparse, json, math, os, random, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

EMOJI = {  # name: codepoints (Noto file naming, no fe0f)
    "joy": "1f602", "rofl": "1f923", "sob": "1f62d", "flushed": "1f633", "mind_blown": "1f92f", "cool": "1f60e",
    "heart_eyes": "1f60d", "hot_face": "1f975", "cold_face": "1f976", "huffing": "1f624", "clown": "1f921",
    "eye_roll": "1f644", "smirk": "1f60f", "salute": "1fae1", "grimace": "1f62c", "holding_tears": "1f979",
    "open_mouth": "1f62e", "cursing": "1f92c", "devil": "1f608", "melting": "1fae0", "shush": "1f92b",
    "partying": "1f973", "thumbs_up": "1f44d", "thumbs_down": "1f44e", "clap": "1f44f", "raised_hands": "1f64c",
    "point_right": "1f449", "point_left": "1f448", "point_up": "1f446", "point_at_you": "1faf5",
    "fingers_crossed": "1f91e", "collision": "1f4a5", "lightning": "26a1", "star": "2b50", "glowing_star": "1f31f",
    "sparkles": "2728", "anger": "1f4a2", "speech": "1f4ac", "question": "2753", "exclamation": "2757",
    "siren": "1f6a8", "megaphone": "1f4e2", "dollar": "1f4b5", "coin": "1fa99", "bar_chart": "1f4ca", "key": "1f511",
    "lock": "1f512", "camera_flash": "1f4f8", "gift": "1f381", "ring": "1f48d", "bride": "1f470",
    "couple_heart": "1f491", "kiss": "1f48b", "detective": "1f575", "magnifier": "1f50d", "globe": "1f30d",
    "flag_us": "1f1fa_1f1f8", "flag_bd": "1f1e7_1f1e9", "flag_cn": "1f1e8_1f1f3", "airplane": "2708",
    "race_car": "1f3ce", "house": "1f3e0", "soccer": "26bd", "slot_machine": "1f3b0", "bomb": "1f4a3",
    "robot": "1f916", "popcorn": "1f37f", "moai": "1f5ff", "red_circle": "1f534", "green_circle": "1f7e2",
}
NOTO = "https://fonts.gstatic.com/s/e/notoemoji/latest/{}/512.png"  # Noto Emoji (Apache-2.0), Google Fonts CDN

RED, GREEN, YEL, WHITE, BLACK, BLUE = (235, 30, 40), (20, 200, 90), (255, 214, 0), (255, 255, 255), (0, 0, 0), (29, 155, 240)
S = 4  # supersample


def font(size):
    for p in [os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\Anton-Regular.ttf"),
              r"C:\Windows\Fonts\Anton-Regular.ttf", r"C:\Windows\Fonts\impact.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def done(im, w, h, shadow=True):
    im = im.resize((w, h), Image.LANCZOS)
    if not shadow:
        return im
    a = im.split()[3].filter(ImageFilter.GaussianBlur(10))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * 0.45)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (6, 10))
    out.alpha_composite(im)
    return out


def arrow(d, x0, y0, x1, y1, col, wdt):
    d.line([(x0, y0), (x1, y1)], fill=col, width=wdt)
    ang = math.atan2(y1 - y0, x1 - x0)
    L = wdt * 2.6
    p1 = (x1 + math.cos(ang) * wdt, y1 + math.sin(ang) * wdt)
    p2 = (x1 - L * math.cos(ang - 0.6), y1 - L * math.sin(ang - 0.6))
    p3 = (x1 - L * math.cos(ang + 0.6), y1 - L * math.sin(ang + 0.6))
    d.polygon([p1, p2, p3], fill=col)


def text_center(d, box, txt, size, col):
    f = font(size)
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    x = box[0] + (box[2] - box[0] - (r - l)) / 2 - l
    y = box[1] + (box[3] - box[1] - (b - t)) / 2 - t
    d.text((x, y), txt, font=f, fill=col)


def editor_pngs():
    out = {}
    W = 1024
    # 1 ring
    im = canvas(W, W); d = ImageDraw.Draw(im)
    d.ellipse([60 * S, 60 * S, 964 * S, 964 * S], outline=RED, width=48 * S)
    out["red_ring"] = (done(im, W, W), "circle a face / number / chart level")
    # 2 hand-drawn ring
    im = canvas(W, W); d = ImageDraw.Draw(im); random.seed(3)
    pts = []
    for i in range(0, 400):
        a = i / 360 * 2 * math.pi * 1.08
        r = 430 + 18 * math.sin(i / 23) + random.uniform(-3, 3)
        pts.append((512 * S + r * S * math.cos(a), 512 * S + r * 0.82 * S * math.sin(a)))
    d.line(pts, fill=RED, width=34 * S, joint="curve")
    out["red_ring_scribble"] = (done(im, W, W), "hand-drawn circle highlight")
    # 3-6 straight arrows
    for nm, (a, b, c, e) in {"right": (120, 512, 900, 512), "left": (900, 512, 120, 512),
                              "up": (512, 900, 512, 120), "down": (512, 120, 512, 900)}.items():
        im = canvas(W, W); d = ImageDraw.Draw(im)
        arrow(d, a * S, b * S, c * S, e * S, RED, 70 * S)
        out[f"red_arrow_{nm}"] = (done(im, W, W), "point at something")
    # 7 curved arrow
    im = canvas(W, W); d = ImageDraw.Draw(im)
    pts = [(150 * S + t * 600 * S, 820 * S - math.sin(t * math.pi * 0.9) * 560 * S) for t in [i / 60 for i in range(61)]]
    d.line(pts[:-4], fill=RED, width=56 * S, joint="curve")
    arrow(d, pts[-8][0], pts[-8][1], pts[-1][0], pts[-1][1], RED, 56 * S)
    out["red_arrow_curved"] = (done(im, W, W), "swooping pointer")
    # 8 underline brush
    im = canvas(1600, 260); d = ImageDraw.Draw(im)
    pts = [(60 * S + t * 1480 * S, 150 * S + math.sin(t * 7) * 18 * S - t * 40 * S) for t in [i / 80 for i in range(81)]]
    d.line(pts, fill=YEL, width=60 * S, joint="curve")
    out["underline_yellow"] = (done(im, 1600, 260), "underline a word")
    # 9 X / 10 check
    im = canvas(W, W); d = ImageDraw.Draw(im)
    d.line([(170 * S, 170 * S), (854 * S, 854 * S)], fill=RED, width=150 * S)
    d.line([(854 * S, 170 * S), (170 * S, 854 * S)], fill=RED, width=150 * S)
    out["big_x_red"] = (done(im, W, W), "wrong / myth / don't")
    im = canvas(W, W); d = ImageDraw.Draw(im)
    d.line([(150 * S, 540 * S), (410 * S, 810 * S), (880 * S, 210 * S)], fill=GREEN, width=150 * S, joint="curve")
    out["big_check_green"] = (done(im, W, W), "correct / do this")
    # 11 marker highlight
    im = canvas(1600, 300); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20 * S, 40 * S, 1580 * S, 260 * S], radius=40 * S, fill=(255, 230, 0, 150))
    out["highlight_marker"] = (done(im, 1600, 300, shadow=False), "behind a word (multiply-like highlight)")
    # 12 speech bubble / 13 thought bubble
    im = canvas(1400, 1000); d = ImageDraw.Draw(im)
    d.rounded_rectangle([40 * S, 40 * S, 1360 * S, 720 * S], radius=120 * S, fill=WHITE)
    d.polygon([(300 * S, 700 * S), (520 * S, 700 * S), (220 * S, 960 * S)], fill=WHITE)
    out["speech_bubble"] = (done(im, 1400, 1000), "quote / what someone said")
    im = canvas(1400, 1000); d = ImageDraw.Draw(im)
    d.ellipse([60 * S, 40 * S, 1340 * S, 700 * S], fill=WHITE)
    for (x, y, r) in [(330, 790, 70), (220, 900, 42), (150, 965, 26)]:
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=WHITE)
    out["thought_bubble"] = (done(im, 1400, 1000), "thinking / imagine")
    # 14 breaking news banner / 15 LIVE / 16 subscribe
    im = canvas(1900, 300); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 640 * S, 300 * S], fill=RED)
    d.rectangle([640 * S, 0, 1900 * S, 300 * S], fill=WHITE)
    text_center(d, (0, 0, 640 * S, 300 * S), "BREAKING", 170 * S, WHITE)
    text_center(d, (640 * S, 0, 1900 * S, 300 * S), "NEWS", 190 * S, BLACK)
    out["breaking_news_banner"] = (done(im, 1900, 300), "news hook top bar")
    im = canvas(640, 260); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 640 * S, 260 * S], radius=40 * S, fill=RED)
    d.ellipse([60 * S, 90 * S, 140 * S, 170 * S], fill=WHITE)
    text_center(d, (160 * S, 0, 620 * S, 260 * S), "LIVE", 170 * S, WHITE)
    out["live_badge"] = (done(im, 640, 260), "live / happening now")
    im = canvas(1300, 330); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 1300 * S, 330 * S], radius=60 * S, fill=RED)
    text_center(d, (0, 0, 1300 * S, 330 * S), "SUBSCRIBE", 200 * S, WHITE)
    out["subscribe_button"] = (done(im, 1300, 330), "CTA end card")
    # 17 comic starburst / 18 explosion burst
    for nm, col, inner, spikes in [("starburst_yellow", YEL, None, 18), ("explosion_burst", (255, 120, 0), YEL, 14)]:
        im = canvas(W, W); d = ImageDraw.Draw(im); random.seed(spikes)
        pts = []
        for i in range(spikes * 2):
            a = i / (spikes * 2) * 2 * math.pi
            r = (480 if i % 2 == 0 else 300) + random.uniform(-40, 30)
            pts.append((512 * S + r * S * math.cos(a), 512 * S + r * S * math.sin(a)))
        d.polygon(pts, fill=col)
        if inner:
            d.polygon([(512 * S + (p[0] - 512 * S) * 0.6, 512 * S + (p[1] - 512 * S) * 0.6) for p in pts], fill=inner)
        out[nm] = (done(im, W, W), "behind a number pop / impact")
    # 19 price tag
    im = canvas(1200, 600); d = ImageDraw.Draw(im)
    d.polygon([(220 * S, 40 * S), (1160 * S, 40 * S), (1160 * S, 560 * S), (220 * S, 560 * S), (40 * S, 300 * S)], fill=YEL)
    d.ellipse([150 * S, 260 * S, 230 * S, 340 * S], fill=(0, 0, 0, 0))
    out["price_tag"] = (done(im, 1200, 600), "put a price / number on it")
    # 20 verified badge
    im = canvas(W, W); d = ImageDraw.Draw(im); random.seed(1)
    pts = [(512 * S + (440 if i % 2 == 0 else 390) * S * math.cos(i / 32 * 2 * math.pi),
            512 * S + (440 if i % 2 == 0 else 390) * S * math.sin(i / 32 * 2 * math.pi)) for i in range(32)]
    d.polygon(pts, fill=BLUE)
    d.line([(300 * S, 530 * S), (450 * S, 680 * S), (740 * S, 360 * S)], fill=WHITE, width=90 * S, joint="curve")
    out["verified_badge"] = (done(im, W, W), "real / confirmed / official")
    # 21 notification badge
    im = canvas(600, 600); d = ImageDraw.Draw(im)
    d.ellipse([20 * S, 20 * S, 580 * S, 580 * S], fill=RED)
    text_center(d, (0, 0, 600 * S, 600 * S), "1", 380 * S, WHITE)
    out["notification_badge"] = (done(im, 600, 600), "new message / alert")
    # 22 crosshair
    im = canvas(W, W); d = ImageDraw.Draw(im)
    d.ellipse([140 * S, 140 * S, 884 * S, 884 * S], outline=RED, width=26 * S)
    d.ellipse([340 * S, 340 * S, 684 * S, 684 * S], outline=RED, width=18 * S)
    for a, b, c, e in [(512, 40, 512, 330), (512, 694, 512, 984), (40, 512, 330, 512), (694, 512, 984, 512)]:
        d.line([(a * S, b * S), (c * S, e * S)], fill=RED, width=22 * S)
    out["crosshair"] = (done(im, W, W), "target / lock on a person")
    # 23 play button
    im = canvas(1200, 840); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 1200 * S, 840 * S], radius=200 * S, fill=RED)
    d.polygon([(480 * S, 240 * S), (480 * S, 600 * S), (800 * S, 420 * S)], fill=WHITE)
    out["play_button"] = (done(im, 1200, 840), "video / watch this")
    # 24 cursor
    im = canvas(600, 800); d = ImageDraw.Draw(im)
    cur = [(60, 40), (60, 660), (210, 520), (320, 760), (420, 715), (310, 480), (510, 480)]
    d.polygon([(x * S, y * S) for x, y in cur], fill=BLACK)
    d.line([(x * S, y * S) for x, y in cur + [cur[0]]], fill=WHITE, width=26 * S, joint="curve")
    out["mouse_cursor"] = (done(im, 600, 800), "click / UI demo")
    # 25 progress bar
    im = canvas(1600, 200); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 40 * S, 1600 * S, 160 * S], radius=60 * S, fill=(255, 255, 255, 90), outline=WHITE, width=10 * S)
    d.rounded_rectangle([20 * S, 60 * S, 1150 * S, 140 * S], radius=40 * S, fill=GREEN)
    out["progress_bar"] = (done(im, 1600, 200, shadow=False), "loading / progress (crop or scale X to animate)")
    # 26 vignette / 27 bottom shade / 28 rec frame (full 2160x3840)
    FW, FH = 2160, 3840
    v = Image.new("L", (FW // 8, FH // 8), 0); dv = ImageDraw.Draw(v)
    dv.ellipse([-FW // 40, FH // 40, FW // 8 + FW // 40, FH // 8 - FH // 40], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(40)).resize((FW, FH), Image.BICUBIC)
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0)); im.putalpha(v.point(lambda p: int((255 - p) * 0.85)))
    out["vignette_2160x3840"] = (im, "full-frame dark edges")
    g = Image.new("L", (1, 256)); g.putdata([int(max(0, (i - 120) / 136) ** 1.4 * 235) for i in range(256)])
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0)); im.putalpha(g.resize((FW, FH), Image.BICUBIC))
    out["bottom_shade_2160x3840"] = (im, "behind lower captions")
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    m, L, t = 140, 320, 22
    for cx, cy, sx, sy in [(m, m, 1, 1), (FW - m, m, -1, 1), (m, FH - m, 1, -1), (FW - m, FH - m, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=WHITE, width=t)
        d.line([(cx, cy), (cx, cy + sy * L)], fill=WHITE, width=t)
    d.ellipse([m + 40, m + 60, m + 120, m + 140], fill=RED)
    d.text((m + 160, m + 40), "REC", font=font(110), fill=WHITE)
    out["rec_frame_2160x3840"] = (im, "camera / CCTV / exposed look")
    # 29/30 chart lines
    for nm, col, ys in [("chart_up_green", GREEN, [820, 700, 760, 560, 610, 380, 430, 200]),
                        ("chart_down_red", RED, [200, 330, 280, 500, 450, 650, 600, 840])]:
        im = canvas(1400, 1000); d = ImageDraw.Draw(im)
        xs = [80 + i * 170 for i in range(len(ys))]
        pts = [(x * S, y * S) for x, y in zip(xs, ys)]
        d.line(pts[:-1], fill=col, width=50 * S, joint="curve")
        arrow(d, pts[-2][0], pts[-2][1], pts[-1][0] + 60 * S, pts[-1][1] + (-60 if "up" in nm else 60) * S, col, 50 * S)
        out[nm] = (done(im, 1400, 1000), "price pumps / crashes")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/TarZo/Edits/Assets/PNG")
    a = ap.parse_args()
    root = Path(a.out)
    (root / "emoji_pack").mkdir(parents=True, exist_ok=True)
    (root / "editor").mkdir(parents=True, exist_ok=True)
    idx = []
    for name, cp in EMOJI.items():
        dst = root / "emoji_pack" / f"{name}.png"
        if not dst.exists():
            try:
                req = urllib.request.Request(NOTO.format(cp), headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    dst.write_bytes(r.read())
            except Exception as e:
                print("emoji fail", name, cp, e)
                continue
        idx.append({"name": name, "file": f"emoji_pack/{name}.png", "kind": "emoji", "source": "Noto Emoji (Apache-2.0)"})
    for name, (im, use) in editor_pngs().items():
        dst = root / "editor" / f"{name}.png"
        im.save(dst)
        idx.append({"name": name, "file": f"editor/{name}.png", "kind": "editor", "use": use, "size": list(im.size)})
    (root / "pack_index.json").write_text(json.dumps(idx, indent=1), encoding="utf-8")
    print(len([i for i in idx if i["kind"] == "emoji"]), "emoji +", len([i for i in idx if i["kind"] == "editor"]), "editor PNGs")


if __name__ == "__main__":
    main()
