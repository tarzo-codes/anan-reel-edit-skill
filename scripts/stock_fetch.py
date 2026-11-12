"""Pexels & Pixabay Stock Video/Photo Search & Downloader (`stock_fetch.py`).

Shared asset fetcher for Claude and Antigravity in `shorts-editor-skill`.
Searches and downloads high-resolution stock videos and photos directly into `E:/Anan/Assets/`
and prints exact `(filename, width, height, duration)` ready for `reelkit.py` (`r.card` / `r.full`).

Supports TWO automatic modes per provider:
  1. Official REST API when `PEXELS_API_KEY` / `PIXABAY_API_KEY` are set (env or `E:/Anan/.env`).
  2. Zero-key Chrome-TLS fallback (`curl_cffi` impersonation) when no API keys are configured!

CLI Examples:
  # Search local `references/stock.md` first + search Pexels & Pixabay:
  python stock_fetch.py "gym workout" --orientation portrait --limit 4

  # Download top 1 matching clip to E:/Anan/Assets and register in references/stock.md:
  python stock_fetch.py "gym workout" --orientation portrait --download --limit 1 --use-for "gym, fitness, body"

  # Download horizontal card B-roll from Pixabay or Pexels:
  python stock_fetch.py "esports gaming phone" --source both --orientation landscape --download --limit 1
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, quote_plus

SKILL_ROOT = Path(__file__).resolve().parent.parent
STOCK_MD = SKILL_ROOT / "references" / "stock.md"
DEFAULT_ASSETS_DIR = Path("E:/Anan/Assets")
ENV_CANDIDATES = [
    Path("E:/Anan/.env"),
    Path.home() / ".claude" / ".env",
    Path.home() / ".gemini" / ".env",
]


def _load_env_keys() -> dict[str, str]:
    env = dict(os.environ)
    for p in ENV_CANDIDATES:
        if p.exists():
            for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip("'\""))
    return env


def _http_get(url: str, headers: dict[str, str] | None = None, timeout: int = 20):
    try:
        import curl_cffi.requests as creq
        return creq.get(url, headers=headers or {}, impersonate="chrome", timeout=timeout, allow_redirects=True)
    except ImportError:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()

            class _Resp:
                status_code = resp.status
                content = body
                text = body.decode("utf-8", errors="replace")

                def json(self):
                    return json.loads(self.text)

            return _Resp()


def _http_head_ok(url: str, timeout: int = 10) -> bool:
    try:
        import curl_cffi.requests as creq
        r = creq.head(url, impersonate="chrome", timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return True
        if r.status_code in (403, 405):
            r2 = creq.get(url, headers={"Range": "bytes=0-1023"}, impersonate="chrome", timeout=timeout, allow_redirects=True)
            return r2.status_code in (200, 206)
        return False
    except Exception:
        return False


def _download_binary(url: str, dest: Path, timeout: int = 120) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    referer = "https://pixabay.com/" if "pixabay" in url else "https://www.pexels.com/"
    hdrs = {"Referer": referer}
    try:
        import curl_cffi.requests as creq
        r = creq.get(url, headers=hdrs, impersonate="chrome", stream=True, timeout=timeout, allow_redirects=True)
        try:
            if r.status_code not in (200, 206):
                raise RuntimeError(f"HTTP {r.status_code} downloading {url}")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content():
                    if chunk:
                        f.write(chunk)
        finally:
            if hasattr(r, "close"):
                r.close()
    except ImportError:
        r = _http_get(url, headers=hdrs, timeout=timeout)
        if r.status_code not in (200, 206):
            raise RuntimeError(f"HTTP {r.status_code} downloading {url}")
        tmp.write_bytes(r.content)
    tmp.replace(dest)
    return dest


def _ffprobe_bin() -> str:
    found = shutil.which("ffprobe")
    if found:
        return found
    for fb in (
        Path("C:/Program Files/Unified Media Studio/ffmpeg/bin/ffprobe.exe"),
        Path("C:/ffmpeg/bin/ffprobe.exe"),
    ):
        if fb.exists():
            return str(fb)
    return "ffprobe"


def probe_media(path: Path) -> dict:
    """Return exact width, height, duration, fps for a video or image using ffprobe / PIL."""
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp"):
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        return {"width": w, "height": h, "duration": 0.0, "fps": 0.0, "orientation": "v" if h > w else "h"}

    cmd = [
        _ffprobe_bin(), "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration",
        "-of", "json",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {"width": 0, "height": 0, "duration": 0.0, "fps": 0.0, "orientation": "?"}
    info = json.loads(res.stdout or "{}")
    st = (info.get("streams") or [{}])[0]
    fmt = info.get("format") or {}
    w = int(st.get("width") or 0)
    h = int(st.get("height") or 0)
    dur = round(float(fmt.get("duration") or 0.0), 2)
    fps_raw = st.get("r_frame_rate", "0/1")
    try:
        num, den = fps_raw.split("/")
        fps = round(float(num) / max(1.0, float(den)), 2)
    except Exception:
        fps = 0.0
    return {"width": w, "height": h, "duration": dur, "fps": fps, "orientation": "v" if h > w else "h"}


def search_local_stock(query: str) -> list[dict]:
    """Search `references/stock.md` for already-downloaded clips matching `query` keywords."""
    if not STOCK_MD.exists():
        return []
    words = [w.lower() for w in re.split(r"\W+", query) if len(w) >= 2]
    hits = []
    for line in STOCK_MD.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("|") or line.startswith("| file") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 4:
            continue
        fname, orient, shows, use_for = cols[0], cols[1], cols[2], cols[3]
        hay = f"{shows} {use_for} {fname}".lower()
        score = sum(2 if w in use_for.lower() else 1 for w in words if w in hay)
        if score > 0:
            fpath = DEFAULT_ASSETS_DIR / fname
            hits.append({
                "source": "local",
                "file": fname,
                "exists": fpath.exists(),
                "orientation": orient,
                "shows": shows,
                "use_for": use_for,
                "score": score,
            })
    hits.sort(key=lambda x: x["score"], reverse=True)
    return hits


def _matches_orientation(w: int, h: int, orientation: str) -> bool:
    if orientation == "any" or not w or not h:
        return True
    if orientation == "portrait":
        return h > w
    if orientation == "landscape":
        return w >= h
    return True


def _parse_iso_duration(iso_str: str) -> float:
    if not iso_str:
        return 0.0
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", str(iso_str))
    if not m:
        return 0.0
    hrs = float(m.group(1) or 0)
    mins = float(m.group(2) or 0)
    secs = float(m.group(3) or 0)
    return round(hrs * 3600 + mins * 60 + secs, 2)


# ---------------------------------------------------------------------------
# PEXELS (API + Keyless `__NEXT_DATA__` fallback)
# ---------------------------------------------------------------------------
def search_pexels(query: str, media_type: str = "video", orientation: str = "any", limit: int = 6, api_key: str = "") -> list[dict]:
    results: list[dict] = []
    q_enc = quote_plus(query)
    orient_param = f"&orientation={orientation}" if orientation in ("portrait", "landscape") else ""

    if api_key:
        if media_type == "video":
            url = f"https://api.pexels.com/videos/search?query={q_enc}&per_page={limit * 2}{orient_param}"
            r = _http_get(url, headers={"Authorization": api_key})
            if r.status_code == 200:
                for v in r.json().get("videos", []):
                    files = sorted(
                        [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width")],
                        key=lambda f: abs(min(f["width"], f["height"]) - 1080),
                    )
                    if not files:
                        continue
                    best = files[0]
                    w, h = int(best.get("width") or v.get("width") or 0), int(best.get("height") or v.get("height") or 0)
                    if not _matches_orientation(w, h, orientation):
                        continue
                    results.append({
                        "source": "pexels",
                        "id": str(v["id"]),
                        "type": "video",
                        "title": (v.get("url") or "").rstrip("/").split("/")[-1].replace("-", " "),
                        "width": w,
                        "height": h,
                        "duration": float(v.get("duration") or 0),
                        "download_url": best["link"],
                        "ext": ".mp4",
                    })
                if results:
                    return results[:limit]
        else:
            url = f"https://api.pexels.com/v1/search?query={q_enc}&per_page={limit * 2}{orient_param}"
            r = _http_get(url, headers={"Authorization": api_key})
            if r.status_code == 200:
                for p in r.json().get("photos", []):
                    w, h = int(p.get("width") or 0), int(p.get("height") or 0)
                    if not _matches_orientation(w, h, orientation):
                        continue
                    src = p.get("src") or {}
                    dl = src.get("large2x") or src.get("original")
                    if dl:
                        results.append({
                            "source": "pexels",
                            "id": str(p["id"]),
                            "type": "image",
                            "title": p.get("alt") or query,
                            "width": w,
                            "height": h,
                            "duration": 0.0,
                            "download_url": dl,
                            "ext": ".jpg",
                        })
                if results:
                    return results[:limit]

    # Keyless Pexels search via Chrome-TLS + __NEXT_DATA__
    q_path = quote(query)
    orient_q = f"?orientation={orientation}" if orientation in ("portrait", "landscape") else ""
    web_url = (
        f"https://www.pexels.com/search/videos/{q_path}/{orient_q}"
        if media_type == "video"
        else f"https://www.pexels.com/search/{q_path}/{orient_q}"
    )
    r = _http_get(web_url)
    if r.status_code != 200:
        return results
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m:
        return results
    data = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("initialData", {}).get("data", [])
    for item in data:
        attrs = item.get("attributes") or item
        iid = str(attrs.get("id") or item.get("id") or "")
        if not iid:
            continue
        w = int(attrs.get("width") or 0)
        h = int(attrs.get("height") or 0)
        if not _matches_orientation(w, h, orientation):
            continue
        title = attrs.get("title") or attrs.get("description") or (attrs.get("slug") or "").replace("-", " ") or query
        if media_type == "video":
            vid = attrs.get("video") or {}
            dl = vid.get("src")
            if not dl:
                continue
            # Extract actual resolution from Pexels filename if present (e.g. _1080_1920_30fps.mp4 or _2160_3840_25fps.mp4)
            rm = re.search(r"_(\d{3,4})_(\d{3,4})_\d+fps\.mp4", dl)
            if rm:
                w, h = int(rm.group(1)), int(rm.group(2))
            dur = float(attrs.get("duration") or vid.get("duration") or 0.0)
            results.append({
                "source": "pexels",
                "id": iid,
                "type": "video",
                "title": title[:90],
                "width": w,
                "height": h,
                "duration": dur,
                "download_url": dl,
                "ext": ".mp4",
            })
        else:
            img = attrs.get("image") or {}
            dl = None
            if isinstance(img, dict):
                dl = img.get("large") or img.get("medium") or img.get("download_link")
            if not dl:
                dl = f"https://images.pexels.com/photos/{iid}/pexels-photo-{iid}.jpeg?auto=compress&cs=tinysrgb&w=2160"
            results.append({
                "source": "pexels",
                "id": iid,
                "type": "image",
                "title": title[:90],
                "width": w,
                "height": h,
                "duration": 0.0,
                "download_url": dl,
                "ext": ".jpg",
            })
        if len(results) >= limit:
            break
    return results


# ---------------------------------------------------------------------------
# PIXABAY (API + Keyless JSON-LD `VideoObject` / `ImageObject` fallback)
# ---------------------------------------------------------------------------
def search_pixabay(query: str, media_type: str = "video", orientation: str = "any", limit: int = 6, api_key: str = "") -> list[dict]:
    results: list[dict] = []
    q_enc = quote_plus(query)

    if api_key:
        if media_type == "video":
            url = f"https://pixabay.com/api/videos/?key={api_key}&q={q_enc}&per_page={max(10, limit * 3)}"
            r = _http_get(url)
            if r.status_code == 200:
                for hit in r.json().get("hits", []):
                    vids = hit.get("videos") or {}
                    cand = vids.get("large") or vids.get("medium") or vids.get("small") or {}
                    dl = cand.get("url")
                    w, h = int(cand.get("width") or 0), int(cand.get("height") or 0)
                    if not dl or not _matches_orientation(w, h, orientation):
                        continue
                    results.append({
                        "source": "pixabay",
                        "id": str(hit["id"]),
                        "type": "video",
                        "title": hit.get("tags") or query,
                        "width": w,
                        "height": h,
                        "duration": float(hit.get("duration") or 0),
                        "download_url": dl,
                        "ext": ".mp4",
                    })
                    if len(results) >= limit:
                        return results
        else:
            ori = "vertical" if orientation == "portrait" else ("horizontal" if orientation == "landscape" else "all")
            url = f"https://pixabay.com/api/?key={api_key}&q={q_enc}&image_type=photo&orientation={ori}&per_page={max(10, limit * 2)}"
            r = _http_get(url)
            if r.status_code == 200:
                for hit in r.json().get("hits", []):
                    w, h = int(hit.get("imageWidth") or 0), int(hit.get("imageHeight") or 0)
                    dl = hit.get("largeImageURL") or hit.get("webformatURL")
                    if not dl or not _matches_orientation(w, h, orientation):
                        continue
                    results.append({
                        "source": "pixabay",
                        "id": str(hit["id"]),
                        "type": "image",
                        "title": hit.get("tags") or query,
                        "width": w,
                        "height": h,
                        "duration": 0.0,
                        "download_url": dl,
                        "ext": ".jpg",
                    })
                    if len(results) >= limit:
                        return results

    # Keyless Pixabay search via Chrome-TLS + JSON-LD schema objects
    q_px = quote(query)
    if media_type == "video":
        web_url = f"https://pixabay.com/videos/search/{q_px}/"
    else:
        ori_q = "?orientation=vertical" if orientation == "portrait" else ("?orientation=horizontal" if orientation == "landscape" else "")
        web_url = f"https://pixabay.com/images/search/{q_px}/{ori_q}"

    r = _http_get(web_url)
    if r.status_code != 200:
        return results

    ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', r.text, re.S)
    for raw in ld_blocks:
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        otype = obj.get("@type", "")
        if media_type == "video" and otype == "VideoObject":
            tiny_url = obj.get("contentUrl", "")
            if not tiny_url:
                continue
            w = int(obj.get("width") or 0)
            h = int(obj.get("height") or 0)
            if (w or h) and not _matches_orientation(w, h, orientation):
                continue
            id_m = re.search(r"/(\d+)(?:-\d+)?_tiny\.mp4", tiny_url)
            iid = id_m.group(1) if id_m else str(abs(hash(tiny_url)) % 10000000)
            # Upgrade Pixabay CDN URL from _tiny.mp4 -> _large.mp4 (fallback _medium.mp4)
            large_url = tiny_url.replace("_tiny.mp4", "_large.mp4")
            med_url = tiny_url.replace("_tiny.mp4", "_medium.mp4")
            results.append({
                "source": "pixabay",
                "id": iid,
                "type": "video",
                "title": (obj.get("name") or obj.get("description") or query)[:90],
                "width": w,
                "height": h,
                "duration": _parse_iso_duration(obj.get("duration", "")),
                "download_url": large_url,
                "fallback_url": med_url,
                "tiny_url": tiny_url,
                "ext": ".mp4",
            })
        elif media_type == "image" and otype == "ImageObject":
            c_url = obj.get("contentUrl", "")
            if not c_url:
                continue
            w = int(str(obj.get("width") or "0").replace("px", "").strip() or 0)
            h = int(str(obj.get("height") or "0").replace("px", "").strip() or 0)
            if (w or h) and not _matches_orientation(w, h, orientation):
                continue
            id_m = re.search(r"-(\d+)_\d+\.", c_url) or re.search(r"/(\d+)_", c_url)
            iid = id_m.group(1) if id_m else str(abs(hash(c_url)) % 10000000)
            results.append({
                "source": "pixabay",
                "id": iid,
                "type": "image",
                "title": (obj.get("name") or obj.get("caption") or query)[:90],
                "width": w,
                "height": h,
                "duration": 0.0,
                "download_url": c_url,
                "ext": Path(c_url.split("?")[0]).suffix or ".jpg",
            })
        if len(results) >= limit * 2:
            break

    return results[: max(limit, 8)]


def fetch_stock(
    query: str,
    source: str = "both",
    media_type: str = "video",
    orientation: str = "any",
    limit: int = 3,
    min_dur: float = 0.0,
    max_dur: float = 120.0,
    download: bool = False,
    out_dir: Path = DEFAULT_ASSETS_DIR,
    use_for: str | None = None,
) -> dict:
    """Search local `stock.md` + Pexels + Pixabay, and optionally download top `limit` items to `out_dir`."""
    env = _load_env_keys()
    px_key = env.get("PEXELS_API_KEY", "")
    pb_key = env.get("PIXABAY_API_KEY", "")

    local_hits = search_local_stock(query)
    candidates: list[dict] = []

    if source in ("pexels", "both"):
        candidates.extend(search_pexels(query, media_type=media_type, orientation=orientation, limit=limit * 2, api_key=px_key))
    if source in ("pixabay", "both"):
        candidates.extend(search_pixabay(query, media_type=media_type, orientation=orientation, limit=limit * 2, api_key=pb_key))

    # Interleave Pexels and Pixabay when source == "both"
    if source == "both":
        px_list = [c for c in candidates if c["source"] == "pexels"]
        pb_list = [c for c in candidates if c["source"] == "pixabay"]
        merged = []
        for i in range(max(len(px_list), len(pb_list))):
            if i < len(px_list):
                merged.append(px_list[i])
            if i < len(pb_list):
                merged.append(pb_list[i])
        candidates = merged

    filtered = []
    for c in candidates:
        dur = c.get("duration") or 0.0
        if media_type == "video" and dur > 0 and (dur < min_dur or dur > max_dur):
            continue
        filtered.append(c)

    downloaded: list[dict] = []
    if download:
        for c in filtered:
            if len(downloaded) >= limit:
                break
            slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")[:24]
            fname = f"{c['source']}_{c['id']}_{slug}{c['ext']}"
            dest = out_dir / fname
            if not dest.exists():
                dl_url = c["download_url"]
                if c["source"] == "pixabay" and c.get("fallback_url") and not _http_head_ok(dl_url):
                    dl_url = c["fallback_url"] if _http_head_ok(c["fallback_url"]) else c.get("tiny_url", dl_url)
                try:
                    _download_binary(dl_url, dest)
                except Exception as exc:
                    c["download_error"] = str(exc)
                    continue

            meta = probe_media(dest)
            # Enforce exact orientation check post-probe (in case keyless Pixabay omitted width/height in JSON-LD)
            if not _matches_orientation(meta["width"], meta["height"], orientation):
                dest.unlink(missing_ok=True)
                continue

            rec = {
                **c,
                "file": dest.name,
                "path": str(dest).replace("\\", "/"),
                **meta,
            }
            if meta["orientation"] == "v":
                rec["reelkit_snippet"] = f'full(t0, t1, "{dest.name}", {meta["width"]}, {meta["height"]}, 1)'
            else:
                rec["reelkit_snippet"] = f'card(t0, t1, "{dest.name}", {meta["width"]}, {meta["height"]}, 1)'
            downloaded.append(rec)

            if use_for and STOCK_MD.exists():
                existing = STOCK_MD.read_text(encoding="utf-8", errors="ignore")
                if dest.name not in existing:
                    shows_clean = c["title"].replace("|", "-").strip()
                    row = f"| {dest.name} | {meta['orientation']} | {shows_clean} | {use_for} |\n"
                    with open(STOCK_MD, "a", encoding="utf-8") as sf:
                        if not existing.endswith("\n"):
                            sf.write("\n")
                        sf.write(row)

    return {
        "query": query,
        "local_matches": local_hits[:5],
        "remote_candidates": filtered[: limit * 2],
        "downloaded": downloaded,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Search & download Pexels + Pixabay stock B-roll/photos for Anan reels.")
    ap.add_argument("query", help="Search keywords (e.g. 'gym workout', 'luxury house', 'mobile gaming')")
    ap.add_argument("--source", choices=["both", "pexels", "pixabay", "local"], default="both")
    ap.add_argument("--type", dest="media_type", choices=["video", "image"], default="video")
    ap.add_argument("--orientation", choices=["any", "portrait", "landscape"], default="any")
    ap.add_argument("--limit", type=int, default=2, help="Number of assets to return/download (default: 2)")
    ap.add_argument("--min-dur", type=float, default=2.0, help="Minimum video duration in seconds")
    ap.add_argument("--max-dur", type=float, default=90.0, help="Maximum video duration in seconds")
    ap.add_argument("--download", action="store_true", help="Download matching file(s) into --out-dir")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    ap.add_argument("--use-for", type=str, default=None, help="If set with --download, append entry to references/stock.md")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = ap.parse_args()

    if args.source == "local":
        res = {"query": args.query, "local_matches": search_local_stock(args.query), "remote_candidates": [], "downloaded": []}
    else:
        res = fetch_stock(
            query=args.query,
            source=args.source,
            media_type=args.media_type,
            orientation=args.orientation,
            limit=args.limit,
            min_dur=args.min_dur,
            max_dur=args.max_dur,
            download=args.download,
            out_dir=args.out_dir,
            use_for=args.use_for,
        )

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print(f"=== STOCK SEARCH: {args.query!r} ({args.source}, {args.media_type}, {args.orientation}) ===")
    if res["local_matches"]:
        print("\n[Local `references/stock.md` Matches]")
        for m in res["local_matches"]:
            print(f"  - {m['file']} [{m['orientation']}] :: {m['shows']} (use for: {m['use_for']})")

    if args.download:
        print(f"\n[Downloaded {len(res['downloaded'])} file(s) -> {args.out_dir}]")
        for d in res["downloaded"]:
            print(f"  + {d['file']}  ({d['width']}x{d['height']}, {d['duration']}s, {d['fps']}fps) -> {d['reelkit_snippet']}")
        if not res["downloaded"]:
            errs = [c.get("download_error") for c in res["remote_candidates"] if c.get("download_error")]
            if errs:
                print(f"  ! Download error(s): {errs[0]}", file=sys.stderr)
    else:
        print(f"\n[Remote Candidates ({len(res['remote_candidates'])})]")
        for c in res["remote_candidates"][: args.limit * 2]:
            print(f"  * [{c['source']}:{c['id']}] {c['width']}x{c['height']} ({c.get('duration', 0)}s) :: {c['title']}")


if __name__ == "__main__":
    main()
