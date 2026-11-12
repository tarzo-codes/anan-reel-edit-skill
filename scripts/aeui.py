"""Screen-space UI pieces for Anan reels (8-11-2026 user review of the handcam pilot), built as live AE layers:

  step_badge  - numbers / pointers: an animated number inside a coloured circle (pop + drawn ring that spins)
  comment_ui  - CTA: a simple TikTok (white sheet, pink send) or YouTube (dark sheet, blue send) comment box that
                types the comment (Bangla-cluster-safe), sends it, and the comment pops into the list.
                Replaces Motion_Templates/elements/comment_bubble_type.mov (it shows "@yourhandle").

    from aeui import step_badge, comment_ui
    r.ae(step_badge(r, "R1_FRONT", t0, t1, "2", 300, 506, color=GOLD))
    r.ae(comment_ui(r, "R1_FRONT", t0, t1, "আমি ট্রেডিং শিখতে চাই", type_start, type_end, send, platform="tiktok"))
Put them in the reel's _FRONT comp (screen space, does not zoom with punches).
"""
import json

from aecards import _glow, _k, _shape, _text, _NEON_N, GOLD

INK = [0.06, 0.08, 0.13]


def step_badge(r, comp, t0, t1, num, x, y, size=260, color=GOLD, ink=INK):
    """(x, y) = circle centre. Filled disc pops 0 -> 118 -> 100 %, outer ring draws on and spins, number pops a beat later."""
    _NEON_N[0] += 1
    nm = f"BADGE_{_NEON_N[0]:02d}"
    out = round(max(t0 + 0.3, t1 - 0.14), 2)
    ops = _shape(comp, nm + "_disc", t0, t1, [x, y], [{"ellipse": [size, size], "fill": color}])
    ops += _k(comp, nm + "_disc", ["Transform", "Scale"], [t0, round(t0 + 0.16, 2), round(t0 + 0.28, 2), out, t1],
              [[0, 0], [118, 118], [100, 100], [100, 100], [0, 0]], ease=[2, 3])
    ring = round(size * 1.24)
    ops += _shape(comp, nm + "_ring", t0, t1, [x, y], [{"ellipse": [ring, ring], "trim": True, "stroke": color, "width": 9}])
    ops += _k(comp, nm + "_ring", ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [round(t0 + 0.08, 2), round(t0 + 0.45, 2)], [0, 100], ease=[2])
    ops += _k(comp, nm + "_ring", ["Transform", "Opacity"], [t0, round(t0 + 0.08, 2), out, t1], [0, 100, 100, 0])
    ops.append({"operation": "expression.set", "args": {"comp": comp, "layer": nm + "_ring", "property": ["Transform", "Rotation"],
                                                        "expression": "(time-inPoint)*40"}})
    ops += _glow(comp, nm + "_ring", radius=30, intensity=1.2)
    fs = round(size * 0.62)
    ops += _text(comp, nm + "_num", str(num), t0, t1, [x, round(y + fs * 0.36, 1)], "PlusJakartaSans-ExtraBold", fs, ink, just="center")
    ops += _k(comp, nm + "_num", ["Transform", "Scale"], [round(t0 + 0.08, 2), round(t0 + 0.24, 2), round(t0 + 0.36, 2), out, t1],
              [[0, 0], [125, 125], [100, 100], [100, 100], [0, 0]], ease=[2, 3])
    r.sfx("pop-39222.mp3", t0, "extra", -7, 0.4)
    return ops


def bn_clusters(s):
    """Prefix lengths at Bangla grapheme-cluster boundaries: typing never shows a lone vowel sign or a hanging hasant."""
    marks = set(range(0x0981, 0x0984)) | {0x09BC} | set(range(0x09BE, 0x09CE)) | {0x09D7, 0x200C, 0x200D}
    b = [0]
    for i in range(1, len(s)):
        if ord(s[i]) in marks or ord(s[i - 1]) == 0x09CD:
            continue
        b.append(i)
    b.append(len(s))
    return b


def comment_ui(r, comp, t0, t1, text, type_start, type_end, send, platform="tiktok", cy=2880, w=1900, tag="CMT",
               user="@you", count=None):
    tt = platform == "tiktok"
    BG = [1.0, 1.0, 1.0] if tt else [0.06, 0.06, 0.06]
    FG = [0.09, 0.09, 0.14] if tt else [0.95, 0.95, 0.95]
    MUTE = [0.55, 0.56, 0.60] if tt else [0.67, 0.67, 0.67]
    FIELD = [0.94, 0.94, 0.95] if tt else [0.16, 0.16, 0.16]
    ACC = [1.0, 0.17, 0.33] if tt else [0.24, 0.65, 1.0]
    AVA = [0.15, 0.85, 0.85] if tt else [0.96, 0.45, 0.10]
    h = 880  # sizes x1.35 after the pilot review: 58-72 px text read tiny on a phone
    top, x0 = cy - h / 2, 1080 - w / 2
    sheet = f"{tag}_sheet"
    ops = _shape(comp, sheet, t0, t1, [1080, cy], [{"rect": [w, h], "round": 64, "fill": BG}])
    ops += [{"operation": "effect.add", "args": {"comp": comp, "layer": sheet, "matchName": "ADBE Drop Shadow"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": sheet, "effectIndex": 1, "property": ["Opacity"], "value": 60}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": sheet, "effectIndex": 1, "property": ["Distance"], "value": 20}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": sheet, "effectIndex": 1, "property": ["Softness"], "value": 80}}]
    kids = []

    def kid(o, name):
        kids.append(name)
        return o

    hdr = f"{count or '1,284'} comments" if tt else f"Comments   {count or '3.2K'}"
    ops += kid(_text(comp, f"{tag}_hdr", hdr, t0, t1, [1080 if tt else x0 + 90, top + 125], "PlusJakartaSans-ExtraBold", 76, FG,
                     just="center" if tt else "left"), f"{tag}_hdr")
    ops += kid(_text(comp, f"{tag}_x", "x", t0, t1, [x0 + w - 110, top + 125], "PlusJakartaSans-ExtraBold", 84, MUTE, just="center"), f"{tag}_x")
    # the posted comment row (appears at send)
    ry = top + 340
    ops += kid(_shape(comp, f"{tag}_ava", t0, t1, [x0 + 170, ry], [{"ellipse": [170, 170], "fill": AVA}]), f"{tag}_ava")
    ops += kid(_text(comp, f"{tag}_user", user + ("" if tt else "  ·  just now"), t0, t1, [x0 + 300, ry - 34],
                     "PlusJakartaSans-ExtraBold", 62, MUTE), f"{tag}_user")
    ops += kid(_text(comp, f"{tag}_said", text, t0, t1, [x0 + 300, ry + 86], "HindSiliguri-Bold", 100, FG), f"{tag}_said")
    ops += kid(_text(comp, f"{tag}_like", "<3" if tt else "Reply", t0, t1, [x0 + w - 130, ry + 22], "PlusJakartaSans-ExtraBold", 66, MUTE,
                     just="center"), f"{tag}_like")
    for nm in (f"{tag}_ava", f"{tag}_user", f"{tag}_said", f"{tag}_like"):
        ops += _k(comp, nm, ["Transform", "Opacity"], [round(send + 0.05, 2), round(send + 0.2, 2)], [0, 100])
    # input field + typing
    iy = top + h - 165
    fx0 = x0 + (70 if tt else 250)
    fx1 = x0 + w - 230
    if not tt:
        ops += kid(_shape(comp, f"{tag}_me", t0, t1, [x0 + 140, iy], [{"ellipse": [150, 150], "fill": AVA}]), f"{tag}_me")
    ops += kid(_shape(comp, f"{tag}_field", t0, t1, [round((fx0 + fx1) / 2), iy], [{"rect": [round(fx1 - fx0), 210], "round": 105, "fill": FIELD}]),
               f"{tag}_field")
    ops += kid(_text(comp, f"{tag}_ph", "Add comment..." if tt else "Add a comment...", t0, t1, [fx0 + 70, iy + 28],
                     "PlusJakartaSans-ExtraBold", 76, MUTE), f"{tag}_ph")
    ops += _k(comp, f"{tag}_ph", ["Transform", "Opacity"], [type_start, round(type_start + 0.04, 2)], [100, 0])
    b = bn_clusters(text)
    rate = round((len(b) - 1) / max(0.3, type_end - type_start), 3)
    expr = (f"var s={json.dumps(text)}; var b={json.dumps(b)}; var k=Math.floor(Math.max(0,time-{type_start})*{rate}); "
            f"var n=b[Math.min(k,b.length-1)]; var on=(k<b.length-1)||(Math.floor(time*3)%2==0); "
            f"(time<{send}) ? s.substr(0,n)+(on?'|':'') : ''")
    ops += kid(_text(comp, f"{tag}_typed", text, t0, t1, [fx0 + 70, iy + 34], "HindSiliguri-Bold", 96, FG), f"{tag}_typed")
    ops += [{"operation": "expression.set", "args": {"comp": comp, "layer": f"{tag}_typed", "property": ["Text", "Source Text"], "expression": expr}}]
    ops += kid(_shape(comp, f"{tag}_send", t0, t1, [x0 + w - 120, iy],
                      [{"path": [[0, 32], [0, -32]], "stroke": [1, 1, 1], "width": 15},
                       {"path": [[-26, -6], [0, -32], [26, -6]], "stroke": [1, 1, 1], "width": 15},
                       {"ellipse": [160, 160], "fill": ACC}]), f"{tag}_send")
    ops += _k(comp, f"{tag}_send", ["Transform", "Opacity"], [t0, type_start, round(type_start + 0.1, 2)], [35, 35, 100])
    ops += _k(comp, f"{tag}_send", ["Transform", "Scale"], [round(send - 0.02, 2), round(send + 0.06, 2), round(send + 0.18, 2), round(send + 0.3, 2)],
              [[100, 100], [78, 78], [116, 116], [100, 100]], ease=[3])
    for k_ in kids:  # everything rides the sheet
        # jump=False keeps each kid where it was placed (jump=True would read its screen position as an offset)
        ops.append({"operation": "layer.set_parent", "args": {"comp": comp, "layer": k_, "parentLayer": sheet, "jump": False}})
    ops += _k(comp, sheet, ["Transform", "Position"], [t0, round(t0 + 0.32, 2), round(t1 - 0.25, 2), t1],
              [[1080, cy + 1200], [1080, cy], [1080, cy], [1080, cy + 1200]], ease=[2, 4])
    r.sfx("whoosh-motion-243505.mp3", round(t0 - 0.05, 2), "bed", -14, 0.6)
    r.sfx("koiroylers-gear-click-351962.mp3", type_start, "extra", -12, round(type_end - type_start, 2))
    r.sfx("mouse-click-104737.mp3", send, "feat", -4, 0.3)
    r.sfx("pop-39222.mp3", round(send + 0.08, 2), "extra", -8, 0.4)
    return ops


def _is_bn(s):
    return any("ঀ" <= ch <= "৿" for ch in (s or ""))


def hook_slam(t0, hero):
    """time the hero SLAMS in hook_title (HC lands the money / fire burst on the same frame)"""
    reveal0 = round(t0 + 0.28, 2)
    if _is_bn(hero):
        return round(reveal0 + 0.18, 2)
    return round(reveal0 + min(0.6, 0.06 * len(hero) + 0.12), 2)


def hook_title(r, comp, t0, t1, kicker, hero, sub=None, color=None, tag="HOOK", big=False, center=1920):
    """HOOK v2 (user, 8-11-2026 pass 3: "nice animation, impactful, centred, no subtitles while it is shown").
    CENTRED in the frame over a soft dark band: the kicker TYPES in (mono, gold); the HERO cascades in letter by letter
    (each letter drops + shrinks from 170 % with blur), then the whole line SLAMS (scale bounce + shake) with a white
    flash, 10 sparks and an underline that draws across; the sub line rises; it exits with a zoom-through (scale up +
    fade). Long heroes stack on 2 lines. Captions are suppressed by HC.hook for the same span."""
    import math
    from aecards import EMERALD
    from reelkit import _measure
    color = color or EMERALD
    reveal0 = round(t0 + 0.28, 2)
    words = hero.split()
    bn = _is_bn(hero)          # 9-11-2026: the hero is the word he SAYS, in Bangla when he says it in Bangla
    mst = "bn_w" if bn else "sans_w"
    fs = 430 if big else 330
    lines = [hero]
    if _measure(hero, mst, fs) > 1800 and len(words) > 1:
        best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    wmax = max(_measure(l, mst, fs) for l in lines)
    if wmax > 1800:
        fs = int(fs * 1800 / wmax); wmax = 1800
    reveal1 = hook_slam(t0, hero)
    slam, out = reveal1, round(t1 - 0.25, 2)
    lead = round(fs * 1.0)
    nl = len(lines)
    block = 110 + 70 + nl * lead + (170 if sub else 0)
    top = center - block / 2 - 120                      # whole group centred a bit above the frame centre
    ky = round(top + 110)
    hy = round(ky + 70 + fs * 0.80)                   # baseline of hero line 1
    uy = hy + (nl - 1) * lead + 70
    sy = uy + 160
    ops = _shape(comp, f"{tag}_band", t0, t1, [1080, round((top + sy + 60) / 2)], [{"rect": [2600, round(sy + 60 - top + 500)], "fill": [0, 0, 0]}])
    ops += [{"operation": "effect.add", "args": {"comp": comp, "layer": f"{tag}_band", "matchName": "ADBE Gaussian Blur 2"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": f"{tag}_band", "effectIndex": 1, "property": ["Blurriness"], "value": 280}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": f"{tag}_band", "effectIndex": 1, "property": ["Repeat Edge Pixels"], "value": 0}}]
    ops += _k(comp, f"{tag}_band", ["Transform", "Opacity"], [t0, round(t0 + 0.2, 2), out, t1], [0, 62, 62, 0])
    # kicker types in
    kbn = _is_bn(kicker)
    ops += _text(comp, f"{tag}_kick", kicker, t0, t1, [1080, ky], "HindSiliguri-Bold" if kbn else "JetBrainsMono-ExtraBold",
                 165 if big else (130 if kbn else 110), GOLD, just="center")
    B = bn_clusters(kicker) if kbn else list(range(len(kicker) + 1))   # Bangla types whole clusters (no lone vowel signs)
    n = len(B) - 1
    ops += [{"operation": "expression.set", "args": {"comp": comp, "layer": f"{tag}_kick", "property": ["Text", "Source Text"],
                                                     "expression": f"var s={json.dumps(kicker)}; var B={json.dumps(B)}; var k=Math.floor(Math.max(0,time-{t0})*{round(n / 0.28, 1)}); "
                                                                   f"s.substr(0,B[Math.min(k,B.length-1)])+((k<B.length-1)?'_':'')"}}]
    ops += _k(comp, f"{tag}_kick", ["Transform", "Opacity"], [t0, round(t0 + 0.04, 2), out, t1], [0, 100, 100, 0])
    # hero: per-letter cascade, then slam
    hn = f"{tag}_hero"
    ops += _text(comp, hn, "\r".join(lines), t0, t1, [1080, hy], "HindSiliguri-Bold" if bn else "PlusJakartaSans-ExtraBold", fs, color, just="center")
    if nl > 1:
        ops.append({"operation": "text.set_style", "args": {"comp": comp, "layer": hn, "leading": lead, "autoLeading": False}})
    cy = round(hy + (nl - 1) * lead / 2 - fs * 0.36)  # visual centre of the hero block
    ops += [{"operation": "layer.set_props", "args": {"comp": comp, "layer": hn, "props": {"motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": hn, "property": ["Transform", "Anchor Point"], "value": [0, cy - hy]}},
            {"operation": "property.set", "args": {"comp": comp, "layer": hn, "property": ["Transform", "Position"], "value": [1080, cy]}}]
    if bn:   # Bangla: the whole word slams in from 320 % (a per-letter cascade would split the vowel signs)
        ops += _k(comp, hn, ["Transform", "Opacity"], [reveal0, round(reveal0 + 0.06, 2)], [0, 100])
        ops += _k(comp, hn, ["Transform", "Scale"], [reveal0, round(slam - 0.04, 2)], [[320, 320], [100, 100]], ease=[2])
    else:
        ops += [{"operation": "text.add_animator", "args": {"comp": comp, "layer": hn, "name": "Cascade", "selector": "range",
                                                            "properties": {"ADBE Text Position 3D": [0, -260, 0], "ADBE Text Opacity": 0,
                                                                           "ADBE Text Scale 3D": [170, 170, 100], "ADBE Text Blur": [25, 25]}}}]
        ops += _k(comp, hn, ["Text", "Animators", "Cascade", "Selectors", "Range Selector 1", "Offset"], [reveal0, reveal1], [0, 100], ease=[2])
    ops += _k(comp, hn, ["Transform", "Scale"], [round(slam - 0.02, 2), round(slam + 0.08, 2), round(slam + 0.22, 2), out, t1],
              [[100, 100], [116, 116], [100, 100], [104, 104], [140, 140]], ease=[3, 4])
    ops += _k(comp, hn, ["Transform", "Opacity"], [out, t1], [100, 0])
    ops.append({"operation": "expression.set", "args": {"comp": comp, "layer": hn, "property": ["Transform", "Position"],
                                                        "expression": f"var u=time-{slam}; (u>0&&u<0.35)? value+[Math.sin(u*90)*24*(0.35-u)/0.35, Math.cos(u*70)*16*(0.35-u)/0.35] : value"}})
    ops += _glow(comp, hn, radius=40, intensity=0.9)
    ops += [{"operation": "effect.add", "args": {"comp": comp, "layer": hn, "matchName": "ADBE Drop Shadow"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": hn, "effectIndex": 2, "property": ["Softness"], "value": 40}}]
    # underline draws L -> R at the slam
    uw = min(1800, round(wmax * 0.95))
    ops += _shape(comp, f"{tag}_line", slam, t1, [1080, uy], [{"path": [[-uw / 2, 0], [uw / 2, 0]], "trim": True, "stroke": color, "width": 18}])
    ops += _k(comp, f"{tag}_line", ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [slam, round(slam + 0.32, 2)], [0, 100], ease=[2])
    ops += _k(comp, f"{tag}_line", ["Transform", "Opacity"], [slam, out, t1], [100, 100, 0])
    # sparks shoot out of the slam
    sp = []
    for i in range(10):
        a = i * math.pi / 5 + 0.3
        r0, r1_ = 0.55 * uw / 2, 0.55 * uw / 2 + 190
        sp.append({"path": [[round(math.cos(a) * r0), round(math.sin(a) * r0 * 0.6)], [round(math.cos(a) * r1_), round(math.sin(a) * r1_ * 0.6)]],
                   "trim": True, "stroke": color if i % 2 else [1, 1, 1], "width": 13})
    ops += _shape(comp, f"{tag}_spark", slam, round(slam + 0.6, 2), [1080, cy], sp)
    for gi in range(1, 11):
        ops += _k(comp, f"{tag}_spark", ["Contents", f"g{gi}", "Contents", "Trim Paths 1", "End"], [slam, round(slam + 0.18, 2)], [0, 100])
        ops += _k(comp, f"{tag}_spark", ["Contents", f"g{gi}", "Contents", "Trim Paths 1", "Start"], [round(slam + 0.12, 2), round(slam + 0.45, 2)], [0, 100])
    ops += _shape(comp, f"{tag}_flash", slam, round(slam + 0.3, 2), [1080, 1920], [{"rect": [2160, 3840], "fill": [1, 1, 1]}])
    ops += _k(comp, f"{tag}_flash", ["Transform", "Opacity"], [slam, round(slam + 0.04, 2), round(slam + 0.3, 2)], [0, 40, 0])
    if sub:
        ops += _text(comp, f"{tag}_sub", sub, t0, t1, [1080, sy], "HindSiliguri-Bold" if _is_bn(sub) else "PlusJakartaSans-ExtraBold",
                     140 if big else 120, [1, 1, 1], just="center")
        ops += _k(comp, f"{tag}_sub", ["Transform", "Opacity"], [round(slam + 0.25, 2), round(slam + 0.4, 2), out, t1], [0, 100, 100, 0])
        ops += _k(comp, f"{tag}_sub", ["Transform", "Position"], [round(slam + 0.25, 2), round(slam + 0.45, 2)], [[1080, sy + 70], [1080, sy]], ease=[2])
    r.sfx("glitch.mp3", round(t0 + 0.02, 2), "extra", -14, 0.3)
    r.sfx("whoosh-vortex-243128.mp3", round(reveal0 - 0.1, 2), "bed", -12, 0.8)
    r.sfx("Short but Boomy.wav", slam, "feat", -4, 0.8)
    r.sfx("Subtle Whoosh.wav", out, "bed", -14, 0.6)
    return ops
