"""Pass-3 cut fixes (user, 8-11-2026): never clip his voice, give a little lead-in before each line, and remove dead pauses
INSIDE a line so the punchline hits. Works on the measured voice (RMS, 20 ms windows), not Whisper's word times.

  python tighten_cuts.py N [N ...]      rewrites rN_cuts.json (backup rN_cuts_pre_tighten.json) and prints every change
"""
import json, math, os, struct, sys, wave

STEP, VOICE, SILENT = 0.02, -36.0, -40.0
LEAD, TAIL, MAX_GAP = 0.10, 0.08, 0.16          # lead-in before the voice, tail after it, gap allowed inside a word
PAUSE, KEEP = 0.45, 0.12                        # a silence longer than PAUSE inside a piece is cut down to KEEP + KEEP


def track(wav):
    w = wave.open(wav); sr = w.getframerate(); n = w.getnframes()
    d = struct.unpack("<" + "h" * n, w.readframes(n)); s = int(STEP * sr); out = []
    for k in range(0, n - s, s):
        seg = d[k:k + s]; r = math.sqrt(sum(x * x for x in seg) / len(seg)) or 1; out.append(20 * math.log10(r / 32768))
    return out


def db(R, t):
    i = int(t / STEP)
    return R[i] if 0 <= i < len(R) else -90


def onset(R, t, limit):
    """walk back from t while the voice continues (gaps <= MAX_GAP); return where it starts"""
    x, last_voiced, gap = t, t, 0.0
    while x > limit:
        x -= STEP
        if db(R, x) > VOICE:
            last_voiced, gap = x, 0.0
        else:
            gap += STEP
            if gap > MAX_GAP:
                break
    return last_voiced


def offset(R, t, limit):
    x, last_voiced, gap = t, t, 0.0
    while x < limit:
        if db(R, x) > VOICE:
            last_voiced, gap = x + STEP, 0.0
        else:
            gap += STEP
            if gap > MAX_GAP:
                break
        x += STEP
    return last_voiced


def snap(t):
    return round(t * 25) / 25


def run(n):
    global SILENT
    if not os.path.exists(f"r{n}_cuts_pre_tighten.json"):
        json.dump(json.load(open(f"r{n}_cuts.json")), open(f"r{n}_cuts_pre_tighten.json", "w"), indent=0)
    cuts = json.load(open(f"r{n}_cuts_pre_tighten.json"))  # always start from the approved cut
    R = track(f"E:/Anan/NEW/wav/r{n}.wav")
    pstart = {p["i"]: p["s"] for p in json.load(open(f"r{n}_ph.json", encoding="utf-8"))["phrases"]}
    lv = sorted(db(R, c["src_in"] + j * STEP) for c in cuts for j in range(int((c["src_out"] - c["src_in"]) / STEP)))
    level = lv[int(len(lv) * 0.75)]
    SILENT = level - 12  # pause = 12 dB under his speech level (breath blips at -33 broke a fixed -40)
    print(f"reel {n}: speech level {level:.0f} dB, pause below {SILENT:.0f} dB")
    seen = set()
    out, notes = [], []
    for k, c in enumerate(cuts):
        a, b = c["src_in"], c["src_out"]
        prev_end = out[-1]["src_out"] if out else 0.0
        nxt = cuts[k + 1]["src_in"] if k + 1 < len(cuts) else 1e9
        # head: if the voice is already running at the cut, walk back to its real start (max 0.8 s)
        first_voice = next((a + j * STEP for j in range(0, 25) if db(R, a + j * STEP) > VOICE), a)
        on = onset(R, first_voice, max(prev_end, a - 0.8))
        na = max(prev_end, snap(min(a, on - LEAD)))
        if c["i"] in seen or a > pstart.get(c["i"], a) + 0.15:
            na = a  # piece starts INSIDE a line on purpose (retake / false start trimmed): never walk back into it
        seen.add(c["i"])
        # tail: if a word is still sounding at the cut, run on to its end (max 0.5 s)
        off = offset(R, b - STEP, min(nxt if nxt > b else 1e9, b + 0.5))
        nb = snap(max(b, off + TAIL)) if off > b - STEP else b
        if nxt > b:
            nb = min(nb, nxt) if nxt - b < 0.02 else nb
        if abs(na - a) > 0.03:
            notes.append(f"P{c['i']} head {a:.2f} -> {na:.2f}")
        if abs(nb - b) > 0.03:
            notes.append(f"P{c['i']} tail {b:.2f} -> {nb:.2f}")
        # dead pauses inside the piece
        segs, s0, t, run_start = [], na, na + KEEP, None
        while t < nb - KEEP:
            if db(R, t) < SILENT:
                run_start = t if run_start is None else run_start
            else:
                if run_start is not None and t - run_start >= PAUSE:
                    segs.append([s0, snap(run_start + KEEP)]); s0 = snap(t - KEEP)
                    notes.append(f"P{c['i']} pause {run_start:.2f}-{t:.2f} cut")
                run_start = None
            t += STEP
        segs.append([s0, nb])
        for x, y in segs:
            if y - x >= 0.2:
                out.append({"i": c["i"], "src_in": snap(x), "src_out": snap(y)})
    t = 0.0
    for c in out:
        c["tl"] = round(t, 2); t += c["src_out"] - c["src_in"]
    json.dump(out, open(f"r{n}_cuts.json", "w"), indent=0)
    old = sum(c["src_out"] - c["src_in"] for c in cuts)
    print(f"reel {n}: {len(cuts)} -> {len(out)} pieces, {old:.2f}s -> {t:.2f}s")
    for x in notes:
        print("   ", x)


for n in sys.argv[1:]:
    run(int(n))
