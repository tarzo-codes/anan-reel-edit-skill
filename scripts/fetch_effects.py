"""Download an overlay-effects pack (light leaks, film burns, glitch, flares, particles...) from Pexels (+ Pixabay fallback).

    python fetch_effects.py                      # default 50-clip pack -> D:/TarZo/Edits/Assets/Effects/<category>/
    python fetch_effects.py --out D:/X/Effects --only glitch,light_leak

Clips are mostly on black: put them on a track above the A-roll with blend mode Screen (or Add) in Premiere.
Keys: PEXELS_API_KEY / PIXABAY_API_KEY from env or ~/.claude/.env. Writes <out>/index.json (+ credits).
Reject a clip that is not on black: set "rejected": true on its index entry (file deleted) and rerun -
its id stays blacklisted and the category is refilled. Picks the mp4 rendition whose long side is closest to 1920 (keeps the pack ~1 GB, upscales fine as an overlay).
"""
import argparse, json, os, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

PACK = [  # (category, query, count)
    ("light_leak", "light leak overlay", 5),
    ("film_burn", "film burn transition", 4),
    ("lens_flare", "lens flare black background", 4),
    ("glitch", "glitch effect overlay", 4),
    ("vhs_static", "tv static noise", 4),
    ("film_dust", "film grain scratches overlay black", 3),
    ("smoke", "smoke overlay black background", 3),
    ("sparks", "fire sparks black background", 4),
    ("bokeh", "bokeh lights particles", 4),
    ("confetti", "confetti falling black background", 3),
    ("money_rain", "dollar bills falling black background", 2),
    ("lightning", "lightning storm night", 2),
    ("explosion", "explosion black background", 3),
    ("flash", "white light flash transition overlay", 2),
    ("rain_overlay", "rain black background", 2),
    ("snow_particles", "dust particles floating black background", 1),
]


def key(name):
    if os.environ.get(name):
        return os.environ[name]
    env = Path.home() / ".claude" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return ""


def jget(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def download(url, dst):
    tmp = dst.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    tmp.replace(dst)


def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(p)],
                         capture_output=True, text=True).stdout
    try:
        j = json.loads(out)
        s = j["streams"][0]
        return s["width"], s["height"], round(float(j["format"]["duration"]), 2)
    except Exception:
        return None


def pexels(q, n, k, seen):
    res = jget("https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": q, "per_page": 30}),
               {"Authorization": k})
    out = []
    for v in res.get("videos", []):
        if v["id"] in seen or v.get("duration", 0) < 3:
            continue
        files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")]
        if not files:
            continue
        best = min(files, key=lambda f: abs(max(f["width"], f["height"]) - 1920))
        out.append({"src": "pexels", "id": v["id"], "link": best["link"], "by": v["user"]["name"], "page": v["url"]})
        if len(out) >= n:
            break
    return out


def pixabay(q, n, k, seen):
    res = jget("https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": k, "q": q, "per_page": 30}))
    out = []
    for v in res.get("hits", []):
        pid = "px%d" % v["id"]
        if pid in seen:
            continue
        r = v["videos"].get("large") or v["videos"].get("medium")
        if not r or not r.get("url"):
            continue
        out.append({"src": "pixabay", "id": pid, "link": r["url"], "by": v.get("user", ""), "page": v["pageURL"]})
        if len(out) >= n:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/TarZo/Edits/Assets/Effects")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    idx_p = out / "index.json"
    idx = json.loads(idx_p.read_text(encoding="utf-8")) if idx_p.exists() else []
    seen = {e["id"] for e in idx}
    kp, kx = key("PEXELS_API_KEY"), key("PIXABAY_API_KEY")
    only = set(filter(None, a.only.split(",")))
    for cat, q, n in PACK:
        if only and cat not in only:
            continue
        have = sum(1 for e in idx if e["category"] == cat and not e.get("rejected"))
        need = n - have
        if need <= 0:
            continue
        cands = []
        try:
            if kp:
                cands += pexels(q, need, kp, seen)
        except Exception as e:
            print("pexels fail", cat, e)
        if len(cands) < need and kx:
            try:
                cands += pixabay(q, need - len(cands), kx, seen)
            except Exception as e:
                print("pixabay fail", cat, e)
        (out / cat).mkdir(exist_ok=True)
        for c in cands[:need]:
            dst = out / cat / f"{cat}_{c['src']}_{c['id']}.mp4"
            try:
                if not dst.exists():
                    download(c["link"], dst)
                pr = probe(dst)
                e = {"category": cat, "query": q, "file": str(dst.relative_to(out)).replace("\\", "/"),
                     "id": c["id"], "source": c["src"], "by": c["by"], "page": c["page"],
                     "w": pr[0] if pr else None, "h": pr[1] if pr else None, "dur": pr[2] if pr else None}
                idx.append(e)
                seen.add(c["id"])
                idx_p.write_text(json.dumps(idx, indent=1, ensure_ascii=False), encoding="utf-8")
                print(f"{len(idx):3d}  {e['file']}  {e['w']}x{e['h']} {e['dur']}s", flush=True)
            except Exception as ex:
                print("download fail", dst.name, ex, flush=True)
        time.sleep(0.5)
    cred = ["# Effects pack credits", "", "Pexels / Pixabay licence: free to use, no attribution required (credited anyway).", ""]
    cred += [f"- `{e['file']}` - {e['by']} ({e['source']}) {e['page']}" for e in idx if not e.get("rejected")]
    (out / "CREDITS.md").write_text("\n".join(cred), encoding="utf-8")
    print("total", len(idx))


if __name__ == "__main__":
    main()
