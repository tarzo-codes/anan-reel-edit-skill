---
name: shorts-editor-skill
description: End-to-end automated viral editing of Anan's Bangla/Banglish trading & finance reels (2160x3840 @ 25fps) in Premiere Pro + After Effects + Remotion. Uses the 2025-2026 Motion-Designer 3D Camera Plane & FinTech Edit Style (Keanu Visuals, Capitaojack, Devin Jatho, Iman Gadzhi, Umar Ashraf / TradeZella, MagnatesMedia). Covers silence-chunked Bangla transcription + separate SRT generation for E:\Anan\NEW (transcribe_new.py), 5-font modern FinTech typography (Plus Jakarta Sans, Syne, Anton/Bebas Neue, Instrument Serif Italic, JetBrains Mono, Hind Siliguri Bold), 4-Node After Effects 3D Camera Rig moving across an Infinite 3D Grid Plane (ae3d.py), 3D Trim Paths Flowcharts, Multi-Plane Z-Parallax Glass UI Cards (aecards.py), RSMB Pro, Audio Stop-Drops, and 4-layer SFX.
---

# Anan 2025–2026 3D Camera Plane & FinTech Viral Reel Pipeline

> **CRITICAL DIRECTIVE:**
> 1. **NEVER use old homemade fonts (`LucidaHandwriting`, `Magneto-Bold`, `Impact`) or generic Windows system fonts (`Times New Roman`, `Consolas`, `Li Shadhinata`).** Use the installed **2025–2026 Motion-Designer Font Stack**: `PlusJakartaSans-ExtraBold`, `Syne-ExtraBold`, `Anton-Regular` / `BebasNeue-Regular`, `InstrumentSerif-Italic`, `JetBrainsMono-ExtraBold`, and `HindSiliguri-Bold`.
> 2. **Use the After Effects 3D Camera Plane Motion Graphics System (`ae3d.py` & `aecards.py`):** Instead of flat 2D text/cards popping in place, build **3D Spatial Canvas scenes** where a **4-Node 3D Camera Rig (`CAM3D_POS` $\rightarrow$ `CAM3D_ORBIT` $\rightarrow$ `CAM3D_DRIFT` $\rightarrow$ `CAM3D_35MM`)** glides, banks (`Z-Roll`), tilts (`X-Pitch` / `Y-Yaw`), and pivots `90°` across an **Infinite 3D Perspective Grid Plane (`ADBE Grid`)** with `Trim Paths` 3D Flowchart Conduits and Multi-Plane Z-Parallax Glass UI Cards!

Before writing any edit plan or running any script, **read both canonical references**:
1. **[`references/style.md`](references/style.md)** (mirrored at **`E:\Anan\EDIT_STYLE.md`**) — Complete 2025–2026 Motion-Designer 3D Camera Plane & FinTech technical bible.
2. **[`references/viral_philosophy.md`](references/viral_philosophy.md)** (mirrored at **`E:\Anan\VIRAL_PHILOSOPHY.md`**) — Web-viral hook psychology, 6 viral trading script frameworks, retention curve engineering, Audio Stop-Drops, and the `E:\Anan\NEW` transcription pipeline.

---

## 1. Turnkey Workflow for New Videos in `E:\Anan\NEW`

### Step 1 — Transcribe & Generate Separate SRTs + Claude Brief (`transcribe_new.py`)
Run:
```bash
python "C:/Users/btaza/.claude/skills/shorts-editor-skill/scripts/transcribe_new.py" --dir "E:/Anan/NEW"
```
- **Outputs created automatically in `E:\Anan\NEW`:**
  - `E:\Anan\NEW\srt\<video_name>.srt` & `r<N>.srt` — Clean phrase-level SubRip `.srt` files.
  - `E:\Anan\NEW\srt\<video_name>_claude.srt` & `r<N>_claude.srt` — **Word-indexed `.srt` files** showing `[P#i | start-end (dur) | gap | AUTO_TRIGGERS]`, full Bangla phrase text, and `WORDS: [0:word@s-e 1:word@s-e ...]` for exact `r.W(i, k)` / `r.T(i, w0, w1)` word-sync.
  - `E:\Anan\NEW\edit\r<N>_ph.json` & `r<N>_ph.txt` — Exact `reelkit.py` inputs.
  - `E:\Anan\NEW\CLAUDE_VIRAL_ANALYSIS.md` — Consolidated viral analysis brief across all videos in `E:\Anan\NEW`.
- **Audio pass before Whisper (10-11-2026, user):** the analysis WAV is high-passed (80 Hz), FFT-denoised and levelled to
  -20 LUFS (`wav/rN.wav.clean` marks it); pauses are detected at -31 dB (11 dB under the voice); chunks > 9 s split at the
  quietest 60 ms, never fixed windows. Any word > 1.2 s or talking gap > 0.8 s is re-transcribed alone and spliced in
  (`[re-hear]` in the log). Raw-audio Whisper had dropped a whole sentence in reel 1 by stretching 'বের' over 5 s.
  Premiere keeps the original audio. Whisper runs on CPU int8 here (CUDA driver too old for ctranslate2): ~10 min/reel.
- **Auto-retake is not trusted blindly:** read every `retake:` line. It cut contrasts ("guarantee দিতে পারছি না… বাট
  guarantee দিচ্ছি") and lines that merely start with the same word ("এবং congratulations" vs "এবং আপনার…") -> `keep={i}`.

### Step 2 — Curate the Viral Cut & Plan (`plan_rN.py` with `reelkit.py` + `ae3d.py` + `aecards.py`)
1. **Cut Slates, False Starts & Retakes (`drop` & `trim`):**
   - `Reel(..., auto_retakes=True)` automatically detects repeated opening clauses and drops the first failed take. Add any manual slate/outtake indices to `drop={...}`.
   - **Half-said false starts** ("টেলিগ্রাম চ-" ... pause ... "আমার টেলিগ্রাম চ্যানেলের লিংক") are swallowed by Whisper's phrase pass. ALWAYS run
     `python scripts/false_starts.py E:/Anan/NEW/edit/rN_ph.json` before planning: it re-hears every short voice burst that is followed by a
     restart and writes `"fs"` spans into the phrase; reelkit then cuts them out (the phrase becomes 2 A-roll pieces, `W/E/S` still work).
     Read its printout; keep a wrong hit with `Reel(..., keep_fs={i})`.
2. **FAST-CUT VERSION is the default (references/style.md section 0, read it first):** a new visual every ~2 s, exact semantic B-roll matched to the spoken word & emotion (search `references/stock.md` first, and download any missing concept immediately via `scripts/stock_fetch.py`), 3-4-word text chunks on the word (`r.chunks`), a 3D camera scene in the hook, neon outline overlays (`aecards.neon`, using `kind="badge_num"` for concentric ring+number badges), ASCII `TK` instead of `৳` in Latin fonts, clean zero-vocal instrumental music beds (`E:/Anan/Assets/Music/*.mp3`), and NO stroke/`Accepts Lights` on any text that lives on a 3D plane.
3. **Use the 2025–2026 Motion-Designer Font Stack (`reelkit.py`):**
   - **Primary FinTech & Kinetic Sans (`PlusJakartaSans-ExtraBold`):** `sans_w`, `sans_g`, `sans_r`, `sans_gold`, `sans_cyan`
   - **Architectural Hero & Pillar Display (`Syne-ExtraBold` / `Anton-Regular` / `BebasNeue-Regular`):** `sans_hero`, `sans_slam`, `pillar_w`
   - **Neo-Luxury Editorial Serif Italic (`InstrumentSerif-Italic`):** `serif_gold`, `serif_w`, `serif_g`
   - **Quant HUD Tabular Monospace (`JetBrainsMono-ExtraBold`):** `mono_g`, `mono_r`, `mono_w`, `mono_hero`, `label_slate`
   - **Modern Geometric UI Bangla (`HindSiliguri-Bold`):** `bn_w`, `bn_g`, `bn_r`, `bn_gold`, `bn_hero`
4. **Rotate Across All 5 Distinct 3D Camera Motion-Graphics Variations (`reelkit.py` + `ae3d.py`) — NEVER Reuse Only `plane_canvas`:**
   - **Variation 1 — `r.plane_canvas(t0, t1, stops, ...)`:** Connected FinTech Terminal Mind-Map Board with dedicated `98px` header strips and orthogonal `Trim Paths` conduits (use for 3-step technical breakdowns & pattern chains).
   - **Variation 2 — `r.plane_tunnel(t0, t1, stops, ...)`:** 3D Z-Depth Chronological Fly-Through Corridor (`X Rotation = +84°` floor grid + central Z-runway + staggered floating milestones with pylons as the camera flies forward into Z-depth; use for timelines, roadmaps, `2026 -> 2027`, step-by-step journeys).
   - **Variation 3 — `r.plane_hub(t0, t1, hub, satellites, ...)`:** Central circular double-ring Core Hub + 2–4 radiating spoke satellites with orbital camera whips and wide full-wheel pullback (use when 1 core rule/strategy governs 3 life areas or options).
   - **Variation 4 — `r.plane_versus(t0, t1, left_side, right_side, verdict=..., ...)`:** Opposing 3D Angled V-Stage Monoliths (`+16°` vs `-16°` Y-yaw) + popping Center Verdict Bridge (use for binary choices, `Risk -1R vs Reward +2R -> 1:2 RR`, `Cut Finger vs Lose Hand`).
   - **Variation 5 — `r.plane_kinetic(t0, t1, beats, ...)`:** Pure box-free 3D Architectural Typography with `90°` Camera `Z Rotation` pivot banks and floor guide rails (use for punchy philosophical hooks, rule triads, and life lessons).
   - **3D Multi-Plane Glass UI Cards (`aecards.prompt_card` & `aecards.answer_card`):** Opens in 3D space (`threeDLayer=True`, `Accepts Lights=0`) with child text hovering at `Z = -12px`.

### Step 2b — Fetch Missing Semantic Stock B-Roll (`stock_fetch.py`)
Whenever local `references/stock.md` lacks an exact visual match for the spoken word/emotion (e.g. gym lifting, breakup, roulette/gambling, hourglass patience, mobile gaming), fetch from Pexels + Pixabay automatically (works with or without API keys):
```bash
python "C:/Users/btaza/.claude/skills/shorts-editor-skill/scripts/stock_fetch.py" "man lifting weights dark gym" --source both --orientation portrait --limit 1 --download --use-for "gym workout, discipline"
```
Always visually inspect downloaded clips before placing them on the timeline (reject flat white-background cartoons).

---

## 2. Script Reference (`C:\Users\btaza\.claude\skills\shorts-editor-skill\scripts\`)

| Script | Purpose |
|---|---|
| **`transcribe_new.py`** | Primary batch pipeline for `E:\Anan\NEW`. Generates `<video>.srt`, `<video>_claude.srt`, `rN_ph.json`, `rN_ph.txt`, and `CLAUDE_VIRAL_ANALYSIS.md`. |
| **`stock_fetch.py`** | **Pexels & Pixabay Stock Video/Photo Search & Downloader** (API + zero-key Chrome-TLS fallback). Downloads into `E:\Anan\Assets`, probes exact `(w, h, dur, fps)`, prints `reelkit` snippet, and appends to `references/stock.md`. |
| **`reelkit.py`** | Declarative Python DSL with the 2025–2026 Motion-Designer Font Stack, punch-aware text clamping, and `plane_canvas` / `plane_tunnel` / `plane_hub` / `plane_versus` / `plane_kinetic`. |
| **`ae3d.py`** | **After Effects 3D Camera Plane Engine** implementing all 5 distinct 3D spatial variations (`canvas_board_plane_3d`, `timeline_tunnel_3d`, `radial_hub_3d`, `versus_split_3d`, `kinetic_wall_3d`). |
| **`aecards.py`** | **3D Multi-Plane Glass UI Card & Neon Builders** (`prompt_card`, `answer_card`, `logo_behind`, `neon` including concentric `badge_num`). |
| **`false_starts.py`** | Finds half-said false starts inside phrases (burst + pause + restart) and writes `"fs"` cut spans into `rN_ph.json`. Run after transcription. |
| **`cutout_rvm.py`** | Robust Video Matting (`resnet50`, `fp16` CUDA) $\rightarrow$ `ProRes 4444` `.mov` with alpha for `V7` behind-presenter text/logos. |
| **`jsx/build_reel.jsx`** | ExtendScript builder that populates `V1–V10` and `A1–A6` in Premiere Pro, applies Film Impact effects/transitions, and grades A-roll + cutouts. |
| **`hc_handcam_template.py`** | Handcam / casual plan helper (`HC`: hook, cap, top, step, cash, burst, comment, own, punch...). Copy to the batch `edit/` as `hc.py`. |
| **`aeui.py`** | AE UI builders: `step_badge` (number in an animated circle), `comment_ui` (TikTok / YouTube comment that types), `hook_title` v2. |
| **`tighten_cuts.py`** | After pass-1 approval: lead-in before the voice, clipped tails run on, dead air > 0.45 s inside a line cut. |
| **`en_words.py`** | Rewrites Bangla-spelled English in plans to Latin ("ট্রেডিং" -> "trading"). |
| **`ae_diff.py`** | Updates only the changed AE layers of a reel the user already edited (no comp deletion). |
| **`mix_levels.py`** | Measures voice + music (EBU R128) -> voice / music gains (voice -15 LUFS, bed 10 LU under). Used by reelkit auto_mix. |
| **`jsx/relevel_pass.jsx`** | Re-levels a finished / hand-edited reel by multiplying every Level key (music by its delta, voice + SFX by the voice delta). |
| **`jsx/limiters_pass.jsx`** | Adds a default Hard Limiter to every non-music audio track (build_reel now does it itself). |
| **`jsx/render_reels.jsx`** | Queues reels in AME with `assets/Anan Reel 4K H264 80Mbps.epr` (MP4, 80/100 Mbps, AAC 320k), in/out reset first. |
| **`jsx/export_frames.jsx`** | QE check-frame export (`EXP={dir,seq,tag,times}`), own call after `openSequence`. |


---

## 3. Professional Visual Editor Rules & Collision Prevention

To maintain broadcast-tier visual quality and eliminate amateur typographic defects across all reels, strictly enforce the following rules in every plan and AE builder:

### 1. Step / Pillar Badges vs Behind-Head Hero Typography
- **Never overlap badges with hero text:** Upper-corner badges (`badge_num`, `check`, `cross` at $(1740, 740)$) must NEVER be active at the same timestamp as behind-head hero typography (`pillar_w`, `sans_slam`, `sans_hero` at $y = 1050$).
- **Root cause:** Hero fonts (Bebas, Anton) at size $\ge 500$ span $> 1400\text{px}$ in width and $> 400\text{px}$ in cap-height. Their top-right characters cross $x = 1600$ and $y = 800$, smashing directly under the badge ring and making numbers illegible.
- **The Golden Edit Pattern:** Stagger them sequentially to match the speaker's natural cadence:
  - When the speaker says the number ("সেকেন্ড" / "Second" / "02"), pop the badge in upper-right for $0.6 - 0.8\text{s}$.
  - When the speaker speaks the topic keyword ("MARKET"), let the badge exit and slam the hero text behind the head.
  - Zero visual collision, perfect narrative synchronization.

### 2. 3D Camera Frustum Safe Margins (`kinetic_wall_3d` & `ae3d.py`)
- **Frustum Width Constraint:** In 3D space with a 35mm/50mm camera at $Z = -2666.7$ (Zoom $= 3000$, magnification $1.125\times$), the total visible width of a $2160\times 3840$ comp is only $1920\text{px}$.
- **Font Width Factor:** Wide geometric fonts (`Syne-ExtraBold`) have a character factor of $\approx 0.96 \times \text{fontSize}$ (not $0.62$).
- **Safe Width Limit:** All 3D titles on `kinetic_wall_3d` must be clamped to $\text{local width} \le 1380\text{px}$ (projects to $\le 1540\text{px}$ on screen, leaving $\ge 310\text{px}$ safe margins on each side).
- **Rule Bar & Tags:**
  - Accent rule bars must have vertices $\le [[-600, 0], [600, 0]]$ ($1200\text{px}$ local / $1350\text{px}$ on screen).
  - Top mono tags (`[ 03 // BLUEPRINT // 3 STEPS ]`) must use `fontSize = 46`, `tracking = 20`.
  - Outer characters (e.g. "A", "E", "M", "S") will never touch or clip against the canvas boundaries.

### 3. Sequential vs Concurrent Text Layouts (No Double-Text Blobs)
- **Contrasting Keywords:** When the speaker contrasts two states (e.g. "Penny" vs "Peak"), sequentialize their display. "PENNY" displays during its spoken word and exits as "PEAK" enters. Never leave both active at the same horizontal center with overlapping vertical baselines.
- **Stacked Kicker + Hero Pairs:** When pairing a top kicker with a hero word (e.g. "BEST" above "STRATEGY", or "STILL" above "PROFITABLE"):
  - Kicker: Use `kicker_w` or `kicker_gold` (`fontSize = 160`, $y = 620$).
  - Hero: Use `pillar_w` or `sans_slam` (`fontSize = 500-540`, $y = 1050$, behind head).
  - Vertical baseline distance must be $\ge 400\text{px}$ to ensure at least $100\text{px}$ of clear negative space between them.

### 4. Dynamic Link Online Integrity & Track Routing
- **Clean Relinking:** When rebuilding AE comps, query existing project items via `findAEItem` and check `!c.isOffline()` before replacing clips.
- **Strict Track Separation:** Screen-space foreground elements (captions, kickers, overlays) always route to `R*_FRONT` (Track V11, above V9 camera zoom). Only behind-head cutouts and behind-head typography route to `R*_TEXT` (Track V7, below V9).

### 5. The 6 Distinct 3D Plane Styles Matrix & Required Variety
Never use the same 3D plane animation style across multiple reels. In any batch of reels (e.g. Reels 1–6), each reel MUST feature its own distinct 3D spatial variation tailored to its narrative structure:
1. **Variation 1 — `r.plane_canvas` (`canvas_board_plane_3d`):** 3D FinTech Terminal Mind-Map Canvas Board with illuminated orthogonal conduits (best for multi-step breakdowns, 4 trading types, category mind-maps).
2. **Variation 2 — `r.plane_tunnel` (`timeline_tunnel_3d`):** 3D Z-Depth Fly-Through Corridor with $+84°$ floor grid runway, floating milestone cards, and pylons (best for chronological progressions, 5 candlestick patterns, evolutionary journeys).
3. **Variation 3 — `r.plane_hub` (`radial_hub_3d`):** 3D Radial Core Hub with radiating glowing laser spokes to satellite cards and orbital camera whip-pans (best for foundational pillars, central hubs governing 3-4 satellites).
4. **Variation 4 — `r.plane_versus` (`versus_split_3d`):** 3D Opposing Monolith Split Showdown with $+16°$ vs $-16°$ Y-yaw slabs and glowing center verdict bridge (best for binary contrasts, SMC vs Retail, indicator myth vs real price action).
5. **Variation 5 — `r.plane_kinetic` (`kinetic_wall_3d`):** Pure 3D Kinetic Typography Wall with lit floor grid and $90°$ Z-pivot camera banking turns (best for punchy philosophical statements, 3 golden rules, psychological mindsets).
6. **Variation 6 — `r.plane_flowchart` (`plane_flowchart_3d`):** 3D Step-by-Step Decision Tree Flowchart with curved glowing guide rails connecting milestone nodes (best for roadmaps, 30-day blueprints, action workflows).

### 6. Zero-Collision Text Rules & Safe-Lane Flipping
- **Lower Third Caption Protection:** Spoken Bengali subtitle chunks (`r.chunks`) must sit strictly in designated safe zones:
  - During A-roll presenter shots: $y = 2800$ (below chin/chest level, above Instagram UI).
  - During cards / b-roll: $y = 3120$ (below centered media cards) or $y = 620$ (if lower media occupies bottom half).
- **Automated Collision Flipping:** If a subtitle chunk and a hero callout/kicker overlap in time within $450\text{px}$ vertically:
  - Automatically flip the chunk to the opposite safe lane ($y = 2800$ if callout is top; $y = 620$ if callout is bottom).
  - NEVER permit subtitle chunks and callout text to occupy the same vertical half of the frame concurrently.
- **Beat Clamping for Chunks:** Consecutive subtitle chunks must clamp `c_curr.end = c_next.t` to eliminate double-chunk stacking.

### 7. Text Stroke Sanity Rule (No Same-Color or White-on-White Strokes)
- **Zero White-on-Light Strokes:** NEVER apply a white or light stroke to white, cream, or light-colored text. It destroys typographic form and causes muddy, illegible blobs.
- **Zero Same-Color Strokes:** If `strokeColor` is within $0.4$ Euclidean distance of `fillColor`, stroke MUST be stripped (`applyStroke = False`).
- **Explicit `applyStroke: False` in AE Payloads:** Because After Effects inherits sticky Character panel strokes, every standard text style payload (`mono_hero`, `mono_g`, `mono_r`, `mono_w`, `sans_w`, `sans_slam`, `pillar_w`) must explicitly pass `"applyStroke": false` unless an intentional high-contrast dark stroke (e.g. pure black `#000000` on bright fill) is specified.

### 8. Camera Adjustment Layer Zoom Isolation (2D Transform vs 3D AE Camera)
- **Filter Punches During 3D Scenes:** Premiere Pro's V9 camera adjustment layer applies 2D Transform punch zooms ($1.14\times - 1.32\times$) across V1–V8. Applying 2D Transform scaling over an After Effects 3D camera scene causes grotesque camera fighting, lens distortion, and edge clipping.
- **Automatic Filtering:** `reelkit.py` must filter out any punches overlapping `self.plane_spans` from `prem["punches"]`.
- **Safe Margins During Presenter Punches:** When 2D punches ARE active during A-roll, top text must never sit higher than $y = 580$ and bottom text no lower than $y = 2880$ so punches do not crop letterforms off screen.

### 9. Dynamic Link Auto-Save & Clean Refresh Protocol
- **Immediate AE Project Save:** After executing build scripts in After Effects via BridgeTalk, ALWAYS call `app.project.save()` immediately before Premiere Pro touches the comps.
- **Trash-Bin Purge for Offline Comps:** If Premiere Pro displays offline or stale comp items in bin `"AE"`, move them to a temporary trash bin (`createBin` $\rightarrow$ `moveBin` $\rightarrow$ `deleteBin`) and re-import fresh via `app.project.importAEComps`. Verify `isOffline() == false` across all tracks.

### 10. Keyframe Monotonicity in ExtendScript (`_k` Helper)
- In `ae3d.py`, all keyframe sequences passed to `keyframe.set_batch` must enforce strictly monotonic timestamps:
  `times[j] >= times[j-1] + 0.04` (at least 1 frame @ 25fps). Identical timestamps collapse into a single keyframe in After Effects, causing subsequent `keyframe.set_easing` calls with `keyIndex: 2` to throw "key index out of range". Ease indices must always be checked with `1 <= i <= len(times)`.

### 11. High-Stimulation Fast-Cuts, Stock B-Roll & Bilingual Stacked Captions
- **Stimulating Visual Rhythm:** Talking head alone for $>2.5\text{s}$ makes the edit feel bland. Every beat must feature a visual reset every $1.8 - 2.5\text{s}$ rotating: presenter cutout $\rightarrow$ stock video card $\rightarrow$ full-screen stock footage $\rightarrow$ 3D spatial plane $\rightarrow$ presenter punch.
- **Stock B-Roll Integration:** Use 7 to 12 stock video scenes per reel. For landscape stock clips ($1920\times 1080$), use `overflow=True` ($2160\text{px}$ width edge-to-edge, bare borders) with the blueprint grid background filling top and bottom.
- **Bilingual Stacking Captions (`r.stack`):** Replace boring one-line subtitles with dynamic stacked pairs:
  - Upper: English topic kicker in `PlusJakartaSans-ExtraBold` or `JetBrainsMono` ($140 - 150\text{px}$, tracking $35 - 40$).
  - Lower: Spoken Bengali subtitle chunk ($190 - 210\text{px}$) with keyword highlights.
  - Spacing: $220 - 260\text{px}$ vertical separation ($y = 2580 / 2820$ lower-third, or $y = 500 / 720$ top).
- **Music is balanced ON THE VOICE, measured (user, 8-11-2026: "bg music is too low"):** never a fixed `music_db`. `Reel(auto_mix=True)` (default) runs `mix_levels.solve` at write(): voice -> **-15 LUFS**, music bed **10 LU under** (-25 LUFS), from EBU R128 of the cut voice and the music span. Fixed -22 dB had left beds 12-22 LU under (reel 2 buried). See section 15.

### 12. Premiere Pro File Import Guard (Zero Modal Dialogs & Missing Media)
- **Pre-Check Existence Before `importFiles`:** Never call `app.project.importFiles([path], ...)` in ExtendScript without first verifying `var f = new File(path); if (!f.exists) { return null; }`. Attempting to import non-existent files triggers Premiere Pro's blocking "File Import Failure: We were unable to open the file on disk" modal dialog, halting automation.
- **Cutout Guard in `reelkit.py`:** Only append cutout spans to `prem["cutouts"]` if the target `.mov` file exists on disk (or matches an existing rendered cutout within $0.8\text{s}$). Never pass non-existent cutouts into Premiere.
- **Offline Clip Audit:** After building sequences, always run the automated ExtendScript clip audit across all tracks to verify `offlineCount == 0`.

### 13. Zero Text Across Presenter's Face & Top Curtain Bar Subtitling
- **Hard Face Zone Exclusion:** Presenter's face sits between $Y = 1250$ and $Y = 3050$ (especially when 2D camera punch zoom pulls the chin down into $Y = 2200 - 2800$). Placing subtitles at $Y = 2800$ during talking head lands directly across Anan's mouth and beard.
- **Top Curtain Bar Routing (`r.cap`):** All spoken dialogue subtitles and bilingual kickers during A-roll talking head must be routed to the top curtain bar zone: English kicker at $Y = 600$, Bengali subtitle at $Y = 868$. This zone is backed by `top_cover_curtain.png` ($Y \in [0, 1073]$) and is 100% free of facial obstruction.
- **Continuous Top Cover Without Cross Dissolve:** `top_cover_curtain.png` must be placed continuously from $0$ to $D.total$ on track V3 without a Cross Dissolve at $0\text{s}$ (which previously dissolved in from transparent and exposed the curtain rod for the first 20 frames).

### 14. Zero Sentence Butchering & Speech Alignment Integrity
- **Protect Opening Hooks:** Never drop phrases 0 or 1 (`drop={0, 1}`) if it contains the primary hook of the reel (e.g. in Reel 5: "মার্কেট উপরে যাবে নাকি নিচে আসবে চার্ট দেখার সাথে সাথে তুমি বুঝতে পারবা").
- **Zero Audio Bleed on Trims:** When trimming false starts or stumbled words (e.g. Reel 1 "দুই নামবার থা হচ্ছে" before "সেকেন্ড হচ্ছে", or Reel 6 "সিখার মত্তে" before "ট্রেডিংয়ের কোর্স কিনার মতো টাকা নাই"), ensure cut boundaries do not bleed into neighboring syllables:
  `a = max(_w_start(p["w"][w0]) - pre, _w_end(p["w"][w0 - 1]) + 0.02)`
  `b = min(_w_end(p["w"][w1]) + post, _w_start(p["w"][w1 + 1]) - 0.02)`
- **Dynamic Link Online Verification:** In Premiere Pro, purge any cached offline Dynamic Link comps before importing fresh comps saved in After Effects. Verify `isOffline() == false` across all tracks.

### 15. Audio Mix, Limiter & Render (8-11-2026, user: "bg music too low", "higher bitrate", "mp4")
- **Mix by measurement, per reel.** Every mp3 is mastered differently and every raw has its own voice level (his raws:
  -18 to -23 LUFS, peaks -1.5 dBFS). `mix_levels.py <edit dir> 1 2 ...` prints / writes the gains; reelkit applies them
  automatically (`auto_mix=True`). Targets: voice **-15 LUFS** on the timeline, music bed **10 LU under** (GAP_LU in
  mix_levels.py), SFX keep their per-event dB but ride with the voice gain.
- **Re-levelling a finished or user-edited reel: never rebuild.** Compute deltas (new gain - gain it was built with,
  recorded in `rN_prem.json`), then `var RELEVEL=[{seq, music, music_delta_db, voice_delta_db}]; $.evalFile(relevel_pass.jsx)`:
  multiplies every Level key, so fades, stop-drops and the user's tweaks survive. Write the new gains back into
  `rN_prem.json` so a second run is a no-op.
- **Limiter:** voice +3..+8 dB over -1.5 dBFS peaks would clip -> default **Hard Limiter** on every non-music track
  (build_reel adds it; `limiters_pass.jsx` for older reels). QE `setParamValue` takes normalised STRINGS ("0.95"; a number
  throws "Illegal Parameter type"), `getParamControlValue` does not update, `component.remove()` returns true but does
  nothing and undo does not revert QE param writes -> do not experiment on a live track; use the defaults.
- **Render:** `render_reels.jsx` with `assets/Anan Reel 4K H264 80Mbps.epr` (copy in `E:/Anan/Assets/presets`): H.264 **.mp4**
  (system folder `4E49434B_48323634`), VBR 1-pass 80 / 100 Mbps, AAC 320 kbps, on the **CPU renderer** (render_reels sets
  `qe.project.setRenderer("Mercury Playback Engine Software Only")`): the GPU / OpenCL renderer crashed AME in `amdocl64.dll`
  (Windows logged an IOMMU fault first) and froze the PC on 8-11-2026; 2-pass doubled that GPU load and was dropped. The `3F3F3F3F_4D6F6F56` "H264 Match Source"
  preset is the QuickTime exporter: it wrote `.mov` at 12 Mbps with PCM audio even when the path said .mp4.
  Reset in/out to the full sequence before queuing (stale out points cut renders short). After the batch, ffprobe each
  file (duration = sequence end, 2160x3840 h264 + aac) and run `ebur128=peak=true` (expect about -14 LUFS, peak <= 0 dBFS).
- **Result on 8-11-2026 (after a reboot, AME, 1-pass):** all six at exact length, 80 Mbps video, AAC 317 kbps,
  -14.8 to -15.1 LUFS, true peak +0.1 / +0.2 dBTP (AAC overshoot over the -0.1 dB limiter ceiling; harmless after platform
  normalisation). After a GPU driver fault AME stays broken ("Accelerated Renderer Error", "Unable to allocate host memory")
  until the PC is restarted - reboot first, then re-queue. About 50 min for the six reels.


### 16. Anan's Own Clips Must Match the Rest of the Reel (user, 8-11-2026)
When a beat uses his own clips (E:\Anan\Telegram Desktop), they must look like part of the same edit as the A-roll
and the stock, never a raw phone clip dropped in. Probed 8-11-2026: most are iPhone **HLG HDR** (3840x2160,
10-bit, Rec.2020, `arib-std-b67`, 59.94/60 fps); a few (IMG_1365...) are SDR Rec.709 1072x1920 @ 60.
- **Colour:** HLG clips on a Rec.709 timeline look washed and flat -> convert to SDR first (Lumetri: Input LUT /
  HDR-to-SDR tone map, or `ffmpeg zscale=t=linear:npl=100,tonemap=hable,zscale=p=bt709:t=bt709:m=bt709,format=yuv420p`),
  THEN apply "Anan Warm Pop v2" (`references/grade/`) so blacks, contrast and warmth sit with the A-roll. Mixed
  lighting (hotel tungsten, car interior, night cruise) gets a white-balance fix before the grade.
- **Motion & frame rate:** conform 60 fps to the 25 fps timeline (Interpret Footage or use the extra frames as a
  smooth slow-mo); stabilise shaky handheld (Warp Stabilizer, Smooth 5-10 %, Crop) so it matches stock steadiness.
- **Same treatment as stock:** same framing rules (fill / `overflow=True` / card), same transitions, vignette,
  sharpen, camera moves and caption placement as the stock clip next to it; mute his clip audio (or bury it
  ambient under the music) so the mix stays voice + bed + SFX.
- **Check:** export a frame of each own clip next to the neighbouring A-roll / stock frame and compare skin, blacks
  and saturation; if it still jumps out, adjust before the review pass.

### 17. Pass-2 Rules & Tools from the 10-11-2026 Batch (user notes)
Copy `scripts/hc_handcam_template_10-11.py` -> batch `edit/hc.py` and `scripts/hc10_template.py` -> `edit/hc10.py`; plans use `HC10`.
- **Emojis: ANIMATED and BIG, behind him.** `scripts/emoji_anim.py name=codepoint ...` pulls Noto Animated Emoji (fonts.gstatic.com,
  512 px animated WebP, Apache 2.0) -> ProRes 4444 `.mov` in `E:/Anan/Assets/PNG/emoji_anim/` (37 made; money_bag, no_entry,
  briefcase, sunglasses are NOT animated in Noto). `h.emoji(t0, t1, name)` = bare card (V5/6) at `head_y` + his cut-out (V8)
  so the bottom tucks behind his head; `h.logo_behind()` the same for logos. Never small static PNG emojis.
- **Subtitles: Bangla only** (`h.sub`), no English kicker / translation stacked on top. English words he SAYS stay Latin.
- **Impact:** a stock clip, `h.desat(t0, t1)` for sad beats (build_reel keys Lumetri Basic AND Creative Saturation on the
  A-roll + cut-outs; Basic alone left the warm LUT colouring the skin), or `h.mark(t, "cross"|"check")` - full-screen
  drawn X / tick with a dim, glow and shake. Time a cross on the negated word and keep it short (0.7 s) so it does not
  sit over the next positive line.
- **Comment reels:** `h.reply_popup(t0, t1, "@demo_user", [lines])` = TikTok "Reply to @user's comment" sticker (white,
  rounded, avatar, Bangla lines) on the wall above his head; no captions under it.
- **Vibe switch inside a reel:** `h.second_music(t, path)` (measured gain, crossfade; build_reel `D.music.until` + `D.music2`
  on the spare audio track) - sad bed + desat for the problem, normal bed + colour back on the explain line.
- **Black hook:** `h.black_words(t0, t1, [(t, "WORD"), ...], fs=360, accent=GOLD)` - cut to black after his first word, Impact
  words stacked one per line as he says them, all on one screen, punch back in.
- **Hook position:** `hook_title(..., center=)` / `megahook(..., center=)`; desk framing (face 1100-2100) -> center 760.
- **His own clips:** `HC10.own()` probes color_transfer (ffprobe csv prints a trailing comma - strip it) and tone-maps HLG to
  SDR 25 fps into `E:/Anan/Assets/own_sdr/`; check the frame (IMG_4837 opens on vape smoke, IMG_3634 on a blurry window).
- **Premiere A-roll item names must keep `.MP4`** (build_reel finds the A-roll by name). QE `exportFramePNG` needs
  BACKSLASH paths (forward slashes throw "Unknown error exception"); exporting frames right after a Dynamic Link rebuild
  can hang Premiere for minutes (it renders the AE comps) - save before exporting.
- `tighten_cuts.py` restores voice the user cut by hand (it extended reel 3 P00 back over "এবং খুব ভালো মতো"): re-apply the
  user's out points after running it.
- `scripts/render_cutouts.py N ...` renders every cut-out a plan asked for; re-run the plan afterwards (a plan run before the
  renders writes no cut-outs into rN_prem.json).
