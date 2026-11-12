# Explainer template (Remotion, flat vector) - from reel 5 v2 of 2-11-2026 (Binance hot/cold wallet + bank analogy)
Use when he explains HOW something works. Copy this folder next to the reel's edit folder, then:
- node_modules: copy an installed one (e.g. robocopy from E:\#TECH_RESSOLVE\Shorts_Batch_01\edit\remotion\node_modules,
  it includes Remotion's headless browser) instead of downloading.
- public/: Poppins-ExtraBold.ttf (Assets/Motion_Templates/fonts) and pip.mp4 = the A-roll pieces under the window,
  concatenated + face-cropped (ffmpeg trim/concat/crop, see plan_r5v2.py's beats.json "segs") so lip sync holds.
- beats.json (written by the reel plan): {"duration", "beats": {name: seconds from the window start}, "segs"}.
- Explainer.tsx: blue blueprint grid like the reels, header with the subject's real logo, presenter circle top-right,
  phases that cross-fade on beats; labels never wrap; negated things get a red strike + X on the word he negates.
- `node render.mjs stills 12,238,...` (frames) -> check -> `node render.mjs video` (1080x1920 at scale 2 = 2160x3840 h264).
- In the plan: r.scene("full", X0, X1, [{"file": ".../out/<name>.mp4", "scale": 100, "src_in": 0}]) and NO text,
  overlays or punches inside the window.
- Grade the PiP before rendering so the face matches the graded reel: `ffmpeg -i pip_raw.mp4 -vf "lut3d=file='E\:/Anan/Assets/grade/Anan_Warm_Pop_v2.cube'" -crf 18 public/pip.mp4`
  (references/grade). Re-render to a NEW file name (`OUT=out/<name>_v2.mp4 node render.mjs video`) and swap it into
  Premiere with `projectItem.changeMediaPath(newPath, true)` - Premiere keeps the old file open, and the swap keeps the
  clip's position, trims and transitions.
