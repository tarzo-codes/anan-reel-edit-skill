"""In-place AE update for a reel the user already edited in Premiere: compare the old and new plan ops per (comp, layer)
and emit only what changed - text content/style/position/keys/expressions on existing layers, full ops for NEW layers.
Never deletes or recreates comps, so Premiere's Dynamic Link items stay linked and the user's Premiere edits survive."""
import json, sys
from collections import OrderedDict
sys.stdout.reconfigure(encoding="utf-8")

def ops(p):
    a = json.load(open(p, encoding="utf-8")); A = a["args"]
    return A["args"]["ops"] if "args" in A and "ops" in A["args"] else A["ops"]

def by_layer(lst):
    g = OrderedDict()
    for o in lst:
        a = o.get("args", {})
        if o["operation"] in ("comp.delete", "comp.create"):
            continue
        key = (a.get("comp"), a.get("layer") or a.get("name"))
        g.setdefault(key, []).append(o)
    return g

old, new = by_layer(ops(sys.argv[1])), by_layer(ops(sys.argv[2]))
out, changed, added = [], 0, 0
for key, lst in new.items():
    if key not in old:
        out += lst; added += 1; continue
    if json.dumps(lst, sort_keys=True) == json.dumps(old[key], sort_keys=True):
        continue
    changed += 1
    for o in lst:
        op, a = o["operation"], o["args"]
        if op == "layer.create_text":
            out.append({"operation": "text.set_content", "args": {"comp": a["comp"], "layer": a["name"], "text": a["text"]}})
        elif op in ("layer.create_shape", "effect.add", "effect.set_property", "shape.add_group", "shape.add_rect", "shape.add_ellipse",
                    "shape.add_path", "shape.add_trim_paths", "shape.add_stroke", "shape.add_fill", "layer.set_parent"):
            continue  # structure already exists on the layer
        else:
            out.append(o)
removed = [k for k in old if k not in new]
json.dump({"operation": "batch.run", "args": {"ops": out}, "timeoutMs": 600000}, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
print(f"changed layers {changed}, new layers {added}, ops {len(out)}, layers only in old {len(removed)}")
