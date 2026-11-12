// render_reels.jsx - queue finished reels in Media Encoder as high-bitrate MP4 (user, 8-11-2026: "export at a higher bitrate, mp4").
// var RENDER = {seqs: ["Reel_1_8-11-2026", ...], out: "E:/Anan/8-11-2026/exports/", names: ["reel 1", ...]}; $.evalFile(".../render_reels.jsx");
// Preset: assets/Anan Reel 4K H264 80Mbps.epr (copy kept in E:/Anan/Assets/presets) = H.264 in .mp4 (exporter NICK_H264),
// match source 2160x3840 @25, VBR 1-pass target 80 / max 100 Mbps, AAC 320 kbps 48 kHz.
// NEVER the "3F3F3F3F_4D6F6F56/H264 Match Source - High bitrate" system preset: that is the QuickTime exporter -> .mov at 12 Mbps.
// Renders on the CPU renderer (qe.project.setRenderer("Mercury Playback Engine Software Only")): on 8-11-2026 the GPU
// (OpenCL) renderer crashed AME inside amdocl64.dll with an IOMMU fault and froze the PC. 2-pass was dropped for the same reason.
// 9-11-2026: GPU (OpenCL, RX 580 8 GB) "finished" 7 reels in 33 min but the PICTURE FROZE 24 s into reel 3 and every
// later reel was that one stuck frame (audio fine, so loudness checks passed). CPU re-render = clean. Keep Software Only;
// after EVERY render run ffmpeg freezedetect (n=0.001:d=2) and look at a 1-frame-per-4-s tile, not just ebur128.
// PRESET FIX 9-11: ADBEVideoBitrateEncoding 1 = CBR (every 8-11 render was CBR); 2 = VBR 1 pass (verified in AMEEncodingLog).
// In/out are reset to the full sequence first (stale out points from older cuts had been left on 5 of 6 reels).
(function () {
    var P = app.project, out = [];
    var preset = RENDER.preset || "E:/Anan/Assets/presets/Anan Reel 4K H264 80Mbps.epr";
    app.enableQE(); try { qe.project.setRenderer(RENDER.renderer || "Mercury Playback Engine Software Only"); } catch (eR) {}
    preset = preset.replace(/\//g, "\\");
    if (!new File(preset).exists) return "preset missing: " + preset;
    function seqByName(n) { for (var i = 0; i < P.sequences.numSequences; i++) if (P.sequences[i].name == n) return P.sequences[i]; return null; }
    app.encoder.launchEncoder();
    for (var k = 0; k < RENDER.seqs.length; k++) {
        var S = seqByName(RENDER.seqs[k]); if (!S) { out.push(RENDER.seqs[k] + ": no sequence"); continue; }
        // RENDER.outs (11-11-2026): the cut length - S.end lags after SFX tails are trimmed, so encode in->out instead of ENTIRE
        S.setInPoint(0); S.setOutPoint(RENDER.outs ? RENDER.outs[k] : S.end / 254016000000);
        var f = RENDER.out.replace(/\//g, "\\") + (RENDER.names ? RENDER.names[k] : S.name) + ".mp4";
        out.push(S.name + " -> " + f + " job " + app.encoder.encodeSequence(S, f, preset, RENDER.outs ? app.encoder.ENCODE_IN_TO_OUT : app.encoder.ENCODE_ENTIRE, 1));
    }
    P.save();
    app.encoder.startBatch();
    return out.join("\n");
})();
