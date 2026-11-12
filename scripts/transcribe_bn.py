"""Word timings for Anan's Bangla (+English) talking head, to time keyword text and cuts.

  python transcribe_bn.py C0812.MP4 out.json [--model large-v3] [--offset SECONDS]

Writes {"segments": [{s, e, t, w: [[start, end, word, prob], ...]}]} and prints a readable list.

Bangla ASR is weak (the C0804 attempt garbled whole stretches and misheard English words written in
Bangla script: "রেট কেন্ডেল" = red candle). Treat the output as TIMING, not text:
- words with prob < 0.5 are flagged "?" - never put them on screen without the user confirming;
- English words come back in Bangla script - write them in English on screen ("Trading", "Skill");
- for the on-screen words, ask the user (or the script they recorded from) when anything is unclear.
Needs faster-whisper (installed in the user's Python; run without -I). large-v3 is much better for
Bangla than medium; first run downloads it.
"""
import json
import sys

from faster_whisper import WhisperModel


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows redirects stdout as cp1252, which can't hold Bangla
    src, out = sys.argv[1], sys.argv[2]
    model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "large-v3"
    off = float(sys.argv[sys.argv.index("--offset") + 1]) if "--offset" in sys.argv else 0.0
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segs, _ = model.transcribe(src, language="bn", word_timestamps=True, vad_filter=True,
                               initial_prompt="ট্রেডিং, স্কিল, মার্কেট, প্রফিট, candle, trading, skill, analysis")
    res = []
    for s in segs:
        w = [[round(x.start + off, 2), round(x.end + off, 2), x.word.strip(), round(x.probability, 2)] for x in s.words]
        res.append({"s": round(s.start + off, 2), "e": round(s.end + off, 2), "t": s.text.strip(), "w": w})
        print(f"{s.start + off:7.2f}-{s.end + off:7.2f}  " +
              " ".join(f"{x[2]}{'?' if x[3] < 0.5 else ''}" for x in w))
    json.dump({"source": src, "segments": res}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
