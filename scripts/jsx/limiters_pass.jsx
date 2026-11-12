// limiters_pass.jsx - var LIM_SEQ = "Reel_1_...", LIM_MUSIC = "<music file>"; $.evalFile(...). Adds a default Hard Limiter (ceiling -0.1 dB)
// to every audio track of LIM_SEQ that has none, except the music bed (for reels built before build_reel did it itself).
(function () {
    app.enableQE(); var P = app.project, S = null;
    for (var i = 0; i < P.sequences.numSequences; i++) if (P.sequences[i].name == LIM_SEQ) S = P.sequences[i];
    if (!S) return LIM_SEQ + ": no sequence";
    P.openSequence(S.sequenceID);
    var q = qe.project.getActiveSequence(), fx = qe.project.getAudioEffectByName("Hard Limiter"), r = [];
    for (var a = 0; a < S.audioTracks.numTracks; a++) {
        var cl = S.audioTracks[a].clips, music = false;
        for (var k = 0; k < cl.numItems; k++) { try { if (cl[k].projectItem.name == LIM_MUSIC) music = true; } catch (e) {} }
        if (music || !cl.numItems) continue;
        var t = q.getAudioTrackAt(a), has = false;
        for (var c = 0; c < t.numComponents; c++) if (String(t.getComponentAt(c).name).indexOf("Hard Limiter") >= 0) has = true;
        if (!has) { t.addAudioEffect(fx); r.push("A" + (a + 1) + "+"); } else r.push("A" + (a + 1) + "=");
    }
    return LIM_SEQ + ": " + r.join(" ");
})();
