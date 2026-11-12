"""Catch HALF-SAID false starts that Whisper swallows ("টেলিগ্রাম চ-" ... pause ... "আমার টেলিগ্রাম চ্যানেলের লিংক").

The phrase pass hears the clean restart and stretches one word over the stumble, so retake detection never sees it.
Here every phrase is split into voice bursts (25 ms RMS, gaps >= 0.12 s). A short burst (<= 1.0 s) followed by a
restart is re-transcribed on its own; when most of its letters re-appear at the start of what follows, it is a false
start and its span goes into the phrase's "fs" list. reelkit cuts every "fs" span out of the A-roll.

    python false_starts.py E:/Anan/NEW/edit/r1_ph.json [--force]

Writes "fs": [[a, b], ...] (source seconds) and "fs_checked": true into each phrase, and prints what it found.
Plans can keep a flagged span with Reel(..., keep_fs={i}).
"""
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import wave
from difflib import SequenceMatcher

PUNCT = "।,?!.;:-–—'\"… "


def _norm(s):
    return "".join(ch for ch in s if ch not in PUNCT)


def bursts(wav, t0, t1, floor_db=-36.0, win=0.025, min_gap=0.12):
    w = wave.open(wav)
    sr, ch = w.getframerate(), w.getnchannels()
    t0 = max(0.0, t0)
    w.setpos(int(t0 * sr))
    n = int((t1 - t0) * sr)
    raw = w.readframes(n)  # the last phrase + 0.1 s can run past the end of the WAV (11-11-2026)
    n = len(raw) // (2 * ch)
    d = struct.unpack("<" + "h" * (n * ch), raw[:n * 2 * ch])
    step = int(win * sr)
    on = []
    for k in range(0, n - step, step):
        seg = d[k * ch:(k + step) * ch]
        rms = math.sqrt(sum(x * x for x in seg) / len(seg)) or 1
        on.append(20 * math.log10(rms / 32768) > floor_db)
    out, cur, gap = [], None, 0
    for k, v in enumerate(on):
        t = t0 + k * win
        if v:
            if cur is None:
                cur = [t, t + win]
            elif gap * win >= min_gap:
                out.append(cur)
                cur = [t, t + win]
            else:
                cur[1] = t + win
            gap = 0
        else:
            gap += 1
    if cur:
        out.append(cur)
    return [b for b in out if b[1] - b[0] >= 0.08]


def coverage(frag, nxt):
    """share of frag's letters that re-appear, in order, near the start of nxt"""
    if not frag or not nxt:
        return 0.0
    m = SequenceMatcher(None, frag, nxt[:len(frag) + 8])
    return sum(b.size for b in m.get_matching_blocks()) / len(frag)


def main(path, force=False):
    from faster_whisper import WhisperModel
    data = json.load(open(path, encoding="utf-8"))
    wav = data["source"]
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    except Exception:
        model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=max(4, os.cpu_count() or 8))

    def hear(a, b):
        with tempfile.TemporaryDirectory() as td:
            f = os.path.join(td, "c.wav")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", wav, "-ar", "16000", "-ac", "1", f],
                           check=True)
            segs, _ = model.transcribe(f, language="bn", beam_size=5, vad_filter=False, condition_on_previous_text=False)
            return _norm(" ".join(s.text for s in segs))

    found = 0
    for p in data["phrases"]:
        if p.get("fs_checked") and not force:
            found += len(p.get("fs", []))
            continue
        fs = []
        bs = bursts(wav, p["s"] - 0.05, p["e"] + 0.1)
        starts = [w[0] if isinstance(w, list) else w["s"] for w in p["w"]]
        for b0, b1 in zip(bs, bs[1:]):
            if b0[1] - b0[0] > 1.0 or b1[0] - b0[1] > 1.2:
                continue
            # cheap filter: Whisper put no word boundary in this pause (one word stretched over burst + pause + restart)
            # -> that is where a swallowed stumble hides. Pauses with a word starting right after them are normal speech.
            if any(b0[1] - 0.05 <= t <= b1[0] + 0.12 for t in starts):
                continue
            frag = hear(b0[0] - 0.03, b0[1] + 0.03)
            nxt = hear(b1[0] - 0.03, min(b1[0] + 2.2, p["e"] + 0.1))
            if len(frag) < 3 or len(nxt) < len(frag):
                continue
            cov = coverage(frag, nxt)
            if cov >= 0.7:
                fs.append([round(b0[0] - 0.03, 2), round(b1[0] - 0.05, 2)])
                print(f"P{p['i']}: false start {b0[0]:.2f}-{b0[1]:.2f} '{frag}' -> restart {b1[0]:.2f} '{nxt[:24]}' (cov {cov:.2f})")
        p["fs"], p["fs_checked"] = fs, True
        found += len(fs)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{found} false start(s) in {os.path.basename(path)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main(sys.argv[1], "--force" in sys.argv)
