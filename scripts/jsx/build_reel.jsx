// build_reel.jsx - lay out one Anan reel in Premiere from a data file (made by a reel's plan .py).
// Run in one execute_extendscript call:
//   var BUILD_DATA = "E:/.../rN_prem.json"; $.evalFile("C:/Users/btaza/.claude/skills/anan-reel-edit/scripts/jsx/build_reel.jsx");
// Clears the sequence, then places (track map TK below): V1 grid BG, V2 A-roll cuts (+Lumetri), V3 top cover, V9 camera
// adjustment layers, V4 scene bases (grid copy / full-frame B-roll) with Film Impact in/out transitions, V5-V6 cards (Impact
// Stroke + Rounded Crop, eased entry) or flying hook cards, V7 the AE text comp (Dynamic Link), V8 cut-outs, V10 overlays
// (keyed elements like the green-screen clock, eased pop-in), SFX + music with levels. Returns JSON.
// Learned the hard way (Premiere 26): sequences count with numSequences; addTransition(tr, TRUE, dur)
// = at the clip START (false = end); QE lookups by name always return an object, even for typos, so
// check transitions afterwards via track.transitions[k].name; Premiere keys can't take ease handles from
// script, so smooth moves are written as eased keys every 2 frames.
// CAMERA moves (punch-ins, pushes) go on an ADJUSTMENT LAYER on V9 (TK.cam), above the A-roll AND the cut-outs (user's
// rule): one move for the whole picture, so a cut-out can never drift off the face it was cut from. Needs a project
// item named "Adjustment Layer" (File > New > Adjustment Layer - scripts can't make one).
// ALL animation goes on a Transform effect (user's rule): Motion only holds the static placement, so the
// user can drag a clip anywhere in the Program Monitor and its animation plays from there. Transform
// position is normalised to the CLIP's own frame (before Motion scale): a frame-pixel move F = F/(clipW*scale).
(function () {
    var TPS = 254016000000;
    var f = new File(BUILD_DATA); f.encoding = "UTF-8"; f.open("r"); var D = eval("(" + f.read() + ")"); f.close();
    // Track map (0-based). V1 grid, V2 A-roll, V3 top cover, V4 scene bases / full B-roll, V5-V6 cards, V7 AE text,
    // V8 cut-outs, V9 camera adjustment layers, V10 overlays, V11 AE FRONT comp.
    var TK = { grid: 0, aroll: 1, cover: 2, scene: 3, cardA: 4, text: 6, cut: 7, cam: 8, ovl: 9, front: 10 };
    app.enableQE();
    var P = app.project, R = P.rootItem, rep = { warn: [] };
    function findSeq(n) { var ss = P.sequences, N = ss.numSequences || ss.length || 0; for (var i = 0; i < N; i++) if (ss[i].name == n) return ss[i]; return null; }
    var S = findSeq(D.seq); if (!S) return JSON.stringify({ error: "no sequence " + D.seq });
    P.openSequence(S.sequenceID);
    var Q = qe.project.getActiveSequence();
    function snap(t) { return Math.round(t * 25) / 25; }
    function bin(n) { for (var i = 0; i < R.children.numItems; i++) if (R.children[i].name == n && R.children[i].type == 2) return R.children[i]; return R.createBin(n); }
    function findItem(name, root) {
        root = root || R;
        for (var i = 0; i < root.children.numItems; i++) {
            var c = root.children[i];
            if (c.type == 2) { var r = findItem(name, c); if (r) return r; }
            else if (c.name == name) return c;
        }
        return null;
    }
    function norm(p) { return String(p).replace(/\\/g, "/").toLowerCase(); }
    function findByPath(path, root) { // match the FILE, not the name: an older reel's "r1_cut1.mov" has the same name
        root = root || R; var want = norm(path);
        for (var i = 0; i < root.children.numItems; i++) {
            var c = root.children[i];
            if (c.type == 2) { var r = findByPath(path, c); if (r) return r; }
            else { try { if (norm(c.getMediaPath()) == want) return c; } catch (e) {} }
        }
        return null;
    }
    function item(path) {
        var it = findByPath(path); if (it) return it;
        var f = new File(path);
        if (!f.exists) { rep.warn.push("missing on disk: " + path); return null; }
        P.importFiles([path], true, bin("BROLL"), false);
        it = findByPath(path); if (!it) rep.warn.push("import failed " + path);
        return it;
    }
    function raw(db) { return Math.pow(10, (db - 15) / 20); }
    function comp(clip, name) { for (var i = 0; i < clip.components.numItems; i++) if (clip.components[i].displayName == name) return clip.components[i]; return null; }
    function prop(c, name) { if (!c) return null; for (var i = 0; i < c.properties.numItems; i++) if (c.properties[i].displayName == name) return c.properties[i]; return null; }
    function clipAt(track, t) { for (var i = 0; i < track.clips.numItems; i++) { var c = track.clips[i]; if (Math.abs(c.start.seconds - t) < 0.03) return c; } return null; }
    function clipCovering(track, t) { for (var i = 0; i < track.clips.numItems; i++) { var c = track.clips[i]; if (c.start.seconds <= t + 0.001 && c.end.seconds > t) return c; } return null; }
    function place(track, pi, t, len, srcIn) {
        srcIn = srcIn || 0;
        pi.setInPoint(srcIn, 4); pi.setOutPoint(snap(srcIn + len) + 0.001, 4);
        track.overwriteClip(pi, snap(t));
        pi.clearInPoint(4); pi.clearOutPoint(4);
        return clipAt(track, snap(t));
    }
    // ---- smooth keys: segments [[t, value], ...]; each segment eased (in-out cubic), keys every 2 frames
    function ease(u, kind) { if (kind == "out") return 1 - Math.pow(1 - u, 3); if (kind == "in") return u * u * u;
        return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; }
    function lerp(a, b, u) { if (a instanceof Array) { var o = []; for (var i = 0; i < a.length; i++) o.push(a[i] + (b[i] - a[i]) * u); return o; } return a + (b - a) * u; }
    function skeys(clip, p, list, kind) {
        if (!p) return;
        p.setTimeVarying(true);
        var pts = [];
        for (var i = 0; i < list.length; i++) {
            if (i > 0) {
                var t0 = list[i - 1][0], t1 = list[i][0], v0 = list[i - 1][1], v1 = list[i][1], same = String(v0) == String(v1);
                if (!same) for (var tt = t0 + 0.08; tt < t1 - 0.02; tt += 0.08) pts.push([tt, lerp(v0, v1, ease((tt - t0) / (t1 - t0), list[i][2] || kind))]);
            }
            pts.push([list[i][0], list[i][1]]);
        }
        for (var j = 0; j < pts.length; j++) {
            var kt = clip.inPoint.seconds + (pts[j][0] - clip.start.seconds);
            p.addKey(kt); p.setValueAtKey(kt, pts[j][1], true);
        }
    }
    function qeItem(vi, t) {
        var tr = Q.getVideoTrackAt(vi);
        for (var k = 0; k < tr.numItems; k++) { var q = tr.getItemAt(k); if (q && q.type != "Empty" && Math.abs(Number(q.start.ticks) / TPS - t) < 0.03) return q; }
        return null;
    }
    function fx(vi, t, name) { var q = qeItem(vi, t); if (q) q.addVideoEffect(qe.project.getVideoEffectByName(name)); else rep.warn.push("no qe item V" + (vi + 1) + "@" + t); }
    function tfx(vi, t, clip) { // Transform for animation: uniform scale, its own 180-degree shutter (motion blur)
        fx(vi, t, "Transform"); var c = comp(clip, "Transform"); if (!c) return null;
        for (var i = 0; i < c.properties.numItems; i++) { var p = c.properties[i], n = p.displayName;
            try { if (n == "Uniform Scale") p.setValue(true, true); else if (n.indexOf("Composition") >= 0) p.setValue(false, true);
                  else if (n == "Shutter Angle") p.setValue(180, true); } catch (e) {} }
        return c;
    }
    function grade(lc) { // the standard grade (references/grade): keys "Name" = 1st occurrence, "Name#2" = 2nd (Creative)...
        if (!lc) return; var seen = {};
        for (var p = 0; p < lc.properties.numItems; p++) { var pr = lc.properties[p], dn = pr.displayName; if (!dn) continue;
            seen[dn] = (seen[dn] || 0) + 1; var key = seen[dn] == 1 ? dn : dn + "#" + seen[dn];
            if (D.lumetri[key] !== undefined) { try { pr.setValue(D.lumetri[key], true); } catch (e) {} } }
    }
    function trans(vi, t, name, frames, atStart) {
        var q = qeItem(vi, t); if (!q) { rep.warn.push("no item for " + name + "@" + t); return; }
        q.addTransition(qe.project.getVideoTransitionByName(name), atStart, "00:00:00:" + (frames < 10 ? "0" : "") + frames);
    }
    // ---- tracks
    var needV = (D.ae && D.ae.front) ? TK.front + 1 : TK.ovl + 1, needA = 8;
    if (S.videoTracks.numTracks < needV || S.audioTracks.numTracks < needA)
        Q.addTracks(Math.max(0, needV - S.videoTracks.numTracks), S.videoTracks.numTracks, Math.max(0, needA - S.audioTracks.numTracks), 1, S.audioTracks.numTracks, 0, 0);
    for (var v = 0; v < S.videoTracks.numTracks; v++) for (var c = S.videoTracks[v].clips.numItems - 1; c >= 0; c--) S.videoTracks[v].clips[c].remove(false, false);
    for (var a = 0; a < S.audioTracks.numTracks; a++) for (var c2 = S.audioTracks[a].clips.numItems - 1; c2 >= 0; c2--) S.audioTracks[a].clips[c2].remove(false, false);
    var V = S.videoTracks, A = S.audioTracks, TF = D.trans_frames || 20;
    // ---- V2 A-roll
    var ar = findItem(D.aroll);
    for (var i = 0; i < D.cuts.length; i++) { var k = D.cuts[i]; place(V[TK.aroll], ar, k.tl, k.src_out - k.src_in, k.src_in); }
    var voiceA = -1; for (a = 0; a < A.numTracks; a++) if (A[a].clips.numItems > 0) { voiceA = a; break; }
    rep.voiceTrack = voiceA + 1; rep.arollClips = V[TK.aroll].clips.numItems;
    for (i = 0; i < A[voiceA].clips.numItems; i++) { var vp = prop(comp(A[voiceA].clips[i], "Volume"), "Level"); if (vp) vp.setValue(raw(D.voice_db), true); }
    // cuts with mute:true (11-11-2026): silent A-roll filler under a full-screen insert (TTS correction) - voice clip disabled
    for (i = 0; i < D.cuts.length; i++) if (D.cuts[i].mute) { var mc0 = clipAt(A[voiceA], snap(D.cuts[i].tl)); if (mc0) mc0.disabled = true; else rep.warn.push("mute: no voice clip @" + D.cuts[i].tl); }
    for (i = 0; i < V[TK.aroll].clips.numItems; i++) {
        var ac = V[TK.aroll].clips[i]; fx(TK.aroll, ac.start.seconds, "Lumetri Color");
        grade(comp(ac, "Lumetri Color"));
    }
    // ---- JUMP-CUT COVER (user 9-11-2026: "cuts feel jittery, put something over them"): at every real jump (source gap)
    // the framing alternates between D.jump.scales (face-centred, on the A-roll's own Transform), each new framing settles
    // in from +4% over 6 frames, and a short D.jump.trans (Zoom Blur, 4 f) sits on the cut. Clips under a burst cut-out
    // stay at 100 so the cut-out keeps matching his face; no transition on a cut inside a cut-out span.
    var J = D.jump; rep.jumps = 0;
    if (J && D.cuts.length > 1) {
        var CO = D.cutouts || [], jst = 0;
        var inCO = function (a, b) { for (var q = 0; q < CO.length; q++) if (a < CO[q].t1 + 0.1 && b > CO[q].t0 - 0.1) return true; return false; };
        for (i = 0; i < D.cuts.length; i++) {
            var cc = D.cuts[i], isJump = i > 0 && (cc.src_in - D.cuts[i - 1].src_out) > 0.08, t0j = snap(cc.tl);
            var t1j = snap(cc.tl + cc.src_out - cc.src_in);
            if (isJump) jst = 1 - jst;
            var sj = inCO(t0j, t1j) ? 100 : J.scales[jst], acj = clipCovering(V[TK.aroll], t0j + 0.02);
            if (!acj) continue;
            if (sj != 100 || isJump) {
                var tj = tfx(TK.aroll, acj.start.seconds, acj);
                if (tj) {
                    var jfy = 0.36, ky = [], kp = [], ss = (isJump && !inCO(t0j, t1j)) ? [[t0j, sj + 4], [t0j + 0.24, sj]] : [[t0j, sj]];
                    for (var jj = 0; jj < ss.length; jj++) { var s1 = ss[jj][1] / 100, jlim = (s1 - 1) / 2;
                        var jpy = Math.max(0.5 - jlim, Math.min(0.5 + jlim, jfy - (jfy - 0.5) * s1));
                        ky.push([ss[jj][0], ss[jj][1]]); kp.push([ss[jj][0], [0.5, jpy]]); }
                    if (ky.length > 1) { skeys(acj, prop(tj, "Scale Height"), ky, "out"); skeys(acj, prop(tj, "Position"), kp, "out"); }
                    else { prop(tj, "Scale Height").setValue(ky[0][1], true); prop(tj, "Position").setValue(kp[0][1], true); }
                }
            }
            if (isJump && J.trans && !inCO(t0j - 0.2, t0j + 0.2)) { trans(TK.aroll, acj.start.seconds, J.trans, J.frames || 4, true); rep.jumps++; }
        }
    }
    function applyPunch(cl, pu, vi) { // eased scale + face-centred position, on a Transform (Motion stays free)
        var mo = tfx(vi, cl.start.seconds, cl), sk = [], pk = [];
        for (var j = 0; j < pu.keys.length; j++) {
            var s = pu.keys[j][1] / 100, fy = pu.fy || 0.36, fxx = pu.fx || 0.5;
            var py = fy - (fy - 0.5) * s, px = fxx - (fxx - 0.5) * s, lim = (s - 1) / 2;
            py = Math.max(0.5 - lim, Math.min(0.5 + lim, py)); px = Math.max(0.5 - lim, Math.min(0.5 + lim, px));
            sk.push([pu.keys[j][0], pu.keys[j][1]]); pk.push([pu.keys[j][0], [px, py]]);
        }
        skeys(cl, prop(mo, "Scale Height"), sk, "inout"); skeys(cl, prop(mo, "Position"), pk, "inout");
    }
    var adjItem = findItem(D.adjustment || "Adjustment Layer");
    if (!adjItem) rep.warn.push("no 'Adjustment Layer' project item - camera moves skipped (File > New > Adjustment Layer)");
    var PS = D.punches.slice(0).sort(function (a, b) { return a.keys[0][0] - b.keys[0][0]; });
    for (i = 0; i < PS.length && adjItem; i++) {
        var pu = PS[i], k0 = snap(pu.keys[0][0]), host = clipCovering(V[TK.aroll], k0 + 0.01);
        if (!host) { rep.warn.push("no aroll at punch " + k0); continue; }
        var pend = host.end.seconds; if (i + 1 < PS.length) pend = Math.min(pend, snap(PS[i + 1].keys[0][0]));
        var ac2 = place(V[TK.cam], adjItem, k0, pend - k0, 0); if (!ac2) { rep.warn.push("camera clip failed @" + k0); continue; }
        applyPunch(ac2, pu, TK.cam);
    }
    rep.cameraMoves = V[TK.cam].clips.numItems;
    if (V[TK.aroll].clips.numItems) trans(TK.aroll, V[TK.aroll].clips[0].start.seconds, D.open_transition || "Zoom Blur", TF, true);
    // ---- V1 grid
    var grid = item(D.grid);
    var g = place(V[TK.grid], grid, 0, D.total, 0); if (g) prop(comp(g, "Motion"), "Scale").setValue(D.grid_scale, true);
    // ---- scenes
    var TIN = D.trans_in || ["Light Leak", "Blur Dissolve", "Light Sweep", "Directional Blur", "Push", "Flash"];
    var ti = 0;
    for (i = 0; i < D.scenes.length; i++) {
        var sc = D.scenes[i], len = sc.t1 - sc.t0;
        var tin = sc.tin || TIN[ti++ % TIN.length], tout = sc.tout || "Blur Dissolve";
        if (sc.type == "cards" && !sc.no_base) { var gb = place(V[TK.scene], grid, sc.t0, len, 0);
            if (gb) { prop(comp(gb, "Motion"), "Scale").setValue(D.grid_scale, true); trans(TK.scene, snap(sc.t0), tin, TF, true); trans(TK.scene, snap(sc.t0), tout, TF, false); } }
        for (j = 0; j < sc.items.length; j++) {
            var it = sc.items[j], pi = item(it.file); if (!pi) continue;
            var tr = sc.type == "full" ? TK.scene : TK.cardA + (j % 2);
            var at = snap(sc.type == "full" ? sc.t0 : it.at), ln = snap((it.t1 || sc.t1)) - at;
            var pc = place(V[tr], pi, at, ln, it.src_in || 0); if (!pc) { rep.warn.push("place failed " + it.file); continue; }
            var m = comp(pc, "Motion");
            if (sc.type == "full") { prop(m, "Scale").setValue(it.scale, true); if (it.rot) prop(m, "Rotation").setValue(it.rot, true);
                // it.blend: Premiere's Opacity > Blend Mode enum, measured 8-11-2026: 3 Darken, 11 Lighten, 12 Screen, 14 Add
                if (it.blend) { var opc = comp(pc, "Opacity"); if (opc && opc.properties.numItems > 1) opc.properties[1].setValue(it.blend, true); }
                if (tin != "none") trans(TK.scene, at, tin, TF, true); if (tout != "none") trans(TK.scene, at, tout, TF, false); continue; }
            if (!it.bare) { // PNG glass cards carry their own frame; footage cards get a thin screen-space border
            // Added Stroke then Rounded Crop so Rounded Crop sits ABOVE (BEFORE) Stroke in processing stack
            fx(tr, at, "Stroke"); fx(tr, at, "Rounded Crop");
            var rcc = comp(pc, "Rounded Crop");
            if (rcc) {
                var r_prop = prop(rcc, "Roundness"); if (r_prop) r_prop.setValue(35, true);
                var l_prop = prop(rcc, "Left"); if (l_prop) l_prop.setValue(3, true);
                var rt_prop = prop(rcc, "Right"); if (rt_prop) rt_prop.setValue(3, true);
                var t_prop = prop(rcc, "Top"); if (t_prop) t_prop.setValue(3, true);
                var b_prop = prop(rcc, "Bottom"); if (b_prop) b_prop.setValue(3, true);
            }
            var stc = comp(pc, "Stroke"), spx = D.stroke_px || 16;
            if (stc) { // spx on screen whatever the card's scale (Impact Stroke is drawn before Motion scale)
                var sz = prop(stc, "Size"), col = prop(stc, "Color");
                if (sz) sz.setValue(Math.max(2, Math.min(120, spx / (it.scale / 100))), true);
                if (col) try { col.setColorValue(D.stroke_alpha || 255, 255, 255, 255, true); } catch (e) {} } }
            var end = at + ln, x0 = it.x || 0.5;
            // Motion = where the card sits (drag it freely); Transform = how it moves
            prop(m, "Position").setValue([x0, it.y], true); prop(m, "Scale").setValue(it.scale, true);
            if (it.rot) prop(m, "Rotation").setValue(it.rot, true);
            var tf = tfx(tr, at, pc); if (!tf) continue;
            var op = prop(tf, "Opacity");
            if (sc.type == "cards") {
                if (it.overflow) {
                    skeys(pc, op, [[at, 0], [at + 0.25, 100], [end - 0.25, 100], [end, 0, "in"]], "out");
                } else {
                    skeys(pc, prop(tf, "Scale Height"), [[at, 55], [at + 0.6, 100], [end - 0.35, 100], [end, 85, "in"]], "out");
                    skeys(pc, op, [[at, 0], [at + 0.3, 100], [end - 0.3, 100], [end, 0, "in"]], "out");
                }
            } else { // fly: slide in from its own side at chest height with a tilt (never crosses the face), leave the other way
                var cw = (it.w || 1920) * it.scale / 100, dx = 2160 * 0.95 / cw, r0 = x0 < 0.5 ? -9 : 9;
                var from = x0 < 0.5 ? 0.5 - dx : 0.5 + dx, to = x0 < 0.5 ? 0.5 + dx : 0.5 - dx;
                skeys(pc, prop(tf, "Position"), [[at, [from, 0.5]], [at + 0.6, [0.5, 0.5]], [end - 0.5, [0.5, 0.5]], [end, [to, 0.5], "in"]], "out");
                skeys(pc, prop(tf, "Rotation"), [[at, r0], [at + 0.6, 0], [end - 0.5, 0], [end, -r0 / 2, "in"]], "out");
            }
        }
    }
    // ---- top cover (user rule): hides the wall / door / curtain rod above the curtain. It lives on its OWN track
    // between the A-roll and the scenes, one clip per continuous A-roll span: the scenes on V4 fade in and out OVER a
    // covered A-roll. (Until 4-11-2026 it sat in the gaps between scenes on the scene track, so every scene's 0.5 s
    // in/out transition showed the uncovered room for ~12 frames.) It fades in with the opening transition.
    if (D.cover) {
        var cvi = item(D.cover);
        if (cvi) {
            var coverStart = (V[TK.aroll].clips.numItems && V[TK.aroll].transitions.numItems) ? snap(V[TK.aroll].transitions[0].end.seconds) : 0;
            place(V[TK.cover], cvi, coverStart, snap(D.total - coverStart), 0);
            rep.coverPieces = 1;
        }
    }
    // ---- V7 cut-outs of the presenter (cutout_rvm.py), above the AE text; same punch keys as the A-roll
    var co = D.cutouts || [];
    for (i = 0; i < co.length; i++) {
        var cu = co[i], cpi = item(cu.file); if (!cpi) continue;
        try { var fi = cpi.getFootageInterpretation(); fi.alphaUsage = 1; cpi.setFootageInterpretation(fi); } catch (e) {}
        var cc = place(V[TK.cut], cpi, cu.t0, snap(cu.t1) - snap(cu.t0), 0); if (!cc) { rep.warn.push("cutout failed " + cu.file); continue; }
        // no own keys: the camera adjustment layer on V8 moves it together with the A-roll.
        // Same grade as the A-roll (the cut-out comes from ungraded footage):
        fx(TK.cut, snap(cu.t0), "Lumetri Color"); grade(comp(cc, "Lumetri Color"));
    }
    // ---- V9 overlays (keyed elements: clock etc.) - above the camera layer, so they don't zoom with it
    var ov = D.overlays || [];
    for (i = 0; i < ov.length; i++) {
        var o = ov[i], opi = item(o.file); if (!opi) continue;
        var oc = place(V[TK.ovl], opi, o.t0, snap(o.t1) - snap(o.t0), o.src_in || 0); if (!oc) { rep.warn.push("overlay failed " + o.file); continue; }
        if (o.key) { fx(TK.ovl, snap(o.t0), "Ultra Key"); var uk = prop(comp(oc, "Ultra Key"), "Key Color");
            if (uk) try { uk.setColorValue(255, o.key[0], o.key[1], o.key[2], true); } catch (e) { rep.warn.push("key color " + e); } }
        var om = comp(oc, "Motion"), t0 = snap(o.t0), t1 = snap(o.t1);
        prop(om, "Position").setValue([o.x, o.y], true); prop(om, "Scale").setValue(o.scale, true);
        if (o.rot) prop(om, "Rotation").setValue(o.rot, true);
        if (o.blend) { var oop = comp(oc, "Opacity"); if (oop && oop.properties.numItems > 1) oop.properties[1].setValue(o.blend, true); } // 12 = Screen
        var otf = tfx(TK.ovl, t0, oc);
        if (otf && o.plain) { skeys(oc, prop(otf, "Opacity"), [[t0, 0], [t0 + 0.12, 100], [t1 - 0.25, 100], [t1, 0, "in"]], "out"); }
        else if (otf) { skeys(oc, prop(otf, "Scale Height"), [[t0, 0], [t0 + 0.45, 106], [t0 + 0.65, 100, "inout"], [t1 - 0.3, 100], [t1, 0, "in"]], "out");
                   skeys(oc, prop(otf, "Rotation"), [[t0, -12], [t0 + 0.6, 0]], "out"); }
    }
    // ---- audio: strip b-roll audio, then SFX by role, music bed
    for (a = 0; a < A.numTracks; a++) { if (a == voiceA) continue; for (c = A[a].clips.numItems - 1; c >= 0; c--) A[a].clips[c].remove(false, false); }
    var others = []; for (a = 0; a < A.numTracks; a++) if (a != voiceA) others.push(a);
    var roles = { feat: others[0], bed: others[1], extra: others[2], pop: others[3], music: others[4] };
    var missing = [];
    for (i = 0; i < D.sfx.length; i++) {
        var sx = D.sfx[i], si = findItem(sx.file); if (!si) { missing.push(sx.file); continue; }
        var at2 = A[roles[sx.role]];
        si.setInPoint(sx.src_in || 0, 4); si.setOutPoint((sx.src_in || 0) + sx.len, 4);
        at2.overwriteClip(si, snap(sx.t)); si.clearInPoint(4); si.clearOutPoint(4);
        var sc2 = clipAt(at2, snap(sx.t)); if (sc2) { var lv = prop(comp(sc2, "Volume"), "Level"); if (lv) lv.setValue(raw(sx.db), true); }
    }
    var mu = D.music.path ? item(D.music.path) : findItem(D.music.file);
    if (mu) { var mc = place(A[roles.music], mu, 0, D.total, D.music.src_in);
        if (mc) { var ml = prop(comp(mc, "Volume"), "Level"); ml.setTimeVarying(true);
            var kk = [], dr = D.music.drops || [], cv = D.music.curve && D.music.curve.length ? D.music.curve : [[0, 0]];
            // ramp-evening keys (music_curve.py, user 9-11-2026), skipped inside stop-drops and the end fade
            for (j = 0; j < cv.length; j++) { var ct = cv[j][0], busy = ct > D.total - D.music.fade - 0.3;
                for (var q = 0; q < dr.length; q++) if (ct > dr[q][0] - 0.5 && ct < dr[q][1] + 1.5) busy = true;
                if (!busy || j == 0) kk.push([ct, raw(D.music.db + cv[j][1])]); }
            for (j = 0; j < dr.length; j++) // Audio Stop-Drop: dip to silence, slam back on the climax word
                kk.push([dr[j][0] - 0.12, raw(D.music.db)], [dr[j][0], raw(-80)], [dr[j][1] - 0.04, raw(-80)], [dr[j][1], raw(D.music.db + 3)], [dr[j][1] + 1.2, raw(D.music.db)]);
            kk.push([D.total - D.music.fade, raw(D.music.db)], [D.total - 0.04, raw(-60)]);
            if (D.music.until) { // 10-11-2026: bed 1 hands over to D.music2 (sad -> normal): fade out across the crossfade
                var u = D.music.until, xf = (D.music2 && D.music2.xfade) || 1.2, k2 = [];
                for (j = 0; j < kk.length; j++) if (kk[j][0] < u - xf / 2) k2.push(kk[j]);
                k2.push([u - xf / 2, raw(D.music.db)], [u + xf / 2, raw(-60)]); kk = k2; }
            kk.sort(function (a, b) { return a[0] - b[0]; });
            for (j = 0; j < kk.length; j++) { var mt = mc.inPoint.seconds + kk[j][0]; ml.addKey(mt); ml.setValueAtKey(mt, kk[j][1], true); } } }
    else missing.push(D.music.file);
    if (D.music2) { // second bed on the spare audio track, fades in across the crossfade and out at the end
        var m2 = D.music2, mi2 = item(m2.path), xf2 = m2.xfade || 1.2, a0 = snap(Math.max(0, m2.t0 - xf2 / 2));
        // 11-11-2026: m2.until = hand-over to D.music3 (up to 3 beds per reel, user: "change the music by mood")
        var xf3 = (D.music3 && D.music3.xfade) || 1.2, e2 = m2.until ? snap(Math.min(D.total, m2.until + xf3 / 2)) : D.total;
        if (mi2 && others.length > 5) { var mc2 = place(A[others[5]], mi2, a0, snap(e2 - a0), m2.src_in || 0);
            if (mc2) { var ml2 = prop(comp(mc2, "Volume"), "Level"); ml2.setTimeVarying(true);
                var k3 = m2.until ? [[0, raw(-60)], [xf2, raw(m2.db)], [m2.until - xf3 / 2 - a0, raw(m2.db)], [e2 - a0 - 0.04, raw(-60)]]
                                  : [[0, raw(-60)], [xf2, raw(m2.db)], [D.total - a0 - (D.music.fade || 1.5), raw(m2.db)], [D.total - a0 - 0.04, raw(-60)]];
                for (j = 0; j < k3.length; j++) { var mt2 = mc2.inPoint.seconds + k3[j][0]; ml2.addKey(mt2); ml2.setValueAtKey(mt2, k3[j][1], true); } } }
        else missing.push("music2 " + m2.file); }
    if (D.music3) { // third bed, same crossfade-in / end-fade as bed 2
        var m3 = D.music3, mi3 = item(m3.path), a3 = snap(Math.max(0, m3.t0 - xf3 / 2));
        if (mi3 && others.length > 6) { var mc3 = place(A[others[6]], mi3, a3, snap(D.total - a3), m3.src_in || 0);
            if (mc3) { var ml3 = prop(comp(mc3, "Volume"), "Level"); ml3.setTimeVarying(true);
                var k4 = [[0, raw(-60)], [xf3, raw(m3.db)], [D.total - a3 - (D.music.fade || 1.5), raw(m3.db)], [D.total - a3 - 0.04, raw(-60)]];
                for (j = 0; j < k4.length; j++) { var mt3 = mc3.inPoint.seconds + k4[j][0]; ml3.addKey(mt3); ml3.setValueAtKey(mt3, k4[j][1], true); } } }
        else missing.push("music3 " + m3.file); }
    // ---- desaturation spans (10-11-2026, sad beats): key Lumetri Basic "Saturation" on every A-roll / cut-out clip in the span
    var DS = D.desat || [];
    if (DS.length) {
        var base = D.lumetri["Saturation"] !== undefined ? D.lumetri["Saturation"] : 100, tks = [TK.aroll, TK.cut];
        for (var di = 0; di < DS.length; di++) { var d0 = DS[di][0], d1 = DS[di][1], dv = DS[di][2];
            for (var tq = 0; tq < tks.length; tq++) { var cls = V[tks[tq]].clips;
                for (j = 0; j < cls.numItems; j++) { var cl = cls[j], cs = cl.start.seconds, ce = cl.end.seconds;
                    if (ce <= d0 || cs >= d1) continue;
                    var lc = comp(cl, "Lumetri Color"); if (!lc) continue; var sps = [];
                    // Basic Saturation AND Creative Saturation (the warm LUT in Creative re-adds colour otherwise)
                    for (var pp = 0; pp < lc.properties.numItems && sps.length < 2; pp++) if (lc.properties[pp].displayName == "Saturation") sps.push(lc.properties[pp]);
                    if (!sps.length) { rep.warn.push("no Saturation on clip @" + cs); continue; }
                    for (var si2 = 0; si2 < sps.length; si2++) { var sp = sps[si2];
                    var off = cl.inPoint.seconds - cs, ks = [];
                    var bs = si2 == 0 ? base : (D.lumetri["Saturation#2"] !== undefined ? D.lumetri["Saturation#2"] : 100);
                    var sv = function (t) { if (t <= d0 || t >= d1) return bs; var r1 = Math.min(1, (t - d0) / 0.5, (d1 - t) / 0.4); return bs + (dv - bs) * r1; };
                    var pts = [cs, Math.max(cs, d0), Math.min(ce, d0 + 0.5), Math.max(cs, d1 - 0.4), Math.min(ce, d1), ce - 0.01];
                    if (!sp.isTimeVarying()) sp.setTimeVarying(true);
                    for (var q2 = 0; q2 < pts.length; q2++) { var pt = Math.max(cs, Math.min(ce - 0.01, pts[q2])); sp.addKey(pt + off); sp.setValueAtKey(pt + off, sv(pt), true); } } } } }
        rep.desat = DS.length; }
    // ---- safety limiter (8-11-2026): auto-mix lifts the voice 3-8 dB over raws that peak at -1.5 dBFS -> a default Hard
    // Limiter (ceiling -0.1 dB, boost 0) on every audio track except the music bed. QE param writes are normalised strings
    // and do not read back, so the defaults are used as they are. Check the render's true peak (mix_levels / ebur128).
    try { var qs = qe.project.getActiveSequence(), hl = qe.project.getAudioEffectByName("Hard Limiter");
        for (a = 0; a < A.numTracks; a++) { if (a == roles.music || !A[a].clips.numItems) continue;
            var qt = qs.getAudioTrackAt(a), has = false;
            for (var qc = 0; qc < qt.numComponents; qc++) if (String(qt.getComponentAt(qc).name).indexOf("Hard Limiter") >= 0) has = true;
            if (!has) qt.addAudioEffect(hl); } } catch (eL) { missing.push("limiter: " + eL); }
    // ---- V6 AE text (Dynamic Link items are named "<comp>/<file>.aep")
    function purgeProjectItem(item) {
        if (!item) return;
        try {
            var trash = P.rootItem.createBin("__TRASH_" + (new Date()).getTime());
            item.moveBin(trash);
            trash.deleteBin();
        } catch (e) {}
    }
    function findAEItem(name) {
        function search(node) {
            for (var j = 0; j < node.children.numItems; j++) {
                var ch = node.children[j];
                if (ch.type == 2) { var r = search(ch); if (r) return r; }
                else if (ch.name.indexOf(name) !== -1 && !ch.isOffline()) return ch;
            }
            return null;
        }
        return search(R);
    }
    if (D.ae) {
        var aeName = D.ae.comp + "/" + D.ae.aep.replace(/^.*[\\\/]/, "");
        var aeIt = findAEItem(aeName);
        if (!aeIt) {
            P.importAEComps(D.ae.aep, [D.ae.comp], bin("AE"));
            aeIt = findAEItem(aeName);
        }
        if (aeIt && !aeIt.isOffline()) { V[TK.text].overwriteClip(aeIt, 0); rep.aeText = true; } else rep.warn.push("AE comp offline or not found: " + aeName);

        // V10 FRONT comp: words that play during a cut-out (else his body covers them); above the cut-outs on V7
        if (D.ae.front) {
            var frName = D.ae.front + "/" + D.ae.aep.replace(/^.*[\\\/]/, "");
            var frIt = findAEItem(frName);
            if (!frIt) {
                P.importAEComps(D.ae.aep, [D.ae.front], bin("AE"));
                frIt = findAEItem(frName);
            }
            if (frIt && !frIt.isOffline()) { V[TK.front].overwriteClip(frIt, 0); rep.aeFront = true; } else rep.warn.push("AE comp offline or not found: " + frName);
        }
    }
    // ---- report: transitions actually applied (names), sounds present
    rep.transitions = [];
    for (v = 0; v <= TK.scene; v++) { var T2 = V[v].transitions; for (k = 0; k < T2.numItems; k++) rep.transitions.push("V" + (v + 1) + "@" + T2[k].start.seconds.toFixed(1) + " " + T2[k].name); }
    var n = 0; for (a = 0; a < others.length; a++) n += A[others[a]].clips.numItems;
    rep.sfxPlaced = n; rep.sfxPlanned = D.sfx.length + 1; rep.missing = missing; rep.cutouts = V[TK.cut].clips.numItems; rep.overlays = V[TK.ovl].clips.numItems;
    rep.end = Math.round(S.end / TPS * 100) / 100;
    P.save();
    return JSON.stringify(rep);
})();
