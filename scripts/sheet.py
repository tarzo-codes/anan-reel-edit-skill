"""sheet.py PREFIX "t1,t2,..." out.jpg  - wait for PREFIX_0..N-1.png (Premiere exportFramePNG), tile them with times."""
import os, sys, time
from PIL import Image, ImageDraw
pre, T, out = sys.argv[1], [float(x) for x in sys.argv[2].split(",")], sys.argv[3]
for _ in range(90):
    if all(os.path.exists(f"{pre}_{i}.png") for i in range(len(T))): break
    time.sleep(2)
time.sleep(2)
w, h, cols = 270, 480, 6
S = Image.new("RGB", (cols * w, ((len(T) + cols - 1) // cols) * h)); d = ImageDraw.Draw(S)
for i, t in enumerate(T):
    try: im = Image.open(f"{pre}_{i}.png").convert("RGB").resize((w, h))
    except Exception: continue
    x, y = (i % cols) * w, (i // cols) * h; S.paste(im, (x, y)); d.rectangle([x, y, x + 50, y + 16], fill="black"); d.text((x + 3, y + 3), f"{t:.1f}s", fill="yellow")
S.save(out, quality=85); print(out)
