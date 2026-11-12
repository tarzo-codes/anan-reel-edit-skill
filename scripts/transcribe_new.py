"""
Turnkey Transcription + Separate SRT + Claude Viral Analysis Pipeline for E:\\Anan\\NEW.

Why this exists:
- Whole-file Whisper on Anan's Banglish Sony 4K clips drops 5-15s stretches of speech
  and smears word timestamps.
- This script splits each video's audio on natural pauses (>=0.30s at -35dB) via ffmpeg,
  sub-splits any long chunk (>9s) into ~6s windows, and runs faster-whisper large-v3
  independently on every chunk with word timestamps.
- Audio pass first (10-11-2026): the WAV Whisper hears is cleaned (80 Hz high-pass, adaptive FFT
  denoise) and set to -20 LUFS, so the -35 dB pause threshold means the same thing on every raw
  (his raws ran -18 to -25 LUFS). Premiere keeps the original audio; only the analysis copy changes.
- Dropped-word re-hear (10-11-2026): Whisper sometimes skips a whole sentence inside a chunk and
  stretches the word before it over the gap (reel 1: 'বের' 82.77-87.93 hid "আমার টিম মেম্বার ... বিশ
  হাজার টাকা"). Any word > 1.2 s or word gap > 0.8 s with speech-level audio is transcribed again on
  its own and the new words are spliced in.

Outputs generated per video in E:\\Anan\\NEW:
  1. E:\\Anan\\NEW\\srt\\<video_stem>.srt          -> Clean phrase-level .srt (Premiere & human review)
  2. E:\\Anan\\NEW\\srt\\<video_stem>_claude.srt   -> Word-indexed .srt for Claude (shows phrase_i + word_idx + gaps + triggers)
  3. E:\\Anan\\NEW\\edit\\r<N>_ph.json             -> Exact reelkit.py phrase/word JSON
  4. E:\\Anan\\NEW\\edit\\r<N>_ph.txt              -> Compact phrase dump
  5. E:\\Anan\\NEW\\CLAUDE_VIRAL_ANALYSIS.md       -> Consolidated viral hook/cut/motion-design brief for Claude

Usage:
  python transcribe_new.py                       # processes all videos in E:\\Anan\\NEW
  python transcribe_new.py --dir "E:\\Anan\\NEW"   # custom folder
  python transcribe_new.py --force               # re-transcribe even if outputs exist
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_NEW_DIR = r"E:\Anan\NEW"
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v"}
IGNORE_DIRS = {"srt", "edit", "wav", "renders", "cutouts", "remotion", "__pycache__"}

def is_hallucinated_repetition(text: str, words: list[dict], chunk_dur: float) -> bool:
    """Detect Whisper breath/noise hallucinations where a single word/phrase loops."""
    clean = text.strip()
    if not clean:
        return True
    tokens = [re.sub(r"[^\w\u0980-\u09FF]", "", t) for t in clean.split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return True
    # Single very short noise blip (<0.42s) with multiple tokens is always a breath/click hallucination
    if chunk_dur < 0.42 and len(tokens) >= 3:
        return True
    # Speech-rate sanity check: human speech never exceeds ~5.5 Bangla words/sec on short chunks or 7.0 words/sec overall
    wps = len(tokens) / max(chunk_dur, 0.1)
    if (chunk_dur < 2.0 and len(tokens) >= 6 and wps > 5.2) or (len(tokens) >= 8 and wps > 7.0):
        return True
    # 3+ identical consecutive tokens (e.g., "ক্যান্ডেলস্টিক ক্যান্ডেলস্টিক ক্যান্ডেলস্টিক")
    consec = 1
    for k in range(1, len(tokens)):
        if tokens[k] == tokens[k - 1]:
            consec += 1
            if consec >= 3:
                return True
        else:
            consec = 1
    # Or >60% of a >=4 token phrase is the exact same word
    if len(tokens) >= 4:
        most_common = max( tokens.count(t) for t in set(tokens) )
        if most_common / len(tokens) >= 0.60:
            return True
    return False


def dedupe_repeated_clauses(text: str) -> str:
    """Clean any trailing 2-3 word stutter loop at the end of a chunk."""
    tokens = text.split()
    out = []
    for tok in tokens:
        if len(out) >= 2 and out[-1] == tok and out[-2] == tok:
            continue
        out.append(tok)
    return " ".join(out)


# Keyword trigger detectors for automatic Claude Motion-Design & Edit recommendations
MONEY_WORDS = ["ডলার", "টাকা", "হাজার", "লাখ", "কোটি", "প্রফিট", "লাভ", "ইনকাম", "আয়", "ক্যাপিটাল", "ব্যালেন্স", "পোর্টফোলিও", "$", "৳", "%"]
SHOCK_LOSS_WORDS = ["লস", "ভুল", "ধ্বংস", "ফকির", "রিস্ক", "স্ক্যাম", "ফেইক", "বিপদ", "কখনোই", "না", "বন্ধ", "চোক", "ফাঁদ", "হারাম"]
CHART_SKILL_WORDS = ["ক্যান্ডেল", "চার্ট", "মার্কেট", "ট্রেডিং", "ট্রেডার", "বাই", "সেল", "স্ট্র্যাটেজি", "অ্যানালাইসিস", "স্কিল", "টাইমফ্রেম", "ট্রেন্ড"]
NUMBER_WORDS_BN = ["এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়", "দশ", "বিশ", "ত্রিশ", "পঞ্চাশ", "শত", "হাজার", "লাখ", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯", "০"]


def format_srt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis -= 1000
    if secs >= 60:
        minutes += 1
        secs -= 60
    if minutes >= 60:
        hours += 1
        minutes -= 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def fast_file_signature(path: str) -> str:
    size = os.path.getsize(path)
    h = hashlib.sha256()
    h.update(str(size).encode())
    with open(path, "rb") as f:
        h.update(f.read(65536))
        if size > 65536:
            f.seek(max(0, size - 65536))
            h.update(f.read(65536))
    return f"{size}:{h.hexdigest()[:16]}"


def probe_video_info(video_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,stream_tags=rotate:stream_side_data=rotation:format=duration",
        "-of", "json",
        video_path,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    info = {"width": 2160, "height": 3840, "fps": 25.0, "duration": 0.0}
    try:
        data = json.loads(p.stdout)
        if data.get("streams"):
            st = data["streams"][0]
            w = int(st.get("width", 2160))
            h = int(st.get("height", 3840))
            rot = 0
            if st.get("tags") and st["tags"].get("rotate"):
                rot = abs(int(float(st["tags"]["rotate"])))
            for sd in st.get("side_data_list", []):
                if "rotation" in sd:
                    rot = abs(int(float(sd["rotation"])))
            # Sony 4K vertical cameras store 2160x3840 as 3840x2160 with rotation flag or vertical portrait
            if rot in (90, 270) or (w == 3840 and h == 2160):
                info["width"], info["height"] = min(w, h), max(w, h)
            else:
                info["width"], info["height"] = w, h
            r_fps = st.get("r_frame_rate", "25/1")
            if "/" in r_fps:
                n, d = r_fps.split("/", 1)
                info["fps"] = round(float(n) / max(float(d), 1.0), 2)
            else:
                info["fps"] = float(r_fps)
        if data.get("format") and data["format"].get("duration"):
            info["duration"] = round(float(data["format"]["duration"]), 3)
    except Exception:
        pass
    return info


CLEAN_AF = "highpass=f=80,afftdn=nr=10:nf=-50:tn=1"
TARGET_LUFS = -20.0


def measure_lufs(path: str, af: str = "") -> float | None:
    chain = (af + "," if af else "") + "ebur128"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-ac", "1", "-af", chain, "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    vals = re.findall(r"^\s+I:\s+(-?[0-9.]+) LUFS", p.stderr, re.M)
    return float(vals[-1]) if vals else None


def extract_wav(video_path: str, wav_path: str, force: bool = False, clean: bool = True):
    """16 kHz mono analysis WAV. clean=True: high-pass + denoise + gain to TARGET_LUFS (sidecar <wav>.clean marks it)."""
    marker = wav_path + ".clean"
    if os.path.exists(wav_path) and os.path.getsize(wav_path) > 1024 and not force and (os.path.exists(marker) or not clean):
        with open(wav_path, "rb") as fh:  # a run killed mid-write leaves a zero-filled WAV (8-11-2026 reel 5: 0 speech chunks)
            if fh.read(4) == b"RIFF":
                return
        print(f"  [wav] {wav_path} is damaged - re-extracting", flush=True)
    os.makedirs(os.path.dirname(wav_path), exist_ok=True)
    af = CLEAN_AF
    if clean:
        lufs = measure_lufs(video_path, CLEAN_AF)
        gain = max(-12.0, min(15.0, TARGET_LUFS - lufs)) if lufs is not None else 0.0
        af += f",volume={gain:.1f}dB,alimiter=limit=0.95:level=false"
        print(f"  [wav] audio pass: {lufs} LUFS -> gain {gain:+.1f} dB, high-pass 80 Hz, FFT denoise", flush=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", video_path, "-vn", "-ac", "1"]
    if clean:
        cmd += ["-af", af]
    cmd += ["-ar", "16000", wav_path]
    subprocess.run(cmd, check=True)
    if clean:
        open(marker, "w").write(af)
    elif os.path.exists(marker):
        os.remove(marker)


def span_rms_db(wav_path: str, a: float, b: float) -> float:
    """Mean RMS (dBFS) of a span of a 16-bit mono WAV."""
    import wave, struct, math
    with wave.open(wav_path) as w:
        sr = w.getframerate()
        w.setpos(max(0, int(a * sr)))
        n = max(1, int((b - a) * sr))
        raw = w.readframes(n)
    cnt = len(raw) // 2
    if not cnt:
        return -120.0
    vals = struct.unpack(f"<{cnt}h", raw[: cnt * 2])
    ms = sum(v * v for v in vals) / cnt
    return 10 * math.log10(ms / 32768.0 ** 2) if ms > 0 else -120.0


def detect_speech_spans(wav_path: str, noise_db: int = -35, min_pause: float = 0.3) -> list[tuple[float, float]]:
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", wav_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_pause}",
        "-f", "null", "-",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    s_starts, s_ends = [], []
    dur = None
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m:
            s_starts.append(float(m.group(1)))
        m = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m:
            s_ends.append(float(m.group(1)))
        m = re.search(r"Duration:\s*(\d+):(\d+):([0-9.]+)", line)
        if m:
            dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

    silences = []
    for i, st in enumerate(s_starts):
        en = s_ends[i] if i < len(s_ends) else (dur or st)
        silences.append((st, en))

    speech = []
    cur = 0.0
    for st, en in silences:
        if st - cur > 0.15:
            speech.append((max(0.0, cur - 0.08), st + 0.08))
        cur = en
    if dur and dur - cur > 0.2:
        speech.append((max(0.0, cur - 0.08), dur))

    out = []
    for s, e in speech:
        d = e - s
        if d <= 9.0:
            out.append((s, e))
        else:
            # split at the quietest 60 ms near each ~6 s mark (10-11-2026): fixed windows cut mid-word, the two
            # halves overlapped by 0.1 s and Whisper hallucinated at the edge ("আপনাদের আপনাদের আপন")
            n = int(d // 6.0) + 1
            step = d / n
            cuts = [s]
            for k in range(1, n):
                tgt = s + k * step
                lo, hi = max(cuts[-1] + 2.0, tgt - 1.5), min(e - 2.0, tgt + 1.5)
                best, best_db = tgt, 1e9
                t = lo
                while t <= hi:
                    db = span_rms_db(wav_path, t, t + 0.06)
                    if db < best_db:
                        best, best_db = t + 0.03, db
                    t += 0.03
                cuts.append(best)
            cuts.append(e)
            for a, b in zip(cuts, cuts[1:]):
                out.append((a, b))
    return out


def cut_wav_chunk(src_wav: str, s: float, e: float, dst_wav: str):
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{s:.3f}", "-to", f"{e:.3f}",
            "-i", src_wav, "-ar", "16000", "-ac", "1", dst_wav,
        ],
        check=True,
    )


def analyze_phrase_triggers(phrase: dict, prev_end: float, idx: int, total_phrases: int) -> list[str]:
    text = phrase["t"]
    dur = phrase["e"] - phrase["s"]
    gap = max(0.0, phrase["s"] - prev_end)
    tags = []

    if idx == 0 and (dur < 1.1 or len(phrase.get("w", [])) <= 2):
        tags.append("POSSIBLE_SLATE_OR_FALSE_START")
    if idx == total_phrases - 1 and (dur < 1.0 or len(phrase.get("w", [])) <= 2):
        tags.append("POSSIBLE_TAIL_OUTTAKE")
    if gap >= 1.25 and idx > 0:
        tags.append(f"LONG_PAUSE_BEFORE({gap:.2f}s->CHECK_RETAKE)")
    if idx <= 2 and dur >= 1.1:
        tags.append("HOOK_ZONE(3D_BehindText+GlassUI_Cards+MatchZoom)")

    if any(k in text for k in MONEY_WORDS) or re.search(r"\d{2,}", text):
        tags.append("MONEY/PNL(mono_emerald+GlassPnL_Card+TickerCounter)")
    if any(k in text for k in SHOCK_LOSS_WORDS):
        tags.append("SHOCK/LIQUIDATION(gotham_crimson+JitterGlow+AudioStopDrop+SubBoom)")
    if any(k in text for k in CHART_SKILL_WORDS):
        tags.append("TERMINAL/CHART(3D_TiltCard_Bokeh+LiquiditySweep_or_RR_Vector)")
    if any(k in text for k in NUMBER_WORDS_BN) or re.search(r"\d", text):
        tags.append("DATA_METRIC(mono_pill_badge+SpeedGraph_Counter)")

    return tags


def write_clean_srt(phrases: list[dict], srt_path: str):
    lines = []
    for seq_num, p in enumerate(phrases, start=1):
        start_tc = format_srt_time(p["s"])
        end_tc = format_srt_time(p["e"])
        lines.append(f"{seq_num}")
        lines.append(f"{start_tc} --> {end_tc}")
        lines.append(p["t"])
        lines.append("")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_claude_word_srt(phrases: list[dict], claude_srt_path: str, reel_id: str, video_name: str):
    lines = []
    prev_end = 0.0
    total = len(phrases)
    for seq_num, p in enumerate(phrases, start=1):
        i = p["i"]
        start_tc = format_srt_time(p["s"])
        end_tc = format_srt_time(p["e"])
        dur = p["e"] - p["s"]
        gap = max(0.0, p["s"] - prev_end)
        triggers = analyze_phrase_triggers(p, prev_end, i, total)
        prev_end = p["e"]

        trig_str = f" | {', '.join(triggers)}" if triggers else ""
        word_tokens = " ".join(
            f"[{wi}:{w[2]}@{w[0]:.2f}-{w[1]:.2f}]" if isinstance(w, list) else f"[{wi}:{w['w']}@{w['s']:.2f}-{w['e']:.2f}]"
            for wi, w in enumerate(p.get("w", []))
        )

        lines.append(f"{seq_num}")
        lines.append(f"{start_tc} --> {end_tc}")
        lines.append(f"[P#{i:02d} | {p['s']:.2f}s-{p['e']:.2f}s ({dur:.2f}s) | gap={gap:.2f}s{trig_str}]")
        lines.append(p["t"])
        if word_tokens:
            lines.append(f"WORDS: {word_tokens}")
        lines.append("")
    with open(claude_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_phrase_txt(phrases: list[dict], txt_path: str, video_path: str):
    lines = [f"# Source: {video_path}", f"# Total Phrases: {len(phrases)}", ""]
    prev_end = 0.0
    for p in phrases:
        dur = p["e"] - p["s"]
        gap = max(0.0, p["s"] - prev_end)
        prev_end = p["e"]
        w_str = " ".join(
            f"{wi}:{w[2]}({w[0]:.2f})" if isinstance(w, list) else f"{wi}:{w['w']}({w['s']:.2f})"
            for wi, w in enumerate(p.get("w", []))
        )
        lines.append(f"[{p['i']:02d}] {p['s']:6.2f}-{p['e']:6.2f} ({dur:4.2f}s, gap={gap:4.2f}s): {p['t']}")
        if w_str:
            lines.append(f"     words: {w_str}")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def infer_reel_id(video_name: str, fallback_idx: int) -> tuple[str, int]:
    stem = Path(video_name).stem
    # Match "reel 1 (2)" -> 1, "reel 4" -> 4, "r5" -> 5
    m = re.search(r"(?:reel|r)\s*[_-]?\s*(\d+)", stem, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        return f"r{num}", num
    m2 = re.search(r"(\d+)", stem)
    if m2:
        num = int(m2.group(1))
        return f"r{num}", num
    return f"r{fallback_idx}", fallback_idx


def generate_claude_master_brief(results: list[dict], out_md_path: str):
    lines = [
        "# CLAUDE WEB-VIRAL TRADING REEL ANALYSIS BRIEF (`E:\\Anan\\NEW`)",
        "",
        "> **Auto-Generated by `transcribe_new.py`** — Read this file + the individual `srt/<video>_claude.srt` and `edit/rN_ph.json` files to design every reel using the **2025–2026 Web-Viral Trading Edit Style** (`E:\\Anan\\EDIT_STYLE.md` & `E:\\Anan\\VIRAL_PHILOSOPHY.md`, reverse-engineered from Umar Ashraf / TradeZella, Devin Jatho, Iman Gadzhi, TJR, Tori Trades, and MagnatesMedia).",
        "",
        "## 1. Mandatory Web-Viral Pre-Edit Audit Checklist for Claude",
        "1. **Cut the Dead Air & Retakes First (`r.drop` & `r.trim`):** Check every phrase flagged `POSSIBLE_SLATE_OR_FALSE_START`, `LONG_PAUSE_BEFORE`, or repeated wording. Drop false starts and trim sentence tails so inter-phrase gaps are `0.00s` (or `-0.04s` J-cut overlap).",
        "2. **Cold-Open Hook Audit (`0.00s–3.00s`):** If Phrase `0` or `1` is a weak throat-clearing intro, either `drop` it so the reel starts directly on the boldest contrarian claim, OR place the climax 1.8-second phrase first as a Cold-Open Flash-Forward.",
        "3. **Frame-0 Triple-Channel Attack:** Frame `0` must fire simultaneously: (a) Optical Zoom Snap (`132% -> 100%` over `0.24s`) + Film Impact `Zoom Blur` + `RGB Split` (`Amount: 18 -> 0`) on `V2`, (b) `BEHIND` (`1300`) oversized `sans_hero` (`Syne-ExtraBold` / `Anton-Regular`, `500px`) title occluded behind Anan's RVM cutout (`V7`) + 2 3D Frosted Glass Hook Cards (`>=1500px` wide at `y=0.68–0.74`, thin `5px` screen-space border) with `gun-scope-zoom-in-106101.mp3`, and (c) `whoosh-vortex-243128.mp3` + `Short but Boomy.wav` + music bed (`-22 dB`).",
        "4. **After Effects 3D Camera Plane Motion Graphics (`ae3d.py` & `aecards.py`):** Instead of flat 2D graphics popping in place, use **`ae3d.flowchart_plane_3d`** (3D Frosted Glass Nodes on an Infinite 3D Grid Plane connected by glowing `Trim Paths` conduits with a 4-Node 3D Camera Rig gliding across the plane), **`ae3d.spatial_text_plane`** (3D kinetic word clusters across world waypoints `[wx, wy, wz]` with `90°` Z-axis camera pivot turns), and **`aecards.prompt_card` / `answer_card`** (`threeDLayer=True` with `Z=-24px` child depth separation and continuous 3D orientation float).",
        "5. **2025–2026 Motion-Designer 5-Font Stack:** Pair `sans_w/g/r/gold/cyan` (`PlusJakartaSans-ExtraBold`) + `sans_hero/sans_slam/pillar_w` (`Syne-ExtraBold` / `Anton-Regular` / `BebasNeue-Regular`) + `serif_gold/w/g` (`InstrumentSerif-Italic` in Sovereign Gold `#F59E0B` or White) + `mono_g/r/w/hero` (`JetBrainsMono-ExtraBold` for all `$USD / ৳BDT` numbers, `%`, and `1:4 RR` ratios) + modern geometric UI Bangla `bn_w/g/r/gold` (`HindSiliguri-Bold`: White setup, Emerald `#00E676` profit/skill, Crimson `#FF1E42` loss/trap, Gold `#F59E0B` mindset).",
        "6. **Audio Stop-Drop at the Pivot (`60–75%` mark):** Cut music (`A6`) to `-inf dB` silence `0.40s` before the climax truth/number with `Sharp Reverse.wav`, let the keyword land in dead silence, and slam music + `Short but Boomy.wav` back in.",
        "",
        "---",
        "",
        "## 2. Video-by-Video Transcript & Viral Edit Diagnostics",
        "",
    ]

    for res in results:
        rid = res["reel_id"]
        vname = res["video_name"]
        vpath = res["video_path"]
        info = res["video_info"]
        phrases = res["phrases"]
        speech_dur = sum(p["e"] - p["s"] for p in phrases)

        lines.append(f"### Reel `{rid.upper()}` — `{vname}`")
        if res.get("duplicate_of"):
            lines.append(f"> [!WARNING] **DUPLICATE VIDEO DETECTED:** `{vname}` has the exact same file size and binary hash as `{res['duplicate_of']}`.")
        lines.append(f"- **Video File:** `{vpath}` (`{info['width']}×{info['height']} @ {info['fps']}fps`, Raw Duration: `{info['duration']:.2f}s`, Active Speech: `{speech_dur:.2f}s`, Phrases: `{len(phrases)}`)")
        lines.append(f"- **Clean SRT:** `srt/{Path(vname).stem}.srt`")
        lines.append(f"- **Claude Word-Indexed SRT:** `srt/{Path(vname).stem}_claude.srt`")
        lines.append(f"- **Reelkit Phrase JSON:** `edit/{rid}_ph.json`")
        lines.append("")
        lines.append("#### Phrase Table & Automated Edit Flags")
        lines.append("| `i` | Time (`s`) | Dur | Gap | Transcript (Bangla) | Word Count | Auto-Detected Edit & Motion Triggers |")
        lines.append("|---:|---:|---:|---:|---|---:|---|")

        prev_e = 0.0
        for p in phrases:
            dur = p["e"] - p["s"]
            gap = max(0.0, p["s"] - prev_e)
            trigs = analyze_phrase_triggers(p, prev_e, p["i"], len(phrases))
            prev_e = p["e"]
            trig_cell = ", ".join(f"`{t}`" for t in trigs) if trigs else "—"
            safe_t = p["t"].replace("|", "\\|")
            lines.append(
                f"| `{p['i']}` | `{p['s']:.2f}–{p['e']:.2f}` | `{dur:.2f}s` | `{gap:.2f}s` | {safe_t} | {len(p.get('w', []))} | {trig_cell} |"
            )
        lines.append("")
        lines.append(f"#### Ready-to-Edit `plan_{rid}.py` Starter Skeleton (3D Camera Plane & Modern FinTech Style)")
        lines.append("```python")
        lines.append("import sys")
        lines.append("sys.path.insert(0, r'C:/Users/btaza/.claude/skills/anan-reel-edit/scripts')")
        lines.append("from reelkit import (")
        lines.append("    Reel, TOP, UPPER, LOWER, BOTTOM, BEHIND, CENTER,")
        lines.append("    sans_w, sans_g, sans_r, sans_gold, sans_hero, sans_slam,")
        lines.append("    serif_gold, serif_w, serif_g,")
        lines.append("    mono_g, mono_r, mono_w, mono_hero,")
        lines.append("    bn_w, bn_g, bn_r, bn_gold, bn_hero,")
        lines.append(")")
        lines.append("from ae3d import flowchart_plane_3d, spatial_text_plane, EMERALD, CRIMSON, GOLD")
        lines.append("from aecards import prompt_card, answer_card")
        lines.append("")
        lines.append(f"r = Reel({res['reel_num']}, r'{vpath}', r'{res['json_path']}')")
        lines.append("# 1. Add 3D Plane Kinetic Typography (PlusJakartaSans-ExtraBold + InstrumentSerif-Italic + HindSiliguri-Bold)")
        lines.append("# r.text(r.E(1), [(r.W(1, 0), 'THE', 'sans_w', 820, UPPER, 'plane_flip'), (r.W(1, 1), 'illusion', 'serif_gold', 1320, UPPER, 'rise')])")
        lines.append("# 2. Add After Effects 3D Camera Plane Flowchart (4-Node Camera Rig gliding across Infinite 3D Grid Plane)")
        lines.append("# r.ae(flowchart_plane_3d(r, f'R{r.key}_TEXT', r.S(3), r.E(5), [")
        lines.append("#     {'t': r.W(3, 0), 'pos': [1080, 1350, 0], 'badge': 'STEP 01', 'title': 'টেকনিক্যাল অ্যানালাইসিস', 'sub': 'Chart Structure', 'color': EMERALD},")
        lines.append("#     {'t': r.W(4, 0), 'pos': [2480, 2250, -200], 'badge': 'STEP 02', 'title': 'মানি ম্যানেজমেন্ট', 'sub': 'Risk 1:4 RR', 'color': GOLD},")
        lines.append("# ]))")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def load_whisper_model():
    from faster_whisper import WhisperModel
    cpu_threads = max(4, (os.cpu_count() or 8))
    try:
        print("[Whisper] Loading large-v3 on CUDA (float16)...", flush=True)
        return WhisperModel("large-v3", device="cuda", compute_type="float16")
    except Exception as e:
        print(f"[Whisper] CUDA float16 unavailable ({e}), using fast CPU int8 (threads={cpu_threads})...", flush=True)
        return WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=cpu_threads)


LONG_WORD_S = 1.2   # a Bangla word held longer than this is a stretched timestamp over skipped speech
GAP_S = 0.8         # word gap inside a chunk worth a second listen
SPEECH_DB = -38.0   # mean RMS of the (levelled, -20 LUFS) analysis WAV above this = someone is talking


def _whisper_words(model, wav_path: str, a: float, b: float, td: str, tag: str) -> list[list]:
    ch = os.path.join(td, f"rh_{tag}.wav")
    cut_wav_chunk(wav_path, a, b, ch)
    segs, _ = model.transcribe(ch, language="bn", beam_size=5, vad_filter=False, word_timestamps=True,
                               condition_on_previous_text=False)
    out = []
    for seg in segs:
        for w in (seg.words or []):
            wt = w.word.strip()
            if wt:
                out.append([round(a + float(w.start), 2), round(a + float(w.end), 2), wt])
    return out


def rehear_dropped(model, wav_path: str, words: list[list], s: float, e: float, td: str, tag: str) -> tuple[list[list], list[str]]:
    """Re-transcribe stretched words / talking gaps on their own and splice the new words in."""
    out, notes = [], []
    prev_end = s
    for k, w in enumerate(words):
        # gap before this word (incl. chunk start)
        if w[0] - prev_end > GAP_S and span_rms_db(wav_path, prev_end + 0.1, w[0] - 0.1) > SPEECH_DB:
            new = [x for x in _whisper_words(model, wav_path, prev_end - 0.02, w[0] + 0.02, td, f"{tag}g{k}")
                   if prev_end - 0.05 <= x[0] < w[0] - 0.05]
            if new:
                out += new
                notes.append(f"gap {prev_end:.2f}-{w[0]:.2f}: +{len(new)} words")
        if w[1] - w[0] > LONG_WORD_S and span_rms_db(wav_path, w[0] + 0.3, w[1] - 0.1) > SPEECH_DB:
            new = _whisper_words(model, wav_path, w[0] - 0.05, w[1] + 0.05, td, f"{tag}w{k}")
            new = [[max(x[0], w[0]), min(x[1], w[1]), x[2]] for x in new if x[0] < w[1] - 0.05]
            if len(new) >= 2:
                out += new
                notes.append(f"stretched '{w[2]}' {w[0]:.2f}-{w[1]:.2f}: {len(new)} words")
                prev_end = w[1]
                continue
        out.append(w)
        prev_end = w[1]
    if words and e - prev_end > GAP_S + 0.2 and span_rms_db(wav_path, prev_end + 0.1, e - 0.1) > SPEECH_DB:
        new = [x for x in _whisper_words(model, wav_path, prev_end - 0.02, e, td, f"{tag}t") if x[0] >= prev_end - 0.05]
        if new:
            out += new
            notes.append(f"tail {prev_end:.2f}-{e:.2f}: +{len(new)} words")
    return out, notes


def transcribe_video_chunks(model, wav_path: str, spans: list[tuple[float, float]]) -> list[dict]:
    phrases = []
    with tempfile.TemporaryDirectory() as td:
        for i, (s, e) in enumerate(spans):
            if e - s < 0.28:
                continue
            ch_wav = os.path.join(td, f"c{i:03d}.wav")
            cut_wav_chunk(wav_path, s, e, ch_wav)
            segs, _ = model.transcribe(
                ch_wav,
                language="bn",
                beam_size=5,
                vad_filter=False,
                word_timestamps=True,
                condition_on_previous_text=False,
            )
            words = []
            text_parts = []
            for seg in segs:
                t = seg.text.strip()
                if t:
                    text_parts.append(t)
                for w in (seg.words or []):
                    wt = w.word.strip()
                    if wt:
                        words.append([
                            round(s + float(w.start), 2),
                            round(s + float(w.end), 2),
                            wt,
                        ])
            full = dedupe_repeated_clauses(" ".join(text_parts).strip())
            if words:
                words2, notes = rehear_dropped(model, wav_path, words, s, e, td, f"{i:03d}")
                if notes:
                    words = words2
                    full = dedupe_repeated_clauses(" ".join(x[2] for x in words))
                    print(f"  [re-hear] chunk {i}: " + "; ".join(notes), flush=True)
            if full and not is_hallucinated_repetition(full, words, e - s):
                ps = words[0][0] if words else round(s, 2)
                pe = words[-1][1] if words else round(e, 2)
                phrases.append({
                    "i": len(phrases),
                    "s": round(ps, 2),
                    "e": round(pe, 2),
                    "t": full,
                    "w": words,
                })
                print(f"  [{len(phrases)-1:02d}] {ps:6.2f}-{pe:6.2f} ({pe-ps:4.2f}s): {full}", flush=True)
    return phrases


def discover_videos(new_dir: str, explicit_files: list[str] | None = None) -> list[str]:
    if explicit_files:
        return [os.path.abspath(f) for f in explicit_files if os.path.exists(f)]
    found = []
    for entry in sorted(os.listdir(new_dir)):
        full = os.path.join(new_dir, entry)
        if os.path.isdir(full):
            continue
        if Path(entry).suffix.lower() in VIDEO_EXTS:
            found.append(os.path.abspath(full))
    # Sort naturally by reel number
    def sort_key(p):
        _, num = infer_reel_id(os.path.basename(p), 999)
        return (num, os.path.basename(p).lower())
    return sorted(found, key=sort_key)


def main():
    ap = argparse.ArgumentParser(description="Transcribe all videos in E:\\Anan\\NEW into separate SRTs + reelkit JSONs + Claude Viral Analysis Brief.")
    ap.add_argument("--dir", default=DEFAULT_NEW_DIR, help="Directory containing new camera videos (default: E:\\Anan\\NEW)")
    ap.add_argument("--files", nargs="*", help="Optional specific video files to process")
    ap.add_argument("--force", action="store_true", help="Re-transcribe even if JSON/SRT files already exist")
    args = ap.parse_args()

    new_dir = os.path.abspath(args.dir)
    if not os.path.exists(new_dir):
        print(f"Directory not found: {new_dir}")
        sys.exit(1)

    videos = discover_videos(new_dir, args.files)
    if not videos:
        print(f"No video files ({', '.join(VIDEO_EXTS)}) found in {new_dir}")
        sys.exit(0)

    srt_dir = os.path.join(new_dir, "srt")
    edit_dir = os.path.join(new_dir, "edit")
    wav_dir = os.path.join(new_dir, "wav")
    os.makedirs(srt_dir, exist_ok=True)
    os.makedirs(edit_dir, exist_ok=True)
    os.makedirs(wav_dir, exist_ok=True)

    print(f"Found {len(videos)} video(s) in {new_dir}:", flush=True)
    for v in videos:
        print(f"  - {os.path.basename(v)}", flush=True)

    model = None
    results = []
    sig_cache = {}  # sig -> (video_name, phrases)

    for idx, vpath in enumerate(videos, start=1):
        vname = os.path.basename(vpath)
        vstem = Path(vname).stem
        reel_id, reel_num = infer_reel_id(vname, idx)
        sig = fast_file_signature(vpath)
        dup_of = None

        wav_path = os.path.join(wav_dir, f"{reel_id}.wav")
        json_path = os.path.join(edit_dir, f"{reel_id}_ph.json")
        txt_path = os.path.join(edit_dir, f"{reel_id}_ph.txt")
        clean_srt_path = os.path.join(srt_dir, f"{vstem}.srt")
        claude_srt_path = os.path.join(srt_dir, f"{vstem}_claude.srt")
        # Also write canonical rN.srt and rN_claude.srt aliases so scripts/Claude can reference by rN
        alias_srt_path = os.path.join(srt_dir, f"{reel_id}.srt")
        alias_claude_srt_path = os.path.join(srt_dir, f"{reel_id}_claude.srt")

        vinfo = probe_video_info(vpath)
        print(f"\n=== [{idx}/{len(videos)}] {vname} -> {reel_id} ({vinfo['width']}x{vinfo['height']} @ {vinfo['fps']}fps, {vinfo['duration']}s) ===", flush=True)

        if sig in sig_cache and not args.force:
            dup_of, phrases = sig_cache[sig]
            print(f"  [Duplicate] Exact binary match with {dup_of}; reusing {len(phrases)} phrases.", flush=True)
            payload = {
                "source": wav_path,
                "video": vpath,
                "reel_id": reel_id,
                "reel_num": reel_num,
                "duplicate_of": dup_of,
                "video_info": vinfo,
                "phrases": phrases,
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        elif os.path.exists(json_path) and not args.force:
            print(f"  [Cached] Loading existing {json_path} (use --force to re-transcribe)", flush=True)
            with open(json_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            raw_phrases = cached.get("phrases", [])
            phrases = []
            for p in raw_phrases:
                t_clean = dedupe_repeated_clauses(p.get("t", "").strip())
                if t_clean and not is_hallucinated_repetition(t_clean, p.get("w", []), p["e"] - p["s"]):
                    p["i"] = len(phrases)
                    p["t"] = t_clean
                    phrases.append(p)
            if len(phrases) != len(raw_phrases):
                cached["phrases"] = phrases
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(cached, f, ensure_ascii=False, indent=2)
                print(f"  [Cleaned] Filtered {len(raw_phrases) - len(phrases)} noise/breath hallucination phrase(s) from {json_path}", flush=True)
            dup_of = cached.get("duplicate_of")
            sig_cache[sig] = (vname, phrases)
        else:
            if model is None:
                model = load_whisper_model()
            print(f"  [1/3] Extracting cleaned 16kHz mono WAV -> {wav_path}", flush=True)
            extract_wav(vpath, wav_path, force=args.force)
            nd = TARGET_LUFS - 11 if os.path.exists(wav_path + ".clean") else -35  # levelled audio: 11 dB under the voice = old -35 on a -24 LUFS raw
            print(f"  [2/3] Detecting speech spans ({nd:.0f}dB, >=0.3s pause)...", flush=True)
            spans = detect_speech_spans(wav_path, noise_db=nd)
            print(f"  [3/3] Transcribing {len(spans)} speech chunks with faster-whisper large-v3...", flush=True)
            phrases = transcribe_video_chunks(model, wav_path, spans)
            sig_cache[sig] = (vname, phrases)

            payload = {
                "source": wav_path,
                "video": vpath,
                "reel_id": reel_id,
                "reel_num": reel_num,
                "video_info": vinfo,
                "phrases": phrases,
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        # Always regenerate SRTs & txt from phrases so formatting is up to date
        write_clean_srt(phrases, clean_srt_path)
        write_clean_srt(phrases, alias_srt_path)
        write_claude_word_srt(phrases, claude_srt_path, reel_id, vname)
        write_claude_word_srt(phrases, alias_claude_srt_path, reel_id, vname)
        write_phrase_txt(phrases, txt_path, vpath)

        print(f"  -> Wrote Clean SRT:        {clean_srt_path} (& {alias_srt_path})", flush=True)
        print(f"  -> Wrote Claude Word SRT:  {claude_srt_path} (& {alias_claude_srt_path})", flush=True)
        print(f"  -> Wrote Reelkit JSON/TXT: {json_path}", flush=True)

        results.append({
            "reel_id": reel_id,
            "reel_num": reel_num,
            "video_name": vname,
            "video_path": vpath,
            "video_info": vinfo,
            "json_path": json_path,
            "phrases": phrases,
            "duplicate_of": dup_of,
        })

    brief_path = os.path.join(new_dir, "CLAUDE_VIRAL_ANALYSIS.md")
    generate_claude_master_brief(results, brief_path)
    print(f"\n[DONE] Generated Master Claude Viral Analysis Brief -> {brief_path}", flush=True)


if __name__ == "__main__":
    main()
