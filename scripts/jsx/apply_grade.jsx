// apply_grade.jsx - apply the standard Lumetri grade (references/grade/*.json) to the A-roll clips of sequences.
// var GRADE = "C:/.../references/grade/anan_warm_pop.json"; var GRADE_SEQS = ["Reel_1_2-11", ...]; var GRADE_TRACK = 1;
// $.evalFile(".../apply_grade.jsx");
// Only Lumetri Color on clips of GRADE_TRACK (0-based; V2 = 1) is touched: added if missing, recipe values set.
// Optional: GRADE_SKIP = {"<seq>": [start seconds, ...]} - clips the user graded by hand are left alone;
//           GRADE_ALSO = "_cut\d+\.mov$" - also grade clips with matching names on ANY track (presenter cut-outs,
//           which are cut from ungraded footage and must match the graded A-roll under them).
// Lumetri repeats display names (Basic / Creative / HSL), so recipe keys are "Name" = 1st occurrence, "Name#2" = 2nd...
// (Basic: Temperature, Tint, Saturation, Exposure, Contrast, Highlights, Shadows, Whites, Blacks;
//  Creative: Faded Film, Sharpen, Vibrance, Saturation#2; Vignette: Amount, Midpoint, Roundness, Feather.)
(function () {
    var f = new File(GRADE); f.encoding = "UTF-8"; f.open("r"); var G = eval("(" + f.read() + ")"); f.close();
    app.enableQE();
    var P = app.project, out = [], TPS = 254016000000, trk = (typeof GRADE_TRACK == "number") ? GRADE_TRACK : 1;
    function seqByName(n) { var ss = P.sequences; for (var i = 0; i < ss.numSequences; i++) { try { if (ss[i].name == n) return ss[i]; } catch (e) {} } return null; }
    for (var s = 0; s < GRADE_SEQS.length; s++) {
        var S = seqByName(GRADE_SEQS[s]); if (!S) { out.push(GRADE_SEQS[s] + ": not found"); continue; }
        P.openSequence(S.sequenceID); var Q = qe.project.getActiveSequence().getVideoTrackAt(trk);
        var skip = (typeof GRADE_SKIP == "object" && GRADE_SKIP[S.name]) || [], also = (typeof GRADE_ALSO == "string") ? new RegExp(GRADE_ALSO) : null;
        var jobs = [], cl = S.videoTracks[trk].clips, n = 0, added = 0, skipped = 0, miss = {};
        for (var c0 = 0; c0 < cl.numItems; c0++) jobs.push([trk, cl[c0]]);
        if (also) for (var vt = 0; vt < S.videoTracks.numTracks; vt++) { if (vt == trk) continue; var xc = S.videoTracks[vt].clips;
            for (var xi = 0; xi < xc.numItems; xi++) { try { if (also.test(xc[xi].projectItem.name)) jobs.push([vt, xc[xi]]); } catch (e) {} } }
        for (var c = 0; c < jobs.length; c++) {
            var clip = jobs[c][1], lum = null, jt = jobs[c][0], hand = false;
            for (var sk = 0; sk < skip.length; sk++) if (jt == trk && Math.abs(clip.start.seconds - skip[sk]) < 0.03) hand = true;
            if (hand) { skipped++; continue; }
            Q = qe.project.getActiveSequence().getVideoTrackAt(jt);
            for (var k = 0; k < clip.components.numItems; k++) if (clip.components[k].displayName == "Lumetri Color") lum = clip.components[k];
            if (!lum) { // add it through QE (match the QE item by start time)
                for (var q = 0; q < Q.numItems; q++) { var it = Q.getItemAt(q);
                    if (it && it.type != "Empty" && Math.abs(Number(it.start.ticks) / TPS - clip.start.seconds) < 0.03) { it.addVideoEffect(qe.project.getVideoEffectByName("Lumetri Color")); added++; break; } }
                for (k = 0; k < clip.components.numItems; k++) if (clip.components[k].displayName == "Lumetri Color") lum = clip.components[k];
                if (!lum) continue;
            }
            var seen = {};
            for (var p = 0; p < lum.properties.numItems; p++) {
                var pr = lum.properties[p], dn = pr.displayName; if (!dn) continue;
                seen[dn] = (seen[dn] || 0) + 1; var key = seen[dn] == 1 ? dn : dn + "#" + seen[dn];
                if (G.lumetri[key] !== undefined) { try { pr.setValue(G.lumetri[key], true); } catch (e) { miss[key] = 1; } }
            }
            n++;
        }
        var ms = []; for (var m in miss) ms.push(m);
        out.push(S.name + ": graded " + n + " clips (V" + (trk + 1) + (also ? " + matching" : "") + ")" + (skipped ? ", left " + skipped + " hand-graded" : "") + (added ? " (Lumetri added to " + added + ")" : "") + (ms.length ? " | could not set: " + ms.join(",") : ""));
    }
    P.save();
    return out.join("\n");
})();
