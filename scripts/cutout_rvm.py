"""Cut the presenter out of an A-roll range (alpha matte) so text/graphics can sit BEHIND him.

  python cutout_rvm.py src.MP4 SRC_IN DURATION out.mov [--model E:/Anan/Assets/models/rvm_mobilenetv3_fp32.onnx]

RobustVideoMatting (ONNX, CPU) runs at 1080x1920 (downsample 0.25); the matte is upscaled and applied to
the full-res 2160x3840 frames (ffmpeg auto-rotates the Sony clips). Output: ProRes 4444 with alpha, 25 fps,
exactly DURATION long, video only. In Premiere it goes on a track ABOVE the AE text, at the same timeline
time as the A-roll piece it was cut from, with the same punch-in keys (build_reel.jsx does both).
~0.4-0.8 s per frame on this CPU, so keep cut-outs to short hero moments (2-4 s).
"""
import subprocess
import sys

import cv2
import numpy as np
import onnxruntime as ort

W, H, FPS = 2160, 3840, 25


def main():
    src, ss, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "E:/Anan/Assets/models/rvm_mobilenetv3_fp32.onnx"
    n = int(round(dur * FPS))
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
    dr = np.array([0.25], dtype=np.float32)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", src, "-frames:v", str(n), "-vf", f"fps={FPS},scale={W}:{H}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-an", out], stdin=subprocess.PIPE)
    k = 0
    while k < n:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        small = cv2.resize(frame, (1080, 1920), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        inp = small.transpose(2, 0, 1)[None]
        fgr, pha, *rec = sess.run(None, {"src": inp, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": dr})
        a = cv2.resize(pha[0, 0], (W, H), interpolation=cv2.INTER_LINEAR)
        a = np.clip((a - 0.04) / 0.92, 0, 1)  # firm up the edge a little
        rgba = np.dstack([frame, (a * 255).astype(np.uint8)])
        enc.stdin.write(rgba.tobytes())
        k += 1
    while k < n and k > 0:  # pad with the last frame if the decoder came up short
        enc.stdin.write(rgba.tobytes()); k += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(out, k, "frames")


if __name__ == "__main__":
    main()
