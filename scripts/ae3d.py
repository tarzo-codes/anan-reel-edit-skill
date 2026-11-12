"""After Effects 3D Camera Plane & Multi-Variation Spatial Motion Graphics Engine (`ae3d.py`).

Implements 5 distinct 2025-2026 "Moving in a 3D Plane" Motion Graphics Variations (Keanu Visuals / Capitaojack /
Devin Jatho / Iman Gadzhi / Umar Ashraf TradeZella / MagnatesMedia style) via @kumoproductions/mcp-aftereffects:

  1. `canvas_board_plane_3d` (`r.plane_canvas`) — Connected FinTech Terminal Mind-Map Board with orthogonal glowing
                                                  conduits and clean header-bar cards (zero badge/stat border overlap).
  2. `timeline_tunnel_3d`    (`r.plane_tunnel`) — 3D Z-Depth Fly-Through Corridor: camera flies forward along Z down a
                                                  glowing perspective floor spine past staggered left/right milestones.
  3. `radial_hub_3d`         (`r.plane_hub`)    — Central Core Hub + Radiating Spoke Satellites with orbital camera
                                                  whips and full-wheel pullback reveal.
  4. `versus_split_3d`       (`r.plane_versus`) — Opposing 3D Angled V-Stage Monoliths (`+18°` vs `-18°` Y-yaw) + center
                                                  bridge badge for high-stakes comparisons (Stop-Loss, Risk:Reward).
  5. `kinetic_wall_3d`       (`r.plane_kinetic`)— Box-free 3D Architectural Typography on a lit grid plane with `90°`
                                                  camera Z-pivot whip turns and glowing neon accent rules.

Alignment & Typography Guarantees:
  - Zero foreground `Z < 0` HUD text crossing over cards (grid telemetry lives flat on the floor perimeter).
  - Zero `৳` (\u09f3) glyph-fallback collisions inside Latin fonts (auto-sanitized to `TK `).
  - All 3D text layers set `Accepts Lights = 0` so spotlight/point lights illuminate the 3D plane & glass cards while
    keeping every English & Bangla character 100% razor-sharp (`applyStroke=False`, positive Bangla tracking).
"""
import json
import math
import os
import subprocess
import tempfile

OBS = [0.04, 0.06, 0.10]
GRID_DARK = [0.02, 0.03, 0.06]
VOID_LIT = [0.07, 0.09, 0.14]
CARD_DARK = [0.05, 0.08, 0.14]
HEADER_DARK = [0.08, 0.12, 0.20]
WHITE = [0.97, 0.98, 0.99]
SLATE = [0.62, 0.68, 0.76]
DIM_SLATE = [0.22, 0.28, 0.36]
EMERALD = [0.00, 0.90, 0.46]
CRIMSON = [1.00, 0.12, 0.26]
GOLD = [0.96, 0.62, 0.04]
CYAN = [0.22, 0.74, 0.97]


def _has_bangla(txt: str) -> bool:
    return any("\u0980" <= ch <= "\u09FF" for ch in str(txt))


def _safe_text(txt: str, font: str) -> str:
    """Ensure `৳` (\u09f3) never triggers broken fallback advance-width collisions inside Latin fonts."""
    s = str(txt)
    if "\u09f3" in s and "Siliguri" not in font and "Bangla" not in font:
        s = s.replace("\u09f3 ", "TK ").replace("\u09f3", "TK ")
    return s


def _fit_size(txt: str, base_size: int, max_px: float, is_bn: bool = False, char_factor: float = None) -> int:
    """Auto-scale font size so long titles or Bangla captions never overflow card/column bounds or collide."""
    s = str(txt)
    if not s:
        return base_size
    if char_factor is None:
        char_factor = 0.56 if is_bn else 0.62
    est_w = len(s) * base_size * char_factor
    if est_w > max_px:
        return max(32, int(base_size * max_px / est_w))
    return base_size


def _k(comp, layer, prop, times, values, ease=None, in_inf=86, out_inf=38):
    # Defensive deduplication & monotonic increase: ensure each timestamp is strictly > previous by at least 0.04s (1 frame @ 25fps)
    sanitized_times = []
    for t in times:
        rt = round(float(t), 2)
        if not sanitized_times:
            sanitized_times.append(rt)
        else:
            prev = sanitized_times[-1]
            if rt <= prev:
                sanitized_times.append(round(prev + 0.04, 2))
            else:
                sanitized_times.append(rt)
    times = sanitized_times

    ops = [{"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": layer, "property": prop, "times": times, "values": values}}]
    for i in (ease or []):
        if 1 <= i <= len(times):
            ops.append({
                "operation": "keyframe.set_easing",
                "args": {
                    "comp": comp,
                    "layer": layer,
                    "property": prop,
                    "keyIndex": i,
                    "inSpeed": 0,
                    "inInfluence": in_inf,
                    "outSpeed": 0,
                    "outInfluence": out_inf,
                },
            })
    return ops


def _material(comp, layer, casts=0, accepts_shadows=1, accepts_lights=1, specular=None, shininess=None):
    ops = [
        {"operation": "property.set", "args": {"comp": comp, "layer": layer, "property": ["Material Options", "Casts Shadows"], "value": casts}},
        {"operation": "property.set", "args": {"comp": comp, "layer": layer, "property": ["Material Options", "Accepts Shadows"], "value": accepts_shadows}},
        {"operation": "property.set", "args": {"comp": comp, "layer": layer, "property": ["Material Options", "Accepts Lights"], "value": accepts_lights}},
    ]
    if specular is not None:
        ops.append({"operation": "property.set", "args": {"comp": comp, "layer": layer, "property": ["Material Options", "Specular Intensity"], "value": specular}})
    if shininess is not None:
        ops.append({"operation": "property.set", "args": {"comp": comp, "layer": layer, "property": ["Material Options", "Specular Shininess"], "value": shininess}})
    return ops


def _create_3d_text(comp, name, txt, font, size, color, t0, t1, pos, just="center", parent=None, tracking=None, shadow=False):
    """Create a crisp 3D text layer with `Accepts Lights = 0`, `applyStroke = False`, and safe Bangla/Latin metrics."""
    is_bn = "Siliguri" in font or "Bangla" in font
    clean_txt = _safe_text(txt, font)
    trk = tracking if tracking is not None else (16 if is_bn else (-15 if size >= 110 else 10))
    sty = {
        "comp": comp,
        "layer": name,
        "font": font,
        "fontSize": size,
        "fillColor": color,
        "applyStroke": False,
        "tracking": trk,
        "justification": just,
        "composerEngine": "universal" if is_bn else "latinCjk",
    }
    ops = [
        {"operation": "layer.create_text", "args": {"comp": comp, "name": name, "text": clean_txt}},
        {"operation": "text.set_style", "args": sty},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": name, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": name, "props": {"threeDLayer": True, "motionBlur": True}}},
    ]
    ops += _material(comp, name, casts=0, accepts_shadows=0, accepts_lights=0)
    if parent:
        ops.append({"operation": "layer.set_parent", "args": {"comp": comp, "layer": name, "parentLayer": parent, "jump": True}})
    ops.append({"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "value": list(pos)}})
    if shadow:
        ops += [
            {"operation": "effect.add", "args": {"comp": comp, "layer": name, "matchName": "ADBE Drop Shadow"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Opacity"], "value": 195}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Distance"], "value": 18}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Softness"], "value": 48}},
        ]
    return ops


def import_plane_assets(file_map: dict[str, str]) -> dict[str, int]:
    """Import image/video files into the active After Effects project and return `{key: item_id}`."""
    ae_call = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ae_call.mjs")
    ops = [{"operation": "project.import_file", "args": {"path": os.path.abspath(p), "name": f"PLANE_{k}"}} for k, p in file_map.items()]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"operation": "batch.run", "args": {"ops": ops}}, f)
        tmp = f.name
    try:
        r = subprocess.run(["node", ae_call, "call", "ae_do", "@" + tmp], capture_output=True, text=True)
        data = json.loads(r.stdout[r.stdout.find("{"):])
        out = {}
        for k, res in zip(file_map.keys(), data.get("results", [])):
            if res.get("itemId"):
                out[k] = res["itemId"]
        return out
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def camera_rig_3d(comp, t0, t1, waypoints, tag="CAM3D", drift=True):
    """Build a 4-node 3D Camera Rig (`CAM_POS` -> `CAM_ORBIT` -> `CAM_DRIFT` -> `CAM_35MM`)."""
    pos_null = f"{tag}_POS"
    orb_null = f"{tag}_ORBIT"
    drf_null = f"{tag}_DRIFT"
    cam_name = f"{tag}_35MM"

    ops = [
        {"operation": "layer.create_null", "args": {"comp": comp, "name": pos_null}},
        {"operation": "layer.create_null", "args": {"comp": comp, "name": orb_null}},
        {"operation": "layer.create_null", "args": {"comp": comp, "name": drf_null}},
        {"operation": "layer.create_camera", "args": {"comp": comp, "name": cam_name}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": pos_null, "props": {"threeDLayer": True}}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": orb_null, "props": {"threeDLayer": True}}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": drf_null, "props": {"threeDLayer": True}}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": pos_null, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": orb_null, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": drf_null, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": cam_name, "inPoint": t0, "outPoint": t1}},
        {"operation": "property.set", "args": {"comp": comp, "layer": pos_null, "property": ["Transform", "Position"], "value": [1080, 1920, 0]}},
        {"operation": "property.set", "args": {"comp": comp, "layer": orb_null, "property": ["Transform", "Position"], "value": [1080, 1920, 0]}},
        {"operation": "property.set", "args": {"comp": comp, "layer": drf_null, "property": ["Transform", "Position"], "value": [1080, 1920, 0]}},
        {"operation": "layer.set_parent", "args": {"comp": comp, "layer": orb_null, "parentLayer": pos_null, "jump": False}},
        {"operation": "layer.set_parent", "args": {"comp": comp, "layer": drf_null, "parentLayer": orb_null, "jump": False}},
        {"operation": "layer.set_parent", "args": {"comp": comp, "layer": cam_name, "parentLayer": drf_null, "jump": False}},
        {"operation": "property.set", "args": {"comp": comp, "layer": cam_name, "property": ["Transform", "Position"], "value": [0, 0, -2666.7]}},
    ]

    if drift:
        ops += [
            {
                "operation": "expression.set",
                "args": {
                    "comp": comp,
                    "layer": drf_null,
                    "property": ["Transform", "Position"],
                    "expression": "var u=time-inPoint; value + [Math.sin(u*1.2)*18, Math.cos(u*0.95)*14, Math.sin(u*0.75)*24]",
                },
            },
            {
                "operation": "expression.set",
                "args": {
                    "comp": comp,
                    "layer": drf_null,
                    "property": ["Transform", "Orientation"],
                    "expression": "var u=time-inPoint; value + [Math.sin(u*0.85)*1.0, Math.cos(u*1.1)*1.3, Math.sin(u*0.65)*0.5]",
                },
            },
        ]

    if waypoints:
        p_times = [round(w["t"], 2) for w in waypoints]
        p_vals = [w.get("pos", [1080, 1920, 0]) for w in waypoints]
        rx_vals = [w.get("orbit", [0, 0, 0])[0] for w in waypoints]
        ry_vals = [w.get("orbit", [0, 0, 0])[1] for w in waypoints]
        rz_vals = [w.get("orbit", [0, 0, 0])[2] for w in waypoints]
        ease_idx = list(range(1, len(p_times) + 1))

        ops += _k(comp, pos_null, ["Transform", "Position"], p_times, p_vals, ease=ease_idx, in_inf=86, out_inf=80)
        ops += _k(comp, orb_null, ["Transform", "X Rotation"], p_times, rx_vals, ease=ease_idx, in_inf=85, out_inf=78)
        ops += _k(comp, orb_null, ["Transform", "Y Rotation"], p_times, ry_vals, ease=ease_idx, in_inf=85, out_inf=78)
        ops += _k(comp, orb_null, ["Transform", "Z Rotation"], p_times, rz_vals, ease=ease_idx, in_inf=86, out_inf=78)

    return ops


def infinite_grid_plane(comp, t0, t1, tag="PLANE3D", center=(2200, 2600, 420), pitch_x=0, yaw_y=0, roll_z=0,
                        grid_color=SLATE, opaque_bg=True, width=9600, height=10800, lit=False):
    """Create a 3D Infinite Perspective Grid Plane (`ADBE Grid`).
    Perimeter coordinate stamps sit FLAT on the floor plane (`Z = center[2] - 8`) far outside card zones so they NEVER collide with cards."""
    plane = f"{tag}_GRID"
    ops = []
    if opaque_bg:
        bg = f"{tag}_VOID"
        ops += [
            {"operation": "layer.create_solid", "args": {"comp": comp, "name": bg, "color": VOID_LIT if lit else GRID_DARK,
                                                         "width": min(30000, width * 2), "height": min(30000, height * 2)}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": bg, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": bg, "props": {"threeDLayer": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": bg, "property": ["Transform", "Position"],
                                                   "value": [center[0], center[1], center[2] + 90]}},
        ]

    ops += [
        {"operation": "layer.create_solid", "args": {"comp": comp, "name": plane, "color": OBS, "width": width, "height": height}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": plane, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": plane, "props": {"threeDLayer": True, "blendingMode": "add"}}},
        {"operation": "property.set", "args": {"comp": comp, "layer": plane, "property": ["Transform", "Position"], "value": list(center)}},
        {"operation": "property.set", "args": {"comp": comp, "layer": plane, "property": ["Transform", "X Rotation"], "value": pitch_x}},
        {"operation": "property.set", "args": {"comp": comp, "layer": plane, "property": ["Transform", "Y Rotation"], "value": yaw_y}},
        {"operation": "property.set", "args": {"comp": comp, "layer": plane, "property": ["Transform", "Z Rotation"], "value": roll_z}},
        {"operation": "property.set", "args": {"comp": comp, "layer": plane, "property": ["Transform", "Opacity"], "value": 22}},
        {"operation": "effect.add", "args": {"comp": comp, "layer": plane, "matchName": "ADBE Grid"}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": plane, "effectIndex": 1, "property": ["Anchor"], "value": [width / 2, height / 2]}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": plane, "effectIndex": 1, "property": ["Width"], "value": 180}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": plane, "effectIndex": 1, "property": ["Border"], "value": 2.2}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": plane, "effectIndex": 1, "property": ["Color"], "value": grid_color}},
    ]

    if pitch_x == 0 and yaw_y == 0:
        # Subtle architectural blueprint ticks flat on the background floor perimeter (BEHIND all Z=0 cards, never in front!)
        fz = center[2] - 10
        hud_coords = [
            (center[0] - 2300, center[1] - 2400, fz, "GRID.REF // 00.1"),
            (center[0] + 2100, center[1] - 2400, fz, "AXIS.XY // 4K"),
            (center[0] - 2300, center[1] + 2400, fz, "QUANT.SYS // LIVE"),
            (center[0] + 2100, center[1] + 2400, fz, "PLANE.3D // SYNC"),
        ]
        for idx, (hx, hy, hz, label) in enumerate(hud_coords, 1):
            nm = f"{tag}_HUD_{idx}"
            ops += _create_3d_text(comp, nm, f"+ {label}", "CascadiaMonoRoman-Bold", 38, DIM_SLATE, t0, t1, [hx, hy, hz], just="left", tracking=50)
            ops.append({"operation": "property.set", "args": {"comp": comp, "layer": nm, "property": ["Transform", "Opacity"], "value": 20}})
    return ops


def plane_lighting(comp, t0, t1, waypoints, tag="LIGHT3D", accents=None, key_offset=(-680, -1050, -1650)):
    """3-light rig for a 3D plane scene (illuminates floor + glass card surfaces; 3D text ignores lights to stay razor-sharp)."""
    amb, key, acc = f"{tag}_AMBIENT", f"{tag}_KEY", f"{tag}_ACCENT"
    lo = "Light Options"
    ops = [
        {"operation": "layer.create_light", "args": {"comp": comp, "name": amb, "lightType": "ambient"}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": amb, "inPoint": t0, "outPoint": t1}},
        {"operation": "property.set", "args": {"comp": comp, "layer": amb, "property": [lo, "Intensity"], "value": 44}},
        {"operation": "property.set", "args": {"comp": comp, "layer": amb, "property": [lo, "Color"], "value": [0.76, 0.84, 1.0, 1]}},
        {"operation": "layer.create_light", "args": {"comp": comp, "name": key, "lightType": "spot"}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": key, "inPoint": t0, "outPoint": t1}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Intensity"], "value": 120}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Color"], "value": [1.0, 0.96, 0.90, 1]}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Cone Angle"], "value": 78}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Cone Feather"], "value": 72}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Casts Shadows"], "value": 1}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Shadow Darkness"], "value": 52}},
        {"operation": "property.set", "args": {"comp": comp, "layer": key, "property": [lo, "Shadow Diffusion"], "value": 95}},
    ]
    times = [round(w["t"], 2) for w in waypoints]
    poi = [[w["pos"][0], w["pos"][1], w["pos"][2]] for w in waypoints]
    lpos = [[p[0] + key_offset[0], p[1] + key_offset[1], p[2] + key_offset[2]] for p in poi]
    ease = list(range(1, len(times) + 1))
    ops += _k(comp, key, ["Transform", "Point of Interest"], times, poi, ease=ease, in_inf=86, out_inf=80)
    ops += _k(comp, key, ["Transform", "Position"], times, lpos, ease=ease, in_inf=86, out_inf=80)
    if accents:
        ops += [
            {"operation": "layer.create_light", "args": {"comp": comp, "name": acc, "lightType": "point"}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": acc, "inPoint": t0, "outPoint": t1}},
            {"operation": "property.set", "args": {"comp": comp, "layer": acc, "property": [lo, "Intensity"], "value": 65}},
            {"operation": "property.set", "args": {"comp": comp, "layer": acc, "property": [lo, "Falloff"], "value": 2}},
            {"operation": "property.set", "args": {"comp": comp, "layer": acc, "property": [lo, "Radius"], "value": 260}},
            {"operation": "property.set", "args": {"comp": comp, "layer": acc, "property": [lo, "Falloff Distance"], "value": 1550}},
        ]
        at = [round(a[0], 2) for a in accents]
        ops += _k(comp, acc, ["Transform", "Position"], at, [list(a[2]) for a in accents], ease=list(range(1, len(at) + 1)), in_inf=86, out_inf=80)
        ops += [{"operation": "keyframe.set_batch", "args": {"comp": comp, "layer": acc, "property": [lo, "Color"],
                                                             "times": at, "values": [list(a[1]) + [1] for a in accents]}}]
    return ops


def _vector_illustration_groups(icon_type: str, col: list[float], oy: float = 42.0) -> list[dict]:
    """Built-in crisp vector graphics centered around `(0, oy)` inside the terminal card body (below the 96px top header bar)."""
    if icon_type == "hammer":
        return [
            # Downtrend context curve
            {"name": "trend_in", "path": [[-260, oy - 110], [-150, oy - 30], [-90, oy + 40]], "stroke": CRIMSON, "width": 8},
            # Hammer long lower wick + small emerald body at top
            {"name": "wick", "path": [[0, oy - 70], [0, oy + 170]], "stroke": EMERALD, "width": 10},
            {"name": "body", "rect": [88, 70], "at": [0, oy - 55], "round": 8, "fill": EMERALD},
            # Dynamic upward reversal arrow
            {"name": "arrow_stem", "path": [[90, oy + 80], [170, oy + 10], [250, oy - 120]], "stroke": EMERALD, "width": 14},
            {"name": "arrow_head", "path": [[180, oy - 120], [250, oy - 120], [250, oy - 50]], "stroke": EMERALD, "width": 14},
            {"name": "glow_dot", "ellipse": [34, 34], "at": [250, oy - 120], "fill": EMERALD},
        ]
    if icon_type == "shooting_star":
        return [
            # Uptrend context curve
            {"name": "trend_in", "path": [[-260, oy + 110], [-150, oy + 30], [-90, oy - 40]], "stroke": EMERALD, "width": 8},
            # Shooting star long upper wick + small crimson body at bottom
            {"name": "wick", "path": [[0, oy - 170], [0, oy + 70]], "stroke": CRIMSON, "width": 10},
            {"name": "body", "rect": [88, 70], "at": [0, oy + 55], "round": 8, "fill": CRIMSON},
            # Dynamic downward reversal arrow
            {"name": "arrow_stem", "path": [[90, oy - 80], [170, oy - 10], [250, oy + 120]], "stroke": CRIMSON, "width": 14},
            {"name": "arrow_head", "path": [[180, oy + 120], [250, oy + 120], [250, oy + 50]], "stroke": CRIMSON, "width": 14},
            {"name": "glow_dot", "ellipse": [34, 34], "at": [250, oy + 120], "fill": CRIMSON},
        ]
    if icon_type == "bullish_engulfing":
        return [
            # Prior small red candle
            {"name": "red_wick", "path": [[-120, oy - 90], [-120, oy + 90]], "stroke": CRIMSON, "width": 6},
            {"name": "red_body", "rect": [64, 100], "at": [-120, oy], "round": 8, "fill": CRIMSON},
            # Giant green engulfing candle
            {"name": "grn_wick", "path": [[30, oy - 170], [30, oy + 170]], "stroke": EMERALD, "width": 10},
            {"name": "grn_body", "rect": [98, 250], "at": [30, oy], "round": 12, "fill": EMERALD},
            # Giant upward reversal arrow
            {"name": "arrow_stem", "path": [[140, oy + 60], [210, oy - 20], [270, oy - 120]], "stroke": EMERALD, "width": 14},
            {"name": "arrow_head", "path": [[200, oy - 120], [270, oy - 120], [270, oy - 50]], "stroke": EMERALD, "width": 14},
            {"name": "glow_dot", "ellipse": [34, 34], "at": [270, oy - 120], "fill": EMERALD},
        ]
    if icon_type == "bearish_engulfing":
        return [
            # Prior small green candle
            {"name": "grn_wick", "path": [[-120, oy - 90], [-120, oy + 90]], "stroke": EMERALD, "width": 6},
            {"name": "grn_body", "rect": [64, 100], "at": [-120, oy], "round": 8, "fill": EMERALD},
            # Giant red engulfing candle
            {"name": "red_wick", "path": [[30, oy - 170], [30, oy + 170]], "stroke": CRIMSON, "width": 10},
            {"name": "red_body", "rect": [98, 250], "at": [30, oy], "round": 12, "fill": CRIMSON},
            # Giant downward crash arrow
            {"name": "arrow_stem", "path": [[140, oy - 60], [210, oy + 20], [270, oy + 120]], "stroke": CRIMSON, "width": 14},
            {"name": "arrow_head", "path": [[200, oy + 120], [270, oy + 120], [270, oy + 50]], "stroke": CRIMSON, "width": 14},
            {"name": "glow_dot", "ellipse": [34, 34], "at": [270, oy + 120], "fill": CRIMSON},
        ]
    if icon_type == "doji":
        return [
            # Vertical wick line
            {"name": "wick", "path": [[0, oy - 180], [0, oy + 180]], "stroke": GOLD, "width": 8},
            # Horizontal body bar (equal open/close)
            {"name": "body_bar", "rect": [150, 16], "at": [0, oy], "round": 4, "fill": GOLD},
            # Balance circle ring
            {"name": "ring", "ellipse": [200, 200], "at": [0, oy], "stroke": GOLD, "width": 4},
            # Equilibrium left/right arrows
            {"name": "arrow_l", "path": [[-130, oy - 30], [-210, oy], [-130, oy + 30]], "stroke": GOLD, "width": 8},
            {"name": "arrow_r", "path": [[130, oy - 30], [210, oy], [130, oy + 30]], "stroke": GOLD, "width": 8},
        ]
    if icon_type == "candlestick":
        return [
            {"name": "wick1", "path": [[-210, oy - 115], [-210, oy + 125]], "stroke": CRIMSON, "width": 8},
            {"name": "body1", "rect": [58, 120], "at": [-210, oy + 10], "round": 10, "fill": CRIMSON},
            {"name": "wick2", "path": [[-70, oy - 145], [-70, oy + 95]], "stroke": CRIMSON, "width": 8},
            {"name": "body2", "rect": [58, 135], "at": [-70, oy - 15], "round": 10, "fill": CRIMSON},
            {"name": "wick3", "path": [[70, oy - 95], [70, oy + 155]], "stroke": EMERALD, "width": 8},
            {"name": "body3", "rect": [58, 150], "at": [70, oy + 30], "round": 10, "fill": EMERALD},
            {"name": "wick4", "path": [[210, oy - 175], [210, oy + 110]], "stroke": EMERALD, "width": 10},
            {"name": "body4", "rect": [66, 195], "at": [210, oy - 35], "round": 12, "fill": EMERALD},
        ]
    if icon_type in ("chart_down", "loss", "crash"):
        return [
            {"name": "trend_dn", "path": [[-290, oy - 115], [-95, oy - 30], [65, oy - 75], [285, oy + 130]], "stroke": CRIMSON, "width": 15},
            {"name": "arrow_dn", "path": [[215, oy + 130], [285, oy + 130], [285, oy + 60]], "stroke": CRIMSON, "width": 15},
        ]
    if icon_type in ("warning", "trap", "x"):
        return [
            {"name": "x1", "path": [[-90, oy - 90], [90, oy + 90]], "stroke": CRIMSON, "width": 18},
            {"name": "x2", "path": [[90, oy - 90], [-90, oy + 90]], "stroke": CRIMSON, "width": 18},
            {"name": "ring", "ellipse": [280, 280], "at": [0, oy], "stroke": CRIMSON, "width": 9},
        ]
    if icon_type in ("target", "zone"):
        return [
            {"name": "outer", "ellipse": [290, 290], "at": [0, oy], "stroke": col, "width": 7},
            {"name": "inner", "ellipse": [155, 155], "at": [0, oy], "stroke": col, "width": 9},
            {"name": "dot", "ellipse": [34, 34], "at": [0, oy], "fill": col},
            {"name": "ch_h", "path": [[-190, oy], [190, oy]], "stroke": DIM_SLATE, "width": 4},
            {"name": "ch_v", "path": [[0, oy - 175], [0, oy + 175]], "stroke": DIM_SLATE, "width": 4},
        ]
    if icon_type in ("rr", "scale_rr"):
        return [
            {"name": "risk_box", "rect": [170, 95], "at": [-140, oy + 75], "round": 12, "fill": CRIMSON},
            {"name": "rew_box", "rect": [170, 225], "at": [140, oy + 10], "round": 12, "fill": EMERALD},
            {"name": "base_ln", "path": [[-280, oy + 125], [280, oy + 125]], "stroke": SLATE, "width": 6},
        ]
    if icon_type in ("shield", "stop_loss"):
        return [
            {"name": "sh", "path": [[0, oy - 135], [135, oy - 80], [110, oy + 60], [0, oy + 145], [-110, oy + 60], [-135, oy - 80]], "closed": True, "stroke": col, "width": 12},
            {"name": "cut_ln", "path": [[-190, oy], [190, oy]], "stroke": CRIMSON, "width": 10},
        ]
    # Default: bullish upward equity/chart curve
    return [
        {"name": "trend_up", "path": [[-290, oy + 115], [-100, oy + 30], [60, oy + 65], [285, oy - 125]], "stroke": col, "width": 15},
        {"name": "arrow_up", "path": [[215, oy - 125], [285, oy - 125], [285, oy - 55]], "stroke": col, "width": 15},
        {"name": "glow_dot", "ellipse": [36, 36], "at": [285, oy - 125], "fill": col},
    ]


def _build_terminal_card(comp, frame_name, idx, st, t0, t1, wx, wy, wz, img_w=1040, img_h=640, lit=True):
    """Reusable FinTech Terminal Card with a dedicated 98px Header Strip (`[ BADGE ]` left, `STAT` right)
    and spacious viewport below so nothing EVER overlaps a border stroke or icon."""
    col = st.get("color", EMERALD)
    hdr_h = 98
    ops = [
        {"operation": "layer.create_shape", "args": {"comp": comp, "name": frame_name}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": frame_name, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": frame_name, "props": {"threeDLayer": True, "motionBlur": True}}},
        {"operation": "property.set", "args": {"comp": comp, "layer": frame_name, "property": ["Transform", "Position"], "value": [wx, wy, wz]}},
    ]

    gi = 0
    if not st.get("item_id"):
        v_groups = _vector_illustration_groups(st.get("icon", "chart_up"), col, oy=44.0)
        for vg in v_groups:
            gi += 1
            ops.append({"operation": "shape.add_group", "args": {"comp": comp, "layer": frame_name, "name": vg.get("name", f"vg{gi}")}})
            if "rect" in vg:
                ops.append({"operation": "shape.add_rect", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi,
                                                                     "size": vg["rect"], "position": vg.get("at", [0, 0]), "roundness": vg.get("round", 0)}})
            if "ellipse" in vg:
                ops.append({"operation": "shape.add_ellipse", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi,
                                                                        "size": vg["ellipse"], "position": vg.get("at", [0, 0])}})
            if "path" in vg:
                ops.append({"operation": "shape.add_path", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi,
                                                                     "vertices": vg["path"], "closed": vg.get("closed", False)}})
            if "stroke" in vg:
                ops.append({"operation": "shape.add_stroke", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi,
                                                                       "color": vg["stroke"] + [1], "width": vg.get("width", 10)}})
            if "fill" in vg:
                ops.append({"operation": "shape.add_fill", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi,
                                                                     "color": vg["fill"] + [1], "opacity": 100}})

    # Header divider line at `y = -img_h/2 + hdr_h`
    gi += 1
    div_y = -img_h / 2 + hdr_h
    ops += [
        {"operation": "shape.add_group", "args": {"comp": comp, "layer": frame_name, "name": "hdr_div"}},
        {"operation": "shape.add_path", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi,
                                                 "vertices": [[-img_w / 2 + 12, div_y], [img_w / 2 - 12, div_y]], "closed": False}},
        {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi, "color": DIM_SLATE + [1], "width": 3}},
    ]

    # Main outer glass box (drawn last so it sits behind vector icons & divider)
    gi += 1
    ops += [
        {"operation": "shape.add_group", "args": {"comp": comp, "layer": frame_name, "name": "box"}},
        {"operation": "shape.add_rect", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi, "size": [img_w, img_h], "roundness": 42}},
        {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi, "color": col + [1], "width": 7}},
        {"operation": "shape.add_fill", "args": {"comp": comp, "layer": frame_name, "groupIndex": gi, "color": CARD_DARK + [1], "opacity": 96}},
        {"operation": "effect.add", "args": {"comp": comp, "layer": frame_name, "matchName": "ADBE Drop Shadow"}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": frame_name, "effectIndex": 1, "property": ["Distance"], "value": 38}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": frame_name, "effectIndex": 1, "property": ["Softness"], "value": 95}},
    ]
    if lit:
        ops += _material(comp, frame_name, casts=1, specular=40, shininess=22)

    if st.get("item_id"):
        img_layer = f"{frame_name}_IMG"
        isc = st.get("item_scale", 56)
        ops += [
            {"operation": "layer.create_footage", "args": {"comp": comp, "sourceItemId": st["item_id"], "name": img_layer}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": img_layer, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": img_layer, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "layer.set_parent", "args": {"comp": comp, "layer": img_layer, "parentLayer": frame_name, "jump": True}},
            {"operation": "property.set", "args": {"comp": comp, "layer": img_layer, "property": ["Transform", "Position"], "value": [0, 44, -6]}},
            {"operation": "property.set", "args": {"comp": comp, "layer": img_layer, "property": ["Transform", "Scale"], "value": [isc, isc, 100]}},
        ]

    badge_txt = st.get("badge", f"0{idx+1} // NODE")
    title_txt = st.get("title", f"POINT 0{idx+1}")
    sub_txt = st.get("sub", "")
    stat_txt = st.get("stat", "")

    # Header left: `[ BADGE ]` cleanly inside the 98px header strip (Z = -6 -> zero perspective border shift!)
    b_size = _fit_size(f"[ {badge_txt} ]", 40, img_w * 0.56)
    ops += _create_3d_text(
        comp, f"{frame_name}_BDG", f"[ {badge_txt} ]", "CascadiaMonoRoman-Bold", b_size, col,
        t0, t1, [-img_w / 2 + 38, -img_h / 2 + 64, -6], just="left", parent=frame_name, tracking=20
    )

    # Header right: `STAT` cleanly inside the 98px header strip on the right!
    if stat_txt:
        st_size = _fit_size(stat_txt, 50, img_w * 0.34)
        ops += _create_3d_text(
            comp, f"{frame_name}_STAT", stat_txt, "CascadiaMonoRoman-Bold", st_size, WHITE,
            t0, t1, [img_w / 2 - 38, -img_h / 2 + 66, -6], just="right", parent=frame_name, tracking=10
        )

    # Title cleanly below card (`img_h/2 + 135`, Z = -8) with auto-fit width
    t_bn = _has_bangla(title_txt)
    t_font = "HindSiliguri-Bold" if t_bn else "PlusJakartaSans-ExtraBold"
    t_size = _fit_size(title_txt, 108 if t_bn else 112, img_w * 1.22, is_bn=t_bn)
    ops += _create_3d_text(
        comp, f"{frame_name}_TTL", title_txt, t_font, t_size, WHITE,
        t0, t1, [0, img_h / 2 + 132, -8], just="center", parent=frame_name, shadow=True
    )

    # Subtitle cleanly below Title (`img_h/2 + 236`, Z = -8) with auto-fit width
    if sub_txt:
        s_bn = _has_bangla(sub_txt)
        s_font = "HindSiliguri-SemiBold" if s_bn else "InstrumentSerif-Italic"
        s_size = _fit_size(sub_txt, 78 if s_bn else 84, img_w * 1.25, is_bn=s_bn)
        ops += _create_3d_text(
            comp, f"{frame_name}_SUB", sub_txt, s_font, s_size, GOLD if not s_bn else SLATE,
            t0, t1, [0, img_h / 2 + 236, -8], just="center", parent=frame_name, shadow=True
        )
    return ops


# ===========================================================================
# VARIATION 1: CONNECTED MIND-MAP BOARD (`canvas_board_plane_3d`)
# ===========================================================================
def canvas_board_plane_3d(r, comp, t0, t1, stops, tag="BOARD3D", opaque_bg=True, line_style="orthogonal",
                          overview_start=False, overview_end=True, lit=True):
    """VARIATION 1 — Connected FinTech Terminal Mind-Map Board on an `9600x10800` 3D blueprint plane."""
    default_coords = [
        [1080, 1450, 0],
        [3320, 1840, 0],
        [1360, 3480, 0],
        [3580, 3920, 0],
        [2320, 5380, 0],
        [4320, 5740, 0],
    ]
    default_orbits = [
        [17, -12, -2.5],
        [15, 13, 2.5],
        [19, -11, -3.0],
        [14, 12, 2.0],
        [18, -9, -2.0],
        [15, 10, 2.5],
    ]

    coords = [s.get("pos", default_coords[i % len(default_coords)]) for i, s in enumerate(stops)]
    orbits = [s.get("orbit", default_orbits[i % len(default_orbits)]) for i, s in enumerate(stops)]

    cx = sum(c[0] for c in coords) / max(1, len(coords))
    cy = sum(c[1] for c in coords) / max(1, len(coords))

    ops = infinite_grid_plane(comp, t0, t1, tag=f"{tag}_BG", center=(round(cx), round(cy), 420), opaque_bg=opaque_bg, lit=lit)
    waypoints = []
    if overview_start:
        waypoints.append({"t": round(t0, 2), "pos": [round(cx), round(cy), -1950], "orbit": [22, -6, 0]})

    for idx, st in enumerate(stops):
        if idx == 0:
            continue
        parent_idx = st.get("from_stop", idx - 1)
        p0, p1 = coords[parent_idx], coords[idx]
        nt = round(st["t"], 2)
        t_draw0 = round(max(t0, nt - 0.40), 2)
        t_draw1 = round(max(t_draw0 + 0.35, nt), 2)
        col = st.get("color", EMERALD)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        verts = [[0, 0], [dx, dy]] if line_style == "direct" else [[0, 0], [dx * 0.52, 0], [dx * 0.52, dy], [dx, dy]]

        bg_wire = f"{tag}_TRACK_{idx}"
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": bg_wire}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": bg_wire, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": bg_wire, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": bg_wire, "property": ["Transform", "Position"], "value": [p0[0], p0[1], p0[2] + 35]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": bg_wire, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": bg_wire, "groupIndex": 1, "vertices": verts, "closed": False}},
            {"operation": "shape.add_rounded_corners", "args": {"comp": comp, "layer": bg_wire, "groupIndex": 1, "radius": 64}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": bg_wire, "groupIndex": 1, "color": DIM_SLATE + [1], "width": 6}},
        ]

        act_wire = f"{tag}_LINE_{idx}"
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": act_wire}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": act_wire, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": act_wire, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": act_wire, "property": ["Transform", "Position"], "value": [p0[0], p0[1], p0[2] + 28]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": act_wire, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": act_wire, "groupIndex": 1, "vertices": verts, "closed": False}},
            {"operation": "shape.add_rounded_corners", "args": {"comp": comp, "layer": act_wire, "groupIndex": 1, "radius": 64}},
            {"operation": "shape.add_trim_paths", "args": {"comp": comp, "layer": act_wire, "groupIndex": 1, "start": 0, "end": 0}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": act_wire, "groupIndex": 1, "color": col + [1], "width": 14}},
        ]
        if lit:
            ops += _material(comp, act_wire, casts=1)
        ops += _k(comp, act_wire, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [t_draw0, t_draw1], [0, 100], ease=[2])
        r.sfx("whoosh-motion-243505.mp3", t_draw0, "bed", -13, 0.55)

    for idx, st in enumerate(stops):
        nt = round(st["t"], 2)
        if overview_start and idx == 0 and nt <= round(t0 + 0.38, 2):
            nt = round(t0 + 0.42, 2)
        if waypoints and nt <= waypoints[-1]["t"]:
            nt = round(waypoints[-1]["t"] + 0.12, 2)
        wx, wy, wz = coords[idx]
        waypoints.append({"t": nt, "pos": [wx, wy + 115, wz], "orbit": orbits[idx]})

        frame_name = f"{tag}_STOP_{idx+1}"
        ops += _build_terminal_card(comp, frame_name, idx, st, t0, t1, wx, wy, wz, img_w=1040, img_h=640, lit=lit)

        if idx == 0 and not overview_start:
            t_in1 = round(t0 + 0.12, 2)
            t_in2 = max(round(t_in1 + 0.04, 2), round(t1 - 0.16, 2))
            t_in3 = max(round(t_in2 + 0.04, 2), round(t1, 2))
            ops += _k(comp, frame_name, ["Transform", "Scale"], [t0, round(t0 + 0.22, 2), round(t0 + 0.34, 2)],
                      [[76, 76, 100], [104, 104, 100], [100, 100, 100]], ease=[2, 3])
            ops += _k(comp, frame_name, ["Transform", "Opacity"], [t0, t_in1, t_in2, t_in3], [0, 100, 100, 0])
        else:
            t_pre = max(round(t0 + 0.04, 2), round(nt - 0.12, 2))
            t_s1 = max(round(t_pre + 0.04, 2), round(nt + 0.12, 2))
            t_s2 = max(round(t_s1 + 0.04, 2), round(nt + 0.24, 2))
            t_o1 = max(round(t_pre + 0.04, 2), round(nt + 0.08, 2))
            t_o2 = max(round(t_o1 + 0.04, 2), round(t1 - 0.16, 2))
            t_o3 = max(round(t_o2 + 0.04, 2), round(t1, 2))
            ops += _k(comp, frame_name, ["Transform", "Scale"], [t0, t_pre, t_s1, t_s2],
                      [[88, 88, 100], [88, 88, 100], [105, 105, 100], [100, 100, 100]], ease=[3, 4])
            ops += _k(comp, frame_name, ["Transform", "Opacity"], [t0, t_pre, t_o1, t_o2, t_o3], [36, 36, 100, 100, 0])
        r.sfx("mouse-click-104737.mp3", nt, "extra", -5, 0.28)

    if overview_end and len(stops) >= 2 and t1 - waypoints[-1]["t"] >= 0.9:
        t_wide = round(max(waypoints[-1]["t"] + 0.55, t1 - 0.85), 2)
        waypoints.append({"t": t_wide, "pos": [round(cx), round(cy) + 720, -3250], "orbit": [16, 0, 0]})
        r.sfx("whoosh-vortex-243128.mp3", round(t_wide - 0.12, 2), "bed", -14, 0.65)

    ops += camera_rig_3d(comp, t0, t1, waypoints, tag=f"{tag}_CAM", drift=True)
    if lit:
        accents = [(max(t0, s.get("t", t0) - 0.1), s.get("color", EMERALD), [coords[i][0], coords[i][1] + 40, -420])
                   for i, s in enumerate(stops)]
        ops += plane_lighting(comp, t0, t1, waypoints, tag=f"{tag}_LGT", accents=accents)
    return ops


# ===========================================================================
# VARIATION 2: 3D Z-DEPTH TIMELINE CORRIDOR FLY-THROUGH (`timeline_tunnel_3d`)
# ===========================================================================
def timeline_tunnel_3d(r, comp, t0, t1, stops, tag="TUNNEL3D", opaque_bg=True, lit=True):
    """VARIATION 2 — 3D Z-Depth Chronological Fly-Through Corridor!
    A horizontal perspective floor grid (`X Rotation = +78°`) stretches deep into Z-space (`Z = 0 -> +4200`)
    with a glowing center runway spine. Milestones stand staggered left & right at `Z = 0, +1450, +2900, +4350`,
    and the 3D Camera physically FLIES FORWARD down the Z-axis past each milestone!"""
    z_step = 1480
    ops = []
    max_z = max(1, len(stops) - 1) * z_step
    mid_z = max_z / 2.0

    if opaque_bg:
        bg = f"{tag}_VOID"
        ops += [
            {"operation": "layer.create_solid", "args": {"comp": comp, "name": bg, "color": VOID_LIT if lit else GRID_DARK, "width": 16000, "height": 16000}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": bg, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": bg, "props": {"threeDLayer": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": bg, "property": ["Transform", "Position"], "value": [1080, 1920, max_z + 2600]}},
        ]

    # True horizontal floor grid pitched at +82 degrees underneath the camera flight path!
    floor = f"{tag}_FLOOR"
    ops += [
        {"operation": "layer.create_solid", "args": {"comp": comp, "name": floor, "color": OBS, "width": 7200, "height": 12000}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": floor, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": floor, "props": {"threeDLayer": True, "blendingMode": "add"}}},
        {"operation": "property.set", "args": {"comp": comp, "layer": floor, "property": ["Transform", "Position"], "value": [1080, 2680, mid_z]}},
        {"operation": "property.set", "args": {"comp": comp, "layer": floor, "property": ["Transform", "X Rotation"], "value": 84}},
        {"operation": "property.set", "args": {"comp": comp, "layer": floor, "property": ["Transform", "Opacity"], "value": 34}},
        {"operation": "effect.add", "args": {"comp": comp, "layer": floor, "matchName": "ADBE Grid"}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": floor, "effectIndex": 1, "property": ["Anchor"], "value": [3600, 6000]}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": floor, "effectIndex": 1, "property": ["Width"], "value": 200}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": floor, "effectIndex": 1, "property": ["Border"], "value": 3.0}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": floor, "effectIndex": 1, "property": ["Color"], "value": CYAN}},
    ]

    # Glowing central Z-runway line along the floor
    runway = f"{tag}_RUNWAY"
    ops += [
        {"operation": "layer.create_shape", "args": {"comp": comp, "name": runway}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": runway, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": runway, "props": {"threeDLayer": True, "motionBlur": True}}},
        {"operation": "property.set", "args": {"comp": comp, "layer": runway, "property": ["Transform", "Position"], "value": [1080, 2670, mid_z]}},
        {"operation": "property.set", "args": {"comp": comp, "layer": runway, "property": ["Transform", "X Rotation"], "value": 84}},
        {"operation": "shape.add_group", "args": {"comp": comp, "layer": runway, "name": "g1"}},
        {"operation": "shape.add_path", "args": {"comp": comp, "layer": runway, "groupIndex": 1, "vertices": [[0, -5200], [0, 5200]], "closed": False}},
        {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": runway, "groupIndex": 1, "color": CYAN + [1], "width": 16}},
    ]

    waypoints = []
    accents = []
    for idx, st in enumerate(stops):
        nt = round(st["t"], 2)
        if waypoints and nt <= waypoints[-1]["t"]:
            nt = round(waypoints[-1]["t"] + 0.14, 2)
        side = -1 if idx % 2 == 0 else 1
        wx = 1080 + side * 230
        wy = 1760
        wz = idx * z_step
        yaw = -9 * side
        waypoints.append({"t": nt, "pos": [wx, wy + 110, wz - 120], "orbit": [5, yaw, side * 1.8]})
        accents.append((max(t0, nt - 0.1), st.get("color", CYAN), [wx, wy, wz - 380]))

        frame_name = f"{tag}_MILE_{idx+1}"
        ops += _build_terminal_card(comp, frame_name, idx, st, t0, t1, wx, wy, wz, img_w=1020, img_h=620, lit=lit)
        # Subtle inward tilt toward the corridor center
        ops.append({"operation": "property.set", "args": {"comp": comp, "layer": frame_name, "property": ["Transform", "Y Rotation"], "value": -side * 8}})

        # Vertical glowing pylon connecting the floating card down to the 3D floor grid!
        pylon = f"{tag}_PYLON_{idx+1}"
        col = st.get("color", CYAN)
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": pylon}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": pylon, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": pylon, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "layer.set_parent", "args": {"comp": comp, "layer": pylon, "parentLayer": frame_name, "jump": True}},
            {"operation": "property.set", "args": {"comp": comp, "layer": pylon, "property": ["Transform", "Position"], "value": [0, 0, 12]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": pylon, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": pylon, "groupIndex": 1, "vertices": [[0, 320], [0, 910]], "closed": False}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": pylon, "groupIndex": 1, "color": col + [1], "width": 8}},
        ]

        # All future milestones are visible down the Z-corridor ahead of the camera and fade cleanly behind lens
        t_in = round(t0 + 0.10, 2)
        t_out0 = max(round(t_in + 0.08, 2), round(t1 - 0.16, 2))
        ops += _k(comp, frame_name, ["Transform", "Opacity"], [t0, t_in, t_out0, round(t1, 2)], [0, 100, 100, 0])
        if idx > 0:
            r.sfx("fast-woosh-230497.mp3", round(max(t0, nt - 0.18), 2), "bed", -13, 0.55)
        r.sfx("mouse-click-104737.mp3", nt, "extra", -5, 0.28)

    ops += camera_rig_3d(comp, t0, t1, waypoints, tag=f"{tag}_CAM", drift=True)
    if lit:
        ops += plane_lighting(comp, t0, t1, waypoints, tag=f"{tag}_LGT", accents=accents)
    return ops


# ===========================================================================
# VARIATION 3: CENTRAL CORE HUB + RADIATING SPOKE SATELLITES (`radial_hub_3d`)
# ===========================================================================
def radial_hub_3d(r, comp, t0, t1, hub, satellites, tag="HUB3D", opaque_bg=True, overview_end=True, lit=True):
    """VARIATION 3 — Central Core Hub + Orbiting Spoke Satellites!
    `hub`: dict {"t", "badge", "title", "sub", "color"} placed at center `(2200, 2600, 0)` inside a glowing double-ring core.
    `satellites`: list of 2-4 stop dicts radiating outward on diagonal spokes with Trim Paths energy beams!"""
    cx, cy = 2200, 2600
    ops = infinite_grid_plane(comp, t0, t1, tag=f"{tag}_BG", center=(cx, cy, 420), opaque_bg=opaque_bg, lit=lit)

    # Radial satellite offsets around `(cx, cy)` so nothing overlaps!
    n_sat = len(satellites)
    if n_sat == 2:
        offsets = [(-1480, -1080), (1480, 1080)]
    elif n_sat == 3:
        offsets = [(-1450, -1120), (1450, -1120), (0, 1480)]
    else:
        offsets = [(-1480, -1120), (1480, -1120), (-1480, 1280), (1480, 1280)]

    sat_coords = [[cx + offsets[i % len(offsets)][0], cy + offsets[i % len(offsets)][1], 0] for i in range(n_sat)]

    # 1. Draw Radial Spokes from Hub -> Satellites first (behind Hub & Cards)
    for idx, sat in enumerate(satellites):
        sx, sy, sz = sat_coords[idx]
        dx, dy = sx - cx, sy - cy
        nt = round(sat["t"], 2)
        t_draw0 = round(max(t0, nt - 0.38), 2)
        t_draw1 = round(max(t_draw0 + 0.35, nt), 2)
        col = sat.get("color", CYAN)

        spoke_bg = f"{tag}_SPK_BG_{idx+1}"
        spoke_ac = f"{tag}_SPK_{idx+1}"
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": spoke_bg}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": spoke_bg, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": spoke_bg, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": spoke_bg, "property": ["Transform", "Position"], "value": [cx, cy, 32]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": spoke_bg, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": spoke_bg, "groupIndex": 1, "vertices": [[0, 0], [dx, dy]], "closed": False}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": spoke_bg, "groupIndex": 1, "color": DIM_SLATE + [1], "width": 6}},

            {"operation": "layer.create_shape", "args": {"comp": comp, "name": spoke_ac}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": spoke_ac, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": spoke_ac, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": spoke_ac, "property": ["Transform", "Position"], "value": [cx, cy, 24]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": spoke_ac, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": spoke_ac, "groupIndex": 1, "vertices": [[0, 0], [dx, dy]], "closed": False}},
            {"operation": "shape.add_trim_paths", "args": {"comp": comp, "layer": spoke_ac, "groupIndex": 1, "start": 0, "end": 0}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": spoke_ac, "groupIndex": 1, "color": col + [1], "width": 14}},
        ]
        ops += _k(comp, spoke_ac, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [t_draw0, t_draw1], [0, 100], ease=[2])
        r.sfx("whoosh-motion-243505.mp3", t_draw0, "bed", -13, 0.50)

    # 2. Build Central Circular Core Hub at `(cx, cy, 0)`
    h_col = hub.get("color", GOLD)
    hub_name = f"{tag}_CORE"
    ht0 = round(hub.get("t", t0), 2)
    ops += [
        {"operation": "layer.create_shape", "args": {"comp": comp, "name": hub_name}},
        {"operation": "layer.set_timing", "args": {"comp": comp, "layer": hub_name, "inPoint": t0, "outPoint": t1}},
        {"operation": "layer.set_props", "args": {"comp": comp, "layer": hub_name, "props": {"threeDLayer": True, "motionBlur": True}}},
        {"operation": "property.set", "args": {"comp": comp, "layer": hub_name, "property": ["Transform", "Position"], "value": [cx, cy, 0]}},
        {"operation": "shape.add_group", "args": {"comp": comp, "layer": hub_name, "name": "outer_ring"}},
        {"operation": "shape.add_ellipse", "args": {"comp": comp, "layer": hub_name, "groupIndex": 1, "size": [980, 980]}},
        {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": hub_name, "groupIndex": 1, "color": h_col + [1], "width": 6}},
        {"operation": "shape.add_group", "args": {"comp": comp, "layer": hub_name, "name": "core_disc"}},
        {"operation": "shape.add_ellipse", "args": {"comp": comp, "layer": hub_name, "groupIndex": 2, "size": [840, 840]}},
        {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": hub_name, "groupIndex": 2, "color": h_col + [1], "width": 12}},
        {"operation": "shape.add_fill", "args": {"comp": comp, "layer": hub_name, "groupIndex": 2, "color": CARD_DARK + [1], "opacity": 97}},
        {"operation": "effect.add", "args": {"comp": comp, "layer": hub_name, "matchName": "ADBE Drop Shadow"}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": hub_name, "effectIndex": 1, "property": ["Distance"], "value": 42}},
        {"operation": "effect.set_property", "args": {"comp": comp, "layer": hub_name, "effectIndex": 1, "property": ["Softness"], "value": 100}},
    ]
    if lit:
        ops += _material(comp, hub_name, casts=1, specular=50, shininess=25)

    h_badge = hub.get("badge", "CORE // HUB")
    h_title = hub.get("title", "CORE RULE")
    h_sub = hub.get("sub", "")
    ht_bn = _has_bangla(h_title)
    ht_font = "HindSiliguri-Bold" if ht_bn else "Syne-ExtraBold"
    ht_size = _fit_size(h_title, 108, 700, is_bn=ht_bn)

    ops += _create_3d_text(comp, f"{hub_name}_BDG", f"[ {h_badge} ]", "CascadiaMonoRoman-Bold", 40, h_col, t0, t1, [0, -155, -10], just="center", parent=hub_name, tracking=25)
    ops += _create_3d_text(comp, f"{hub_name}_TTL", h_title, ht_font, ht_size, WHITE, t0, t1, [0, 22, -12], just="center", parent=hub_name, shadow=True)
    if h_sub:
        hs_bn = _has_bangla(h_sub)
        hs_font = "HindSiliguri-SemiBold" if hs_bn else "InstrumentSerif-Italic"
        hs_size = _fit_size(h_sub, 70, 680, is_bn=hs_bn)
        ops += _create_3d_text(comp, f"{hub_name}_SUB", h_sub, hs_font, hs_size, SLATE if hs_bn else GOLD, t0, t1, [0, 145, -10], just="center", parent=hub_name)

    t_out0 = max(round(t0 + 0.25, 2), round(t1 - 0.16, 2))
    ops += _k(comp, hub_name, ["Transform", "Scale"], [t0, round(t0 + 0.22, 2), round(t0 + 0.34, 2)], [[65, 65, 100], [106, 106, 100], [100, 100, 100]], ease=[2, 3])
    ops += _k(comp, hub_name, ["Transform", "Opacity"], [t0, round(t0 + 0.10, 2), t_out0, round(t1, 2)], [0, 100, 100, 0])

    waypoints = [{"t": ht0, "pos": [cx, cy, -80], "orbit": [16, 0, 0]}]
    accents = [(t0, h_col, [cx, cy, -440])]

    # 3. Build Radiating Satellites
    for idx, sat in enumerate(satellites):
        nt = round(sat["t"], 2)
        if nt <= waypoints[-1]["t"]:
            nt = round(waypoints[-1]["t"] + 0.14, 2)
        sx, sy, sz = sat_coords[idx]
        yaw = -13 if sx < cx else (13 if sx > cx else 0)
        pitch = 18 if sy <= cy else 14
        roll = -2.5 if sx < cx else (2.5 if sx > cx else 0)
        waypoints.append({"t": nt, "pos": [sx, sy + 100, sz], "orbit": [pitch, yaw, roll]})
        accents.append((max(t0, nt - 0.1), sat.get("color", CYAN), [sx, sy + 40, -420]))

        sat_name = f"{tag}_SAT_{idx+1}"
        ops += _build_terminal_card(comp, sat_name, idx, sat, t0, t1, sx, sy, sz, img_w=980, img_h=600, lit=lit)
        t_pre = max(round(t0 + 0.04, 2), round(nt - 0.12, 2))
        t_s1 = max(round(t_pre + 0.04, 2), round(nt + 0.14, 2))
        t_s2 = max(round(t_s1 + 0.04, 2), round(nt + 0.26, 2))
        ops += _k(comp, sat_name, ["Transform", "Scale"], [t0, t_pre, t_s1, t_s2],
                  [[84, 84, 100], [84, 84, 100], [105, 105, 100], [100, 100, 100]], ease=[3, 4])
        ops += _k(comp, sat_name, ["Transform", "Opacity"], [t0, t_pre, round(t_pre + 0.10, 2), t_out0, round(t1, 2)],
                  [32, 32, 100, 100, 0])
        r.sfx("mouse-click-104737.mp3", nt, "extra", -5, 0.28)

    if overview_end and t1 - waypoints[-1]["t"] >= 0.85:
        t_wide = round(max(waypoints[-1]["t"] + 0.50, t1 - 0.85), 2)
        waypoints.append({"t": t_wide, "pos": [cx, cy + 160, -3100], "orbit": [15, 0, 0]})
        r.sfx("whoosh-vortex-243128.mp3", round(t_wide - 0.12, 2), "bed", -14, 0.65)

    ops += camera_rig_3d(comp, t0, t1, waypoints, tag=f"{tag}_CAM", drift=True)
    if lit:
        ops += plane_lighting(comp, t0, t1, waypoints, tag=f"{tag}_LGT", accents=accents)
    return ops


# ===========================================================================
# VARIATION 4: 3D ANGLED V-STAGE DUAL MONOLITH SHOWDOWN (`versus_split_3d`)
# ===========================================================================
def versus_split_3d(r, comp, t0, t1, left_side, right_side, verdict=None, tag="VS3D", opaque_bg=True, lit=True):
    """VARIATION 4 — Opposing 3D Angled V-Stage Monoliths!
    Two tall architectural 3D monolith cards face inward (`+18°` vs `-18°` Y-yaw) across a glowing center divide,
    with an optional `verdict` center bridge (`1 : 2 RR` or `YOUR CALL`). Camera whips Left -> Right -> Wide Center!"""
    cx, cy = 1980, 1920
    lx, rx = 860, 3100
    ops = infinite_grid_plane(comp, t0, t1, tag=f"{tag}_BG", center=(cx, cy, 460), opaque_bg=opaque_bg, lit=lit)

    mw, mh = 1080, 1380

    def _monolith(name, side, x_pos, yaw_deg, t_hit):
        col = side.get("color", CRIMSON)
        m_ops = [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": name}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": name, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": name, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Transform", "Position"], "value": [x_pos, cy, 0]}},
            {"operation": "property.set", "args": {"comp": comp, "layer": name, "property": ["Transform", "Y Rotation"], "value": yaw_deg}},
        ]
        v_groups = _vector_illustration_groups(side.get("icon", "chart_up"), col, oy=-150.0)
        gi = 0
        for vg in v_groups:
            gi += 1
            m_ops.append({"operation": "shape.add_group", "args": {"comp": comp, "layer": name, "name": vg.get("name", f"vg{gi}")}})
            if "rect" in vg:
                m_ops.append({"operation": "shape.add_rect", "args": {"comp": comp, "layer": name, "groupIndex": gi,
                                                                       "size": vg["rect"], "position": vg.get("at", [0, 0]), "roundness": vg.get("round", 0)}})
            if "ellipse" in vg:
                m_ops.append({"operation": "shape.add_ellipse", "args": {"comp": comp, "layer": name, "groupIndex": gi,
                                                                          "size": vg["ellipse"], "position": vg.get("at", [0, 0])}})
            if "path" in vg:
                m_ops.append({"operation": "shape.add_path", "args": {"comp": comp, "layer": name, "groupIndex": gi,
                                                                       "vertices": vg["path"], "closed": vg.get("closed", False)}})
            if "stroke" in vg:
                m_ops.append({"operation": "shape.add_stroke", "args": {"comp": comp, "layer": name, "groupIndex": gi,
                                                                         "color": vg["stroke"] + [1], "width": vg.get("width", 12)}})
            if "fill" in vg:
                m_ops.append({"operation": "shape.add_fill", "args": {"comp": comp, "layer": name, "groupIndex": gi,
                                                                       "color": vg["fill"] + [1], "opacity": 100}})
        # Accent top bar + main monolith slab
        gi += 1
        m_ops += [
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": name, "name": "top_bar"}},
            {"operation": "shape.add_rect", "args": {"comp": comp, "layer": name, "groupIndex": gi, "size": [mw - 120, 14], "position": [0, -mh / 2 + 54], "roundness": 7}},
            {"operation": "shape.add_fill", "args": {"comp": comp, "layer": name, "groupIndex": gi, "color": col + [1], "opacity": 100}},
        ]
        gi += 1
        m_ops += [
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": name, "name": "slab"}},
            {"operation": "shape.add_rect", "args": {"comp": comp, "layer": name, "groupIndex": gi, "size": [mw, mh], "roundness": 52}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": name, "groupIndex": gi, "color": col + [1], "width": 9}},
            {"operation": "shape.add_fill", "args": {"comp": comp, "layer": name, "groupIndex": gi, "color": CARD_DARK + [1], "opacity": 96}},
            {"operation": "effect.add", "args": {"comp": comp, "layer": name, "matchName": "ADBE Drop Shadow"}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Distance"], "value": 45}},
            {"operation": "effect.set_property", "args": {"comp": comp, "layer": name, "effectIndex": 1, "property": ["Softness"], "value": 110}},
        ]
        if lit:
            m_ops += _material(comp, name, casts=1, specular=48, shininess=24)

        bdg = side.get("badge", "OPTION")
        stat = side.get("stat", "")
        ttl = side.get("title", "")
        sub = side.get("sub", "")

        m_ops += _create_3d_text(comp, f"{name}_BDG", f"[ {bdg} ]", "CascadiaMonoRoman-Bold", 44, col, t0, t1, [0, -mh / 2 + 135, -8], just="center", parent=name, tracking=25)
        if stat:
            st_sz = _fit_size(stat, 170, mw - 140)
            m_ops += _create_3d_text(comp, f"{name}_STAT", stat, "CascadiaMonoRoman-Bold", st_sz, col, t0, t1, [0, 210, -10], just="center", parent=name, shadow=True)
        t_bn = _has_bangla(ttl)
        tf = "HindSiliguri-Bold" if t_bn else "PlusJakartaSans-ExtraBold"
        tsz = _fit_size(ttl, 108, mw - 110, is_bn=t_bn)
        m_ops += _create_3d_text(comp, f"{name}_TTL", ttl, tf, tsz, WHITE, t0, t1, [0, 390, -10], just="center", parent=name, shadow=True)
        if sub:
            s_bn = _has_bangla(sub)
            sf = "HindSiliguri-SemiBold" if s_bn else "InstrumentSerif-Italic"
            ssz = _fit_size(sub, 74, mw - 100, is_bn=s_bn)
            m_ops += _create_3d_text(comp, f"{name}_SUB", sub, sf, ssz, SLATE if s_bn else GOLD, t0, t1, [0, 520, -8], just="center", parent=name)

        t_out0 = max(round(t0 + 0.20, 2), round(t1 - 0.16, 2))
        t_pre = max(round(t0 + 0.04, 2), round(t_hit - 0.10, 2))
        m_ops += _k(comp, name, ["Transform", "Scale"], [t0, t_pre, round(t_hit + 0.16, 2), round(t_hit + 0.28, 2)],
                    [[84, 84, 100], [84, 84, 100], [105, 105, 100], [100, 100, 100]], ease=[3, 4])
        m_ops += _k(comp, name, ["Transform", "Opacity"], [t0, round(t0 + 0.10, 2), t_out0, round(t1, 2)], [0, 100, 100, 0])
        return m_ops

    tl = round(left_side.get("t", t0), 2)
    tr = round(max(tl + 0.25, right_side.get("t", t0 + (t1 - t0) * 0.45)), 2)

    ops += _monolith(f"{tag}_LEFT", left_side, lx, 16, tl)
    ops += _monolith(f"{tag}_RIGHT", right_side, rx, -16, tr)

    waypoints = [
        {"t": tl, "pos": [lx + 80, cy, -120], "orbit": [10, -12, -2]},
        {"t": tr, "pos": [rx - 80, cy, -120], "orbit": [10, 12, 2]},
    ]
    accents = [
        (max(t0, tl - 0.08), left_side.get("color", CRIMSON), [lx, cy, -480]),
        (max(t0, tr - 0.08), right_side.get("color", EMERALD), [rx, cy, -480]),
    ]
    r.sfx("mouse-click-104737.mp3", tl, "extra", -5, 0.28)
    r.sfx("fast-woosh-230497.mp3", round(max(t0, tr - 0.16), 2), "bed", -12, 0.55)
    r.sfx("mouse-click-104737.mp3", tr, "extra", -5, 0.28)

    # Center Verdict / Bridge Pill (`VS` or `1 : 2 RR`) + wide reveal framing BOTH monoliths!
    tv = round((verdict or {}).get("t", max(tr + 0.45, t1 - 1.1)), 2)
    if tv < t1 - 0.22:
        tv_in = max(t0, round(tv - 0.04, 2))
        t_out0 = max(round(tv + 0.16, 2), round(t1 - 0.14, 2))
        v_col = (verdict or {}).get("color", GOLD)
        v_title = (verdict or {}).get("title", "VS")
        v_sub = (verdict or {}).get("sub", "")
        v_name = f"{tag}_BRIDGE"
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": v_name}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": v_name, "inPoint": tv_in, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": v_name, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": v_name, "property": ["Transform", "Position"], "value": [cx, cy, -220]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": v_name, "name": "pill"}},
            {"operation": "shape.add_rect", "args": {"comp": comp, "layer": v_name, "groupIndex": 1, "size": [860, 320], "roundness": 64}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": v_name, "groupIndex": 1, "color": v_col + [1], "width": 9}},
            {"operation": "shape.add_fill", "args": {"comp": comp, "layer": v_name, "groupIndex": 1, "color": OBS + [1], "opacity": 98}},
        ]
        vt_sz = _fit_size(v_title, 124, 760, is_bn=_has_bangla(v_title))
        vt_f = "HindSiliguri-Bold" if _has_bangla(v_title) else "CascadiaMonoRoman-Bold"
        ops += _create_3d_text(comp, f"{v_name}_TTL", v_title, vt_f, vt_sz, v_col, tv_in, t1, [0, 12 if not v_sub else -18, -10], just="center", parent=v_name, shadow=True)
        ops += _k(comp, f"{v_name}_TTL", ["Transform", "Opacity"], [tv_in, round(tv + 0.10, 2), t_out0, round(t1, 2)], [0, 100, 100, 0])
        if v_sub:
            vs_bn = _has_bangla(v_sub)
            vs_f = "HindSiliguri-SemiBold" if vs_bn else "PlusJakartaSans-Bold"
            vs_sz = _fit_size(v_sub, 62, 760, is_bn=vs_bn)
            ops += _create_3d_text(comp, f"{v_name}_SUB", v_sub, vs_f, vs_sz, WHITE, tv_in, t1, [0, 92, -8], just="center", parent=v_name)
            ops += _k(comp, f"{v_name}_SUB", ["Transform", "Opacity"], [tv_in, round(tv + 0.10, 2), t_out0, round(t1, 2)], [0, 100, 100, 0])

        ops += _k(comp, v_name, ["Transform", "Scale"], [tv_in, round(tv + 0.18, 2), round(tv + 0.30, 2)],
                  [[40, 40, 100], [108, 108, 100], [100, 100, 100]], ease=[2, 3])
        ops += _k(comp, v_name, ["Transform", "Opacity"], [tv_in, round(tv + 0.10, 2), t_out0, round(t1, 2)],
                  [0, 100, 100, 0])

        waypoints.append({"t": tv, "pos": [cx, cy + 40, -1850], "orbit": [12, 0, 0]})
        accents.append((tv, v_col, [cx, cy, -650]))
        r.sfx("whoosh-vortex-243128.mp3", round(max(t0, tv - 0.12), 2), "bed", -14, 0.65)

    ops += camera_rig_3d(comp, t0, t1, waypoints, tag=f"{tag}_CAM", drift=True)
    if lit:
        ops += plane_lighting(comp, t0, t1, waypoints, tag=f"{tag}_LGT", accents=accents)
    return ops


# ===========================================================================
# VARIATION 5: 90°-PIVOT ARCHITECTURAL KINETIC WALL (`kinetic_wall_3d`)
# ===========================================================================
def kinetic_wall_3d(r, comp, t0, t1, beats, tag="KWALL3D", opaque_bg=True, lit=True):
    """VARIATION 5 — Pure Box-Free 3D Architectural Typography with 90° Camera Z-Pivot Turns!
    Instead of dark rectangular cards, giant bold typography + glowing neon accent rules + Bangla subtitles
    sit directly on a lit 3D grid floor at alternating `0°` and `+90°` orientations.
    As each statement lands, the 3D Camera physically whips & banks `Z Rotation` (`0° -> -90° -> 0°`) to lock it upright!"""
    # Wide non-overlapping spatial waypoints (even under -90 deg 3840px camera Z-bank!)
    slot_defs = [
        ([1080, 1650, 0], 0, [14, -10, 0]),
        ([4500, 2250, -60], 90, [10, 12, 0]),
        ([4500, 5650, 0], 0, [15, -8, 0]),
        ([7900, 6250, -60], 90, [12, 10, 0]),
    ]
    coords = [b.get("pos", slot_defs[i % len(slot_defs)][0]) for i, b in enumerate(beats)]
    cx = sum(c[0] for c in coords) / max(1, len(coords))
    cy = sum(c[1] for c in coords) / max(1, len(coords))

    ops = infinite_grid_plane(comp, t0, t1, tag=f"{tag}_BG", center=(round(cx), round(cy), 380), opaque_bg=opaque_bg, lit=lit)
    # Enlarge grid + void when 3+ beats span 5650+ px so edges never show during 90-deg camera whips
    ops += [
        {"operation": "property.set", "args": {"comp": comp, "layer": f"{tag}_BG_GRID", "property": ["Transform", "Scale"], "value": [165, 165, 100]}},
    ]
    waypoints = []
    accents = []

    # Sleek glowing guide rail connecting pivots on the 3D floor
    for idx in range(1, len(beats)):
        p0, p1 = coords[idx - 1], coords[idx]
        nt = round(beats[idx]["t"], 2)
        t_draw0 = round(max(t0, nt - 0.35), 2)
        t_draw1 = round(max(t_draw0 + 0.32, nt), 2)
        col = beats[idx].get("color", CYAN)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        rail = f"{tag}_RAIL_{idx}"
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": rail}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": rail, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": rail, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": rail, "property": ["Transform", "Position"], "value": [p0[0], p0[1], 32]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": rail, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": rail, "groupIndex": 1, "vertices": [[0, 0], [dx, 0], [dx, dy]], "closed": False}},
            {"operation": "shape.add_rounded_corners", "args": {"comp": comp, "layer": rail, "groupIndex": 1, "radius": 80}},
            {"operation": "shape.add_trim_paths", "args": {"comp": comp, "layer": rail, "groupIndex": 1, "start": 0, "end": 0}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": rail, "groupIndex": 1, "color": col + [1], "width": 10}},
        ]
        ops += _k(comp, rail, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [t_draw0, t_draw1], [0, 100], ease=[2])

    for idx, bt in enumerate(beats):
        nt = round(bt["t"], 2)
        if waypoints and nt <= waypoints[-1]["t"]:
            nt = round(waypoints[-1]["t"] + 0.14, 2)
        wx, wy, wz = coords[idx]
        _, text_rot, cam_orb = slot_defs[idx % len(slot_defs)]
        col = bt.get("color", EMERALD)

        waypoints.append({"t": nt, "pos": [wx, wy, wz - 60], "orbit": bt.get("orbit", cam_orb)})
        accents.append((max(t0, nt - 0.08), col, [wx, wy, wz - 460]))

        grp_null = f"{tag}_PIVOT_{idx+1}"
        ops += [
            {"operation": "layer.create_null", "args": {"comp": comp, "name": grp_null}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": grp_null, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": grp_null, "props": {"threeDLayer": True}}},
            {"operation": "property.set", "args": {"comp": comp, "layer": grp_null, "property": ["Transform", "Position"], "value": [wx, wy, wz]}},
            {"operation": "property.set", "args": {"comp": comp, "layer": grp_null, "property": ["Transform", "Z Rotation"], "value": text_rot}},
        ]

        badge = bt.get("badge", f"0{idx+1}")
        title = bt.get("title", "")
        sub = bt.get("sub", "")
        stat = bt.get("stat", "")

        # Glowing Trim-Paths architectural accent bar between giant title and Bangla subtitle
        rule = f"{tag}_RULE_{idx+1}"
        ops += [
            {"operation": "layer.create_shape", "args": {"comp": comp, "name": rule}},
            {"operation": "layer.set_timing", "args": {"comp": comp, "layer": rule, "inPoint": t0, "outPoint": t1}},
            {"operation": "layer.set_props", "args": {"comp": comp, "layer": rule, "props": {"threeDLayer": True, "motionBlur": True}}},
            {"operation": "layer.set_parent", "args": {"comp": comp, "layer": rule, "parentLayer": grp_null, "jump": True}},
            {"operation": "property.set", "args": {"comp": comp, "layer": rule, "property": ["Transform", "Position"], "value": [0, 75, -6]}},
            {"operation": "shape.add_group", "args": {"comp": comp, "layer": rule, "name": "g1"}},
            {"operation": "shape.add_path", "args": {"comp": comp, "layer": rule, "groupIndex": 1, "vertices": [[-480, 0], [480, 0]], "closed": False}},
            {"operation": "shape.add_trim_paths", "args": {"comp": comp, "layer": rule, "groupIndex": 1, "start": 0, "end": 0}},
            {"operation": "shape.add_stroke", "args": {"comp": comp, "layer": rule, "groupIndex": 1, "color": col + [1], "width": 14}},
        ]
        ops += _k(comp, rule, ["Contents", "g1", "Contents", "Trim Paths 1", "End"], [max(t0, round(nt - 0.08, 2)), round(nt + 0.24, 2)], [0, 100], ease=[2])

        top_tag = f"[ {badge} // {stat} ]" if stat else f"[ {badge} ]"
        ops += _create_3d_text(comp, f"{tag}_TAG_{idx+1}", top_tag, "CascadiaMonoRoman-Bold", 40, col, t0, t1, [0, -225, -12], just="center", parent=grp_null, tracking=15)

        t_bn = _has_bangla(title)
        tf = "HindSiliguri-Bold" if t_bn else "Syne-ExtraBold"
        # Syne-ExtraBold char_factor ~0.96; fit into 1120px local width so even under 1.18x punch zoom, text width <= 1530px on 2160w comp (>=315px safe margins)
        tsz = _fit_size(title, 140 if not t_bn else 125, 1120, is_bn=t_bn, char_factor=0.65 if t_bn else 0.96)
        ops += _create_3d_text(comp, f"{tag}_TTL_{idx+1}", title, tf, tsz, WHITE, t0, t1, [0, -20, -18], just="center", parent=grp_null, shadow=True)

        if sub:
            s_bn = _has_bangla(sub)
            sf = "HindSiliguri-Bold" if s_bn else "InstrumentSerif-Italic"
            ssz = _fit_size(sub, 80 if s_bn else 88, 1100, is_bn=s_bn, char_factor=0.65 if s_bn else 0.85)
            ops += _create_3d_text(comp, f"{tag}_SUB_{idx+1}", sub, sf, ssz, col if s_bn else GOLD, t0, t1, [0, 210, -10], just="center", parent=grp_null, shadow=True)

        t_out0 = max(round(t0 + 0.20, 2), round(t1 - 0.16, 2))
        t_pre = max(round(t0 + 0.02, 2), round(nt - 0.10, 2))
        ops += _k(comp, grp_null, ["Transform", "Scale"], [t0, t_pre, round(nt + 0.16, 2), round(nt + 0.28, 2)],
                  [[72, 72, 100], [72, 72, 100], [106, 106, 100], [100, 100, 100]], ease=[3, 4])
        if idx > 0:
            r.sfx("fast-woosh-230497.mp3", round(max(t0, nt - 0.16), 2), "bed", -12, 0.55)
        r.sfx("Short but Boomy.wav" if idx == 0 else "mouse-click-104737.mp3", nt, "extra", -7 if idx == 0 else -5, 0.35)

    ops += camera_rig_3d(comp, t0, t1, waypoints, tag=f"{tag}_CAM", drift=True)
    if lit:
        ops += plane_lighting(comp, t0, t1, waypoints, tag=f"{tag}_LGT", accents=accents)
    return ops


def spatial_text_plane(r, comp, t0, t1, clusters, tag="SP3D", with_grid=True):
    """Lay out multiple 3D kinetic word clusters across a 3D plane and glide/pivot the 3D Camera across them."""
    ops = []
    if with_grid:
        ops += infinite_grid_plane(comp, t0, t1, tag=f"{tag}_BG", opaque_bg=False)
    waypoints = []
    for ci, cl in enumerate(clusters, 1):
        wx, wy, wz = cl.get("pos", [1080 + (ci - 1) * 1350, 1920 - (ci % 2) * 520, (ci % 2) * -220])
        rx, ry, rz = cl.get("orbit", [8 if ci % 2 else -6, -12 if ci % 2 else 10, 0])
        waypoints.append({"t": cl["t"], "pos": [wx, wy, wz], "orbit": [rx, ry, rz]})
        if ci > 1:
            r.sfx("whoosh-motion-243505.mp3", max(0.0, cl["t"] - 0.14), "bed", -13, 0.55)
        for wi, w in enumerate(cl.get("words", []), 1):
            wt, txt, font, size, col, dx, dy, dz = w
            lname = f"{tag}_C{ci}_W{wi}"
            tx, ty, tz = wx + dx, wy + dy, wz + dz
            ops += _create_3d_text(comp, lname, txt, font, size, col, max(t0, wt - 0.08), t1, [tx, ty, tz], just="center", shadow=True)
            ops.append({"operation": "property.set", "args": {"comp": comp, "layer": lname, "property": ["Transform", "Z Rotation"], "value": -rz}})
            ops += _k(comp, lname, ["Transform", "Position"], [wt, round(wt + 0.22, 2)], [[tx, ty + 80, tz + 320], [tx, ty, tz]], ease=[2])
            ops += _k(comp, lname, ["Transform", "Scale"], [wt, round(wt + 0.18, 2), round(wt + 0.30, 2)],
                      [[55, 55, 55], [108, 108, 108], [100, 100, 100]], ease=[2, 3])
            ops += _k(comp, lname, ["Transform", "Opacity"], [wt, round(wt + 0.12, 2), round(t1 - 0.16, 2), t1], [0, 100, 100, 0])
    ops += camera_rig_3d(comp, t0, t1, waypoints, tag=f"{tag}_CAM", drift=True)
    return ops


def flowchart_plane_3d(r, comp, t0, t1, nodes, tag="FLOW3D", opaque_bg=True):
    """Alias to `canvas_board_plane_3d` for backward compatibility."""
    return canvas_board_plane_3d(r, comp, t0, t1, nodes, tag=tag, opaque_bg=opaque_bg, overview_end=False)
