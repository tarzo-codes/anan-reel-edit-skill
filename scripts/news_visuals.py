"""Pull real visuals for a reel that talks about NEWS or a named PERSON (no API keys needed).

    python news_visuals.py person "Jensen Huang" --n 4          # Wikipedia lead photo + Wikimedia Commons photos
    python news_visuals.py news "Jensen Huang divorce" --n 6     # latest articles: og:image, headline card, page capture
    python news_visuals.py all --person "Jensen Huang" --person "Lori Huang" --news "Jensen Huang affair Nvidia"

Output (default D:/TarZo/Edits/Assets/news, override with --out):
  faces/<slug>_<k>.jpg              person photos (Commons licences are listed in news_index.json -> credit them)
  <slug>/<k>_og.jpg                 the article's own share image (og:image)
  <slug>/<k>_card.png               1920-wide news card: share image + outlet + headline + date (ready for V-track)
  <slug>/<k>_page.png               headless-Edge capture of the article (1080x1920) -> crop with make_news.py if wanted
  news_index.json                   everything above with source URLs, outlet, date, licence

News source is Bing News RSS (direct publisher links). Read the headlines before using them: only put a claim on
screen that the articles actually make, and prefer cards from big outlets (Reuters, CNBC, Forbes, Bloomberg, BBC).
"""
import argparse, html, json, os, re, subprocess, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def fetch(url, binary=False, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        return data if binary else data.decode(r.headers.get_content_charset() or "utf-8", "replace")


def save_img(url, dst, min_side=300):
    try:
        data = fetch(url, binary=True)
        tmp = dst.with_suffix(".tmp")
        tmp.write_bytes(data)
        im = Image.open(tmp)
        im = ImageOps.exif_transpose(im).convert("RGB")
        if min(im.size) < min_side:
            tmp.unlink()
            return None
        im.save(dst, quality=95)
        tmp.unlink()
        return im.size
    except Exception as e:
        print("  img fail", url[:90], e)
        return None


# ---------------- people ----------------
def person(name, n, out):
    faces = out / "faces"
    faces.mkdir(parents=True, exist_ok=True)
    got, s = [], slug(name)
    try:
        j = json.loads(fetch("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(name.replace(" ", "_"))))
        src = (j.get("originalimage") or j.get("thumbnail") or {}).get("source")
        if j.get("title", "").lower() != name.lower():  # redirected to someone else (e.g. spouse -> famous partner)
            print("  wikipedia redirects to", j.get("title"), "- skipped")
            src = None
        if src:
            dst = faces / f"{s}_wiki.jpg"
            size = save_img(src, dst)
            if size:
                got.append({"file": str(dst), "src": src, "page": j.get("content_urls", {}).get("desktop", {}).get("page"),
                            "licence": "see Wikipedia file page", "size": size, "desc": j.get("description")})
    except Exception as e:
        print("  wikipedia:", e)
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": f'"{name}" filetype:bitmap', "gsrlimit": 25, "prop": "imageinfo",
                                "iiprop": "url|extmetadata|size", "iiurlwidth": 1600})
    try:
        pages = json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + q)).get("query", {}).get("pages", {})
        for p in sorted(pages.values(), key=lambda p: p.get("index", 99)):
            if len(got) >= n:
                break
            ii = (p.get("imageinfo") or [{}])[0]
            if ii.get("width", 0) < 500 or re.search(r"\.(svg|pdf|tif)", p["title"], re.I):
                continue
            if not all(t in p["title"].lower() for t in name.lower().split()):  # file must name the person
                continue
            meta = ii.get("extmetadata", {})
            dst = faces / f"{s}_{len(got)}.jpg"
            size = save_img(ii.get("thumburl") or ii["url"], dst)
            if size:
                got.append({"file": str(dst), "src": ii["url"], "page": ii.get("descriptionurl"),
                            "licence": meta.get("LicenseShortName", {}).get("value"),
                            "author": re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:80], "size": size})
    except Exception as e:
        print("  commons:", e)
    for g in got:
        print(f"  {Path(g['file']).name}  {g['size']}  {g.get('licence')}")
    return {"person": name, "images": got}


# ---------------- news ----------------
def font(size, bold=True):
    for f in (["Anton-Regular.ttf"] if bold else []) + ["arialbd.ttf" if bold else "arial.ttf", "segoeuib.ttf"]:
        for d in [os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts"), r"C:\Windows\Fonts"]:
            p = os.path.join(d, f)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(d, txt, f, w):
    lines, cur = [], ""
    for word in txt.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= w:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def card(img_path, outlet, title, date, dst, W=1920):
    pad = 70
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fh, fo, fd = font(104, False), font(58), font(44, False)
    lines = wrap(d0, title, fh, W - 2 * pad)[:4]
    pic = None
    if img_path and Path(img_path).exists():
        pic = Image.open(img_path).convert("RGB")
        ph = int(W * 9 / 16)
        pic = ImageOps.fit(pic, (W, ph), Image.LANCZOS)
    H = (pic.size[1] if pic else 0) + pad + 70 + 30 + len(lines) * 124 + 40 + 50 + pad
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    y = 0
    if pic:
        im.paste(pic, (0, 0))
        y = pic.size[1]
    y += pad
    d.rectangle([pad, y + 6, pad + 14, y + 64], fill=(214, 20, 30))
    d.text((pad + 34, y), outlet.upper(), font=fo, fill=(214, 20, 30))
    y += 100
    for ln in lines:
        d.text((pad, y), ln, font=fh, fill=(15, 15, 15))
        y += 124
    d.text((pad, y + 30), date, font=fd, fill=(110, 110, 110))
    im.save(dst)


def capture(url, dst):
    edge = next((e for e in EDGE if os.path.exists(e)), None)
    if not edge:
        return False
    try:
        subprocess.run([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
                        f"--user-agent={UA}", "--window-size=1080,1920", f"--screenshot={dst}", url],
                       timeout=60, capture_output=True)
        return Path(dst).exists()
    except Exception:
        return False


def meta(htm, *names):
    for n in names:
        m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']+)' % re.escape(n), htm, re.I) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']%s["\']' % re.escape(n), htm, re.I)
        if m:
            return html.unescape(m.group(1))
    return None


def news(query, n, out, shots=True):
    s = slug(query)
    folder = out / s
    folder.mkdir(parents=True, exist_ok=True)
    rss = fetch("https://www.bing.com/news/search?" + urllib.parse.urlencode({"q": query, "format": "rss", "setlang": "en-us"}))
    items = []
    for it in ET.fromstring(rss).iter("item"):
        link = it.findtext("link") or ""
        m = re.search(r"[?&]url=([^&]+)", link)
        link = urllib.parse.unquote(m.group(1)) if m else link
        items.append({"title": html.unescape(it.findtext("title") or ""), "link": link,
                      "date": (it.findtext("pubDate") or "")[:16],
                      "outlet": it.findtext("{http://www.bing.com/schema/news}Source") or urllib.parse.urlparse(link).netloc})
    res = []
    for it in items:
        if len(res) >= n:
            break
        k = len(res)
        try:
            htm = fetch(it["link"])
        except Exception as e:
            print("  skip", it["outlet"], e)
            continue
        og = meta(htm, "og:image", "twitter:image")
        it["og_title"] = meta(htm, "og:title") or it["title"]
        it["outlet"] = meta(htm, "og:site_name") or it["outlet"]
        ogp = folder / f"{k}_og.jpg"
        it["og_image"] = str(ogp) if og and save_img(urllib.parse.urljoin(it["link"], og), ogp, 200) else None
        cp = folder / f"{k}_card.png"
        card(it["og_image"], it["outlet"], it["og_title"], it["date"], cp)
        it["card"] = str(cp)
        if shots:
            pp = folder / f"{k}_page.png"
            it["page_capture"] = str(pp) if capture(it["link"], str(pp)) else None
        res.append(it)
        print(f"  [{k}] {it['outlet']}: {it['og_title'][:90]}")
    return {"query": query, "articles": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["person", "news", "all"])
    ap.add_argument("q", nargs="?")
    ap.add_argument("--person", action="append", default=[])
    ap.add_argument("--news", action="append", default=[])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--out", default="D:/TarZo/Edits/Assets/news")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    people = a.person + ([a.q] if a.mode == "person" and a.q else [])
    queries = a.news + ([a.q] if a.mode == "news" and a.q else [])
    idx_p = out / "news_index.json"
    idx = json.loads(idx_p.read_text(encoding="utf-8")) if idx_p.exists() else {"people": [], "news": []}
    for p in people:
        print("PERSON", p)
        idx["people"] = [x for x in idx["people"] if x["person"] != p] + [person(p, a.n, out)]
    for q in queries:
        print("NEWS", q)
        idx["news"] = [x for x in idx["news"] if x["query"] != q] + [news(q, a.n, out, not a.no_shots)]
    idx_p.write_text(json.dumps(idx, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
