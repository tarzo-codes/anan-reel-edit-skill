"""mix_levels.py - set the music bed RELATIVE TO HIS VOICE, measured, per reel (user, 8-11-2026: "bg music is too low,
balance the bg audio based on the voice").

A fixed music_db (-22) was too quiet on some tracks and fine on others because every mp3 is mastered differently and
every raw has a different voice level. This measures, with ffmpeg's EBU R128 meter:
  voice  = the A-roll pieces of rN_cuts.json concatenated (what is actually on the timeline), at the clip gain
  music  = the music file over [src_in, src_in + total]
and returns the clip gains that put
  voice integrated at VOICE_LUFS  (the mix then lands near -14 LUFS, the IG/TikTok/YouTube normalisation target)
  music integrated at VOICE_LUFS - GAP_LU  (bed clearly audible but never fighting the words)

  python mix_levels.py E:/Anan/NEW/edit 1 2 3 4 5 6      -> prints a table + writes mix_levels.json
Use the result with jsx/relevel_pass.jsx (keeps every key shape: fades, stop-drops, user edits) or feed music_db /
voice_db into Reel(...) before a build (reelkit does this automatically when auto_mix=True).
"""
import json
import os
import re
import subprocess
import sys

VOICE_LUFS = -15.0   # spoken word target on the timeline
GAP_LU = 10.0        # music bed this many LU under the voice (music_db=-22 left it 12-22 LU under: "too low", 8-11-2026)
MUSIC_MIN, MUSIC_MAX = -30.0, -6.0
VOICE_MIN, VOICE_MAX = -6.0, 12.0


def _ebur128(args):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args + ["-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
    if not m:
        raise RuntimeError(p.stderr[-800:])
    return float(m[-1])


def voice_lufs(raw, cuts):
    """integrated loudness of the cut voice at 0 dB clip gain"""
    parts = "".join(f"[0:a]atrim={c['src_in']}:{c['src_out']},asetpts=PTS-STARTPTS[a{k}];" for k, c in enumerate(cuts))
    cat = "".join(f"[a{k}]" for k in range(len(cuts))) + f"concat=n={len(cuts)}:v=0:a=1[v];[v]ebur128[o]"
    return _ebur128(["-i", raw, "-filter_complex", parts + cat, "-map", "[o]"])


def music_lufs(path, src_in, total):
    return _ebur128(["-ss", str(src_in), "-t", str(total), "-i", path, "-af", "ebur128"])


def solve(raw, cuts, music, src_in, total, voice_target=VOICE_LUFS, gap=GAP_LU):
    v0 = voice_lufs(raw, cuts)
    m0 = music_lufs(music, src_in, total)
    vdb = round(max(VOICE_MIN, min(VOICE_MAX, voice_target - v0)), 1)
    mdb = round(max(MUSIC_MIN, min(MUSIC_MAX, voice_target - gap - m0)), 1)
    return {"voice_lufs_raw": round(v0, 1), "music_lufs_raw": round(m0, 1), "voice_db": vdb, "music_db": mdb,
            "voice_on_tl": round(v0 + vdb, 1), "music_on_tl": round(m0 + mdb, 1)}


if __name__ == "__main__":
    d, ns = sys.argv[1], [int(x) for x in sys.argv[2:]]
    out = {}
    for n in ns:
        prem = json.load(open(os.path.join(d, f"r{n}_prem.json"), encoding="utf-8"))
        cuts = json.load(open(os.path.join(d, f"r{n}_cuts.json"), encoding="utf-8"))
        raw = prem.get("raw") or prem.get("source") or f"E:/Anan/NEW/reel {n}.MP4"
        m = prem["music"]
        res = solve(raw, cuts, m["path"], m.get("src_in", 0), prem["total"])
        res.update(old_voice_db=prem.get("voice_db", 3), old_music_db=m["db"],
                   old_gap=round((res["voice_lufs_raw"] + prem.get("voice_db", 3)) - (res["music_lufs_raw"] + m["db"]), 1))
        out[n] = res
        print(n, res)
    json.dump(out, open(os.path.join(d, "mix_levels.json"), "w"), indent=1)
