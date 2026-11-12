// music_pass.jsx - re-level / swap ONLY the music bed of finished (hand-edited) reels. Touches nothing else.
// var MUSIC_DATA = "E:/.../music_pass.json"; $.evalFile(".../music_pass.jsx");
// json: [{seq, find: "<music file name on the timeline>", parts: [{file (path) | keep: true, gain_db, from?, to?, src_in?}]}]
// - keep: true  -> leave the clip where the user put it, only replace its Level keys
// - file        -> the old music clip is replaced by this file over [from, to] (default: the old clip's span)
// Levels: gain_db constant, 0.5 s fade-in when a part starts after 0 s, 2.5 s fade-out at the reel end
// (0.8 s when a later part takes over). Premiere Level raw = 10^((dB-15)/20).
(function () {
    var f = new File(MUSIC_DATA); f.encoding = "UTF-8"; f.open("r"); var D = eval("(" + f.read() + ")"); f.close();
    var P = app.project, R = P.rootItem, out = [];
    function raw(db) { return Math.pow(10, (db - 15) / 20); }
    function findItem(name, root) { root = root || R; for (var i = 0; i < root.children.numItems; i++) { var c = root.children[i];
        if (c.type == 2) { var r = findItem(name, c); if (r) return r; } else if (c.name == name) return c; } return null; }
    function item(path) { var nm = path.replace(/^.*[\\\/]/, ""); var it = findItem(nm); if (it) return it;
        var b = null; for (var i = 0; i < R.children.numItems; i++) if (R.children[i].name == "SFX") b = R.children[i];
        P.importFiles([path], true, b || R, false); return findItem(nm); }
    function seqByName(n) { var ss = P.sequences; for (var i = 0; i < ss.numSequences; i++) { try { if (ss[i].name == n) return ss[i]; } catch (e) {} } return null; }
    function level(c) { for (var i = 0; i < c.components.numItems; i++) if (c.components[i].displayName == "Volume") {
        var k = c.components[i]; for (var j = 0; j < k.properties.numItems; j++) if (k.properties[j].displayName == "Level") return k.properties[j]; } return null; }
    function keyLevel(c, keys) { var p = level(c); if (!p) return false; p.setTimeVarying(false); p.setTimeVarying(true);
        for (var i = 0; i < keys.length; i++) { var kt = c.inPoint.seconds + (keys[i][0] - c.start.seconds); p.addKey(kt); p.setValueAtKey(kt, raw(keys[i][1]), true); } return true; }
    for (var s = 0; s < D.length; s++) {
        var d = D[s], S = seqByName(d.seq); if (!S) { out.push(d.seq + ": no sequence"); continue; }
        var mt = -1, mc = null;
        for (var a = 0; a < S.audioTracks.numTracks && !mc; a++) { var cl = S.audioTracks[a].clips;
            for (var k = 0; k < cl.numItems; k++) { var c = cl[k], nm = ""; try { nm = c.projectItem.name; } catch (e) {}
                if (nm == d.find && c.end.seconds - c.start.seconds > 20) { mc = c; mt = a; break; } } }
        if (!mc) { out.push(d.seq + ": music clip not found"); continue; }
        var T = S.audioTracks[mt], s0 = mc.start.seconds, e0 = mc.end.seconds, before = 0;
        for (var a2 = 0; a2 < S.audioTracks.numTracks; a2++) before += S.audioTracks[a2].clips.numItems;
        var parts = d.parts, made = [];
        if (parts.length == 1 && parts[0].keep) {
            keyLevel(mc, [[s0, parts[0].gain_db], [Math.max(s0, e0 - 2.5), parts[0].gain_db], [e0 - 0.04, -60]]);
            made.push("kept " + d.find + " " + s0.toFixed(1) + "-" + e0.toFixed(1) + " @" + parts[0].gain_db + "dB");
        } else {
            mc.remove(false, false);
            for (var p = 0; p < parts.length; p++) {
                var pt = parts[p], a0 = pt.from !== undefined ? pt.from : s0, b0 = pt.to !== undefined ? pt.to : e0, it = item(pt.file);
                if (!it) { made.push("import failed " + pt.file); continue; }
                it.setInPoint(pt.src_in || 0, 4); it.setOutPoint((pt.src_in || 0) + (b0 - a0), 4);
                T.overwriteClip(it, a0); it.clearInPoint(4); it.clearOutPoint(4);
                var nc = null; for (var k2 = 0; k2 < T.clips.numItems; k2++) if (Math.abs(T.clips[k2].start.seconds - a0) < 0.03) nc = T.clips[k2];
                if (!nc) { made.push("place failed " + it.name); continue; }
                var last = p == parts.length - 1, fo = last ? 2.5 : 0.8, keys = [];
                if (a0 > 0.05) { keys.push([a0, -60]); keys.push([a0 + 0.5, pt.gain_db]); } else keys.push([a0, pt.gain_db]);
                keys.push([b0 - fo, pt.gain_db]); keys.push([b0 - 0.04, -60]);
                keyLevel(nc, keys); made.push(it.name + " " + a0.toFixed(1) + "-" + b0.toFixed(1) + " @" + pt.gain_db + "dB");
            }
        }
        var after = 0; for (var a3 = 0; a3 < S.audioTracks.numTracks; a3++) after += S.audioTracks[a3].clips.numItems;
        out.push(d.seq + " [A" + (mt + 1) + "]: " + made.join(" | ") + "  (audio clips " + before + " -> " + after + ")");
    }
    P.save();
    return out.join("\n");
})();
