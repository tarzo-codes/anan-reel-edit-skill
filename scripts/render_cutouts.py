# Render every cut-out the plans asked for (rN_cutouts.json), skipping files already on disk. Usage: python render_cutouts.py 1 2 3 4
import json, os, subprocess, sys
S = "C:/Users/btaza/.claude/skills/anan-reel-edit/scripts/cutout_rvm.py"
os.makedirs("cutouts", exist_ok=True)
for n in sys.argv[1:]:
    for src, ss, dur, out in json.load(open(f"r{n}_cutouts.json")):
        if os.path.exists(out) and os.path.getsize(out) > 10000:
            continue
        print(f"r{n} {ss}+{dur} -> {out}", flush=True)
        subprocess.run([sys.executable, S, src, str(ss), str(dur), out], check=False)
print("done", flush=True)
