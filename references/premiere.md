# Premiere recipes for Anan reels

General MCP gotchas (broken tools, QE razor, volume raw values, adjustment-layer stacking, timeouts,
port 8097 held by another session) are in
`C:\Users\btaza\.claude\skills\tr-video-edit\references\premiere-scripting.md`. **Read it before touching
Premiere.** This file only covers what's different for Anan.

## Contents
1. Units at 25 fps
2. Start from the previous reel's project
3. A-roll: cuts, Lumetri, punch-ins
4. Text clips (PNG from render_text.py)
5. B-roll cards and circle headshot
6. Transitions (Impact)
7. Sound
8. Verify

## 1. Units at 25 fps
- 254016000000 ticks per second; **one frame = 10160640000 ticks** (25 fps). Snap every time to
  `Math.round(t*25)/25`.
- Sequence: 2160x3840, 25 fps (`get_sequence_settings` should show this; anything else is wrong).
- Adjustment layers and Graphics have `inPoint` 3600 s: keys go at `clip.inPoint + offset`.

## 2. Start from the previous reel's project
The editor reuses one project per reel (`D:\Assets\04_Projects\Premiere_Pro\anan_reel_NN.prproj`) with
the BG grid nest, the Adjustment Layer item, SFX and stock already imported. Do the same:
1. `app.project.save()`, then copy the newest `anan_reel_NN.prproj` to `anan_reel_<new>.prproj` (ask the
   user to open the copy, or `open_project` it), so the old reel stays untouched.
2. Make a new sequence from the new A-roll (`createNewSequenceFromClips(name, [item], bin)`), check that it's
   2160x3840 / 25 fps, and remove the auto-placed clips.
3. Put the **BG** nest on V1 for the whole length (`overwriteClip` of the BG sequence's project item; trim
   the end to the reel's length).
4. If there's no Adjustment Layer item in the project, ask the user for one (File > New > Adjustment Layer).
   Scripts can't create one.

## 3. A-roll: cuts, Lumetri, punch-ins
- Cutting: transcribe (`scripts/transcribe_bn.py`), then cut every pause and retake down to tight jump
  cuts (gaps under ~0.15 s between phrases). Use QE razor on V2/A1 (`razor_clip` reports success and
  does nothing), then ripple. Keep video and audio cut points identical.
- **Lumetri**: the editor clicks *Auto Tone* in Basic Correction. Add "Lumetri Color" with QE
  `addVideoEffect(qe.project.getVideoEffectByName("Lumetri Color"))`, then list
  `comp.properties[i].displayName` to find Exposure / Contrast / Highlights / Shadows / Whites / Blacks /
  Saturation, and set the reel-88 values (+0.44, +7.8, −15.9, −20.7, +0.8, −7.5, 98). Read them back. If
  the names aren't exposed, tell the user to Paste Attributes from one graded clip. Don't guess indices.
- **Punch-in** (emphasis word): an Adjustment Layer on the track above the A-roll, trimmed to the
  phrase; Transform Scale 100 → 125–142 over 0.3–0.4 s at the word, Position shifted toward the face
  (e.g. [0.64, 0.64]). Hold, then cut back to 100 on the next cut.
- **Slow push**: Transform Scale 100 → 113 over ~0.6 s, hold, back to 100 over ~0.8 s (2.5–4 s window).
- Bezier keys (`setInterpolationTypeAtKey(t, 5, true)`). Read `getValueAtTime` back after keying.

## 4. Text clips (PNG from render_text.py)
- Render: `python scripts/render_text.py spec.json <reel folder>\text` (full-frame 2160x3840 transparent
  PNGs, positioned already). Import them to a bin "TEXT_<reel>".
- Place each PNG with `pi.setInPoint(0,4); pi.setOutPoint(dur,4)` → `track.overwriteClip(pi, start)` →
  clear in/out. Stills placed without that come in at the default still length and overwrite neighbours.
- One word = one clip on its own track (V5, V6, V7...), each starting on its spoken word and **all ending
  together** at the phrase end, so the stack builds word by word and disappears at once.
- **Whip-in from the right** (the editor's Transform keys): add Transform, Position key at clip start
  [1.37, 0.5] → at +0.12 s (3 frames) [0.5, 0.5]. Exit: either a cut, or Position → [−0.58, 0.5] over
  0.12 s at the end (used on "FREE").
- Counters ("$5" → "$5 x" → "$5 x2" → "$7" → "$10"): one PNG per state, butted end to start on one track.

## 5. B-roll cards and circle headshot
- First try the editor's effects: QE `getVideoEffectByName("Stroke")` and `("Rounded Crop")` (Impact
  plugins). If either returns null, bake the card instead: `scripts/make_card.py` (ProRes 4444; set alpha
  interpretation to straight, `fi.alphaUsage = 1`).
- Entry: Motion Scale from ~55% of final to final over 0.25–0.8 s, Opacity 0 → 100 over ~0.2 s. Two cards
  = top card at y ≈ 0.27, bottom card at y ≈ 0.62 of the frame (normalised Motion position).
- Hook cards: add Transform; Position y from −0.89 → 0.5 over 0.36 s with Rotation 9° → 0°; hold;
  exit x → 1.0–1.6 with Rotation −4° over ~0.5 s. Each with gun-scope-zoom (−4 dB).
- Circle headshot: `make_card.py <A-roll> out.mov --circle --ss <source in> --t <len>`, placed top-centre
  (y ≈ 0.2), sliding in from x −0.27 → 0.31 over 0.3 s with a whoosh-vortex (−4 dB). Cards go under it.
- Full-screen stock between talking parts goes straight on V2 (no card) with a Light Leak on the cut.

## 6. Transitions (Impact)
- QE: `qeItem.addTransition(qe.project.getVideoTransitionByName("Light Leak"), false, "00:00:00:15")`
  (0.6 s; the editor uses 0.3–1.2 s). Zoom Blur at frame 0: `getVideoTransitionByName("Zoom Blur")`.
- The MCP `apply_transition` is broken. If QE returns null for an Impact name, list
  `qe.project.getVideoTransitionList()` to find the exact name, or fall back to
  `E:\Anan\Assets\Premiere_AE_Pack\overlays\light_leak_warm_screen_blend.png` on a track above (Screen
  blend, 0.3–0.5 s fade in/out) and say so.

## 7. Sound
- Volume writes: `raw = 10^((dB-15)/20)` on `Volume > Level` (MCP `set_clip_volume` writes silence).
- Voice and music gains are MEASURED per reel (`mix_levels.py`, reelkit auto_mix): voice -15 LUFS, music bed 10 LU under
  (SKILL.md section 15). The old fixed "voice +3 / music -22..-27 dB" left the bed too low (user, 8-11-2026). Music: 2 s fade at the end (Constant Power / "Custom Fade" audio transition, or two volume keys).
- SFX on A2–A4, per event (see style.md "Sound" for the pairings). Long sounds (whoosh-vortex ~3 s,
  whoosh-motion 8 s) must be trimmed before placing: set the project item's out point first, as for
  stills, or they erase the next sound on that track.

## 8. Verify
- Export frames with QE `qeSeq.exportFramePNG(tc, pathWithoutExt)` (≤ 4 per call) at: frame 0, each text
  stack's last frame, each card entry midpoint, the map/counter beat, the CTA. Build a sheet with
  `scripts/contact_sheet.py` style tiles and look at it. Check: text inside the frame, no word covering
  the face, Bangla rendered correctly (vowel signs in place), no black frames between cuts (1-frame
  gaps), cards not see-through.
- You can't hear the mix: say so, and list the SFX you placed with times.

## 9. Bulk pipeline (built on reel 1 of 2-11-2026, works end to end)
1. `scripts/phrases_bn.py voice.wav rN_ph.json` - phrase-by-phrase transcript with exact phrase times
   (whole-file Whisper drops long stretches of Bangla). Then a cut list `rN_cuts.json`: every phrase
   padded 0.08 s / 0.12 s, false starts dropped, `tl` = new timeline time.
2. Copy `assets/plan_template.py` to `plan_rN.py`; write the beats with `T(phrase, fraction)`. It writes
   `rN_ae.json` (AE batch: text layers sized to fit with real font metrics, whip-in keys) and
   `rN_prem.json`. Send the AE batch from the file (the node client in the plan's folder, or ae_do),
   save the .aep, then in Premiere:
   `var BUILD_DATA="E:/.../rN_prem.json"; $.evalFile(".../scripts/jsx/build_reel.jsx");`
   It clears and rebuilds the whole sequence, so re-running after a plan change is safe.
3. Premiere 26 quirks found: `app.project.sequences` counts with `numSequences` (numItems is undefined);
   a Dynamic Link item is named `<comp>/<file>.aep`; Impact Stroke defaults to a thin dark line - set
   Size 24 and `Color.setColorValue(255,255,255,255,true)` (the editor's cards: 22-26, white).
4. Hook flying cards: ~900 px wide at chest height (y 0.66-0.80), never over the face.

## 10. News / article cards (reel 5 of 2-11-2026)
When he talks about a real event, show the real coverage: WebSearch the event, confirm his numbers match the
reporting, then capture each article with headless Edge into `E:\Anan\Assets\news\`:
`msedge --headless=new --disable-gpu --hide-scrollbars --user-data-dir=<fresh dir per page> --window-size=1080,1500 --screenshot=E:/Anan/Assets/news/<name>.png <url>`
- Needs the Bash sandbox off (news sites fail the TLS handshake inside it) - the user approves the prompt.
- Keep the flags minimal (--virtual-time-budget / --force-device-scale-factor made it write nothing) and use a
  forward-slash output path (a `\$n` path wrote a literal "news$n.png").
- Paywalled/blocked pages (Business Standard: "Access Denied") - drop them.
- A cookie modal darkens the page: divide it back out (white measured 89 -> v / (89/253)).
- Full-page shots are unreadable on a phone. Build a tight card: the outlet's logo bar stacked over the
  headline, the headline padded 40 px inside a 10 px red (#E8141C) rounded box; show it ~1950 px wide.

## 11. Lessons from reel 1 of 3-11-2026 (first web-viral-style reel)
- **New batch project:** the user starts an empty `Anan_reel_<date>.prproj`. Bring the "Adjustment Layer" item, SFX
  and grid in with `app.project.importSequences(<last batch .prproj>, [<ObjectUID of one reel sequence>])` (the UID is
  the `<Sequence ObjectUID="...">` in the gunzipped XML), then delete that imported sequence. It runs past the MCP
  timeout; wait ~30 s and check the bins.
- **Name collisions:** the imported items include the old batch's `r1_cut1.mov`, `reel 1 (2).MP4` etc. build_reel's
  `item()` now matches by media PATH; still rename the new A-roll item (e.g. `r1_3-11 reel 1 (2).MP4`) and pass that as
  `aroll` - it is found by name.
- **AE file per batch:** `Reel(..., date="3-11-2026")` writes text to `E:/Anan/Assets/AE/reels_<date>.aep` (save the
  empty AE project there first). Rebuild text with `rN_ae_call.json` (deletes the comp first), then re-run build_reel.
- **Behind-the-head lane:** with this framing the head top is at ~900 px, so `BEHIND = 1020` (not 1300): the word sits
  above the hair and only its bottom edge tucks behind. At 1300 the head hid the middle letters.
- **Cut-outs sit above the cards (V7 over V4/V5):** end a hook cut-out before a chest-height card flies in, or the
  body hides the card.
- **Text rides the camera:** V6 is under the V8 adjustment layer, so a 2-step punch (118 -> 134 %) pushes TOP-lane text
  off frame. Put the climax number on the LOW lane under big punches.
- **PNG glass cards must be 100 % opaque:** Premiere composites in linear light, so a 97 %-alpha dark card still shows
  the shirt through it at ~20 %. Keep alpha 255 for the card body (alpha only on the shadow). Premiere locks imported
  PNGs: write a new file name and `changeMediaPath` instead of overwriting.
- **Cut-out files are named by source span** (`cutouts/rN_cut_<src_in>_<dur>.mov`): a re-planned cut-out can never pick up
  a stale file / Premiere item of another moment (reel 1 v3 nearly showed the old "100 %" cut-out at the Telegram CTA).
- **Two AE comps per reel:** `R<n>_TEXT` on V6 (under the cut-outs, zooms with the V8 camera) and `R<n>_FRONT` on V10
  (over the cut-outs, does not zoom). The first rebuild logs one harmless failure: deleting a FRONT comp that isn't there yet.
- **Cut-outs are split at every A-roll cut** they span (one file per piece): a single continuous render keeps playing
  the dropped source gap after the cut and drifts off him (ghost double head at the end of 3-11 reel 1).
- **The last cut ends on the measured end of his voice** (`_speech_end`, RMS > -34 dB): Whisper's last word runs
  ~0.3 s long and he reaches for the camera right after the last word.
- Building all six reels: plan -> `rN_cutouts.json` renders -> AE `rN_ae_call.json` -> save -> `build_reel.jsx` per reel.
  A long reel's build can outlast the MCP timeout; wait ~60 s and read the sequence back instead of re-running.
- **New fonts need an After Effects restart** before AE (and its Dynamic Link renders) can use them. Check first with
  `font.info {postScriptName}`. Save the .aep, quit AE (if a dialog keeps it open, close it), relaunch - it reopens the last
  project. Premiere's Dynamic Link picked the new fonts up without a restart (3-11-2026).
- **Never send a second script while a timed-out build may still be running.** On 3-11-2026 a build that had timed out was
  still saving when the next call also ran `app.project.save()`; the .prproj was written as 1 MB of zero bytes and Premiere
  could not open it ("An unknown error occurred while opening the project"). Recovery: the newest file in
  `D:\Assets\04_Projects\Premiere_Pro\Adobe Premiere Pro Auto-Save\` (check it gunzips), copied over the project, then
  rebuild the reels. Rule: after a timeout, wait and read the sequence back before the next call; only one save per call;
  copy the .prproj to `backups\` after each build session.
- **After a session drop / AE restart, check `ae_project_info` before building.** On 3-11-2026 AE came back with an empty
  Untitled project and a build went into it ("no comp matching ..." for the delete ops is the tell when the comp should
  exist). Scripted `project.open` fails while the untitled one is dirty (hidden "save changes?" prompt) - open the .aep
  from the File menu, answer "Don't Save", then rebuild.

## 12. Pass 1 (cuts only) - 8-11-2026 batch
The user now works in 3 passes: (1) setup + import + cuts only, then the user reviews the cuts and restores
missed voice; (2) the edit, in the vibe they pick per reel (Simple / Casual / Extreme); (3) self-check and fixes.
- Pass 1 tools live in the batch's `edit/` folder (copy them from `E:/Anan/NEW/edit/` of 8-11-2026):
  `make_cuts.py` (reelkit's own cut logic, so pass 2 cuts match; PLAN per reel = drop / keep / keep_fs / trim / flags;
  writes `rN_cuts.json` + `CUT_REVIEW.md`) and `place_cuts.jsx` (`var CUT_REELS=[..]; $.evalFile(...)`: clears the
  sequence, butts the pieces on V1/A1, one marker `P##` per piece).
- **Before re-running place_cuts on a reel, diff the timeline against `rN_cuts.json`.** The user reviews in Premiere
  while later reels are still being cut; on 8-11 reel 6 had hand trims within minutes. Re-laying it would have erased them.
- `setInPoint(32.48)` floors to the frame before: add +1 ms to in AND out points.
- Never put a `//` comment on the same line as a following statement in a .jsx edit (it commented out setOutPoint and every
  piece ran to the end of the raw).
- The detectors over-fire on PARALLEL sentences - check each hit against the meaning: find_retakes flagged
  "...টাকা ইনকাম করতে পারে, তুমি কেন ... টাকা ইনকাম করতে পারবা না" (use `keep={i}`) and two parents' lines
  "উনি বলতাছে আলহামদুলিল্লাহ / উনি বলতাছে মাশাল্লাহ"; false_starts.py flagged "তুমি বাঁইচা আছো, আমি বাঁইচা আছি" (use `keep_fs={i}`).
- When in doubt about a garbled phrase, KEEP it and flag it in CUT_REVIEW.md: the user restores missed voice, but a kept
  aside is a one-click cut for them.
- CUDA here fails (driver older than the runtime) -> Whisper runs on CPU, ~5 min per reel; false_starts.py ~5-10 min per reel.

## 13. Premiere hangs and offline Dynamic Link (8-11-2026, reel 1 pilot)
- **Export check frames in their OWN calls, never in the same call as build_reel or a save.** Twice a build + export
  call hung the MCP bridge (the response never came back; Premiere had to be reopened). What works: build in one call,
  then a call that does `app.project.openSequence(seq.sequenceID)` first, then QE `exportFramePNG` 1-2 frames per call.
- **After a session drop / Premiere reopen the AE comps can show "Media offline"** (all frames red). Purge every
  `*.aep` project item (move to a temp bin, `deleteBin`) after clearing V7/V11, then re-run build_reel: it imports fresh
  comps. Check `isOffline()` on all `.aep` items before exporting frames.
- Blend mode: Opacity component `properties[1]` ("Blend Mode", not `[2]`): 3 Darken, 11 Lighten, **12 Screen**, 14 Add.
- No "Adjustment Layer" item and `add_adjustment_layer` errors -> `importSequences(<last batch .prproj>, [<one reel's
  ObjectUID>])`, keep Adjustment Layer + SFX/GFX/BROLL bins, `deleteSequence` the imported reel, trash the rest.

## 14. Mix + render (8-11-2026)
- Re-level finished reels with `jsx/relevel_pass.jsx` (deltas from `mix_levels.py`), never with a rebuild or `music_pass.jsx`
  `keep:true` (that one rewrites the keys and loses stop-drops).
- Default Hard Limiter on every non-music track (`build_reel` / `limiters_pass.jsx`). No QE access to the master track
  (`getAudioTrackAt(numAudioTracks)` throws).
- Render with `jsx/render_reels.jsx` + `assets/Anan Reel 4K H264 80Mbps.epr` -> .mp4. Not the MooV "H264 Match Source"
  preset (writes .mov 12 Mbps). Reset sequence in/out first. 1-pass VBR on the Software Only renderer (GPU OpenCL crashed AME + froze the PC, amdocl64.dll, 8-11-2026).
  If AME dies, read the Application event log (Get-WinEvent, Id 1000) for the faulting module before retrying.

