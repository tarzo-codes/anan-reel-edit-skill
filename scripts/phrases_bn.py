"""Phrase-by-phrase Bangla transcript: split the voice at pauses, transcribe each phrase on its own.

  python phrases_bn.py voice.wav out.json [--model large-v3] [--min-pause 0.3]

Why: on whole files faster-whisper (Bangla) drops long stretches and smears word timings (reel 1 of
2-11-2026: 0.8-12 s came back as four words). Short independent chunks fix both: every phrase gets a
transcript and exact start/end times from the pause map, which is what cuts and keyword timing need.
Output: {"phrases": [{"i", "s", "e", "t"}]} and a readable list on stdout.
"""
import json
import re
import subprocess
import sys

from faster_whisper import WhisperModel, decode_audio

SR = 16000


def pauses(path, min_pause):
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", f"silencedetect=noise=-35dB:d={min_pause}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src, out = sys.argv[1], sys.argv[2]
    model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "large-v3"
    mp = float(sys.argv[sys.argv.index("--min-pause") + 1]) if "--min-pause" in sys.argv else 0.3
    audio = decode_audio(src, sampling_rate=SR)
    dur = len(audio) / SR
    # speech spans = gaps between pauses
    spans, cur = [], 0.0
    for a, b in pauses(src, mp):
        if a - cur > 0.15:
            spans.append([cur, a])
        cur = b if b is not None else dur
    if dur - cur > 0.15:
        spans.append([cur, dur])
    # merge very short spans into neighbours, split long ones (>9 s) evenly
    merged = []
    for s in spans:
        if merged and (s[1] - s[0] < 1.0 or merged[-1][1] - merged[-1][0] < 1.0) and s[0] - merged[-1][1] < 0.6:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    chunks = []
    for a, b in merged:
        n = max(1, int((b - a) // 9) + (1 if (b - a) % 9 > 0.5 and b - a > 9 else 0))
        step = (b - a) / n
        chunks += [[a + k * step, a + (k + 1) * step] for k in range(n)]
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    res = []
    for i, (a, b) in enumerate(chunks):
        seg = audio[int(max(0, a - 0.1) * SR):int(min(dur, b + 0.1) * SR)]
        r, _ = model.transcribe(seg, language="bn", vad_filter=False, condition_on_previous_text=False, beam_size=5,
                                word_timestamps=True)
        r = list(r)
        t = " ".join(x.text.strip() for x in r)
        off = max(0, a - 0.1)  # word times -> source seconds; keyword text is timed from these
        words = [[round(w.start + off, 2), round(w.end + off, 2), w.word.strip()] for x in r for w in (x.words or [])]
        res.append({"i": i, "s": round(a, 2), "e": round(b, 2), "t": t, "w": words})
        print(f"{i:3d} {a:6.2f}-{b:6.2f}  " + " ".join(f"{k}:{w[2]}" for k, w in enumerate(words)), flush=True)
    json.dump({"source": src, "phrases": res}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
