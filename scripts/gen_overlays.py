"""Generate transparent overlay effects that stock sites don't have on black (ProRes 4444 with alpha, 1080x1920, 25 fps).

    python gen_overlays.py              -> D:/TarZo/Edits/Assets/Effects/generated/*.mov (+ index.json entries)

confetti_burst / confetti_fall  - coloured paper bits
money_rain / coin_rain          - falling dollar-bill / coin emoji sprites (Assets/PNG/emoji_pack)
white_flash / red_flash         - 0.5 s flash (white = hit, red = loss / crash)
Normal blend (alpha) in Premiere, scale 200 % to fill the 2160x3840 reel.
"""
import json, math, random, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

W, H, FPS = 1080, 1920, 25
ROOT = Path("D:/TarZo/Edits/Assets")
OUT = ROOT / "Effects" / "generated"
COLS = [(255, 59, 48), (255, 204, 0), (52, 199, 89), (0, 122, 255), (175, 82, 222), (255, 149, 0), (255, 255, 255)]


def writer(path, n):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-frames:v", str(n), "-c:v", "prores_ks", "-profile:v", "4444",
                             "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", str(path)], stdin=subprocess.PIPE)


def particles(path, secs, n, spawn, sprite=None, size=(18, 34), seed=1):
    random.seed(seed)
    frames = int(secs * FPS)
    ps = [spawn() for _ in range(n)]
    for p in ps:
        p["w"] = random.uniform(*size)
        p["c"] = random.choice(COLS)
        p["rot"] = random.uniform(0, 360)
        p["vr"] = random.uniform(-14, 14)
        p["ph"] = random.uniform(0, 6.28)
    spr = {}
    pr = writer(path, frames)
    for f in range(frames):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for p in ps:
            if f < p.get("t0", 0):
                continue
            p["vy"] += p.get("g", 0.6)
            p["vx"] *= p.get("drag", 0.985)
            p["vy"] = min(p["vy"], p.get("vmax", 14))
            p["x"] += p["vx"] + math.sin(f / 6 + p["ph"]) * p.get("wob", 1.5)
            p["y"] += p["vy"]
            p["rot"] += p["vr"]
            if not (-200 < p["x"] < W + 200 and -400 < p["y"] < H + 200):
                continue
            if sprite:
                k = int(p["w"])
                if k not in spr:
                    spr[k] = sprite.resize((k, k), Image.LANCZOS)
                s = spr[k].rotate(p["rot"], expand=True, resample=Image.BICUBIC)
                im.alpha_composite(s, (int(p["x"] - s.width / 2), int(p["y"] - s.height / 2)))
            else:
                w, h = p["w"], p["w"] * 0.55 * abs(math.cos(math.radians(p["rot"] * 1.7))) + 3
                piece = Image.new("RGBA", (int(w) + 2, int(h) + 2), p["c"] + (255,))
                piece = piece.rotate(p["rot"], expand=True)
                im.alpha_composite(piece, (int(p["x"]), int(p["y"])))
        pr.stdin.write(im.tobytes())
    pr.stdin.close()
    pr.wait()


def flash(path, col, secs=0.5, peak=0.08):
    frames = int(secs * FPS)
    pr = writer(path, frames)
    for f in range(frames):
        t = f / FPS
        a = t / peak if t < peak else max(0.0, 1 - (t - peak) / (secs - peak)) ** 1.6
        pr.stdin.write(Image.new("RGBA", (W, H), col + (int(255 * a),)).tobytes())
    pr.stdin.close()
    pr.wait()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    emo = ROOT / "PNG" / "emoji_pack"
    jobs = {
        "confetti_burst": lambda p: particles(p, 3.0, 420, lambda: {
            "x": W / 2 + random.uniform(-60, 60), "y": H * 0.62, "vx": random.uniform(-26, 26),
            "vy": random.uniform(-52, -18), "g": 1.3, "drag": 0.96, "vmax": 9, "t0": random.randint(0, 3)}),
        "confetti_fall": lambda p: particles(p, 4.0, 260, lambda: {
            "x": random.uniform(0, W), "y": random.uniform(-1900, -20), "vx": random.uniform(-1, 1),
            "vy": random.uniform(6, 11), "g": 0.0, "vmax": 12, "wob": 2.5}, seed=2),
        "money_rain": lambda p: particles(p, 4.0, 70, lambda: {
            "x": random.uniform(0, W), "y": random.uniform(-1400, H * 0.6), "vx": random.uniform(-1.5, 1.5),
            "vy": random.uniform(9, 15), "g": 0.0, "vmax": 16, "wob": 3}, Image.open(emo / "dollar.png").convert("RGBA"),
            size=(120, 230), seed=3),
        "coin_rain": lambda p: particles(p, 4.0, 80, lambda: {
            "x": random.uniform(0, W), "y": random.uniform(-1400, H * 0.6), "vx": random.uniform(-1, 1),
            "vy": random.uniform(12, 20), "g": 0.2, "vmax": 24, "wob": 0.5}, Image.open(emo / "coin.png").convert("RGBA"),
            size=(80, 150), seed=4),
        "white_flash": lambda p: flash(p, (255, 255, 255)),
        "red_flash": lambda p: flash(p, (255, 20, 30), 0.6, 0.06),
    }
    idx_p = ROOT / "Effects" / "index.json"
    idx = json.loads(idx_p.read_text(encoding="utf-8"))
    for name, fn in jobs.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]:
            continue
        dst = OUT / f"{name}.mov"
        fn(dst)
        rel = f"generated/{name}.mov"
        idx = [e for e in idx if e["file"] != rel]
        dur = {"white_flash": 0.5, "red_flash": 0.6}.get(name, 4.0 if "rain" in name or "fall" in name else 3.0)
        idx.append({"category": "generated", "query": name, "file": rel, "id": "gen_" + name, "source": "generated",
                    "by": "gen_overlays.py", "page": "", "w": W, "h": H, "dur": dur, "alpha": True})
        print(rel, dst.stat().st_size // 1024, "KB")
    idx_p.write_text(json.dumps(idx, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
