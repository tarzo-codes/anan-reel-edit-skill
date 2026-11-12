"""Animated 3D UI cards & Neon Outline Overlays built as live AE layers (editable in the reel's _TEXT comp), for reelkit's Reel.ae().

    from aecards import prompt_card, answer_card, logo_behind, neon
    r.ae(prompt_card(r, "R1_TEXT", t0, t1, "What does it take to\\rbecome a successful\\rtrader?", type_end=..., send=...))

Upgraded to the 2025-2026 Motion-Designer 3D Plane & FinTech Standard:
  - Uses PlusJakartaSans-Bold / PlusJakartaSans-ExtraBold + JetBrainsMono-ExtraBold + HindSiliguri-Bold.
  - Zero glyph-fallback collisions (auto-sanitizes `৳` in Latin fonts to `TK `).
  - `neon(..., kind="badge_num")` draws a perfectly concentric spinning ring + centered number at `(x, y)`.
"""
OBS = [0.04, 0.06, 0.10]
WHITE = [0.97, 0.98, 0.99]
SLATE = [0.58, 0.64, 0.72]
EMERALD = [0.0, 0.90, 0.46]
CRIMSON = [1.0, 0.12, 0.26]
TEAL = [0.06, 0.64, 0.50]
GOLD = [0.96, 0.62, 0.04]
CYAN = [0.22, 0.74, 0.97]
_NEON_N = [0]


def _safe_latin_text(txt: str, font: str) -> str:
    """Prevent `৳` (\u09f3) fallback-glyph smashing inside Latin fonts (`PlusJakartaSans`, `JetBrainsMono`, etc.)."""
    s = str(txt)
    if "\u09f3" in s and "Siliguri" not in font and "Bangla" not in font:
        s = s.replace("\u09f3 ", "TK ").replace("\u09f3", "TK ")
    return s


def _k(comp, layer, prop, times, values, ease=None):
    ops = [{"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": layer, "property": prop, "times": times, "values": values}}]
    for i in (ease or []):
        ops.append({"operation": "keyframe.set_easing", "args": {"comp": comp, "layer": layer, "property": prop, "keyIndex": i,
                                                                  "inSpeed": 0, "inInfluence": 85, "outSpeed": 0, "outInfluence": 40}})
    return ops


def _shape(comp, name, t0, t1, pos, groups):
    """groups: list of dicts {rect|ellipse: size, round, fill, stroke, width, at, path, trim}"""
    ops = [{"operation": "layer.create_shape", "args": {"comp": comp, "name": name}},
           {"operation": "layer.set_timing", "args": {"comp": comp, "layer": name, "inPoint": t0, "outPoint": t1}},
           {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "value": pos}}]
    for gi, g in enumerate(groups, 1):
        ops.append({"operation": "shape.add_group", "args": {"comp": comp, "layer": name, "name": g.get("name", f"g{gi}")}})
        if "rect" in g:
            ops.append({"operation": "shape.add_rect", "args": {"comp": comp, "layer": name, "groupIndex": gi, "size": g["rect"],
                                                                 "position": g.get("at", [0, 0]), "roundness": g.get("round", 0)}})
        if "ellipse" in g:
            ops.append({"operation": "shape.add_ellipse", "args": {"comp": comp, "layer": name, "groupIndex": gi, "size": g["ellipse"]}})
        if "path" in g:
            ops.append({"operation": "shape.add_path", "args": {"comp": comp, "layer": name, "groupIndex": gi, "vertices": g["path"], "closed": g.get("closed", False)}})
        if "trim" in g:
            ops.append({"operation": "shape.add_trim_paths", "args": {"comp": comp, "layer": name, "groupIndex": gi, "start": 0, "end": 0}})
        if "stroke" in g:
            ops.append({"operation": "shape.add_stroke", "args": {"comp": comp, "layer": name, "groupIndex": gi, "color": g["stroke"] + [1], "width": g.get("width", 5)}})
        if "fill" in g:
            ops.append({"operation": "shape.add_fill", "args": {"comp": comp, "layer": name, "groupIndex": gi, "color": g["fill"] + [1], "opacity": g.get("opacity", 100)}})
    return ops


def _text(comp, name, txt, t0, t1, pos, font, size, color, just="left", leading=None):
    txt = _safe_latin_text(txt, font)
    sty = {"comp": comp, "layer": name, "font": font, "fontSize": size, "fillColor": color, "justification": just,
           "applyStroke": False}
    if leading:
        sty.update(leading=leading, autoLeading=False)
    if "Siliguri" in font or "Bangla" in font:
        sty["composerEngine"] = "universal"
        sty["tracking"] = 15
    return [{"operation": "layer.create_text", "args": {"comp": comp, "text": txt, "name": name}},
            {"operation": "text.set_style", "args": sty},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": name, "inPoint": t0, "outPoint": t1}},
            {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "value": pos}}]


def _open_close(comp, card, t0, t1):
    """3D perspective plane flip-open (thin line -> full card with 3D pitch/swivel overshoot + live 3D float)."""
    return ([{"operation": "layer.set_props", "args": {"comp": comp, "layer": card, "props": {"threeDLayer": True, "motionBlur": True}}},
             {"operation": "property.set", "args": {"comp": comp, "layer": card, "property": ["Material Options", "Accepts Lights"], "value": 0}}]
            + _k(comp, card, ["Transform", "Scale"], [t0, t0 + 0.14, t0 + 0.30, t0 + 0.40, t1 - 0.22, t1],
                 [[18, 2, 100], [104, 2, 100], [100, 106, 100], [100, 100, 100], [100, 100, 100], [88, 88, 100]], ease=[2, 3, 4])
            + _k(comp, card, ["Transform", "X Rotation"], [t0, t0 + 0.28, t0 + 0.42, t1 - 0.20, t1],
                 [28, -3, 0, 0, -18], ease=[2, 3])
            + _k(comp, card, ["Transform", "Y Rotation"], [t0, t0 + 0.28, t0 + 0.42, t1 - 0.20, t1],
                 [-12, 2, 0, 0, 10], ease=[2, 3])
            + [{"operation": "expression.set", "args": {"comp": comp, "layer": card, "property": ["Transform", "Orientation"],
                                                        "expression": "var u=time-inPoint; value + [Math.sin(u*1.4)*2.2, Math.cos(u*1.1)*3.2, Math.sin(u*0.85)*0.9]"}}]
            + _k(comp, card, ["Transform", "Opacity"], [t0, t0 + 0.06, t1 - 0.18, t1], [0, 100, 100, 0])
            + [{"operation": "effect.add", "args": {"comp": comp, "layer": card, "matchName": "ADBE Drop Shadow"}},
               {"operation": "effect.set_property", "args": {"comp": comp, "layer": card, "effectIndex": 1, "property": ["Distance"], "value": 34}},
               {"operation": "effect.set_property", "args": {"comp": comp, "layer": card, "effectIndex": 1, "property": ["Softness"], "value": 95}}])


def _parent_all(ops, comp, card, kids, origin):
    """Parent kids to the 3D card in card-local space with subtle negative Z offset (-12px) so text/icons hover cleanly without parallax border collision."""
    kids = set(kids)
    out = []
    for op in ops:
        a = op["args"]
        lay = a.get("layer")
        if lay in kids and a.get("property") == ["Transform", "Position"]:
            if op["operation"] == "property.set":
                a["value"] = [a["value"][0] - origin[0], a["value"][1] - origin[1], -12]
            elif op["operation"] == "keyframe.set_batch":
                a["values"] = [[v[0] - origin[0], v[1] - origin[1], -12] for v in a["values"]]
        out.append(op)
        if op["operation"] in ("layer.create_shape", "layer.create_text") and a.get("name") in kids:
            out.append({"operation": "layer.set_props", "args": {"comp": comp, "layer": a["name"], "props": {"threeDLayer": True, "motionBlur": True}}})
            out.append({"operation": "property.set", "args": {"comp": comp, "layer": a["name"], "property": ["Material Options", "Accepts Lights"], "value": 0}})
            out.append({"operation": "layer.set_parent", "args": {"comp": comp, "layer": a["name"], "parentLayer": card, "jump": True}})
    return out


def _pop_in(comp, layer, t, end):
    return (_k(comp, layer, ["Transform", "Opacity"], [t, t + 0.1], [0, 100])
            + _k(comp, layer, ["Transform", "Scale"], [t, t + 0.18, t + 0.3], [[40, 40, 100], [112, 112, 100], [100, 100, 100]], ease=[2]))


def _icon(comp, tag, t0, t1, hx, hy, logo_id):
    if not logo_id:
        return _shape(comp, f"{tag}_icon", t0, t1, [hx, hy], [{"ellipse": [40, 40], "stroke": WHITE, "width": 9}, {"ellipse": [92, 92], "fill": TEAL}])
    nm = f"{tag}_icon"
    return (_shape(comp, nm, t0, t1, [hx, hy], [{"ellipse": [92, 92], "fill": TEAL}])
            + [{"operation": "layer.create_footage", "args": {"comp": comp, "sourceItemId": logo_id, "name": f"{tag}_logo"}},
               {"operation": "layer.set_timing", "args": {"comp": comp, "layer": f"{tag}_logo", "inPoint": t0, "outPoint": t1}},
               {"operation": "layer.set_props", "args": {"comp": comp, "layer": f"{tag}_logo", "props": {"threeDLayer": True}}},
               {"operation": "property.set", "args": {"comp": comp, "layer": f"{tag}_logo", "property": ["Material Options", "Accepts Lights"], "value": 0}},
               {"operation": "layer.set_parent", "args": {"comp": comp, "layer": f"{tag}_logo", "parentLayer": nm, "jump": True}},
               {"operation": "property.set", "args": {"comp": comp, "layer": f"{tag}_logo", "property": ["Transform", "Position"], "value": [0, 0, -4]}},
               {"operation": "property.set", "args": {"comp": comp, "layer": f"{tag}_logo", "property": ["Transform", "Scale"], "value": [3.9, 3.9, 100]}}])


def prompt_card(r, comp, t0, t1, prompt, type_start, type_end, send, cy=2800, w=1880, h=660, tag="PC", logo_id=None):
    """3D Glass Chat prompt that flips open in 3D space, types itself out, gets sent and 'thinks'."""
    card = f"{tag}_card"
    x0, top = 1080 - w / 2, cy - h / 2
    ops = _shape(comp, card, t0, t1, [1080, cy], [{"rect": [w, h], "round": 56, "fill": OBS, "stroke": SLATE, "width": 5}])
    ops += _open_close(comp, card, t0, t1)
    hx, hy = x0 + 80 + 46, top + 80 + 46
    ops += _icon(comp, tag, t0, t1, hx, hy, logo_id)
    ops += _pop_in(comp, f"{tag}_icon", t0 + 0.32, t1)
    ops += _text(comp, f"{tag}_name", "ChatGPT", t0, t1, [hx + 76, hy + 26], "PlusJakartaSans-ExtraBold", 70, WHITE)
    ops += _k(comp, f"{tag}_name", ["Transform", "Opacity"], [t0 + 0.36, t0 + 0.5], [0, 100])
    n = len(prompt)
    rate = round(n / max(0.4, type_end - type_start), 2)
    expr = (f'var s={prompt!r}; var k=Math.floor(Math.max(0,time-{type_start})*{rate}); '
            f'var on=(k<s.length)||(Math.floor(time*3)%2==0); s.substr(0,Math.min(k,s.length))+(on&&time<{send}?"|":"")')
    ops += _text(comp, f"{tag}_prompt", prompt, t0, t1, [x0 + 80, top + 270], "PlusJakartaSans-Bold", 96, WHITE, leading=124)
    ops += [{"operation": "expression.set", "args": {"comp": comp, "layer": f"{tag}_prompt", "property": ["Text", "Source Text"], "expression": expr}}]
    bx, by = x0 + w - 80 - 50, top + h - 80 - 50
    ops += _shape(comp, f"{tag}_send", t0, t1, [bx, by],
                  [{"path": [[0, 22], [0, -22]], "stroke": OBS, "width": 12}, {"path": [[-18, -4], [0, -22], [18, -4]], "stroke": OBS, "width": 12},
                   {"ellipse": [100, 100], "fill": EMERALD}])
    ops += _k(comp, f"{tag}_send", ["Transform", "Opacity"], [t0 + 0.4, t0 + 0.5, type_end, type_end + 0.1], [0, 35, 35, 100])
    ops += _k(comp, f"{tag}_send", ["Transform", "Scale"], [send - 0.02, send + 0.06, send + 0.18, send + 0.3],
              [[100, 100, 100], [78, 78, 100], [114, 114, 100], [100, 100, 100]], ease=[3])
    dots = 'var d=Math.floor((time-' + str(send) + ')*4)%4; "thinking"+"...".substr(0,d)'
    ops += _text(comp, f"{tag}_think", "thinking", t0, t1, [hx + 470, hy + 22], "JetBrainsMono-ExtraBold", 54, SLATE)
    ops += [{"operation": "expression.set", "args": {"comp": comp, "layer": f"{tag}_think", "property": ["Text", "Source Text"], "expression": dots}}]
    ops += _k(comp, f"{tag}_think", ["Transform", "Opacity"], [send + 0.05, send + 0.2], [0, 100])
    ops = _parent_all(ops, comp, card, [f"{tag}_{c}" for c in ("icon", "name", "prompt", "send", "think")], (1080, cy))
    r.sfx("whoosh-motion-243505.mp3", t0 - 0.05, "bed", -14, 0.6)
    r.sfx("mouse-click-104737.mp3", t0 + 0.32, "extra", -6, 0.3)
    r.sfx("koiroylers-gear-click-351962.mp3", type_start, "extra", -12, round(type_end - type_start, 2))
    r.sfx("mouse-click-104737.mp3", send, "feat", -3, 0.3)
    return ops


def answer_card(r, comp, t0, t1, items, title="6 THINGS", cy=2200, w=1880, step=0.16, tag="AC", logo_id=None,
                mark="check", times=None, header="ChatGPT"):
    """3D Glass Answer card: flips open in 3D space, then each item pops in at Z=-12px with a Trim Paths mark."""
    rowh = 156
    h = 310 + rowh * len(items)
    card = f"{tag}_card"
    x0, top = 1080 - w / 2, cy - h / 2
    ops = _shape(comp, card, t0, t1, [1080, cy], [{"rect": [w, h], "round": 56, "fill": OBS, "stroke": SLATE, "width": 5}])
    ops += _open_close(comp, card, t0, t1)
    hx, hy = x0 + 80 + 46, top + 80 + 46
    ops += _icon(comp, tag, t0, t1, hx, hy, logo_id)
    ops += _pop_in(comp, f"{tag}_icon", t0 + 0.3, t1)
    ops += _text(comp, f"{tag}_name", header, t0, t1, [hx + 76, hy + 26], "PlusJakartaSans-ExtraBold", 70, WHITE)
    ops += _text(comp, f"{tag}_title", title, t0, t1, [x0 + w - 80, hy + 22], "JetBrainsMono-ExtraBold", 56, SLATE, just="right")
    for nm in ("name", "title"):
        ops += _k(comp, f"{tag}_{nm}", ["Transform", "Opacity"], [t0 + 0.34, t0 + 0.48], [0, 100])
    kids = ["icon", "name", "title"]
    for i, it in enumerate(items):
        t = round(times[i], 2) if times else round(t0 + 0.45 + i * step, 2)
        y = top + 275 + i * rowh
        ck = f"{tag}_ck{i + 1}"
        if mark == "x":
            ops += _shape(comp, ck, t0, t1, [x0 + 120, y + 40],
                          [{"path": [[-18, -18], [18, 18]], "trim": True, "stroke": CRIMSON, "width": 11},
                           {"path": [[18, -18], [-18, 18]], "trim": True, "stroke": CRIMSON, "width": 11},
                           {"ellipse": [84, 84], "stroke": CRIMSON, "width": 6}])
            ops += _k(comp, ck, ["Contents", "g2", "Contents", "Trim Paths 1", "End"], [t + 0.14, t + 0.3], [0, 100], ease=[2])
        else:
            ops += _shape(comp, ck, t0, t1, [x0 + 120, y + 40],
                          [{"path": [[-20, 2], [-6, 18], [22, -16]], "trim": True, "stroke": EMERALD, "width": 11},
                           {"ellipse": [84, 84], "stroke": EMERALD, "width": 6}])
        ops += _pop_in(comp, ck, t, t1)
        ops += _k(comp, ck, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [t + 0.08, t + 0.3], [0, 100], ease=[2])
        tx = f"{tag}_it{i + 1}"
        item_font = "HindSiliguri-Bold" if any("\u0980" <= ch <= "\u09FF" for ch in it) else "PlusJakartaSans-Bold"
        fsize = 86 if len(it) <= 26 else max(66, int(86 * 26 / len(it)))
        ops += _text(comp, tx, it, t0, t1, [x0 + 210, y + 70], item_font, fsize, WHITE)
        ops += (_k(comp, tx, ["Transform", "Opacity"], [t, t + 0.12], [0, 100])
                + _k(comp, tx, ["Transform", "Position"], [t, t + 0.24], [[x0 + 290, y + 70], [x0 + 210, y + 70]], ease=[2]))
        kids += [f"ck{i + 1}", f"it{i + 1}"]
        if mark == "x":
            st = f"{tag}_st{i + 1}"
            ln = min(w - 300, int(len(it) * (fsize * 0.58)))
            ops += _shape(comp, st, t0, t1, [x0 + 210, y + 42], [{"path": [[0, 0], [ln, 0]], "trim": True, "stroke": CRIMSON, "width": 11}])
            ops += _k(comp, st, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [t + 0.28, t + 0.5], [0, 100], ease=[2])
            kids.append(f"st{i + 1}")
        r.sfx("pop-39222.mp3" if mark != "x" else "glitch.mp3", t, "extra", -12, 0.3)
    ops = _parent_all(ops, comp, card, [f"{tag}_{c}" for c in kids], (1080, cy))
    r.sfx("whoosh-motion-243505.mp3", t0 - 0.05, "bed", -14, 0.6)
    return ops


def logo_behind(r, comp, item_id, t0, t1, name, y=1150, width=1420, src_w=1600, x=1080):
    """App logo shown HUGE behind Anan in 3D space (sits in V6 under his V7 cutout)."""
    s = round(width / src_w * 100, 2)
    ops = [{"operation": "layer.create_footage", "args": {"comp": comp, "sourceItemId": item_id, "name": name}},
           {"operation": "layer.set_timing", "args": {"comp": comp, "layer": name, "inPoint": t0, "outPoint": t1}},
           {"operation": "layer.set_props", "args": {"comp": comp, "layer": name, "props": {"threeDLayer": True, "motionBlur": True}}},
           {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Material Options", "Accepts Lights"], "value": 0}},
           {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "value": [x, y, 0]}}]
    ops += _k(comp, name, ["Transform", "Scale"], [t0, t0 + 0.22, t0 + 0.38, t1 - 0.24, t1 - 0.12, t1],
              [[0, 0, 100], [s * 1.14, s * 1.14, 100], [s, s, 100], [s, s, 100], [s * 1.08, s * 1.08, 100], [0, 0, 100]], ease=[2, 3, 5])
    ops += _k(comp, name, ["Transform", "Z Rotation"], [t0, t0 + 0.38, t1 - 0.24, t1], [-24, 0, 0, 16], ease=[2])
    ops += _k(comp, name, ["Transform", "Opacity"], [t0, t0 + 0.08, t1 - 0.1, t1], [0, 100, 100, 0])
    live = {
        ("Transform", "Position"): "var u=time-inPoint; value+[Math.sin(u*1.3)*16, Math.sin(u*2.1)*22, Math.cos(u*1.1)*35]",
        ("Transform", "Orientation"): "var u=time-inPoint; value+[Math.sin(u*1.2)*3.5, Math.cos(u*1.5)*5, Math.sin(u*1.8)*2.5]",
        ("Transform", "Scale"): "var b=1+0.025*Math.sin((time-inPoint)*2.6); [value[0]*b, value[1]*b, 100]",
    }
    for prop, ex in live.items():
        ops.append({"operation": "expression.set", "args": {"comp": comp, "layer": name, "property": list(prop), "expression": ex}})
    ops += [{"operation": "effect.add", "args": {"comp": comp, "layer": name, "matchName": "ADBE Drop Shadow"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Opacity"], "value": 170}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Distance"], "value": 24}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Softness"], "value": 80}}]
    r.sfx("whoosh-vortex-243128.mp3", t0 - 0.1, "bed", -16, 0.9)
    r.sfx("Short but Boomy.wav", t0 + 0.05, "feat", -8, 0.7)
    return ops


def _glow(comp, layer, radius=48, intensity=1.45):
    return [{"operation": "effect.add", "args": {"comp": comp, "layer": layer, "matchName": "ADBE Glo2"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": layer, "effectIndex": 1, "property": ["Glow Radius"], "value": radius}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": layer, "effectIndex": 1, "property": ["Glow Intensity"], "value": intensity}},
            {"operation": "expression.set", "args": {"comp": comp, "layer": layer, "property": ["Transform", "Opacity"],
                                                     "expression": "var u=time-inPoint; seedRandom(index,false); value*(u<0.24 ? (random()>0.38?1:0.25) : 1)"}}]


def neon(r, comp, t0, t1, kind, x, y, size=520, color=CYAN, text=None, width=12, draw=0.32, spin=0):
    """Outline NEON overlay that ties the edit together while something is explained: drawn on with Trim Paths,
    Glow + start flicker, fades out. Lives in the reel's _TEXT comp (above the A-roll, under the cut-out)
    or _FRONT comp (screen-space HUD overlay above the camera adjustment layer).

    kind:
      - "badge_num": CONCENTRIC RING + PERFECTLY CENTERED NUMBER at exact `(x, y)` (zero alignment drift!).
                     `size` = outer ring diameter (e.g. 460); digit auto-scales to `size * 0.62`.
      - "ring" | "box" | "underline" | "arrow_down" | "arrow_right" | "check" | "cross" | "bracket" | "num"
    """
    # Auto-route to FRONT comp if this is a screen-space overlay (top header badge, subtitle underline, checkmark, box)
    # so it sits on Track V11 above the camera adjustment layer instead of being distorted or pushed into cutoffs by zoom!
    if comp and comp.endswith("_TEXT"):
        front_comp = comp[:-5] + "_FRONT"
        if kind in ("underline", "box", "check", "arrow_down", "arrow_right", "badge_num") or y < 900 or y > 1500:
            comp = front_comp

    if kind == "badge_num":
        if x > 1400: # Upper right pillar badge
            y = max(740, y)
            size = min(320, size)
            x = min(1750, x)
        ring_diam = float(size)
        num_sz = round(ring_diam * 0.60)
        ops = neon(r, comp, t0, t1, "ring", x, y, size=ring_diam, color=color, width=max(9, width - 2), draw=draw, spin=spin or 36)
        ops += neon(r, comp, round(t0 + 0.05, 2), t1, "num", x, y, size=num_sz, color=color, text=text, width=width)
        return ops

    _NEON_N[0] += 1
    nm = f"NEON_{_NEON_N[0]:02d}_{kind}"
    out = round(max(t0 + 0.12, t1 - 0.14), 2)
    if kind == "num":
        safe_txt = _safe_latin_text(str(text), "JetBrainsMono-ExtraBold")
        # In JetBrainsMono-ExtraBold, cap-height is ~0.72 * fontSize above baseline, so visual center = baseline - 0.36 * fontSize.
        # Placing baseline at `y + size * 0.36` puts the geometric center of the digit at exact `y`!
        ops = [{"operation": "layer.create_text", "args": {"comp": comp, "text": safe_txt, "name": nm}},
               {"operation": "text.set_style", "args": {"comp": comp, "layer": nm, "font": "JetBrainsMono-ExtraBold", "fontSize": size,
                                                        "applyFill": False, "applyStroke": True, "strokeColor": color, "strokeWidth": width,
                                                        "justification": "center"}},
               {"operation": "layer.set_timing", "args": {"comp": comp, "layer": nm, "inPoint": t0, "outPoint": t1}},
               {"operation": "property.set", "args": {"comp": comp, "layer": nm, "property": ["Transform", "Position"],
                                                      "value": [x, round(y + size * 0.36, 1)]}}]
        ops += _k(comp, nm, ["Transform", "Scale"], [t0, round(t0 + 0.18, 2), round(t0 + 0.30, 2), out, t1],
                  [[70, 70], [106, 106], [100, 100], [100, 100], [92, 92]], ease=[2])
        ops += _k(comp, nm, ["Transform", "Opacity"], [t0, round(t0 + 0.06, 2), out, t1], [0, 100, 100, 0])
        return ops + _glow(comp, nm)

    if kind == "box":
        g = {"rect": list(size) if isinstance(size, (list, tuple)) else [size, size * 0.42], "round": 40}
    else:
        g = _neon_path(kind, size)
    g.update(trim=True, stroke=color, width=width)
    return _neon_finish(r, comp, nm, t0, t1, out, x, y, g, draw, spin)


def _neon_path(kind, s):
    return {
        "ring": {"ellipse": [s, s]},
        "underline": {"path": [[-s / 2, 0], [-s / 6, -8], [s / 6, 6], [s / 2, -4]]},
        "arrow_down": {"path": [[0, -s / 2], [0, s / 2], [-s / 5, s / 2 - s / 5], [0, s / 2], [s / 5, s / 2 - s / 5]]},
        "arrow_right": {"path": [[-s / 2, 0], [s / 2, 0], [s / 2 - s / 5, -s / 5], [s / 2, 0], [s / 2 - s / 5, s / 5]]},
        "check": {"path": [[-s / 2, 0], [-s / 6, s / 3], [s / 2, -s / 3]]},
        "cross": {"path": [[-s / 2, -s / 2], [s / 2, s / 2], [0, 0], [s / 2, -s / 2], [-s / 2, s / 2]]},
        "bracket": {"path": [[-s / 2, -s / 4], [-s / 2, -s / 2], [s / 2, -s / 2], [s / 2, -s / 4]]},
    }[kind]


def _neon_finish(r, comp, nm, t0, t1, out, x, y, g, draw, spin):
    ops = _shape(comp, nm, t0, t1, [x, y], [g])
    ops += _k(comp, nm, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [t0, round(t0 + draw, 2)], [0, 100], ease=[2])
    ops += _k(comp, nm, ["Transform", "Opacity"], [t0, round(t0 + 0.05, 2), out, t1], [0, 100, 100, 0])
    if spin:
        ops.append({"operation": "expression.set", "args": {"comp": comp, "layer": nm, "property": ["Transform", "Rotation"],
                                                            "expression": f"(time-inPoint)*{spin}"}})
    return ops + _glow(comp, nm)
