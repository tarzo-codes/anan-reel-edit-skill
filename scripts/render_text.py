"""Render Anan-style keyword text as full-frame transparent PNGs (2160x3840) with headless Edge.

  python render_text.py spec.json OUT_DIR

Why a browser: PIL here has no libraqm and ffmpeg drawtext mis-orders Bangla vowel signs
(আমি -> আমি with the ি after ম). Chromium shapes Bangla correctly.

spec.json:
{
  "items": [
    {"id": "k01_ajke", "layers": [
        {"text": "Ajke", "style": "script_white", "x": 0.07, "y": 0.035, "size": 230}
    ]},
    {"id": "k02_ami", "layers": [
        {"text": "আমি", "style": "bangla_red", "x": 0.42, "y": 0.06, "size": 260}
    ]}
  ]
}
x, y = top-left of the text box as a fraction of the frame; size in px at 2160 wide.
Optional per layer: "color", "stroke" (px), "stroke_color", "rotate" (deg), "align": "center"
(then x is the centre). One item = one PNG = one clip in Premiere, so each word that builds
in on its own gets its own item (the editor stacks them on separate tracks).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 2160, 3840
RED = "#E8141C"
EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
FONT_DIRS = [r"C:\Windows\Fonts", os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts"),
             r"E:\Anan\Assets\Motion_Templates\fonts"]
FONTS = {  # family -> file name
    "LucidaHW": "LHANDW.TTF",
    "Magneto": "MAGNETOB.TTF",
    "Matura": "MATURASC.TTF",
    "Shadhinata": "Li Shadhinata2 2.0 Unicode.ttf",
    "ShadhinataItalic": "Li Shadhinata2 2.0 Unicode Italic.ttf",
    "Anton": "Anton-Regular.ttf",
}
# style -> css. Learned from reel 88 / 94 frames; see references/style.md "Text".
STYLES = {
    "script_white":   dict(font="LucidaHW", color="#FFFFFF", stroke=0),
    "bangla_red":     dict(font="Shadhinata", color=RED, stroke=0),
    "bangla_red_it":  dict(font="ShadhinataItalic", color=RED, stroke=0),
    "bangla_white":   dict(font="Shadhinata", color="#FFFFFF", stroke=0),
    "bangla_outline": dict(font="Shadhinata", color="transparent", stroke=7, stroke_color="#FFFFFF"),
    "magneto_red":    dict(font="Magneto", color=RED, stroke=8, stroke_color="#FFFFFF"),
    "magneto_white":  dict(font="Magneto", color="#FFFFFF", stroke=0),
    "magneto_outline": dict(font="Magneto", color="transparent", stroke=7, stroke_color="#FFFFFF"),
    "matura_red":     dict(font="Matura", color=RED, stroke=0),
    "condensed_red":  dict(font="Anton", color=RED, stroke=0, skew=-8),
    "outline_grey":   dict(font="Anton", color="#3A3F4A", stroke=6, stroke_color="#B9BDC6", skew=-10),
}


def find(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def font_url(fam):
    f = find([os.path.join(d, FONTS[fam]) for d in FONT_DIRS])
    if not f:
        sys.exit(f"font missing for {fam}: {FONTS[fam]} (install it or edit FONTS)")
    return Path(f).as_uri()


def layer_html(L):
    st = dict(STYLES[L.get("style", "bangla_red")])
    st.update({k: L[k] for k in ("color", "stroke", "stroke_color", "font") if k in L})
    size = L.get("size", 220)
    x, y = L.get("x", 0.08) * W, L.get("y", 0.05) * H
    tf = []
    if L.get("align") == "center":
        tf.append("translateX(-50%)")
    if st.get("skew"):
        tf.append(f"skewX({st['skew']}deg)")
    if L.get("rotate"):
        tf.append(f"rotate({L['rotate']}deg)")
    stroke = (f"-webkit-text-stroke:{st['stroke']}px {st.get('stroke_color', '#fff')};paint-order:stroke fill;"
              if st.get("stroke") else "")
    css = (f"position:absolute;left:{x:.0f}px;top:{y:.0f}px;font-family:'{st['font']}';font-size:{size}px;"
           f"color:{st['color']};{stroke}white-space:pre;line-height:1.05;"
           f"transform:{' '.join(tf) or 'none'};transform-origin:left top;")
    text = L["text"].replace("&", "&amp;").replace("<", "&lt;")
    return f'<div style="{css}">{text}</div>'


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    edge = find(EDGE) or sys.exit("no Edge/Chrome found")
    faces = "".join(f"@font-face{{font-family:'{k}';src:url('{font_url(k)}')}}" for k in FONTS
                    if any(STYLES[L.get('style', 'bangla_red')]['font'] == k or L.get('font') == k
                           for it in spec["items"] for L in it["layers"]))
    tmp = Path(tempfile.mkdtemp(prefix="anan_text_"))
    for it in spec["items"]:
        html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{faces}"
                f"html,body{{margin:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden}}"
                f"</style></head><body>{''.join(layer_html(L) for L in it['layers'])}</body></html>")
        page = tmp / f"{it['id']}.html"; page.write_text(html, encoding="utf-8")
        png = out / f"{it['id']}.png"
        subprocess.run([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", "--force-device-scale-factor=1",
                        "--default-background-color=00000000", f"--window-size={W},{H}",
                        "--virtual-time-budget=1500", f"--screenshot={png}", page.as_uri()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        print(("ok  " if png.exists() else "FAIL") + f" {png}")


if __name__ == "__main__":
    main()
