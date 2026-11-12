// relevel_pass.jsx - re-balance a finished (possibly hand-edited) reel's audio WITHOUT touching its shape.
// var RELEVEL = [{seq, music: "<music file name>", music_delta_db, voice_delta_db}]; $.evalFile(".../relevel_pass.jsx");
// Every Level key (or the static Level) is multiplied by 10^(delta/20): the music clip gets music_delta_db, every other
// audio clip (A-roll voice + all SFX) gets voice_delta_db, so the SFX keep their balance against the voice and every
// fade, stop-drop and user tweak survives. Deltas come from mix_levels.py (new gain - gain the reel was built with).
(function () {
    var P = app.project, out = [];
    function seqByName(n) { var ss = P.sequences; for (var i = 0; i < ss.numSequences; i++) { try { if (ss[i].name == n) return ss[i]; } catch (e) {} } return null; }
    function level(c) { for (var i = 0; i < c.components.numItems; i++) if (c.components[i].displayName == "Volume") {
        var k = c.components[i]; for (var j = 0; j < k.properties.numItems; j++) if (k.properties[j].displayName == "Level") return k.properties[j]; } return null; }
    function scale(c, f) {
        var p = level(c); if (!p) return 0;
        if (p.isTimeVarying()) { var ks = p.getKeys(); if (ks && ks.length) { for (var i = 0; i < ks.length; i++) p.setValueAtKey(ks[i], p.getValueAtKey(ks[i]) * f, true); return ks.length; } }
        p.setValue(p.getValue() * f, true); return 1;
    }
    for (var s = 0; s < RELEVEL.length; s++) {
        var d = RELEVEL[s], S = seqByName(d.seq); if (!S) { out.push(d.seq + ": no sequence"); continue; }
        var fm = Math.pow(10, d.music_delta_db / 20), fv = Math.pow(10, d.voice_delta_db / 20), nm = 0, nv = 0, km = 0;
        for (var a = 0; a < S.audioTracks.numTracks; a++) { var cl = S.audioTracks[a].clips;
            for (var k = 0; k < cl.numItems; k++) { var c = cl[k], name = ""; try { name = c.projectItem.name; } catch (e) {}
                if (name == d.music) { km += scale(c, fm); nm++; } else { scale(c, fv); nv++; } } }
        out.push(d.seq + ": music x" + nm + " (" + km + " keys) " + d.music_delta_db + " dB, voice+sfx x" + nv + " " + d.voice_delta_db + " dB");
    }
    P.save();
    return out.join("\n");
})();
