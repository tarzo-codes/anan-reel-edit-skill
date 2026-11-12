"""music_curve.py - read the WHOLE music track and even out its ramps (user, 9-11-2026: "check the whole music audio,
music usually has ramp ups and downs - balance those so it is never too low or too loud").

mix_levels.py sets ONE gain for the bed (integrated loudness 10 LU under the voice). A track that builds from a quiet
intro to a loud drop still swings 6-12 LU inside the reel. This module:
  1. measures momentary loudness (EBU R128 M, 400 ms) every 0.1 s over the whole file, smoothed over 2 s (centred);
  2. pick_start(): chooses where the bed starts - the window of the reel's length whose level is steadiest and closest
     to the track's own typical (median) level, skipping silent intros and the outro;
  3. curve(): gain offsets (dB, relative to the bed gain) every 0.5 s over the used span so the bed sits at its
     integrated level: deviations inside +-DEAD LU are left alone (keeps the music breathing), beyond that they are
     pulled back, clamped to +-MAX_DB, and keys that change < 0.4 dB are dropped.

  python music_curve.py <music.mp3> <reel seconds> [src_in]    -> prints the pick, the level graph and the keys
reelkit applies it at write() (Reel.music["curve"], music_src_in="auto"); build_reel.jsx keys Level = db + offset.
"""
import math
import re
import subprocess
import sys

STEP, SMOOTH, DEAD, MAX_DB, KEY_EVERY = 0.1, 2.0, 1.5, 9.0, 0.5
_CACHE = {}


def loudness(path):
    """[(t, M_lufs)] every 0.1 s over the whole file (ffmpeg ebur128 verbose frame log)"""
    if path in _CACHE:
        return _CACHE[path]
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                        "aresample=48000,asetnsamples=4800,ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=-",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    pts = [(float(t), float(m)) for t, m in re.findall(r"pts_time:([\d.]+)\s*\n\s*lavfi\.r128\.M=(-?[\d.]+|-inf|nan)", p.stdout)
           if m not in ("-inf", "nan")]
    if not pts:
        raise RuntimeError("no loudness frames: " + p.stderr[-400:])
    # centred power-domain moving average over SMOOTH s (M already integrates the last 0.4 s -> shift by 0.2 s)
    n = int(SMOOTH / STEP / 2)
    pw = [10 ** (max(m, -70) / 10) for _, m in pts]
    out = []
    for k, (t, _) in enumerate(pts):
        seg = pw[max(0, k - n):k + n + 1]
        out.append((round(t - 0.2, 2), 10 * math.log10(sum(seg) / len(seg))))
    _CACHE[path] = out
    return out


def _window(L, t0, t1):
    return [m for t, m in L if t0 <= t <= t1]


def pick_start(path, total, lead_skip=2.0):
    """start of the steadiest window of length `total` at the track's typical level (1 s grid)"""
    L = loudness(path)
    dur = L[-1][0]
    loud = sorted(m for _, m in L if m > -45)
    med = loud[len(loud) // 2]
    best, best_t = None, 0.0
    t = lead_skip
    while t + total <= dur - 3.0:
        w = _window(L, t, t + total)
        if w:
            dev = sum(abs(m - med) for m in w) / len(w)
            low = sum(1 for m in w if m < med - 8) / len(w)        # stretches where the bed would vanish
            head = sum(abs(m - med) for m in _window(L, t, t + 2.5)) / max(1, len(_window(L, t, t + 2.5)))
            score = dev + 20 * low + 0.5 * head                    # the hook (first 2.5 s) must have the bed going
            if best is None or score < best:
                best, best_t = score, t
        t += 1.0
    if best is None:          # track shorter than the reel: start at 0
        best_t = 0.0
    return round(best_t, 1), med


def curve(path, src_in, total):
    """[[timeline_t, offset_db], ...] relative to the bed gain; empty if the span is already even"""
    L = loudness(path)
    span = [(t - src_in, m) for t, m in L if src_in <= t <= src_in + total]
    if not span:
        return []
    ref = 10 * math.log10(sum(10 ** (m / 10) for _, m in span) / len(span))   # ~ integrated level of the span
    keys, last, t = [], None, 0.0
    while t <= total + 1e-6:
        w = [m for tt, m in span if abs(tt - t) <= KEY_EVERY / 2 + 1e-6]
        if w:
            m = 10 * math.log10(sum(10 ** (x / 10) for x in w) / len(w))
            dev = m - ref
            off = 0.0 if abs(dev) <= DEAD else -(dev - math.copysign(DEAD, dev))
            if m < -45:            # a real silence / break in the track: don't pump noise up
                off = 0.0
            off = round(max(-MAX_DB, min(MAX_DB, off)), 1)
            if last is None or abs(off - last) >= 0.4:
                keys.append([round(t, 2), off]); last = off
        t += KEY_EVERY
    if all(abs(k[1]) < 0.05 for k in keys):
        return []
    return keys


def report(path, total, src_in=None):
    if src_in is None:
        src_in, med = pick_start(path, total)
    else:
        med = None
    L = loudness(path)
    print(f"{path.split('/')[-1]}: {L[-1][0]:.0f} s, typical {med if med is None else round(med, 1)} LUFS, start {src_in} s")
    for t in range(0, int(L[-1][0]), 5):
        w = _window(L, t, t + 5)
        if w:
            m = sum(w) / len(w)
            mark = "<" if src_in <= t < src_in + total else " "
            print(f"  {t:4d}s {m:6.1f} {mark} " + "#" * max(0, int(m + 40)))
    ks = curve(path, src_in, total)
    print("  keys:", ks)
    return src_in, ks


if __name__ == "__main__":
    report(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else None)
