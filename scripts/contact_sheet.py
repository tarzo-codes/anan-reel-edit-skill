"""Contact sheet of a vertical reel (or any video) with timestamps - to map a reference reel or check an export.

  python contact_sheet.py video.mp4 out.jpg [--fps 2] [--cols 16] [--width 270]
  python contact_sheet.py video.mp4 out.jpg --at 1.2 5.0 20.6      (chosen moments, bigger tiles)

Splits into out_0.jpg, out_1.jpg... every 64 tiles so each image stays readable.
"""
import glob
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw


def arg(name, default, cast=float):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    src, out = sys.argv[1], sys.argv[2]
    fps, cols, width = arg("--fps", 2.0), arg("--cols", 16, int), arg("--width", 270, int)
    tmp = tempfile.mkdtemp(prefix="sheet_")
    if "--at" in sys.argv:
        times = [float(t) for t in sys.argv[sys.argv.index("--at") + 1:]]
        width, cols = arg("--width", 540, int), min(6, len(times))
        for i, t in enumerate(times):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1",
                            "-vf", f"scale={width}:-1", os.path.join(tmp, f"f_{i:03d}.jpg")], check=True)
    else:
        times = None
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"fps={fps},scale={width}:-1",
                        os.path.join(tmp, "f_%03d.jpg")], check=True)
    fs = sorted(glob.glob(os.path.join(tmp, "f_*.jpg")))
    w, h = Image.open(fs[0]).size
    base, ext = os.path.splitext(out)
    for part in range(0, len(fs), 64):
        chunk = fs[part:part + 64]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * w, rows * h), "black")
        d = ImageDraw.Draw(sheet)
        for i, f in enumerate(chunk):
            x, y = (i % cols) * w, (i // cols) * h
            sheet.paste(Image.open(f), (x, y))
            t = times[part + i] if times else (part + i) / fps
            d.rectangle([x, y, x + 56, y + 18], fill="black")
            d.text((x + 3, y + 3), f"{t:.1f}s", fill="yellow")
        name = out if len(fs) <= 64 else f"{base}_{part // 64}{ext}"
        sheet.save(name, quality=85)
        print(name, sheet.size)


if __name__ == "__main__":
    main()
