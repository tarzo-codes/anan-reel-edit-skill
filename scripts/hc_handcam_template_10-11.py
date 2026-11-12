"""Shared HANDCAM helpers for the 10-11-2026 plans (8-11 pattern + vibes: Extreme / Casual / Normal / Sad, extreme hooks,
whole-track music balancing via music_curve)."""
import sys
sys.path.insert(0, "C:/Users/btaza/.claude/skills/anan-reel-edit/scripts")
from reelkit import Reel, A, STY, _measure  # noqa: E402
from aeui import step_badge, comment_ui  # noqa: E402
from ae3d import EMERALD, GOLD, CRIMSON  # noqa: E402

TOP, LOW, CS = 600, 2850, 230
POP_Y = 2600   # stacked lower third: pop on the beard line, sub under it at 2850 (below 2850 = IG/TikTok UI, reelkit clamps) (user 9-11: top = header only, everything else at the bottom)
EMO = "E:/Anan/Assets/PNG/emoji/"
LOGO = "E:/Anan/Assets/logos/"
STY["step_w"] = dict(STY["sans_w"], fontSize=260)
CASH_SFX = "modestas123123-cash-register-kaching-sound-effect-125042.mp3"


class HC:
    def __init__(self, n, music, db=-22, src_in="auto"):
        path = music if ":" in music else A + "Music/" + music
        self.r = r = Reel(n, f"E:/Anan/NEW/reel {n}.MP4", f"r{n}_10-11 reel {n}.MP4", date="10-11-2026", auto_retakes=False,
                          cuts_file=f"r{n}_cuts.json", handcam=True, music=path, music_db=db, music_src_in=src_in)
        self.W, self.E, self.S = r.W, r.E, r.S
        self.F = f"R{n}_FRONT"
        self.hook_end = 0.0
        self._pngs = []
        _w = r.write
        def _write():
            self._flush_pngs()
            _w()
        r.write = _write

    def cap(self, items, end):
        """captions; none while the hook is on screen (user, pass 3)"""
        out = []
        for k, it in enumerate(items):
            nxt = items[k + 1][0] if k + 1 < len(items) else end
            if nxt <= self.hook_end + 0.05:
                continue
            out.append((round(max(it[0], self.hook_end), 2),) + tuple(it[1:]))
        if out:
            self.r.chunks(out, y=LOW, end=end, size=CS)

    def top(self, t0, t1, txt, st="sans_w"):
        """top keyword: BIGGER and STACKED on two lines when it is more than one word (user, pass 3)"""
        if t1 <= self.hook_end:
            return
        t0 = max(t0, self.hook_end)
        if " / " in txt:  # amounts: "TK 70K / MONTH" -> "TK 70K" over "PER MONTH" (a lone "/" line read badly)
            txt = txt.replace(" / ", "\nPER ")
        words = txt.split()
        if len(words) >= 2 and len(txt) >= 9 and "\n" not in txt:
            best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
            txt = " ".join(words[:best]) + "\n" + " ".join(words[best:])
        self.r.text(t1, [(t0, txt, st, 1080, TOP)])

    def step(self, t0, t1, num, word, color=GOLD):
        """number in an animated circle + its word, the PAIR CENTRED on the frame (user, pass 3), with a clear gap"""
        ring, gap = round(270 * 1.24), 80
        fs = 250
        w = _measure(word, "sans_w", fs)
        if ring + gap + w > 1720:
            fs = int(fs * (1720 - ring - gap) / w); w = _measure(word, "sans_w", fs)
        STY.setdefault(f"step_w@{fs}", dict(STY["sans_w"], fontSize=fs))
        left = 1080 - (ring + gap + w) / 2
        self.r.ae(step_badge(self.r, self.F, t0, t1, num, round(left + ring / 2), round(TOP - 0.36 * fs), size=270, color=color))
        self.r.text(t1, [(round(t0 + 0.12, 2), word, f"step_w@{fs}", round(left + ring + gap + w / 2), TOP)])

    def full(self, t0, t1, file, src_in=1):
        self.r.scene("full", t0, t1, [self.r.full(file, None, None, src_in)])

    def card(self, t0, t1, file, src_in=1, **kw):
        self.r.scene("cards", t0, t1, [self.r.card(file, None, None, t0, 0.5, src_in=src_in, **kw)])

    def logo(self, t0, t1, file, width=900):
        self.r.scene("cards", t0, t1, [self.r.card(file, None, None, t0, 0.5, width=width, bare=True)])

    def burst(self, t0, t1):
        self.r.burst("179649-862590064_medium.mp4", t0, t1, src_in=0, front_src_in=4)
        self.r.sfx(CASH_SFX, t0, "extra", -8, 1.2)
        self.r.sfx("Short but Boomy.wav", t0, "feat", -6, 0.8)

    def cash(self, t0, t1, clip, src_in=1):
        """RULE (user, pass 3): an income / money line gets HIS OWN cash clip + the cash-register sound"""
        small = {"IMG_1365.MOV", "IMG_1540.MOV", "IMG_1548.MOV"}  # 1072x1920 clips: scale to fill 2160 wide
        self.own(t0, t1, clip, src_in, scale=201.5 if clip in small else 100)
        self.r.sfx(CASH_SFX, t0, "extra", -8, 1.2)

    def comment(self, t0, t1, type_start, type_end, send, platform, text="আমি trading শিখতে চাই"):
        self.r.ae(comment_ui(self.r, self.F, t0, t1, text, type_start, type_end, send, platform=platform))

    def punch(self, t, to=112):
        self.r.punch([[t, 100], [t + 0.3, to]])

    def whoosh(self, *ts):
        for t in ts:
            self.r.sfx("fast-woosh-230497.mp3", t - 0.1, "bed", -12, 0.8)

    def click(self, *ts):
        for t in ts:
            if t >= self.hook_end:
                self.r.sfx("mouse-click-104737.mp3", t, "extra", -6, 0.4)

    def open(self):
        self.r.punch([[0, 118], [0.24, 100]])
        self.r.sfx("whoosh-vortex-243128.mp3", 0.0, "bed", -14, 1.5)
        self.r.sfx("Short but Boomy.wav", 0.0, "feat", -6, 0.8)

    def own(self, t0, t1, name, src_in=1, scale=100):
        """his own Telegram/iPhone clip (4K portrait after rotation): travel, lifestyle, and his cash (income lines)"""
        self.r.scene("full", t0, t1, [{"file": "E:/Anan/Telegram Desktop/" + name, "scale": scale, "src_in": src_in}])

    def hook(self, t0, t1, kicker, hero, sub=None, color=None):
        """eye-catching animated hook, CENTRED, no captions under it (user, pass 3). Call before any cap()/top()."""
        from aeui import hook_title
        self.hook_end = t1
        self.r.ae(hook_title(self.r, self.F, t0, t1, kicker, hero, sub=sub, color=color))
        self.r.punch([[round(t0 + 0.75, 2), 100], [round(t0 + 0.95, 2), 108], [round(t1, 2), 112]])

    # ---- 10-11-2026 vibe helpers
    def xhook(self, t0, t1, kicker, hero, sub=None, color=None, flashes=()):
        """EXTREME hook: hook v2 + riser into a sub-boom + glitch, a harder camera slam, and 0.4-0.6 s stock flashes
        right after the hero lands (flashes = [(t, t_end, file), ...] full-screen cutaways inside the hook)."""
        self.hook(t0, t1, kicker, hero, sub, color)
        self.r.punches = [p for p in self.r.punches if p["keys"][0][0] < t0 + 0.7]  # replace hook()'s gentle push
        self.r.punch([[round(t0 + 0.75, 2), 100], [round(t0 + 0.9, 2), 116], [round(t0 + 1.3, 2), 108], [round(t1, 2), 118]])
        self.r.sfx("Sharp Reverse.wav", max(0.0, t0 + 0.35), "extra", -10, 0.6)
        self.r.sfx("Short but Boomy.wav", round(t0 + 0.9, 2), "pop", -4, 0.8)
        self.r.sfx("glitch.mp3", round(t0 + 0.88, 2), "bed", -14, 0.4)
        for a, b, f in flashes:
            self.full(a, b, f)
            self.r.sfx("fast-woosh-230497.mp3", a - 0.08, "bed", -12, 0.6)

    def megahook(self, t0, t1, kicker, hero, sub=None, color=None, burst=None, cash=None, after=(), calm=False, center=1920):
        """HOOK v3 (user, 10-11-2026: "the hooks are weak - it says টাকা income করার ইচ্ছা, where is the taka? show
        some money, go crazy on the hooks"). Hero = the word he SAYS (Bangla if he says it in Bangla), BIG; on the slam
        frame: burst="money" (money rain behind his cut-out + big bills in front + cash register) or "fire" (flames
        behind him); then his own cash clip (cash=) and any extra flashes (after=[(t0, t1, file|(raw, src_in))]); riser
        -> boom + glitch, hard camera slam and shake. calm=True (sad reels): same big title, no burst, gentle camera."""
        from aeui import hook_title, hook_slam
        self.hook_end = t1
        self.r.ae(hook_title(self.r, self.F, t0, t1, kicker, hero, sub=sub, color=color, big=True, center=center))
        slam = hook_slam(t0, hero)
        if calm:
            self.r.punch([[round(slam, 2), 100], [round(t1, 2), 108]])
        else:
            self.r.punch([[round(slam - 0.04, 2), 100], [round(slam + 0.1, 2), 124], [round(slam + 0.4, 2), 112], [round(t1, 2), 118]])
            self.r.sfx("Sharp Reverse.wav", max(0.0, round(slam - 0.45, 2)), "extra", -9, 0.5)
            self.r.sfx("glitch.mp3", round(slam - 0.04, 2), "bed", -12, 0.4)
        b1 = round(min(t1 - 0.05, slam + 1.5), 2)
        if burst == "money":
            self.r.burst("179649-862590064_medium.mp4", slam, b1, src_in=0, front_src_in=4)
            self.r.sfx(CASH_SFX, slam, "pop", -5, 1.2)
        elif burst == "fire":
            self.r.burst("pexels_9667144_fire_flames_black_backgr.mp4", slam, b1, src_in=1)
            self.r.sfx("fire-sound-222359.mp3", slam, "pop", -8, 1.5)
        t = b1 if burst else round(slam + 0.4, 2)
        if cash and t + 0.3 < t1:
            c1 = round(min(t1 - 0.05, t + 0.6), 2)
            self.cash(t, c1, cash)
            t = c1
        for a, b, f in after:
            if isinstance(f, tuple):
                self.r.scene("full", a, b, [{"file": f[0], "scale": 100, "src_in": f[1]}])
            else:
                self.full(a, b, f)
            self.r.sfx("fast-woosh-230497.mp3", a - 0.08, "bed", -12, 0.6)
        return slam

    # ---- v2 (10-11-2026 data audit: his winners = fixed header + simple look, 30-40 s)
    def header(self, l1, l2=None, c1=None, c2=None, bar=(0.0, 0.0, 0.0), calm=False):
        """FIXED TOP HEADER for the whole reel (his 157K / 127K TikToks: "ট্রেডিং শিখুন ১ মিনিটে" red on a black bar,
        "২ হাজার -> 30-40 হাজার" green). Black bar y 230-760 (under the platform top UI), line 1 + optional line 2, both
        Bangla-aware; slams in on frame 1 (scale 135 -> 100 + white flash) and stays to the end."""
        from aecards import _shape, _text, _k
        from aeui import _is_bn
        from reelkit import _measure
        W = [0.97, 0.98, 0.99]
        c1, c2 = c1 or W, c2 or EMERALD
        T, F = self.r.total, self.F
        # bar y 190-650; line 2 is the big punchline (his winners: one short huge line); pops go below at y 880
        ops = _shape(F, "HDR_bar", 0, T, [1080, 440], [{"rect": [2160, 500], "fill": list(bar)}])
        ops += _k(F, "HDR_bar", ["Transform", "Opacity"], [0, 0.08], [0, 90])
        lines = [(l1, c1, 185 if l2 else 280, 390 if l2 else 520)] + ([(l2, c2, 240, 645)] if l2 else [])
        for k, (txt, col, fs, y) in enumerate(lines):
            st = "bn_w" if _is_bn(txt) else "sans_w"
            w = _measure(txt, st, fs)
            if w > 1960:
                fs = int(fs * 1960 / w)
            nm = f"HDR_{k + 1}"
            ops += _text(F, nm, txt, 0, T, [1080, y], "HindSiliguri-Bold" if _is_bn(txt) else "PlusJakartaSans-ExtraBold", fs, col, just="center")
            t0 = 0.04 + 0.12 * k
            ops += _k(F, nm, ["Transform", "Scale"], [t0, round(t0 + 0.16, 2), round(t0 + 0.26, 2)], [[135, 135], [96, 96], [100, 100]], ease=[2])
            ops += _k(F, nm, ["Transform", "Opacity"], [t0, round(t0 + 0.05, 2)], [0, 100])
            ops += [{"operation": "effect.add", "args": {"comp": F, "layer": nm, "matchName": "ADBE Drop Shadow"}},
                    {"operation": "effect.set_property", "args": {"comp": F, "layer": nm, "effectIndex": 1, "property": ["Softness"], "value": 30}}]
        ops += _shape(F, "HDR_flash", 0.04, 0.4, [1080, 1920], [{"rect": [2160, 3840], "fill": [1, 1, 1]}])
        ops += _k(F, "HDR_flash", ["Transform", "Opacity"], [0.04, 0.08, 0.4], [0, 35, 0])
        self.r.ae(ops)
        if calm:
            self.r.punch([[0, 106], [0.8, 100]])
            self.r.sfx("Very Subtle.wav", 0.04, "extra", -10, 0.6)
        else:
            self.r.punch([[0, 116], [0.3, 100]])
            self.r.sfx("Short but Boomy.wav", 0.04, "feat", -5, 0.8)
            self.r.sfx("whoosh-vortex-243128.mp3", 0.0, "bed", -14, 1.2)
        self.hook_end = 0.0

    def num(self, t0, t1, txt, st="mono_g"):
        """big number / keyword pop UNDER the header (his '২ হাজার' -> '30-40 হাজার' pops). y 880: above reelkit's
        behind-head lane (900-1700 is dropped without a cut-out) and clear of the header bar (ends at 650)."""
        fs = 190
        w = _measure(txt, st, fs)
        if w > 1300:   # reelkit stacks anything its own (wider) metric puts over 1780 px - keep pops one line
            fs = int(fs * 1300 / w)
        key = f"{st}@{fs}"
        STY.setdefault(key, dict(STY[st], fontSize=fs))
        self.r.text(t1, [(t0, txt, key, 1080, POP_Y)])
        self.r.sfx("mouse-click-104737.mp3", t0, "extra", -7, 0.4)

    def png(self, t0, t1, name, side="r", size=440, y=0.255, sfx=True):
        """PNG / emoji pop beside his head (his 1.1M Telegram-logo video): name = emoji in Assets/PNG/emoji ('fire'),
        'telegram' for the logo, or a full path. side r/l/c. Overlay track V10 (eased pop + tilt in build_reel).
        Placed at write(): trimmed / dropped where it would sit over a full-screen cutaway or a burst."""
        f = name if (":" in name) else (LOGO + "telegram_1600.png" if name == "telegram" else EMO + name + ".png")
        self._pngs.append((round(t0, 2), round(t1, 2), f, side, size, y, sfx))

    def _flush_pngs(self):
        from PIL import Image
        busy = [(sc["t0"], sc["t1"]) for sc in self.r.scenes if sc.get("type") == "full"]
        busy += [(o["t0"], o["t1"]) for o in self.r.overlays if o.get("plain")]
        for t0, t1, f, side, size, y, sfx in self._pngs:
            for b0, b1 in sorted(busy):
                if b0 <= t0 < b1:
                    t0 = b1
                elif t0 < b0 < t1:
                    t1 = b0
            if t1 - t0 < 0.6:
                print(f"  png {f.split('/')[-1]} @{t0} dropped (under a cutaway)")
                continue
            w = Image.open(f).size[0]
            self.r.overlays.append({"file": f, "t0": round(t0, 2), "t1": round(t1, 2), "x": {"r": 0.85, "l": 0.15, "c": 0.5}[side],
                                    "y": y, "scale": round(size / w * 100, 1)})
            if sfx:
                self.r.sfx("mouse-click-104737.mp3", t0, "extra", -9, 0.4)

    def burst_at(self, t, kind="money", ln=1.4, cash=None):
        """the money / fire burst on the first money word (user: 'show the taka'), optional own cash clip after it"""
        if kind == "money":
            self.r.burst("179649-862590064_medium.mp4", t, round(t + ln, 2), src_in=0, front_src_in=4)
            self.r.sfx(CASH_SFX, t, "pop", -5, 1.2)
        else:
            self.r.burst("pexels_9667144_fire_flames_black_backgr.mp4", t, round(t + ln, 2), src_in=1)
            self.r.sfx("fire-sound-222359.mp3", t, "pop", -8, 1.5)
        self.r.sfx("Short but Boomy.wav", t, "feat", -5, 0.8)
        self.r.punch([[round(t - 0.02, 2), 100], [round(t + 0.12, 2), 118], [round(t + ln, 2), 110]])
        if cash:
            self.cash(round(t + ln, 2), round(t + ln + 0.7, 2), cash)

    def slow_push(self, t0, t1, to=108):
        """sad / reflective beats: a slow creep in, no snap"""
        self.r.punch([[t0, 100], [t1, to]])

    def sfx(self, f, t, db=-10, ln=1.0, role="extra"):
        self.r.sfx(f, t, role, db, ln)

    def boom(self, *ts):
        for t in ts:
            self.r.sfx("Short but Boomy.wav", t, "feat", -6, 0.8)
