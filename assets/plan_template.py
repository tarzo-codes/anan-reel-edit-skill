"""Reel 1 (2-11-2026): China story - no stop loss, $8,500 red candle, always use a stop loss.
Writes r1_prem.json (for build_reel.jsx) and r1_ae.json (AE batch.run for the R1_TEXT comp)."""
import json

R = 1
A = "E:/Anan/Assets/"
cuts = json.load(open(f"r{R}_cuts.json"))
PH = {c["i"]: (c["tl"], c["src_out"] - c["src_in"]) for c in cuts}
TOTAL = round(cuts[-1]["tl"] + cuts[-1]["src_out"] - cuts[-1]["src_in"], 2)


def T(i, f=0.0):  # timeline time at fraction f of phrase i
    s, d = PH[i]
    return round(s + f * d, 2)


# ---------------- text (AE): groups of words that build in and leave together
# (start, text, style, x, y)   styles: script, bn, mag_r, mag_w, imp_r
G = [
    (T(0, .40), [(T(0, .04), "Crazy", "script", 760, 520), (T(0, .14), "STORY", "mag_r", 1320, 860)]),
    (T(0, .62), [(T(0, .45), "China", "script", 1080, 600)]),
    (T(1, .50), [(T(1, .05), "Forex", "script", 760, 520), (T(1, .30), "GOLD", "mag_r", 1360, 860)]),
    (T(1, 1.0), [(T(1, .55), "3 Trades", "mag_w", 1080, 520), (T(1, .78), "2 Lot", "mag_r", 1080, 860)]),
    (T(3, .45), [(T(3, .03), "No", "script", 620, 520), (T(3, .10), "Stop Loss", "mag_r", 1180, 860)]),
    (T(3, .72), [(T(3, .45), "No", "script", 620, 520), (T(3, .50), "Take Profit", "mag_r", 1180, 860)]),
    (T(3, 1.0), [(T(3, .75), "Washroom", "script", 1080, 600)]),
    (T(4, 1.0), [(T(4, .05), "1 Minute", "mag_w", 1080, 600)]),
    (T(5, 1.0), [(T(5, .62), "$200 - $300", "mag_w", 1080, 520), (T(5, .80), "Loss", "mag_r", 1080, 860)]),
    (T(7, 1.0), [(T(7, .10), "Stop Loss", "script", 1080, 520), (T(7, .45), "$1000", "mag_r", 1080, 880)]),
    (T(9, 1.0), [(T(9, .0), "WHAT?!", "imp_r", 1080, 760)]),
    (T(10, .58), [(T(10, .05), "$8,500", "mag_r_big", 1080, 640), (T(10, .30), "LOSS", "mag_w", 1080, 960)]),
    (T(10, 1.0), [(T(10, .60), "Red", "script", 760, 520), (T(10, .70), "Candle", "mag_r", 1300, 860)]),
    (T(11, .62), [(T(11, .25), "Just", "script", 700, 520), (T(11, .33), "ঘুম থেকে উঠে", "bn", 1180, 880)]),
    (T(12, 1.0), [(T(12, .05), "Literally", "script", 1080, 520), (T(12, .45), "খারাপ দিন", "bn", 1080, 880)]),
    (T(14, 1.0), [(T(14, .08), "2 Cities", "mag_w", 1080, 520), (T(14, .60), "Recovered", "mag_r", 1080, 860)]),
    (T(16, .0), [(T(15, .05), "Moral of the Story", "script_s", 1080, 520), (T(15, .80), "ALWAYS", "mag_r", 1080, 860)]),
    (T(16, 1.0), [(T(16, .40), "সাথে সাথে", "bn", 1080, 520), (T(16, .60), "STOP LOSS", "mag_r_big", 1080, 900)]),
    (T(17, .70), [(T(17, .05), "Profit", "script", 1080, 600)]),
    (TOTAL, [(T(18, .10), "Follow", "script", 700, 520), (T(18, .35), "Stop Loss", "mag_r", 1280, 860)]),
]
RED, WHITE = [0.91, 0.08, 0.11], [1, 1, 1]
STY = {
    "script": dict(font="LucidaHandwriting-Italic", fontSize=300, fillColor=WHITE),
    "script_s": dict(font="LucidaHandwriting-Italic", fontSize=230, fillColor=WHITE),
    "bn": dict(font="LiShadhinata22.0Unicode", fontSize=360, fillColor=RED, composerEngine="universal"),
    "mag_r": dict(font="Magneto-Bold", fontSize=400, fillColor=RED, applyStroke=True, strokeColor=WHITE, strokeWidth=10, strokeOverFill=False),
    "mag_r_big": dict(font="Magneto-Bold", fontSize=520, fillColor=RED, applyStroke=True, strokeColor=WHITE, strokeWidth=12, strokeOverFill=False),
    "mag_w": dict(font="Magneto-Bold", fontSize=400, fillColor=WHITE),
    "imp_r": dict(font="Impact", fontSize=560, fillColor=RED),
}
import os
from PIL import ImageFont
FONTFILES = {"LucidaHandwriting-Italic": "LHANDW.TTF", "Magneto-Bold": "MAGNETOB.TTF", "Impact": "impact.ttf",
             "LiShadhinata22.0Unicode": "Li Shadhinata2 2.0 Unicode.ttf"}
FDIRS = ["C:/Windows/Fonts", os.path.expandvars("%LOCALAPPDATA%/Microsoft/Windows/Fonts")]


def fit(txt, st, x, maxw=1880):
    """Shrink the style's size until the word fits the frame; keep it inside the edges."""
    s = dict(STY[st]); ff = FONTFILES[s["font"]]
    path = next(os.path.join(d, ff) for d in FDIRS if os.path.exists(os.path.join(d, ff)))
    w = ImageFont.truetype(path, 100).getlength(txt) * s["fontSize"] / 100 * (1.12 if s["font"] == "Magneto-Bold" else 1.0)
    if w > maxw:
        s["fontSize"] = int(s["fontSize"] * maxw / w); w = maxw
    x = min(max(x, 140 + w / 2), 2020 - w / 2)
    return s, round(x)


COMP = f"R{R}_TEXT"
ops = [{"operation": "comp.create", "args": {"name": COMP, "width": 2160, "height": 3840, "fps": 25, "duration": TOTAL}}]
pops = []
n = 0
for end, words in G:
    for (t, txt, st, x, y) in words:
        n += 1
        name = f"T{n:02d}_{txt[:12]}"
        sty, x = fit(txt, st, x)
        y = 560 if y < 700 and y != 600 else (640 if y == 600 else y + 60)  # more room between the two lines
        ops += [
            {"operation": "layer.create_text", "args": {"comp": COMP, "text": txt, "name": name}},
            {"operation": "text.set_style", "args": {"comp": COMP, "layer": name, "justification": "center", **sty}},
            {"operation": "layer.set_timing", "args": {"comp": COMP, "layer": name, "inPoint": t, "outPoint": end}},
            {"operation": "keyframe.set_batch", "args": {"comp": COMP, "layer": name, "property": ["Transform", "Position"],
                                                          "times": [t, round(t + 0.12, 2)], "values": [[x + 2300, y], [x, y]]}},
            {"operation": "keyframe.set_easing", "args": {"comp": COMP, "layer": name, "property": ["Transform", "Position"], "keyIndex": 2, "preset": "easeIn"}},
        ]
        pops.append(t)
json.dump({"operation": "batch.run", "args": {"ops": ops}}, open(f"r{R}_ae.json", "w", encoding="utf-8"), ensure_ascii=False)

# ---------------- Premiere: scenes, punches, sfx
LAND = 1500  # card width for landscape clips


def card(file, w, h, at, y, x=0.5, src_in=0, t1=None, width=LAND):
    sc = (width / w if w >= h else 1500 / h) * 100
    d = {"file": A + file, "at": at, "y": y, "x": x, "scale": round(sc, 1), "src_in": src_in}
    if t1: d["t1"] = t1
    return d


def full(file, w, h, src_in=0):
    return {"file": A + file, "scale": round(max(2160 / w, 3840 / h) * 100, 1), "src_in": src_in}


scenes = [
    # hook cards stay small and below the face (chest height), as in reel 88
    {"type": "fly", "t0": 0.6, "t1": 3.0, "items": [card("6290484-uhd_3840_2160_30fps.mp4", 3840, 2160, 0.6, 0.66, x=0.3, src_in=2, width=900),
                                                     card("308080_medium.mp4", 2560, 1440, 1.2, 0.80, x=0.7, src_in=5, width=900)]},
    {"type": "cards", "t0": T(1, .10), "t1": T(1, .62), "items": [card("191303-889685056_medium.mp4", 2560, 1440, T(1, .12), 0.42, src_in=3),
                                                                  card("16294859_1920_1080_25fps.mp4", 1920, 1080, T(1, .30), 0.68, src_in=4)]},
    {"type": "full", "t0": T(5, .55), "t1": T(5, 1.0), "items": [full("6266251-uhd_2160_3840_25fps.mp4", 1440, 2560, 1)]},
    {"type": "cards", "t0": T(10, .20), "t1": T(10, .75), "items": [card("Seller.mp4", 2560, 1440, T(10, .22), 0.6, src_in=2)]},
    {"type": "cards", "t0": T(11, .10), "t1": T(11, .70), "items": [card("4974702-hd_1920_1080_25fps.mp4", 1920, 1080, T(11, .12), 0.42, src_in=3),
                                                                    card("8077298-uhd_4096_2160_25fps.mp4", 4096, 2160, T(11, .45), 0.68, src_in=4)]},
    {"type": "full", "t0": T(12, .25), "t1": T(12, .62), "items": [full("7698908-uhd_2160_4096_25fps.mp4", 2160, 4096, 3)]},
    {"type": "cards", "t0": T(13, .30), "t1": T(13, 1.0), "items": [card("RAW/IMG_6808.MOV", 464, 824, T(13, .32), 0.62, x=0.3),
                                                                    card("RAW/IMG_6865.MOV", 464, 848, T(13, .55), 0.62, x=0.7)]},
    {"type": "full", "t0": T(14, .55), "t1": T(14, 1.0), "items": [full("RAW/IMG_1616.MOV", 1072, 1920, 2)]},
    {"type": "cards", "t0": T(17, .20), "t1": T(17, .95), "items": [card("Buyer.mp4", 2560, 1440, T(17, .22), 0.6, src_in=2)]},
]
fy = 0.36  # face height in frame (fraction) for punch-in centring
punches = [
    {"keys": [[T(0, .35), 100], [T(0, .45), 113]]},
    {"keys": [[T(3, .10), 100], [T(3, .16), 128]], "fy": fy},
    {"keys": [[T(9, .0) + 0.02, 100], [T(9, .0) + 0.32, 142]], "fy": fy},
    {"keys": [[T(10, .0) + 0.02, 100], [T(10, .12), 113]]},
    {"keys": [[T(13, .0) + 0.02, 100], [T(13, .3), 108]]},
    {"keys": [[T(15, .0) + 0.02, 100], [T(15, .2), 113]]},
    {"keys": [[T(16, .55), 100], [T(16, .62), 130]], "fy": fy},
    {"keys": [[T(18, .0) + 0.02, 100], [T(18, .4), 113], [T(18, .95), 126]], "fy": fy},
]
S = "D:/Assets/01_Audio/SFX/"
sfx = [
    ("whoosh-vortex-243128.mp3", 0.0, "bed", -18, 2.5),
    ("gun-scope-zoom-in-106101.mp3", 0.6, "feat", -4, 0.6), ("gun-scope-zoom-in-106101.mp3", 1.2, "extra", -4, 0.8),
    ("whoosh-vortex-243128.mp3", T(1, .10), "bed", -18, 2.0), ("Subtle Whoosh.wav", T(1, .30), "extra", -8, 0.6),
    ("Soft but Angry.wav", T(3, .10), "feat", -4, 1.0),
    ("slow-whoosh-118247.mp3", T(5, .55), "bed", -18, 2.2),
    ("Soft but Angry.wav", T(9, .0), "feat", -4, 1.0), ("Short but Boomy.wav", T(9, .0), "extra", -8, 0.6),
    ("Short but Boomy.wav", T(10, .05), "extra", -8, 0.6), ("WHIP.wav", T(10, .20), "feat", -6, 0.5),
    ("whoosh-vortex-243128.mp3", T(11, .10), "bed", -18, 2.0),
    ("slow-whoosh-118247.mp3", T(12, .25), "bed", -18, 2.2),
    ("Subtle Whoosh.wav", T(13, .32), "extra", -8, 0.6), ("Subtle Whoosh.wav", T(13, .55), "feat", -8, 0.6),
    ("modestas123123-cash-register-kaching-sound-effect-125042.mp3", T(14, .55), "feat", -4, 2.0),
    ("Soft but Angry.wav", T(16, .60), "feat", -4, 1.0),
    ("slow-whoosh-118247.mp3", T(17, .20), "bed", -18, 2.0),
]
busy = {}
out_sfx = [{"file": f, "t": t, "role": r, "db": db, "len": ln} for f, t, r, db, ln in sfx]
for f, t, r, db, ln in sfx:
    busy.setdefault(r, []).append((t, t + ln))
for t in pops:  # text tick on the pop track, skipping overlaps
    if all(not (a - 0.05 < t < b) for a, b in busy.get("pop", [])):
        out_sfx.append({"file": "Very Subtle.wav", "t": t, "role": "pop", "db": -4, "len": 0.4})
        busy.setdefault("pop", []).append((t, t + 0.4))
prem = {
    "seq": f"Reel_{R}_2-11", "aroll": "reel 1 (2).MP4", "total": TOTAL,
    "grid": A + "bg_blueprint_grid.jpg", "grid_scale": round(3840 / 4001 * 100, 1),
    "cuts": cuts, "voice_db": 3,
    "lumetri": {"Exposure": 0.44, "Contrast": 7.8, "Highlights": -15.9, "Shadows": -20.7, "Whites": 0.8, "Blacks": -7.5, "Saturation": 98},
    "punches": punches, "scenes": scenes, "sfx": out_sfx,
    "music": {"file": "the_mountain-trailer-intense-179466.mp3", "src_in": 19.84, "db": -27, "fade": 2.5},
    "ae": {"aep": "E:/Anan/Assets/AE/reels_2-11-2026.aep", "comp": COMP},
}
json.dump(prem, open(f"r{R}_prem.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("total", TOTAL, "text layers", n, "ae ops", len(ops), "sfx", len(out_sfx), "scenes", len(scenes))
