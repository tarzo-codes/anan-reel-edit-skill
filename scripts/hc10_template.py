"""10-11-2026 batch helpers on top of hc.HC (user notes 10-11-2026):
- animated emojis (Noto, ProRes 4444) BIG and BEHIND him (card + his cut-out on top), never small static PNGs
- Bangla-only captions (no English duplicate), few words, lower lane
- impact = stock clip / desaturation (sad beats) / full-screen tick or cross
- TikTok "Reply to @user's comment" popup, black word-by-word hook (reel 4), a second music bed (sad -> normal)"""
import json, os
from hc import HC, CS
from aecards import _shape, _text, _k, _glow

EMO = "PNG/emoji_anim/"          # relative to reelkit's A (E:/Anan/Assets/)
LOW2 = 2900                      # caption lane for the sofa framing (face 1700-2500)


class HC10(HC):
    def __init__(self, n, music, head_y=0.40, cap_y=2900, **kw):
        super().__init__(n, music, **kw)
        self.head_y = head_y      # emoji centre (fraction of 3840): its lower part tucks behind his head
        self.cap_y = cap_y
        self.desats, self.music2 = [], None
        self._t = 0
        w0 = self.r.write

        def _write():
            w0()
            p = f"r{n}_prem.json"
            d = json.load(open(p, encoding="utf-8"))
            d["desat"] = self.desats
            if self.music2:
                d["music2"] = self.music2
                d["music"]["until"] = self.music2["t0"]
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        self.r.write = _write

    def tag(self, s):
        self._t += 1
        return f"{s}{self._t}"

    # ---- captions: Bangla only (English words he SAYS stay Latin inside the line)
    def sub(self, items, end, y=None):
        out = []
        for k, it in enumerate(items):
            nxt = items[k + 1][0] if k + 1 < len(items) else end
            if nxt <= self.hook_end + 0.05:
                continue
            out.append((round(max(it[0], self.hook_end), 2),) + tuple(it[1:]))
        if out:
            self.r.chunks(out, y=y or self.cap_y, end=end, size=CS)

    # ---- animated emoji behind him
    def emoji(self, t0, t1, name, x=0.5, y=None, width=1250, behind=True, sfx="pop-39222.mp3"):
        y = self.head_y if y is None else y
        self.r.scene("cards", t0, t1, [self.r.card(EMO + name + ".mov", 512, 512, t0, y, x=x, width=width, bare=True)], no_base=True)
        if behind:
            self.r.cutout(t0, t1)
        if sfx:
            self.r.sfx(sfx, t0, "extra", -9, 0.4)

    def logo_behind(self, t0, t1, file, x=0.5, y=None, width=1150):
        y = self.head_y if y is None else y
        self.r.scene("cards", t0, t1, [self.r.card(file, None, None, t0, y, x=x, width=width, bare=True)], no_base=True)
        self.r.cutout(t0, t1)
        self.r.sfx("pop-39222.mp3", t0, "extra", -9, 0.4)

    # ---- his own iPhone clips: HLG HDR -> SDR Rec.709 25 fps (skill section 16), SDR ones used as they are
    def own(self, t0, t1, name, src_in=1, scale=100):
        import subprocess
        src = "E:/Anan/Telegram Desktop/" + name
        trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                              "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().strip(",")
        f = src
        if trc in ("arib-std-b67", "smpte2084"):
            os.makedirs("E:/Anan/Assets/own_sdr", exist_ok=True)
            f = f"E:/Anan/Assets/own_sdr/{os.path.splitext(name)[0]}_sdr.mp4"
            if not os.path.exists(f):
                vf = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
                      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,fps=25")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", "14", "-preset", "fast",
                                "-an", f], check=True)
                print(f"  own {name}: HLG -> SDR {f}")
        self.r.scene("full", t0, t1, [{"file": f, "scale": scale, "src_in": src_in}])

    # ---- sad colour
    def desat(self, t0, t1, sat=22):
        self.desats.append([round(t0, 2), round(t1, 2), sat])

    def second_music(self, t0, path, src_in=0, xfade=1.2):
        from mix_levels import solve
        mx = solve(self.r.src, self.r.cuts, path, src_in, self.r.total)
        self.music2 = {"path": path.replace("\\", "/"), "file": path.replace("\\", "/").split("/")[-1], "t0": round(t0, 2),
                       "src_in": src_in, "db": mx["music_db"], "xfade": xfade}
        print(f"  music2 {self.music2['file']} from {t0}: {mx['music_db']:+} dB")

    # ---- full-screen tick / cross (AE FRONT)
    def mark(self, t, kind="cross", dur=1.0):
        F, nm = self.F, self.tag("MARK")
        t1 = round(t + dur, 2)
        ops = _shape(F, nm + "_dim", t, t1, [1080, 1920], [{"rect": [2160, 3840], "fill": [0, 0, 0]}])
        ops += _k(F, nm + "_dim", ["Transform", "Opacity"], [t, round(t + 0.08, 2), round(t1 - 0.2, 2), t1], [0, 45, 45, 0])
        s = 1500
        if kind == "cross":
            col, w = [0.93, 0.13, 0.17], 170
            groups = [{"path": [[-s / 2, -s / 2], [s / 2, s / 2]], "trim": True, "stroke": col, "width": w, "name": "a"},
                      {"path": [[s / 2, -s / 2], [-s / 2, s / 2]], "trim": True, "stroke": col, "width": w, "name": "b"}]
        else:
            col, w = [0.16, 0.86, 0.42], 170
            groups = [{"path": [[-s / 2, 0], [-s / 6, s / 3], [s / 2, -s / 3]], "trim": True, "stroke": col, "width": w, "name": "a"}]
        ops += _shape(F, nm, t, t1, [1080, 1920], groups)
        ops += _k(F, nm, ["Contents", "a", "Contents", "Trim Paths 1", "End"], [t, round(t + 0.16, 2)], [0, 100], ease=[2])
        if kind == "cross":
            ops += _k(F, nm, ["Contents", "b", "Contents", "Trim Paths 1", "End"], [round(t + 0.12, 2), round(t + 0.28, 2)], [0, 100], ease=[2])
        ops += _k(F, nm, ["Transform", "Scale"], [t, round(t + 0.3, 2), round(t + 0.42, 2), round(t1 - 0.15, 2), t1],
                  [[118, 118], [96, 96], [100, 100], [100, 100], [80, 80]], ease=[2, 3])
        ops += _k(F, nm, ["Transform", "Opacity"], [t, round(t + 0.04, 2), round(t1 - 0.15, 2), t1], [0, 100, 100, 0])
        ops.append({"operation": "expression.set", "args": {"comp": F, "layer": nm, "property": ["Transform", "Position"],
                    "expression": f"var a=Math.max(0,1-(time-{round(t + 0.28, 2)})/0.3); (time>{round(t + 0.28, 2)})?value+[Math.sin(time*90)*28*a,Math.cos(time*70)*18*a]:value"}})
        self.r.ae(ops + _glow(F, nm, radius=60, intensity=1.2))
        if kind == "cross":
            self.r.sfx("Short but Boomy.wav", t, "feat", -5, 0.8)
            self.r.sfx("glitch.mp3", round(t + 0.12, 2), "bed", -14, 0.35)
        else:
            self.r.sfx("ding-101492.mp3", round(t + 0.1, 2), "feat", -8, 1.0)
            self.r.sfx("whoosh-motion-243505.mp3", round(t - 0.08, 2), "bed", -14, 0.5)

    # ---- TikTok "Reply to @user's comment" popup (AE FRONT)
    def reply_popup(self, t0, t1, user, lines, cy=1080, w=1840):
        F, tg = self.F, self.tag("RPL")
        lh = 128
        h = 210 + lh * len(lines) + 70
        top, x0 = cy - h / 2, 1080 - w / 2
        sheet = tg + "_sheet"
        ops = _shape(F, sheet, t0, t1, [1080, cy], [{"rect": [w, h], "round": 56, "fill": [1, 1, 1]}])
        ops += [{"operation": "effect.add", "args": {"comp": F, "layer": sheet, "matchName": "ADBE Drop Shadow"}},
                {"operation": "effect.set_property", "args": {"comp": F, "layer": sheet, "effectIndex": 1, "property": ["Opacity"], "value": 55}},
                {"operation": "effect.set_property", "args": {"comp": F, "layer": sheet, "effectIndex": 1, "property": ["Distance"], "value": 18}},
                {"operation": "effect.set_property", "args": {"comp": F, "layer": sheet, "effectIndex": 1, "property": ["Softness"], "value": 70}}]
        kids = []
        ay = top + 130
        ops += _shape(F, tg + "_ava", t0, t1, [x0 + 135, ay], [{"ellipse": [150, 150], "fill": [0.98, 0.17, 0.33]},
                                                               {"ellipse": [160, 160], "fill": [0.15, 0.85, 0.85]}]); kids.append(tg + "_ava")
        ops += _text(F, tg + "_ini", user[1].upper(), t0, t1, [x0 + 135, ay + 30], "PlusJakartaSans-ExtraBold", 84, [1, 1, 1], just="center"); kids.append(tg + "_ini")
        ops += _text(F, tg + "_rto", f"Reply to {user}'s comment", t0, t1, [x0 + 250, ay + 22], "PlusJakartaSans-ExtraBold", 64,
                     [0.42, 0.43, 0.47]); kids.append(tg + "_rto")
        for k, ln in enumerate(lines):
            nm = f"{tg}_l{k}"
            ops += _text(F, nm, ln, t0, t1, [x0 + 90, top + 290 + k * lh], "HindSiliguri-Bold", 96, [0.08, 0.08, 0.1]); kids.append(nm)
        for k_ in kids:
            ops.append({"operation": "layer.set_parent", "args": {"comp": F, "layer": k_, "parentLayer": sheet, "jump": False}})
        ops += _k(F, sheet, ["Transform", "Scale"], [t0, round(t0 + 0.22, 2), round(t0 + 0.36, 2), round(t1 - 0.2, 2), t1],
                  [[0, 0], [107, 107], [100, 100], [100, 100], [0, 0]], ease=[2, 3, 5])
        ops += _k(F, sheet, ["Transform", "Rotation"], [t0, round(t0 + 0.3, 2)], [-6, 0], ease=[2])
        self.r.ae(ops)
        self.r.sfx("pop-39222.mp3", t0, "feat", -6, 0.4)
        self.r.sfx("whoosh-motion-243505.mp3", round(t1 - 0.2, 2), "bed", -16, 0.5)

    # ---- reel 4: cut to black, words one at a time (Impact), all on one screen
    def black_words(self, t0, t1, words, fs=330, col=(1, 1, 1), accent=None):
        F = self.F
        ops = _shape(F, "BLK_bg", t0, t1, [1080, 1920], [{"rect": [2160, 3840], "fill": [0, 0, 0]}])
        n = len(words)
        gap = fs * 1.06
        y0 = 1920 - gap * (n - 1) / 2 + fs * 0.36
        for k, (t, wd) in enumerate(words):
            nm = f"BLK_w{k}"
            c = list(accent) if (accent and k == n - 1) else list(col)
            ops += _text(F, nm, wd, t, t1, [1080, round(y0 + k * gap)], "Impact", fs, c, just="center")
            ops += _k(F, nm, ["Transform", "Scale"], [t, round(t + 0.1, 2), round(t + 0.18, 2)], [[150, 150], [96, 96], [100, 100]], ease=[2])
            ops += _k(F, nm, ["Transform", "Opacity"], [t, round(t + 0.04, 2)], [0, 100])
            self.r.sfx("Short but Boomy.wav", t, "feat", -9, 0.6)
        self.r.ae(ops)
        self.r.sfx("tv-shut-down-185446.mp3", round(t0 - 0.02, 2), "extra", -12, 0.5)
        self.r.sfx("whoosh-vortex-243128.mp3", round(t1 - 0.3, 2), "bed", -14, 0.8)
        self.r.punch([[round(t1, 2), 120], [round(t1 + 0.3, 2), 100]])
