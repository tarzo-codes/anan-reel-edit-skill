import re
"""Shared machinery for Anan reel plans (2025-2026 Motion-Designer 3D Spatial Canvas & FinTech Edition).

    import sys; sys.path.insert(0, "C:/Users/btaza/.claude/skills/shorts-editor-skill/scripts")
    from reelkit import Reel, BEHIND, BEHIND_P
    r = Reel(1, "E:/Anan/NEW/reel 1 (2).MP4", "reel 1 (2).MP4", drop={1}, trim={7: (0, 4)})
    W, E = r.W, r.E
    r.text(end, [(start, "word", "sans_w", x, y), (start2, "PROFIT", "mono_g", x2, y2, "pop")])
    r.scene(...); r.overlay(...); r.punch(...); r.sfx(...); r.cutout(t0, t1); r.write()

Font Stack (Installed in %LOCALAPPDATA%/Microsoft/Windows/Fonts & E:/Anan/Assets/Fonts):
  - Primary FinTech & Kinetic Sans: PlusJakartaSans-ExtraBold / PlusJakartaSans-Bold
  - Architectural Hero Display Sans: Syne-ExtraBold / Anton-Regular / BebasNeue-Regular
  - Neo-Luxury Editorial Serif:      InstrumentSerif-Italic / InstrumentSerif-Regular
  - Quant HUD Tabular Monospace:     JetBrainsMono-ExtraBold / JetBrainsMono-Bold
  - Modern Geometric UI Bangla:      HindSiliguri-Bold / HindSiliguri-SemiBold
"""
import json
import re
import os
from PIL import ImageFont

A = "E:/Anan/Assets/"
SFX = "D:/Assets/01_Audio/SFX/"

# 2025-2026 FinTech & 3D Spatial Canvas Semantic Color Palette
WHITE = [0.97, 0.98, 0.99]       # Crisp Titanium White (#F8FAFC)
EMERALD = [0.00, 0.90, 0.46]     # Alpha Profit / Bullish Emerald (#00E676)
CRIMSON = [1.00, 0.12, 0.26]     # Stop-Loss / Liquidation Crimson (#FF1E42)
GOLD = [0.96, 0.62, 0.04]        # Sovereign / Editorial Luxury Amber-Gold (#F59E0B)
CYAN = [0.22, 0.74, 0.97]        # 3D Spatial Telemetry Cyan (#38BDF8)
SLATE = [0.58, 0.64, 0.72]       # HUD Muted Coordinate Slate (#94A3B8)
OBSIDIAN = [0.04, 0.06, 0.10]    # Deep Obsidian Plane Backing (#0A0F1A)
RED = CRIMSON                    # Legacy alias

# Y-Lane Constants (2160x3840 canvas - 2026 Mobile Safe Zones)
TOP = 780         # Top title/header (leaves >= 200px clear of top status bar/notch >= 400px)
UPPER = 880       # Upper third
BEHIND = 1540     # Hero typography behind Anan's head (scales to ~940px under 1.32x punch, safe from notch)
BEHIND_P = 1050
CENTER = 1920
LOWER = 2780      # Word-chunk subtitle baseline (clear of IG bottom UI <= 3140px)
BOTTOM = 2950

STY = {
    # --- 1. Modern FinTech Geometric Sans (Plus Jakarta Sans ExtraBold / Syne ExtraBold / Anton) ---
    "sans_w": dict(font="PlusJakartaSans-ExtraBold", fontSize=340, fillColor=WHITE, tracking=-25),
    "sans_g": dict(font="PlusJakartaSans-ExtraBold", fontSize=360, fillColor=EMERALD, tracking=-25),
    "sans_r": dict(font="PlusJakartaSans-ExtraBold", fontSize=380, fillColor=CRIMSON, tracking=-25),
    "sans_gold": dict(font="PlusJakartaSans-ExtraBold", fontSize=360, fillColor=GOLD, tracking=-25),
    "sans_cyan": dict(font="PlusJakartaSans-ExtraBold", fontSize=340, fillColor=CYAN, tracking=-25),
    "sans_hero": dict(font="Syne-ExtraBold", fontSize=460, fillColor=WHITE, tracking=-35),
    "sans_slam": dict(font="Anton-Regular", fontSize=520, fillColor=CRIMSON, tracking=-10),
    "pillar_w": dict(font="BebasNeue-Regular", fontSize=540, fillColor=WHITE, tracking=10),
    "label_slate": dict(font="JetBrainsMono-ExtraBold", fontSize=170, fillColor=SLATE, tracking=40),
    "cap_en_w": dict(font="PlusJakartaSans-ExtraBold", fontSize=220, fillColor=WHITE, tracking=30, applyStroke=False),
    "cap_en_gold": dict(font="PlusJakartaSans-ExtraBold", fontSize=220, fillColor=GOLD, tracking=30, applyStroke=False),
    "cap_en_cyan": dict(font="PlusJakartaSans-ExtraBold", fontSize=220, fillColor=CYAN, tracking=30, applyStroke=False),
    "cap_en_g": dict(font="PlusJakartaSans-ExtraBold", fontSize=220, fillColor=EMERALD, tracking=30, applyStroke=False),
    "cap_en_r": dict(font="PlusJakartaSans-ExtraBold", fontSize=220, fillColor=CRIMSON, tracking=30, applyStroke=False),
    "cap_bn_w": dict(font="HindSiliguri-Bold", fontSize=320, fillColor=WHITE, composerEngine="universal", applyStroke=False),
    "cap_bn_gold": dict(font="HindSiliguri-Bold", fontSize=320, fillColor=GOLD, composerEngine="universal", applyStroke=False),
    "cap_bn_g": dict(font="HindSiliguri-Bold", fontSize=320, fillColor=EMERALD, composerEngine="universal", applyStroke=False),
    "cap_bn_r": dict(font="HindSiliguri-Bold", fontSize=320, fillColor=CRIMSON, composerEngine="universal", applyStroke=False),
    "cap_bn_cyan": dict(font="HindSiliguri-Bold", fontSize=320, fillColor=CYAN, composerEngine="universal", applyStroke=False),
    "kicker_w": dict(font="PlusJakartaSans-ExtraBold", fontSize=160, fillColor=WHITE, tracking=30),
    "kicker_gold": dict(font="PlusJakartaSans-ExtraBold", fontSize=160, fillColor=GOLD, tracking=30),
    "kicker_cyan": dict(font="PlusJakartaSans-ExtraBold", fontSize=150, fillColor=CYAN, tracking=35),
    "kicker_g": dict(font="PlusJakartaSans-ExtraBold", fontSize=150, fillColor=EMERALD, tracking=35),
    "kicker_r": dict(font="PlusJakartaSans-ExtraBold", fontSize=150, fillColor=CRIMSON, tracking=35),
    "mono_kicker_g": dict(font="JetBrainsMono-ExtraBold", fontSize=140, fillColor=EMERALD, tracking=40),
    "mono_kicker_cyan": dict(font="JetBrainsMono-ExtraBold", fontSize=140, fillColor=CYAN, tracking=40),
    "mono_kicker_gold": dict(font="JetBrainsMono-ExtraBold", fontSize=140, fillColor=GOLD, tracking=40),

    # --- 2. Neo-Luxury Editorial Serif Italic (Instrument Serif Italic — Mercury/Stripe/Iman Gadzhi style) ---
    "serif_w": dict(font="InstrumentSerif-Italic", fontSize=360, fillColor=WHITE, tracking=-10),
    "serif_gold": dict(font="InstrumentSerif-Italic", fontSize=380, fillColor=GOLD, tracking=-10),
    "serif_g": dict(font="InstrumentSerif-Italic", fontSize=360, fillColor=EMERALD, tracking=-10),

    # --- 3. Quant / 3D HUD Tabular Monospace (JetBrains Mono ExtraBold) ---
    "mono_g": dict(font="JetBrainsMono-ExtraBold", fontSize=350, fillColor=EMERALD, applyStroke=False),
    "mono_r": dict(font="JetBrainsMono-ExtraBold", fontSize=350, fillColor=CRIMSON, applyStroke=False),
    "mono_w": dict(font="JetBrainsMono-ExtraBold", fontSize=320, fillColor=WHITE, applyStroke=False),
    "mono_hero": dict(font="JetBrainsMono-ExtraBold", fontSize=480, fillColor=EMERALD, applyStroke=False),

    # --- 4. Modern Geometric UI & Motion-Design Bangla (Hind Siliguri Bold — Clean Monolinear Vector Strokes) ---
    "bn_w": dict(font="HindSiliguri-Bold", fontSize=340, fillColor=WHITE, composerEngine="universal", applyStroke=False),
    "bn_g": dict(font="HindSiliguri-Bold", fontSize=360, fillColor=EMERALD, composerEngine="universal", applyStroke=False),
    "bn_r": dict(font="HindSiliguri-Bold", fontSize=360, fillColor=CRIMSON, composerEngine="universal", applyStroke=False),
    "bn_gold": dict(font="HindSiliguri-Bold", fontSize=360, fillColor=GOLD, composerEngine="universal", applyStroke=False),
    "bn_hero": dict(font="HindSiliguri-Bold", fontSize=430, fillColor=WHITE, composerEngine="universal", applyStroke=False),
    "bn_i": dict(font="HindSiliguri-SemiBold", fontSize=320, fillColor=WHITE, composerEngine="universal", applyStroke=False),
    "bn": dict(font="HindSiliguri-Bold", fontSize=350, fillColor=CRIMSON, composerEngine="universal", applyStroke=False),

    # --- Legacy aliases mapped cleanly to the new Motion-Designer Font Stack ---
    "script": dict(font="InstrumentSerif-Italic", fontSize=360, fillColor=WHITE, applyStroke=False),
    "script_s": dict(font="InstrumentSerif-Italic", fontSize=280, fillColor=SLATE, applyStroke=False),
    "mag_r": dict(font="PlusJakartaSans-ExtraBold", fontSize=380, fillColor=CRIMSON, applyStroke=False),
    "mag_r_big": dict(font="JetBrainsMono-ExtraBold", fontSize=480, fillColor=EMERALD, applyStroke=False),
    "mag_w": dict(font="PlusJakartaSans-ExtraBold", fontSize=360, fillColor=WHITE, applyStroke=False),
    "imp_r": dict(font="Anton-Regular", fontSize=520, fillColor=CRIMSON, applyStroke=False),
}

FONTFILES = {
    "PlusJakartaSans-ExtraBold": "PlusJakartaSans-ExtraBold-Static.ttf",
    "PlusJakartaSans-Bold": "PlusJakartaSans-Bold.ttf",
    "PlusJakartaSans-BoldItalic": "PlusJakartaSans-BoldItalic-Static.ttf",
    "Syne-ExtraBold": "Syne-ExtraBold-Static.ttf",
    "Anton-Regular": "Anton-Regular.ttf",
    "BebasNeue-Regular": "BebasNeue-Regular.ttf",
    "InstrumentSerif-Italic": "InstrumentSerif-Italic.ttf",
    "InstrumentSerif-Regular": "InstrumentSerif-Regular.ttf",
    "JetBrainsMono-ExtraBold": "JetBrainsMono-ExtraBold-Static.ttf",
    "JetBrainsMono-Bold": "JetBrainsMono-Bold.ttf",
    "HindSiliguri-Bold": "HindSiliguri-Bold.ttf",
    "HindSiliguri-SemiBold": "HindSiliguri-SemiBold.ttf",
    "HindSiliguri-Medium": "HindSiliguri-Medium.ttf",
    "Gotham-Ultra": "Gotham-Ultra.otf",
    "Gotham-Black": "Gotham-Black.otf",
    "Gotham-Bold": "Gotham-Bold.otf",
    "GothamCond-XBlack": "GothamCond-XBlack.otf",
    "LiShadhinata22.0Unicode": "Li Shadhinata2 2.0 Unicode.ttf",
    "LiShadhinata22.0Unicode-Italic": "Li Shadhinata2 2.0 Unicode Italic.ttf",
}
FDIRS = [
    os.path.expandvars("%LOCALAPPDATA%/Microsoft/Windows/Fonts"),
    "E:/Anan/Assets/Fonts",
    "C:/Windows/Fonts",
]
GRADE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "grade", "anan_warm_pop.json")

CLOCK = {"file": A + "198430-907598392_medium.mp4", "key": [24, 251, 6], "src_in": 2, "scale": 190}
RED_X = {"file": A + "Motion_Templates/elements/red_x_glow.mov", "scale": 140}
FOLLOW = {"file": A + "Motion_Templates/elements/follow_button_click.mov", "scale": 150}
CHECK = {"file": A + "Motion_Templates/elements/check_mark_green.mov", "scale": 140}
CASH_RAIN = {"file": A + "Motion_Templates/elements/cash_rain_loop.mov", "scale": 200}


# Helper token constructors for clean declarative plans: sans_w("WORD"), serif_gold("illusion"), etc.
def _make_tok(style_key):
    def _fn(txt, x=1080, anim=None):
        return (txt, style_key, x, anim)
    return _fn


sans_w = _make_tok("sans_w")
sans_g = _make_tok("sans_g")
sans_r = _make_tok("sans_r")
sans_gold = _make_tok("sans_gold")
sans_cyan = _make_tok("sans_cyan")
sans_hero = _make_tok("sans_hero")
sans_slam = _make_tok("sans_slam")
pillar_w = _make_tok("pillar_w")
label_slate = _make_tok("label_slate")
serif_w = _make_tok("serif_w")
serif_gold = _make_tok("serif_gold")
serif_g = _make_tok("serif_g")
mono_g = _make_tok("mono_g")
mono_r = _make_tok("mono_r")
mono_w = _make_tok("mono_w")
mono_hero = _make_tok("mono_hero")
bn_w = _make_tok("bn_w")
bn_g = _make_tok("bn_g")
bn_r = _make_tok("bn_r")
bn_gold = _make_tok("bn_gold")
bn_hero = _make_tok("bn_hero")


def _w_start(w_entry):
    return w_entry[0] if isinstance(w_entry, list) else w_entry["s"]


def _w_end(w_entry):
    return w_entry[1] if isinstance(w_entry, list) else w_entry["e"]


def _fit(txt, st, x, maxw=1780, stack=False):
    s = dict(STY[st])
    if "\u09f3" in txt and "Siliguri" not in s["font"] and "Bangla" not in s["font"]:
        txt = txt.replace("\u09f3 ", "TK ").replace("\u09f3", "TK ")
    if "Siliguri" in s["font"]:
        s.setdefault("tracking", 12)
    ff = FONTFILES.get(s["font"], "PlusJakartaSans-ExtraBold-Static.ttf")
    path = next((os.path.join(d, ff) for d in FDIRS if os.path.exists(os.path.join(d, ff))), None)
    k = {
        "PlusJakartaSans-ExtraBold": 1.10,
        "PlusJakartaSans-Bold": 1.08,
        "Syne-ExtraBold": 1.16,
        "Anton-Regular": 1.06,
        "BebasNeue-Regular": 1.05,
        "InstrumentSerif-Italic": 1.06,
        "JetBrainsMono-ExtraBold": 1.10,
        "JetBrainsMono-Bold": 1.08,
        "HindSiliguri-Bold": 1.16,
        "HindSiliguri-SemiBold": 1.14,
    }.get(s["font"], 1.10)
    lines = re.split(r"[\r\n]", txt)

    def width(ls):
        if path:
            return max(ImageFont.truetype(path, 100).getlength(l) for l in ls) * s["fontSize"] / 100 * k
        return max(len(l) for l in ls) * s["fontSize"] * 0.60
    w = width(lines)
    # user (8-11-2026 pass 3): text must NEVER clip. Over-wide top text is stacked on 2 balanced lines first
    if w > maxw and stack and len(lines) == 1 and " " in txt.strip():
        words = txt.split()
        best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
        w = width(lines)
    if w > maxw:  # then shrink with no floor that lets it run off the frame (the 160 px floor clipped 2 lines on 8-11)
        s["fontSize"] = max(110, int(s["fontSize"] * maxw / w))
        w = maxw
    if len(lines) > 1:
        s["leading"] = round(s["fontSize"] * 1.14)
        s["autoLeading"] = False
    txt = "\r".join(lines)
    half_vis = maxw / 2
    lo_x = max(140 + w / 2, 1080 - half_vis + w / 2)
    hi_x = min(2020 - w / 2, 1080 + half_vis - w / 2)
    cx = 1080 if lo_x >= hi_x else round(min(max(x, lo_x), hi_x))
    return txt, s, cx


def _measure(txt, st, size=None):
    """width in px of one line of txt in style st at size (PIL advance width; >= what AE renders)"""
    s = dict(STY[st])
    ff = FONTFILES.get(s["font"], "PlusJakartaSans-ExtraBold-Static.ttf")
    path = next((os.path.join(d, ff) for d in FDIRS if os.path.exists(os.path.join(d, ff))), None)
    size = size or s["fontSize"]
    if not path:
        return len(txt) * size * 0.6
    return ImageFont.truetype(path, 100).getlength(txt) * size / 100


def _split_long_chunks(items, style, size, end, maxw=1720, min_size=190):
    """user (8-11-2026 pass 3): a caption chunk that would need < min_size px to fit is split in two, the 2nd half
    landing halfway to the next chunk ("split them shorter"); captions never stack down into the IG caption zone."""
    out = []
    for n, it in enumerate(items):
        t, txt = it[0], it[1]
        st = it[2] if len(it) > 2 else style
        nxt = items[n + 1][0] if n + 1 < len(items) else (end or t + 1.2)
        words = txt.split()
        if len(words) >= 2 and _measure(txt, st, min_size) > maxw:
            best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
            mid = round(t + (nxt - t) / 2, 2)
            out.append((t, " ".join(words[:best])) + tuple(it[2:]))
            out.append((mid, " ".join(words[best:])) + tuple(it[2:]))
        else:
            out.append(it)
    return out


def _default_anim_for_style(st):
    if st in ("sans_slam", "imp_r", "sans_hero", "pillar_w"):
        return "slam"
    if st in ("serif_w", "serif_gold", "serif_g", "label_slate", "script", "script_s"):
        return "rise"
    # 2025-2026 3D type: kinetic sans / mono / Bangla words flip up off the floor plane (style.md 3.3.3)
    return "plane_flip"


def _speech_end(wav, t0, t1, floor_db=-34.0, win=0.05):
    """last moment in [t0, t1] where the voice is above floor_db (RMS, 50 ms windows) - Whisper's word ends run long."""
    import math
    import struct
    import wave
    w = wave.open(wav)
    sr, ch = w.getframerate(), w.getnchannels()
    w.setpos(int(t0 * sr))
    n = int((t1 - t0) * sr)
    raw = w.readframes(n)  # the last cut can end past the WAV end (11-11-2026)
    n = len(raw) // (2 * ch)
    d = struct.unpack("<" + "h" * (n * ch), raw[:n * 2 * ch])
    step, last = int(win * sr), None
    for k in range(0, n - step, step):
        seg = d[k * ch:(k + step) * ch]
        rms = math.sqrt(sum(x * x for x in seg) / len(seg)) or 1
        if 20 * math.log10(rms / 32768) > floor_db:
            last = t0 + (k + step) / sr
    return last


def _norm(w):
    return "".join(ch for ch in (w[2] if isinstance(w, list) else w.get("w", "")) if ch not in "।,?!.;:-–—'\"…").strip()


def _sim(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def _word_hits(a, b, cut=0.7):
    """share of words in a that (fuzzily) appear in b"""
    return sum(1 for x in a if any(_sim(x, y) >= cut for y in b)) / max(1, len(a))


def find_retakes(ph, max_gap=3.0):
    """When a phrase is said more than once in a row, CUT THE FIRST ONE (it's the mistake)."""
    ids = sorted(ph)
    W = {i: [_norm(w) for w in ph[i]["w"]] for i in ids}
    W = {i: [w for w in v if w] for i, v in W.items()}
    drop, trim, notes = set(), {}, []
    for n, a in enumerate(ids):
        for b in ids[n + 1:n + 3]:
            prev = ids[ids.index(b) - 1]
            if ph[b]["s"] - ph[prev]["e"] > max_gap or not W[a] or not W[b]:
                break
            ta, tb = " ".join(W[a]), " ".join(W[b])
            k = min(len(ta), len(tb))
            same_open = k >= 6 and max(_sim(ta[:k], tb[:k]), _sim(ta, tb[:len(ta)])) >= 0.62
            same_words = (len(W[a]) <= 12 and _sim(W[a][0], W[b][0]) >= 0.7 and _word_hits(W[a], W[b]) >= 0.5)
            if same_open or same_words:
                drop.add(a)
                notes.append(f"P{a} said again in P{b} -> drop P{a}")
                break
    for i in ids:
        w = W[i]
        if len(w) < 6 or len(" ".join(w[:3])) < 6:
            continue
        for k in range(len(w) - 3, 2, -1):
            if (_sim(w[0], w[k]) >= 0.85 and all(_sim(w[j], w[k + j]) >= 0.6 for j in range(3))
                    and _sim(" ".join(w[:3]), " ".join(w[k:k + 3])) >= 0.85):
                trim[i] = (k, None)
                notes.append(f"P{i} restarts at word {k} ({w[k]}) -> cut words 0-{k - 1}")
                break
    return drop, trim, notes


class Reel:
    def __init__(self, n, src, aroll_name, drop=(), trim=None, pre=0.06, post=0.10, date="NEW", tag="",
                 music=None, music_db=-22, music_src_in=0, aep=None, auto_retakes=True, keep=(), keep_fs=(), cutw=None,
                 cuts_file=None, handcam=False, auto_mix=True):
        # cuts_file: the cut list the user approved in pass 1 (incl. their own Premiere trims) - overrides the computed cuts.
        # handcam: selfie/handheld A-roll (8-11-2026): face fills the frame -> no curtain top cover, no behind-head lane.
        self.handcam = handcam
        # auto_mix (user, 8-11-2026 "bg music is too low, balance it on the voice"): at write() the voice and music gains are
        # MEASURED (mix_levels.py, EBU R128): voice -> -15 LUFS, music bed 10 LU under it. music_db is only the fallback.
        self.auto_mix = auto_mix
        self.voice_db = 3
        self.n, self.src, self.aroll, self.date, self.tag = n, src, aroll_name, date, tag
        self.aep = aep or f"E:/Anan/Assets/AE/reels_{date}.aep"
        self.key = f"{n}{tag}"
        self.music = {
            "path": music or "D:/Assets/01_Audio/SFX/the_mountain-intense-intense-music-508028.mp3",
            "src_in": music_src_in,
            "db": max(-25, min(-14, music_db)),
            "fade": 2.0,
            "drops": [],
        }
        ph_file = aroll_name if (isinstance(aroll_name, str) and aroll_name.endswith(".json") and os.path.exists(aroll_name)) else f"r{n}_ph.json"
        self.out_dir = os.path.dirname(os.path.abspath(ph_file))
        if isinstance(aroll_name, str) and aroll_name.endswith(".json"):
            self.aroll = os.path.basename(src)
        _phj = json.load(open(ph_file, encoding="utf-8"))
        self.ph = {p["i"]: p for p in _phj["phrases"]}
        trim = dict(trim or {})
        # cutw={phrase: [(w0, w1), ...]}: cut spoken words w0..w1 (inclusive) out of the middle of a phrase
        # (mistakes / restarts like "shikhar moto ... trading er course kinar moto").
        for i, spans in (cutw or {}).items():
            p = self.ph[i]
            for w0, w1 in spans:
                x = _w_start(p["w"][w0]) - 0.03
                y = _w_start(p["w"][w1 + 1]) - 0.04 if w1 + 1 < len(p["w"]) else _w_end(p["w"][w1]) + 0.05
                p.setdefault("fs", []).append([round(x, 2), round(y, 2)])
        if auto_retakes:
            rd, rt, notes = find_retakes(self.ph)
            for line in notes:
                print("retake:", line.encode("ascii", "replace").decode())
            drop = set(drop) | (rd - set(keep))
            for i, v in rt.items():
                if i not in keep:
                    trim.setdefault(i, v)
        cuts, t = [], 0.0
        for i in sorted(self.ph):
            if i in drop:
                continue
            p = self.ph[i]
            a, b = p["s"] - pre, p["e"] + post
            if i in trim:
                w0, w1 = trim[i]
                if w0 is not None:
                    a = _w_start(p["w"][w0]) - pre
                    if w0 > 0:
                        a = max(a, _w_end(p["w"][w0 - 1]) + 0.02)
                if w1 is not None:
                    b = _w_end(p["w"][w1]) + post
                    if w1 + 1 < len(p["w"]):
                        b = min(b, _w_start(p["w"][w1 + 1]) - 0.02)
            a = max(0.0, a)
            if cuts and a < cuts[-1]["src_out"]:
                a = cuts[-1]["src_out"]
            segs = [[a, b]]
            if i not in keep_fs:  # half-said false starts found by false_starts.py ("fs" spans) come out
                for x, y in p.get("fs", []):
                    if x - a < 0.25:
                        print(f"false start: P{i} starts clean at {y:.2f}")
                    else:
                        print(f"false start: P{i} cut {x:.2f}-{y:.2f}")
                    segs = [seg for s0, s1 in segs for seg in ([s0, min(s1, x)], [max(s0, y), s1]) if seg[1] - seg[0] > 0.04]
            for a, b in segs:
                a, b = round(a * 25) / 25, round(b * 25) / 25
                if b - a < 0.2:
                    continue
                cuts.append({"i": i, "src_in": a, "src_out": b, "tl": round(t, 2)})
                t += b - a
        wav = _phj.get("source")
        if cuts and wav and os.path.exists(wav):
            c = cuts[-1]
            e = _speech_end(wav, c["src_in"], c["src_out"])
            if e and e + 0.06 < c["src_out"]:
                new_out = round((e + 0.06) * 25) / 25
                t -= c["src_out"] - new_out
                c["src_out"] = new_out
        if cuts_file:
            cuts = json.load(open(cuts_file, encoding="utf-8"))
            t = sum(c["src_out"] - c["src_in"] for c in cuts)
        self.CUTS = {}
        for c in cuts:
            self.CUTS.setdefault(c["i"], []).append(c)
        self.cuts, self.CUT = cuts, {i: v[0] for i, v in self.CUTS.items()}
        self.total = round(t, 2)
        self.G, self.scenes, self.overlays, self.punches, self.sfx_l, self.cuts_out = [], [], [], [], [], []
        self.plane_spans = []
        self.ae_ops = []  # extra AE ops (ae3d.py 3D camera plane scenes, aecards.py 3D UI cards)

    # ---- timing
    def W(self, i, k):
        s = _w_start(self.ph[i]["w"][k])
        segs = self.CUTS[i]
        c = next((c for c in segs if s < c["src_out"]), segs[-1])  # a word inside a cut-out false start lands on the restart
        return round(c["tl"] + max(0.0, min(s, c["src_out"]) - c["src_in"]), 2)

    def E(self, i):
        c = self.CUTS[i][-1]
        return round(c["tl"] + c["src_out"] - c["src_in"], 2)

    def S(self, i):
        return self.CUT[i]["tl"]

    def T(self, i, w0=0, w1=None):
        """Convenience span helper returning (start_tl, end_tl) for phrase i words [w0..w1]."""
        t0 = self.W(i, w0)
        t1 = self.E(i) if w1 is None else round(self.W(i, min(w1, len(self.ph[i]["w"]) - 1)) + 0.32, 2)
        return (t0, t1)

    def src_of(self, t):
        for c in self.cuts:
            if c["tl"] - 0.001 <= t < c["tl"] + c["src_out"] - c["src_in"]:
                return round(c["src_in"] + t - c["tl"], 3)

    # ---- content
    def text(self, end, words):
        self.G.append((end, words))

    def chunks(self, items, y=2780, style="bn_w", end=None, anim="pop", size=None):
        """Punchy word-chunk captions: 3-4 spoken words grouped into one line that lands ON its first word and
        holds until the next chunk lands (or `end`). items: [(t, "text"), (t, "text", "bn_g"), ...]. Highlight the
        key chunk in a colour style; keep white chunks off the white shirt (y >= 2400 gets the dark edge)."""
        items = _split_long_chunks(items, style, size, end)
        for n, it in enumerate(items):
            t, txt = it[0], it[1]
            st = it[2] if len(it) > 2 else style
            t_end = items[n + 1][0] if n + 1 < len(items) else (end or t + 1.2)
            if size:
                STY.setdefault(f"{st}@{size}", dict(STY[st], fontSize=size))
                st = f"{st}@{size}"
            self.G.append((round(t_end, 2), [(t, txt, st, 1080, y, anim)], "chunk"))

    def stack(self, end, kicker, chunks, y=2820, kicker_y=None, kicker_style="kicker_gold"):
        """High-stimulation bilingual stacked caption: English kicker + Bengali chunks."""
        if kicker_y is None:
            kicker_y = (y - 240) if y >= 1600 else (y - 220)
        if isinstance(kicker, (list, tuple)):
            k_txt, k_st = kicker[0], kicker[1]
        else:
            k_txt, k_st = kicker, kicker_style
        t_start = chunks[0][0] if chunks else 0
        self.text(end, [(t_start, k_txt, k_st, 1080, kicker_y)])
        self.chunks(chunks, y=y, end=end)

    CAP_EN_Y, CAP_BN_Y = 560, 880

    def cap(self, end, en, chunks, en_st="cap_en_gold", bn_st="cap_bn_w"):
        """Top-bar bilingual stack: English kicker (y 600) over spoken Bengali chunks (y 868).
        chunks: [(t, "bangla"), (t, "bangla", "cap_bn_gold"), ...]; each chunk holds until the next one."""
        t0 = chunks[0][0]
        if en:
            self.G.append((round(end, 2), [(t0, en, en_st, 1080, self.CAP_EN_Y, "rise")], "kicker"))
        for n, it in enumerate(chunks):
            t, txt = it[0], it[1]
            st = it[2] if len(it) > 2 else bn_st
            t_end = chunks[n + 1][0] if n + 1 < len(chunks) else end
            self.G.append((round(t_end, 2), [(t, txt, st, 1080, self.CAP_BN_Y, "pop")], "chunk"))

    def _get_dims(self, file, w, h):
        """REAL pixel size (ffprobe, cached in stock_dims.json) - file names lie: 6266251-uhd_2160_3840 is 1440x2560."""
        base = os.path.basename(file)
        cache = "E:/Anan/Assets/stock_dims.json"
        try:
            dims = json.load(open(cache, encoding="utf-8")) if os.path.exists(cache) else {}
            if base not in dims:
                import subprocess
                out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                      "-of", "csv=p=0", A + file], capture_output=True, text=True).stdout.strip().split(",")
                if len(out) >= 2 and out[0].isdigit():
                    dims[base] = [int(out[0]), int(out[1])]
                    json.dump(dims, open(cache, "w", encoding="utf-8"), indent=0)
            if base in dims:
                return dims[base][0], dims[base][1]
        except Exception:
            pass
        dims_path = "E:/Anan/NEW/edit/stock_dims.json"
        if os.path.exists(dims_path):
            try:
                dims = json.load(open(dims_path, encoding="utf-8"))
                if base in dims:
                    return dims[base][0], dims[base][1]
            except Exception:
                pass
        return (w or 1920), (h or 1080)

    def card(self, file, w=None, h=None, at=0, y=0.5, x=0.5, src_in=0, t1=None, width=None, height=1500, rot=0, bare=None, overflow=None):
        """bare=True: no Impact Stroke / Rounded Crop. overflow=True: spans full width 2160 edge-to-edge (Image 2 style)."""
        w, h = self._get_dims(file, w, h)
        is_landscape = (w >= h)
        if overflow is None:
            overflow = False
        if width is None:
            width = 1880
        if bare is None:
            bare = False
        sc = (width / w if is_landscape else height / h) * 100
        d = {"file": A + file, "at": at, "y": y, "x": x, "scale": round(sc, 1), "src_in": src_in, "rot": rot, "w": w, "h": h}
        if bare:
            d["bare"] = True
        if overflow:
            d["overflow"] = True
        if t1:
            d["t1"] = t1
        return d

    def full(self, file, w=None, h=None, src_in=0):
        w, h = self._get_dims(file, w, h)
        return {"file": A + file, "scale": round(max(2160 / w, 3840 / h) * 100, 1), "src_in": src_in}

    def scene(self, typ, t0, t1, items, no_base=False):
        keep = []
        for it in items:
            w, h = it.get("w", 1), it.get("h", 0)
            if typ in ("cards", "fly") and h > w:
                a, b = it["at"], it.get("t1", t1)
                self.scenes.append({"type": "full", "t0": a, "t1": b, "items": [self.full(it["file"][len(A):], w, h, it.get("src_in", 0))]})
                continue
            if typ == "fly" and w and it["scale"] * w / 100 < 1500:
                it["scale"] = round(1500 / w * 100, 1)
            keep.append(it)
        if keep or not items:
            sc = {"type": typ, "t0": t0, "t1": t1, "items": keep}
            if no_base:
                sc["no_base"] = True
            self.scenes.append(sc)

    def burst(self, file, t0, t1, src_in=0, rot=90, blend=12, cutout=True, tin="Cross Dissolve", tout="Cross Dissolve", front_src_in=None):
        """Money/confetti BURST on his real shot (user, 8-11-2026): a black-background clip rotated + scaled to fill the
        frame, Screen-blended (Premiere enum 12) over the A-roll, with his cut-out on top so it bursts BEHIND him."""
        w, h = self._get_dims(file, None, None)
        rw, rh = (h, w) if rot % 180 else (w, h)
        sc = round(max(2160 / rw, 3840 / rh) * 104, 1)
        self.scenes.append({"type": "full", "t0": t0, "t1": t1, "tin": tin, "tout": tout,
                            "items": [{"file": A + file, "scale": sc, "src_in": src_in, "rot": rot, "blend": blend}]})
        if cutout:
            self.cutout(t0, t1)
        if front_src_in is not None:  # handcam: his face fills the frame, so a few big bills also fly IN FRONT of him
            self.overlays.append({"file": A + file, "t0": t0, "t1": t1, "x": 0.5, "y": 0.5, "scale": round(sc * 1.25, 1),
                                  "src_in": front_src_in, "rot": -rot, "blend": blend, "plain": True})

    def overlay(self, el, t0, t1, x=0.5, y=0.74, scale=None):
        d = dict(el)
        d.update({"t0": t0, "t1": t1, "x": x, "y": y})
        d["scale"] = scale or el["scale"]
        self.overlays.append(d)

    def ae(self, ops):
        """Extra AE ops for the text comp (see ae3d.py and aecards.py)."""
        self.ae_ops += ops

    def plane_canvas(self, t0, t1, stops, tag=None, opaque_bg=True, line_style="orthogonal",
                     overview_start=False, overview_end=True):
        """Variation 1 — Connected FinTech Terminal Mind-Map Board on an 9600x10800 3D plane."""
        from ae3d import canvas_board_plane_3d
        tg = tag or f"BOARD_{len(self.scenes)+1}"
        self.plane_spans.append((round(t0, 2), round(t1, 2)))
        if opaque_bg:
            self.scene("cards", t0, t1, [])
        self.ae_ops += canvas_board_plane_3d(
            self, f"R{self.key}_TEXT", t0, t1, stops,
            tag=tg, opaque_bg=opaque_bg, line_style=line_style,
            overview_start=overview_start, overview_end=overview_end,
        )

    def plane_tunnel(self, t0, t1, stops, tag=None, opaque_bg=True):
        """Variation 2 — 3D Z-Depth Chronological Fly-Through Corridor (camera flies forward along Z)."""
        from ae3d import timeline_tunnel_3d
        tg = tag or f"TUNNEL_{len(self.scenes)+1}"
        self.plane_spans.append((round(t0, 2), round(t1, 2)))
        if opaque_bg:
            self.scene("cards", t0, t1, [])
        self.ae_ops += timeline_tunnel_3d(self, f"R{self.key}_TEXT", t0, t1, stops, tag=tg, opaque_bg=opaque_bg)

    def plane_hub(self, t0, t1, hub, satellites, tag=None, opaque_bg=True, overview_end=True):
        """Variation 3 — Central Core Hub + Radiating Spoke Satellites with orbital camera whips."""
        from ae3d import radial_hub_3d
        tg = tag or f"HUB_{len(self.scenes)+1}"
        self.plane_spans.append((round(t0, 2), round(t1, 2)))
        if opaque_bg:
            self.scene("cards", t0, t1, [])
        self.ae_ops += radial_hub_3d(self, f"R{self.key}_TEXT", t0, t1, hub, satellites, tag=tg,
                                     opaque_bg=opaque_bg, overview_end=overview_end)

    def plane_versus(self, t0, t1, left_side, right_side, verdict=None, tag=None, opaque_bg=True):
        """Variation 4 — Opposing 3D Angled V-Stage Monoliths (`+16°` vs `-16°` Y-yaw) + Center Verdict Bridge."""
        from ae3d import versus_split_3d
        tg = tag or f"VS_{len(self.scenes)+1}"
        self.plane_spans.append((round(t0, 2), round(t1, 2)))
        if opaque_bg:
            self.scene("cards", t0, t1, [])
        self.ae_ops += versus_split_3d(self, f"R{self.key}_TEXT", t0, t1, left_side, right_side,
                                       verdict=verdict, tag=tg, opaque_bg=opaque_bg)

    def plane_kinetic(self, t0, t1, beats, tag=None, opaque_bg=True):
        """Variation 5 — Pure Box-Free 3D Architectural Typography with 90° Camera Z-Pivot Turns."""
        from ae3d import kinetic_wall_3d
        tg = tag or f"KWALL_{len(self.scenes)+1}"
        self.plane_spans.append((round(t0, 2), round(t1, 2)))
        if opaque_bg:
            self.scene("cards", t0, t1, [])
        self.ae_ops += kinetic_wall_3d(self, f"R{self.key}_TEXT", t0, t1, beats, tag=tg, opaque_bg=opaque_bg)

    def plane_flowchart(self, t0, t1, nodes=None, tag=None, opaque_bg=True, beats=None):
        nodes = nodes or beats or []
        """Variation 6 — 3D Logic Flowchart / Roadmap Decision Tree on the perspective grid."""
        from ae3d import flowchart_plane_3d
        tg = tag or f"FLOW_{len(self.scenes)+1}"
        self.plane_spans.append((round(t0, 2), round(t1, 2)))
        if opaque_bg:
            self.scene("cards", t0, t1, [])
        self.ae_ops += flowchart_plane_3d(self, f"R{self.key}_TEXT", t0, t1, nodes, tag=tg, opaque_bg=opaque_bg)

    def _max_punch_scale(self, t0, t1):
        """Peak V8 camera adjustment scale overlapping [t0, t1] (ignoring the initial 0.24s hook snap)."""
        peak = 100.0
        s0 = max(0.28, t0)
        if s0 >= t1:
            return 1.0
        for pu in self.punches:
            keys = pu.get("keys", [])
            if not keys:
                continue
            p_start = keys[0][0]
            p_end = keys[-1][0] + 2.5
            if p_end < s0 or p_start > t1:
                continue
            for kt, kv in keys:
                if kt >= 0.25 and s0 - 0.8 <= kt <= t1 + 0.5:
                    peak = max(peak, float(kv))
        return max(1.0, peak / 100.0)

    def punch(self, keys, fy=0.36):
        self.punches.append({"keys": keys, "fy": fy})

    def sfx(self, file, t, role, db, ln):
        self.sfx_l.append({"file": file, "t": t, "role": "pop" if role == "pop" else role, "db": db, "len": ln})

    def stop_drop(self, t0, t1):
        """Audio Stop-Drop: music to silence over [t0, t1] (0.4-0.8 s before the climax word), slams back at t1."""
        self.music["drops"].append([round(t0, 2), round(t1, 2)])

    def cutout(self, t0, t1):
        self.cuts_out.append((t0, t1))

    # ---- output
    def _cutout_cover(self):
        """Cut-out spans the plan asked for, matched against the .mov files that REALLY exist in cutouts/.
        A file covers source [ss_f, ss_f + d_f]; only the overlapping part is used (with src_in into the file)."""
        n = self.key
        cdir = os.path.join(self.out_dir, "cutouts")
        files = []
        if os.path.isdir(cdir):
            for f in os.listdir(cdir):
                m = re.match(rf"r{n}_cut_([0-9.]+)_([0-9.]+)\.mov$", f)
                if m:
                    files.append((float(m.group(1)), float(m.group(2)), os.path.join(cdir, f).replace("\\", "/")))
        jobs, couts = [], []
        for a0, b0 in self.cuts_out:
            for cc in self.cuts:
                c0, c1 = cc["tl"], round(cc["tl"] + cc["src_out"] - cc["src_in"], 2)
                a, b = max(a0, c0), min(b0, c1)
                a, b = round(a * 25) / 25, round(b * 25) / 25
                if b - a < 0.08:
                    continue
                ss = round((cc["src_in"] + a - c0) * 25) / 25
                jobs.append([self.src, ss, round(b - a, 2), os.path.join(cdir, f"r{n}_cut_{ss:.2f}_{b - a:.2f}.mov").replace("\\", "/")])
                best = None
                for fs_, fd_, fp_ in files:
                    o0, o1 = max(ss, fs_), min(ss + (b - a), fs_ + fd_)
                    if o1 - o0 >= 0.3 and (best is None or o1 - o0 > best[1] - best[0]):
                        best = (o0, o1, fs_, fp_)
                if best:
                    o0, o1, fs_, fp_ = best
                    couts.append({"file": fp_, "t0": round(a + o0 - ss, 2), "t1": round(a + o1 - ss, 2), "src_in": round(o0 - fs_, 2)})
                else:
                    print(f"cut-out not rendered for source {ss:.2f}+{b - a:.2f} -> skipped")
        return jobs, couts

    def write(self):
        n, main = self.key, f"R{self.key}_TEXT"
        front = f"R{self.key}_FRONT"
        spans = [(round(a * 25) / 25, round(b * 25) / 25) for a, b in self.cuts_out]
        ops = [{"operation": "comp.create", "args": {"name": main, "width": 2160, "height": 3840, "fps": 25, "duration": self.total}},
               {"operation": "comp.create", "args": {"name": front, "width": 2160, "height": 3840, "fps": 25, "duration": self.total}}]
        pops, k = [], 0
        raw_items = []
        for g in self.G:
            end, words, kind = (g + (None,))[:3]
            for item in words:
                if len(item) == 6:
                    t, txt, st, x, y, anim = item
                else:
                    t, txt, st, x, y = item
                    anim = _default_anim_for_style(st)
                raw_items.append({
                    "t": t, "end": end, "txt": txt, "st": st, "x": x, "y": y,
                    "anim": anim, "kind": kind
                })

        jobs, couts = self._cutout_cover()
        self._couts = couts

        def _bg(t):
            for p0, p1 in self.plane_spans:
                if p0 <= t < p1:
                    return "plane"
            for s in self.scenes:
                if s["t0"] <= t < s["t1"] and s["type"] in ("full", "cards", "fly"):
                    return s["type"]
            return "aroll"

        def _covered(t0, t1):
            return any(cu["t0"] - 0.02 <= t0 and t1 <= cu["t1"] + 0.02 for cu in couts)

        # 1. Consecutive chunks swap cleanly on the beat
        chunks = [it for it in raw_items if it["kind"] == "chunk"]
        chunks.sort(key=lambda it: it["t"])
        for idx in range(len(chunks) - 1):
            c_curr = chunks[idx]
            c_next = chunks[idx + 1]
            if c_curr["end"] > c_next["t"]:
                c_curr["end"] = c_next["t"]

        # 2. Collision resolution between Hero Callouts and Chunks
        callouts = [it for it in raw_items if it["kind"] != "chunk"]
        for c in chunks:
            for h in callouts:
                if max(c["t"], h["t"]) < min(c["end"], h["end"]) - 0.12:
                    dist = abs(c["y"] - h["y"])
                    h_size = STY.get(h["st"], {}).get("fontSize", 200)
                    thresh = 420 if h_size >= 350 else 180
                    if dist < thresh:
                        h["end"] = min(h["end"], c["t"]) if h["t"] < c["t"] else h["end"]
                        print(f"WARNING caption vs callout '{h['txt']}' / '{c['txt']}' - callout shortened")

        # 3. Collision resolution between two Callouts
        for i in range(len(callouts)):
            h1 = callouts[i]
            for j in range(i + 1, len(callouts)):
                h2 = callouts[j]
                if max(h1["t"], h2["t"]) < min(h1["end"], h2["end"]) - 0.12:
                    if abs(h1["y"] - h2["y"]) < 420:
                        if h1["t"] < h2["t"]:
                            h1["end"] = min(h1["end"], h2["t"])
                        elif h2["t"] < h1["t"]:
                            h2["end"] = min(h2["end"], h1["t"])
                        else:
                            if h1["y"] <= h2["y"]:
                                h1["y"] = 600
                                h2["y"] = 1050
                            else:
                                h2["y"] = 600
                                h1["y"] = 1050

        # ---- HARD GUARDS (2026-11-05 review): no text on Anan's face, no duplicate text, no behind-head word
        # without a real cut-out (without the cut-out a "behind" word is simply printed over his head).
        FACE = (1250, 2520) if self.handcam else (1250, 3050)  # handcam (measured 9-11: mouth ends ~2450): pops 2600 + subs 2850 = stacked lower third
        keep_items = []
        for it in raw_items:
            behind_it = (900 <= it["y"] <= 1700) and it["kind"] not in ("chunk", "kicker")
            if behind_it:
                if not _covered(it["t"], min(it["end"], it["t"] + 0.6)):
                    print(f"DROP behind-head word without cut-out: '{it['txt']}' @ {it['t']}")
                    continue
                cov_end = max((cu["t1"] for cu in couts if cu["t0"] - 0.02 <= it["t"] <= cu["t1"]), default=it["end"])
                it["end"] = min(it["end"], cov_end)
            elif FACE[0] <= it["y"] <= FACE[1]:
                bgs = {_bg(it["t"]), _bg(max(it["t"], it["end"] - 0.05))}
                if "aroll" in bgs:
                    raise ValueError(f"TEXT OVER FACE: '{it['txt']}' y={it['y']} @ {it['t']}-{it['end']}")
            keep_items.append(it)
        raw_items = keep_items
        _n = lambda s: "".join(ch for ch in s.upper() if ch.isalnum())
        for i1 in range(len(raw_items)):
            for i2 in range(i1 + 1, len(raw_items)):
                a_, b_ = raw_items[i1], raw_items[i2]
                if max(a_["t"], b_["t"]) < min(a_["end"], b_["end"]) - 0.05:
                    na, nb = _n(a_["txt"]), _n(b_["txt"])
                    # captions now spell spoken English in English (user, 8-11-2026): a caption may CONTAIN the big
                    # keyword above it ("money management করবা" under "MONEY"); only identical overlays are duplicates
                    one_chunk = (a_.get("kind") == "chunk") != (b_.get("kind") == "chunk")
                    sub = (not one_chunk) and min(len(na), len(nb)) >= 4 and (na in nb or nb in na)
                    if na and nb and na == nb and one_chunk:
                        # a caption chunk that IS the big keyword on screen (e.g. split "trading chart" under
                        # "TRADING CHART"): the keyword already says it - hide the caption for that beat
                        (a_ if a_.get("kind") == "chunk" else b_)["drop"] = True
                        continue
                    if na and nb and (na == nb or sub):
                        raise ValueError(f"DUPLICATE TEXT on screen: '{a_['txt']}' / '{b_['txt']}' @ {a_['t']}")
                    if abs(a_["y"] - b_["y"]) < 180:
                        raise ValueError(f"OVERLAP: '{a_['txt']}' / '{b_['txt']}' @ {a_['t']}")

        raw_items = [it for it in raw_items if not it.get("drop")]
        for it in raw_items:
            t = it["t"]
            txt = it["txt"]
            st = it["st"]
            x = it["x"]
            y = it["y"]
            anim = it["anim"]
            kind = it["kind"]
            end = it["end"]

            k += 1
            name = f"T{k:02d}"
            t_end0 = end if end > t + 0.15 else (t + 0.40)
            # Behind Anan's head in R*_TEXT (V7): only hero words explicitly placed in head zone (900 <= y <= 1500) and NOT chunks.
            behind = (900 <= y <= 1700) and (kind not in ("chunk", "kicker"))
            comp = main if behind else front
            zoom_k = self._max_punch_scale(t, t_end0) if comp == main else 1.0
            eff_maxw = min(1760, int(1880 / zoom_k))
            txt, sty, x = _fit(txt, st, x, maxw=eff_maxw, stack=(kind != "chunk"))

            # Strict text stroke policy: eliminate white-on-white, light-on-light, or same-color stroke blobs
            apply_stroke = sty.get("applyStroke", False)
            if apply_stroke:
                fc = sty.get("fillColor", [1.0, 1.0, 1.0])
                sc = sty.get("strokeColor", [0.04, 0.06, 0.10])
                col_diff = sum(abs(a - b) for a, b in zip(fc[:3], sc[:3])) if isinstance(fc, list) and isinstance(sc, list) else 1.0
                is_light_fill = (0.299 * fc[0] + 0.587 * fc[1] + 0.114 * fc[2] > 0.65) if isinstance(fc, list) and len(fc) >= 3 else False
                is_white_stroke = (sc == [1.0, 1.0, 1.0] or sc == WHITE)
                if col_diff < 0.4 or (is_white_stroke and is_light_fill):
                    apply_stroke = False
            sty["applyStroke"] = apply_stroke
            if kind == "chunk" and y >= 2200:  # 11-11-2026: captions on his WHITE shirt vanished -> black stroke BEHIND the fill
                sty.update(applyStroke=True, strokeColor=[0.0, 0.0, 0.0], strokeWidth=22, strokeOverFill=False)

            if not behind:
                if y < 1000:
                    y = max(460, y)  # Allow top kickers at y>=460, clear of status bar (380px)
                elif y >= 2650:
                    y = min(2850, y)  # Allow lower third subtitles at y<=2850, clear of IG UI

            t_end = round(end if end > t else (t + 0.40), 2)
            if kind == "chunk":
                t_out_start = round(max(t + 0.08, t_end - 0.06), 2)
            else:
                t_out_start = round(max(t + 0.12, t_end - 0.12), 2)
            for p0, p1 in self.plane_spans:
                if t < p0 < t_end and p0 - t >= 0.28:
                    t_end = p0
                    t_out_start = round(max(t + 0.16, t_end - 0.12), 2)
                if t < p1 and t_end > p0 and anim in ("plane_flip", "3d_flip"):
                    anim = "pop"

            sh_op = 235 if y >= 2200 else 208
            ops += [
                {"operation": "layer.create_text", "args": {"comp": comp, "text": txt, "name": name}},
                {"operation": "text.set_style", "args": {"comp": comp, "layer": name, "justification": "center", **sty}},
                {"operation": "layer.set_timing", "args": {"comp": comp, "layer": name, "inPoint": t, "outPoint": t_end}},
                {"operation": "effect.add", "args": {"comp": comp, "layer": name, "matchName": "ADBE Drop Shadow"}},
                {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Opacity"], "value": sh_op}},
                {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Distance"], "value": 20}},
                {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Softness"], "value": 50}},
            ]

            if anim in ("plane_flip", "3d_flip"):
                # 3D Spatial Plane Flip-In (threeDLayer=True, X-Rotation +55 -> -4 -> 0, Z-depth +280 -> 0)
                t1 = round(t + 0.22, 2)
                t2 = round(t + 0.34, 2)
                ops += [
                    {"operation": "layer.set_props", "args": {"comp": comp, "layer": name, "props": {"threeDLayer": True}}},
                    {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Material Options", "Accepts Lights"], "value": 0}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"],
                                                                  "times": [t, t1, t_out_start, t_end],
                                                                  "values": [[x, y + 60, 280], [x, y, 0], [x, y, 0], [x, y - 50, -180]]}},
                    {"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "keyIndex": 2,
                                                                   "inSpeed": 0, "inInfluence": 86, "outSpeed": 0, "outInfluence": 35}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "X Rotation"],
                                                                  "times": [t, t1, t2], "values": [55, -4, 0]}},
                    {"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": name, "property": ["Transform", "X Rotation"], "keyIndex": 2,
                                                                   "inSpeed": 0, "inInfluence": 85, "outSpeed": 0, "outInfluence": 35}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Opacity"],
                                                                  "times": [t, round(t + 0.12, 2), t_out_start, t_end],
                                                                  "values": [0, 100, 100, 0]}},
                ]
            elif anim == "pop":
                # Devin Jatho / Keanu Visuals snap-scale overshoot (60% -> 106% -> 100%)
                t1 = round(t + 0.20, 2)
                t2 = round(t + 0.32, 2)
                ops += [
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"],
                                                                  "times": [t, t_end], "values": [[x, y], [x, y]]}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Scale"],
                                                                  "times": [t, t1, t2, t_out_start, t_end],
                                                                  "values": [[60, 60], [106, 106], [100, 100], [100, 100], [86, 86]]}},
                    {"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": name, "property": ["Transform", "Scale"], "keyIndex": 2,
                                                                   "inSpeed": 0, "inInfluence": 85, "outSpeed": 0, "outInfluence": 35}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Opacity"],
                                                                  "times": [t, round(t + 0.12, 2), t_out_start, t_end],
                                                                  "values": [0, 100, 100, 0]}},
                ]
            elif anim == "rise":
                # Editorial vertical reveal rise (y + 110 -> y)
                t1 = round(t + 0.24, 2)
                ops += [
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"],
                                                                  "times": [t, t1, t_out_start, t_end],
                                                                  "values": [[x, y + 110], [x, y], [x, y], [x, y - 70]]}},
                    {"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "keyIndex": 2,
                                                                   "inSpeed": 0, "inInfluence": 85, "outSpeed": 0, "outInfluence": 33}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Opacity"],
                                                                  "times": [t, round(t + 0.16, 2), t_out_start, t_end],
                                                                  "values": [0, 100, 100, 0]}},
                ]
            elif anim == "slam":
                # Z-Depth Shock Slam (185% -> 96% -> 100%)
                t1 = round(t + 0.16, 2)
                t2 = round(t + 0.28, 2)
                ops += [
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"],
                                                                  "times": [t, t_end], "values": [[x, y], [x, y]]}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Scale"],
                                                                  "times": [t, t1, t2, t_out_start, t_end],
                                                                  "values": [[185, 185], [96, 96], [100, 100], [100, 100], [88, 88]]}},
                    {"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": name, "property": ["Transform", "Scale"], "keyIndex": 2,
                                                                   "inSpeed": 0, "inInfluence": 90, "outSpeed": 0, "outInfluence": 30}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Opacity"],
                                                                  "times": [t, round(t + 0.08, 2), t_out_start, t_end],
                                                                  "values": [0, 100, 100, 0]}},
                ]
            else:
                # Fast magnetic whip slide
                t1 = round(t + 0.24, 2)
                ops += [
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"],
                                                                  "times": [t, t1, t_out_start, t_end],
                                                                  "values": [[x + 680, y], [x, y], [x, y], [x - 680, y]]}},
                    {"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "keyIndex": 2,
                                                                   "inSpeed": 0, "inInfluence": 85, "outSpeed": 0, "outInfluence": 33}},
                    {"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": name, "property": ["Transform", "Opacity"],
                                                                  "times": [t, round(t + 0.12, 2), t_out_start, t_end],
                                                                  "values": [0, 100, 100, 0]}},
                ]
            pops.append(t)

        comp = main
        ops += self.ae_ops
        for c in (main, front):
            ops += [{"operation": "comp.set_props", "args": {"comp": c, "props": {"motionBlur": True, "shutterAngle": 180}}}]
            if any(o["args"].get("comp") == c and o["operation"] in ("layer.create_text", "layer.create_shape") for o in ops):
                ops += [{"operation": "layer.set_props", "args": {"comp": c, "layer": "all", "props": {"motionBlur": True}}}]
        dels = [{"operation": "comp.delete", "args": {"comp": c}} for c in (main, front)]
        json.dump({"operation": "batch.run", "args": {"ops": dels + ops}, "timeoutMs": 600000},
                  open(os.path.join(self.out_dir, f"r{n}_ae_call.json"), "w", encoding="utf-8"), ensure_ascii=False)
        json.dump({"operation": "batch.run", "args": {"ops": ops}, "timeoutMs": 600000}, open(os.path.join(self.out_dir, f"r{n}_ae_new.json"), "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(self.cuts, open(os.path.join(self.out_dir, f"r{n}_cuts.json"), "w"), indent=0)
        busy = [(s["t"], s["t"] + s["len"]) for s in self.sfx_l if s["role"] == "pop"]
        out_sfx = list(self.sfx_l)
        for t in pops:
            if all(not (a - 0.05 < t < b) for a, b in busy):
                out_sfx.append({"file": "Very Subtle.wav", "t": t, "role": "pop", "db": -5, "len": 0.35})
                busy.append((t, t + 0.35))
        for s_ in out_sfx:
            s_["len"] = max(0.1, min(s_["len"], round(self.total - s_["t"] - 0.04, 2)))
        jobs, couts = jobs, self._couts
        json.dump(jobs, open(os.path.join(self.out_dir, f"r{n}_cutouts.json"), "w"), indent=0)
        filtered_punches = []
        for pu in self.punches:
            keys = pu.get("keys", [])
            if not keys:
                continue
            pt = keys[0][0]
            in_plane = any(p0 - 0.2 <= pt <= p1 + 0.2 for p0, p1 in self.plane_spans)
            if not in_plane:
                filtered_punches.append(pu)

        # music ramps (user, 9-11-2026): read the WHOLE track, start the bed on its steadiest stretch (music_src_in="auto")
        # and key the Level so swells and dips inside the reel are evened out (music_curve.py)
        try:
            import music_curve
            if self.music["src_in"] == "auto":
                self.music["src_in"] = music_curve.pick_start(self.music["path"], self.total)[0]
            self.music["curve"] = music_curve.curve(self.music["path"], self.music["src_in"], self.total)
            print(f"reel {n} music: start {self.music['src_in']} s, {len(self.music['curve'])} ramp keys")
        except Exception as e:
            if self.music["src_in"] == "auto":
                self.music["src_in"] = 0
            print(f"reel {n} music curve failed ({e})")
        if self.auto_mix:
            try:
                from mix_levels import solve
                mx = solve(self.src, self.cuts, self.music["path"], self.music["src_in"], self.total)
                self.voice_db, self.music["db"] = mx["voice_db"], mx["music_db"]
                print(f"reel {n} mix: voice {mx['voice_lufs_raw']} LUFS -> {mx['voice_db']:+} dB, "
                      f"music {mx['music_lufs_raw']} LUFS -> {mx['music_db']:+} dB (bed {mx['voice_on_tl'] - mx['music_on_tl']:.0f} LU under)")
            except Exception as e:  # ffmpeg missing etc: keep the fixed levels
                print(f"reel {n} mix: measuring failed ({e}); fixed voice +3 / music {self.music['db']} dB")
        prem = {
            "seq": f"Reel_{self.n}_{self.date}" + (f" {self.tag}" if self.tag else ""),
            "aroll": self.aroll,
            "total": self.total,
            "grid": A + "bg_blueprint_grid.jpg",
            "grid_scale": round(3840 / 4001 * 100, 1),
            "trans_frames": 5,
            "jump": getattr(self, "jump", {"scales": [100, 110], "trans": "Zoom Blur", "frames": 4}),
            "trans_in": ["Zoom Blur", "Flash", "Directional Blur", "Cross Dissolve"],
            "trans_out": "Cross Dissolve",
            "stroke_px": 5,
            "stroke_alpha": 115,
            "cuts": self.cuts,
            "voice_db": self.voice_db,
            "lumetri": json.load(open(GRADE, encoding="utf-8"))["lumetri"],
            "punches": filtered_punches,
            "scenes": self.scenes,
            "overlays": self.overlays,
            "cutouts": couts,
            "sfx": out_sfx,
            "music": dict(self.music, file=self.music["path"].replace("\\", "/").split("/")[-1]),
            "cover": None if self.handcam else A + "top_cover_curtain.png",
            "ae": {"aep": self.aep, "comp": main, "front": front},
        }
        json.dump(prem, open(os.path.join(self.out_dir, f"r{n}_prem.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"reel {n}: {self.total}s, {len(self.cuts)} cuts, {k} words, {len(self.scenes)} scenes, {len(self.overlays)} overlays, "
              f"{len(out_sfx)} sfx, cutouts {[(j[1], j[2]) for j in jobs]}")
