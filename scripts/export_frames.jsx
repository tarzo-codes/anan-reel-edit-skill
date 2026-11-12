// var EXP={seq:"Reel_2_8-11-2026", tag:"r2x", times:[...]}; $.evalFile(this)  - open the sequence FIRST, then QE frames
(function () {
    var q = null;
    for (var s = 0; s < app.project.sequences.numSequences; s++) if (app.project.sequences[s].name == EXP.seq) q = app.project.sequences[s];
    app.project.openSequence(q.sequenceID);
    app.enableQE();
    var qs = qe.project.getActiveSequence(), out = [];
    function tc(t) { var f = Math.round(t * 25), ss = Math.floor(f / 25), fr = f % 25, mm = Math.floor(ss / 60); ss = ss % 60; return "00;" + (mm < 10 ? "0" : "") + mm + ";" + (ss < 10 ? "0" : "") + ss + ";" + (fr < 10 ? "0" : "") + fr; }
    for (var i = 0; i < EXP.times.length; i++) { qs.exportFramePNG(tc(EXP.times[i]), EXP.dir + EXP.tag + "_" + i); out.push(tc(EXP.times[i])); }
    return JSON.stringify({ seq: qs.name, n: out.length });
})();
