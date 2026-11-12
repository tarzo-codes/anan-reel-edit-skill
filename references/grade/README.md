# Standard grade - "Anan Warm Pop v2"

The user's brief: colours pop, the face looks warm and alive. Built Nov 2 2026 on the 2-11-2026 batch (Sony A-roll,
navy curtain, Rec.709) and tested on all five reels.

## Files
| File | What | Where it works |
|---|---|---|
| `anan_warm_pop.json` | the **Lumetri recipe** (numeric sliders) - the master | Premiere, applied by script |
| `Anan_Warm_Pop_v2.cube` | 33^3 LUT fitted from Premiere's own output (mean error 2.9/255 vs Lumetri) | Premiere (Lumetri > Creative > Look > Browse), After Effects, DaVinci, ffmpeg `lut3d` |
Copies of the .cube: `E:\Anan\Assets\grade\`.

## The look (why each value)
- Temperature +10, Tint +2: warm skin, slightly away from magenta (v1's +4 tint read pink).
- Exposure +0.2, Highlights -24: brighter face but cheeks never clip (reel 3's cheek hits R 246).
- Contrast +24, Blacks -20, Shadows +10, Whites +6: deep blacks for pop, open shadows so the face keeps shape.
- Vibrance +30 with Saturation only 104: colour pop comes from VIBRANCE (lifts the dull navy, protects skin);
  more plain saturation pushed skin toward orange (v1: 66% -> 89% skin saturation on reel 3).
- Sharpen 18, light vignette (Amount -0.8): crisper face, eye to the centre. (Not in the LUT - spatial.)
Measured: cheek hue stays 17-22 deg, skin saturation +15-20 points, lightness +2.

## Apply
- New reels: automatic - `reelkit` loads the json, `build_reel.jsx` grades every A-roll clip AND the presenter
  cut-outs (they come from ungraded footage and must match).
- Finished / hand-edited reels: `scripts/jsx/apply_grade.jsx`
  `var GRADE=".../anan_warm_pop.json", GRADE_SEQS=[...], GRADE_TRACK=1, GRADE_SKIP={"<seq>":[start s]}, GRADE_ALSO="_cut\\d+\\.mov$"; $.evalFile(".../apply_grade.jsx")`
  First check for clips the user graded by hand (values that differ from the previous grade) and list them in GRADE_SKIP.
- Anything rendered outside Premiere from the A-roll (explainer PiP, cut-outs made with ffmpeg): run it through the
  .cube (`ffmpeg -vf lut3d=file=...cube`) so faces match.

## Making a new version
Throwaway sequence with 1 s of each reel on V1 -> export frames ungraded -> apply recipe -> export -> compare faces
(crop) + measure cheek HSL (box x 0.40-0.50, y 0.44-0.50 of the frame, darkest quarter dropped) -> adjust -> refit the
.cube from the before/after pairs (3rd-order polynomial colour fit on the frame centres) -> bump the version in the json.
