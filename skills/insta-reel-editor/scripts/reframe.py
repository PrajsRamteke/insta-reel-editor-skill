#!/usr/bin/env python3
"""Produce the 1080x1920 A-roll: smart crop (face tracking), static crop, or fit with blurred fill.

Usage:
  python3 reframe.py media/cut.mov --out media/vertical.mp4 [--mode auto|track|center|fit-blur|fit-color]
                     [--x 0.5] [--bg "#101010"] [--deadzone 0.08] [--detector auto|mediapipe|yunet|haar]
                     [--model PATH] [--json reframe.json]

Modes:
  auto       9:16 input -> scale only; otherwise track if a face detector is available, else center
  track      follow the main face with a "lazy camera": holds still inside a dead-zone, then eases to
             the new position (no jitter, no constant drift). Needs opencv-python (+ mediapipe optional)
  center     static crop at --x (0..1 of the free horizontal travel; 0.5 = center)
  fit-blur   whole frame visible, centered, over a blurred + darkened copy (screen recordings, wide yoga
             poses, group shots: anything a crop would amputate)
  fit-color  whole frame visible over a solid --bg color
Also writes reframe.json: mode, crop path keyframes, and a face track (normalized boxes on the 9:16
canvas, ~2/s) that the graphics planner uses to keep text off the face.
"""
from __future__ import annotations

import argparse
import math
import os
import urllib.request
from pathlib import Path

from _common import display_size, ffprobe_json, log, need, parse_rate, run, save_json, video_stream

MP_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/"
                "blaze_face_short_range.tflite")
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
             "face_detection_yunet_2023mar.onnx")
CACHE = Path(os.environ.get("REEL_CACHE", Path.home() / ".cache" / "insta-reel-editor"))


# ------------------------------------------------------------------ detectors
class Detector:
    name = "none"

    def detect(self, frame_bgr, t_ms: int) -> list[tuple[float, float, float, float, float]]:
        """Return [(x0,y0,x1,y1,score)] normalized 0..1."""
        return []


def make_detector(kind: str, model: str | None):
    try:
        import cv2  # noqa: F401
    except ImportError:
        log("[reframe] opencv-python not installed -> no face tracking (pip install opencv-python)")
        return None
    order = ["mediapipe", "yunet", "haar"] if kind == "auto" else [kind]
    for k in order:
        try:
            d = {"mediapipe": MPDetector, "yunet": YuNetDetector, "haar": HaarDetector}[k](model)
            log(f"[reframe] face detector: {d.name}")
            return d
        except Exception as e:  # missing package / model
            log(f"[reframe] {k} unavailable: {type(e).__name__}: {e}")
    return None


def _fetch(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    log(f"[reframe] downloading {url}")
    urllib.request.urlretrieve(url, dest)
    return dest


class MPDetector(Detector):
    name = "mediapipe-blazeface"

    def __init__(self, model: str | None):
        import mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        path = Path(model) if model and model.endswith(".tflite") else _fetch(MP_MODEL_URL, CACHE / "blaze_face_short_range.tflite")
        opts = vision.FaceDetectorOptions(base_options=mpt.BaseOptions(model_asset_path=str(path)),
                                          running_mode=vision.RunningMode.VIDEO, min_detection_confidence=0.5)
        self.mp, self.det = mp, vision.FaceDetector.create_from_options(opts)

    def detect(self, frame_bgr, t_ms):
        import cv2
        h, w = frame_bgr.shape[:2]
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        res = self.det.detect_for_video(img, t_ms)
        out = []
        for d in res.detections:
            b = d.bounding_box
            out.append((b.origin_x / w, b.origin_y / h, (b.origin_x + b.width) / w, (b.origin_y + b.height) / h,
                        d.categories[0].score if d.categories else 0.5))
        return out


class YuNetDetector(Detector):
    name = "opencv-yunet"

    def __init__(self, model: str | None):
        import cv2
        if not hasattr(cv2, "FaceDetectorYN"):
            raise RuntimeError("this OpenCV build has no FaceDetectorYN (needs opencv >= 4.8)")
        if not model or not model.endswith(".onnx"):
            cand = list(CACHE.glob("face_detection_yunet*.onnx"))
            model = str(cand[0]) if cand else str(_fetch(YUNET_URL, CACHE / "face_detection_yunet_2023mar.onnx"))
        self.cv2, self.model, self.det, self.size = cv2, model, None, None

    def detect(self, frame_bgr, t_ms):
        h, w = frame_bgr.shape[:2]
        if self.det is None or self.size != (w, h):
            self.det = self.cv2.FaceDetectorYN.create(self.model, "", (w, h), 0.6)
            self.size = (w, h)
        _, faces = self.det.detect(frame_bgr)
        out = []
        for f in (faces if faces is not None else []):
            x, y, fw, fh, score = f[0], f[1], f[2], f[3], f[-1]
            out.append((x / w, y / h, (x + fw) / w, (y + fh) / h, float(score)))
        return out


class HaarDetector(Detector):
    name = "opencv-haar"

    def __init__(self, model: str | None):
        import cv2
        if not hasattr(cv2, "CascadeClassifier"):
            raise RuntimeError("OpenCV 5 removed Haar cascades; use mediapipe or yunet")
        cands = []
        if model and model.endswith(".xml"):
            cands.append(model)
        base = getattr(getattr(cv2, "data", None), "haarcascades", "") or ""
        cands += [os.path.join(base, "haarcascade_frontalface_default.xml"),
                  str(CACHE / "haarcascade_frontalface_default.xml")]
        path = next((c for c in cands if c and os.path.exists(c)), None)
        if not path:
            raise FileNotFoundError("haarcascade_frontalface_default.xml not found (opencv>=5 dropped it; "
                                    "pass --model path/to/haarcascade_frontalface_default.xml)")
        self.cv2, self.det = cv2, cv2.CascadeClassifier(path)

    def detect(self, frame_bgr, t_ms):
        h, w = frame_bgr.shape[:2]
        gray = self.cv2.cvtColor(frame_bgr, self.cv2.COLOR_BGR2GRAY)
        faces = self.det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(int(h * 0.08),) * 2)
        return [(x / w, y / h, (x + fw) / w, (y + fh) / h, 0.6) for (x, y, fw, fh) in faces]


# ------------------------------------------------------------------ tracking
def sample_faces(path: str, det: Detector, fps_sample: float, max_w: int = 640):
    import cv2
    cap = cv2.VideoCapture(path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(src_fps / fps_sample))
    samples, idx, prev = [], 0, None
    while True:
        ok = cap.grab()
        if not ok:
            break
        if idx % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            h, w = frame.shape[:2]
            if w > max_w:
                frame = cv2.resize(frame, (max_w, round(h * max_w / w)))
            t = idx / src_fps
            faces = det.detect(frame, int(t * 1000))
            pick = None
            if faces:
                if prev is not None:  # continuity: prefer the face nearest the previous one, weighted by size
                    pick = max(faces, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]) - 0.5 * abs((f[0] + f[2]) / 2 - prev))
                else:
                    pick = max(faces, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))
                prev = (pick[0] + pick[2]) / 2
            samples.append({"t": round(t, 3), "face": pick})
        idx += 1
    cap.release()
    return samples


def median(vals):
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def lazy_camera(samples, dur: float, deadzone: float, move_time: float = 0.6, settle: float = 0.5):
    """Face centers -> keyframes [(t, cx)] of a camera that holds, then eases to a new hold."""
    pts = [(s["t"], (s["face"][0] + s["face"][2]) / 2) for s in samples if s["face"]]
    if not pts:
        return [(0.0, 0.5)], 0.0
    coverage = len(pts) / max(1, len(samples))
    # fill gaps + median filter (~1 s window) to kill detector jitter / false positives
    times = [s["t"] for s in samples]
    filled, j = [], 0
    last = pts[0][1]
    lookup = dict(pts)
    for t in times:
        last = lookup.get(t, last)
        filled.append(last)
    k = max(1, round(len(times) / max(dur, 0.1) * 0.5))
    smooth = [median(filled[max(0, i - k): i + k + 1]) for i in range(len(filled))]
    keys = [(0.0, smooth[0])]
    cam, i = smooth[0], 0
    while i < len(times):
        if times[i] > dur - move_time - 0.2:  # never start a move in the last moment of the clip
            break
        if abs(smooth[i] - cam) > deadzone:
            # require the offset to persist for `settle` seconds (ignore glances / gestures)
            j = i
            while j < len(times) and abs(smooth[j] - cam) > deadzone and times[j] - times[i] < settle:
                j += 1
            if j < len(times) and times[j] - times[i] < settle:
                i = j + 1
                continue
            target = median(smooth[i: min(len(smooth), i + max(1, k * 2))])
            t0 = times[i]
            t1 = min(dur, t0 + move_time)
            keys.append((round(t0, 3), cam))
            keys.append((round(t1, 3), target))
            cam = target
            while i < len(times) and times[i] < t1:
                i += 1
        i += 1
    return keys, coverage


def crop_expr(keys, crop_w: int, src_w: int) -> str:
    """Piecewise smoothstep expression of t for ffmpeg crop x."""
    def x_of(cx):
        return max(0, min(src_w - crop_w, round(cx * src_w - crop_w / 2)))

    if len(keys) == 1:
        return str(x_of(keys[0][1]))
    expr = str(x_of(keys[-1][1]))
    # build from the end: if(lt(t,t_i), segment_i, rest)
    for (t0, c0), (t1, c1) in reversed(list(zip(keys, keys[1:]))):
        a, b = x_of(c0), x_of(c1)
        if t1 <= t0 or a == b:
            seg = str(a)
        else:
            p = f"((t-{t0})/{t1 - t0:.4f})"
            seg = f"({a}+({b - a})*(3*{p}*{p}-2*{p}*{p}*{p}))"
        expr = f"if(lt(t,{t1}),{seg},{expr})"
    first = x_of(keys[0][1])
    return f"if(lt(t,{keys[0][0]}),{first},{expr})"


def fit_geometry(src_w, src_h, anchor):
    """Foreground placement for fit modes on the 1080x1920 canvas: (x_off, y_off, w, h) in px."""
    s = min(1080 / src_w, 1920 / src_h)
    w, h = src_w * s, src_h * s
    y = 290 if anchor == "upper" and h < 1920 - 290 else (1920 - h) / 2
    return (1080 - w) / 2, y, w, h


def face_track_on_canvas(samples, mode, src_w, src_h, keys, crop_w, anchor="center"):
    """Map sampled face boxes into normalized 9:16 output coordinates (for graphics placement)."""
    out = []
    every = max(1, round(len(samples) / max(1, samples[-1]["t"] if samples else 1) / 2))
    for s in samples[::every]:
        f = s["face"]
        if not f:
            out.append({"t": s["t"], "box": None})
            continue
        if mode in ("track", "center") and src_w / src_h < 9 / 16:  # taller than 9:16: centred height crop
            crop_h = src_w * 16 / 9
            y0 = (src_h - crop_h) / 2
            box = [f[0], (f[1] * src_h - y0) / crop_h, f[2], (f[3] * src_h - y0) / crop_h]
        elif mode in ("track", "center") and keys is not None:
            cx = interp_keys(keys, s["t"])
            x0px = max(0, min(src_w - crop_w, cx * src_w - crop_w / 2))
            bx0 = (f[0] * src_w - x0px) / crop_w
            bx1 = (f[2] * src_w - x0px) / crop_w
            box = [bx0, f[1], bx1, f[3]]
        elif mode in ("fit-blur", "fit-color"):
            xo, yo, fw, fh = fit_geometry(src_w, src_h, anchor)
            box = [(xo + f[0] * fw) / 1080, (yo + f[1] * fh) / 1920, (xo + f[2] * fw) / 1080, (yo + f[3] * fh) / 1920]
        else:  # scale only
            box = list(f[:4])
        out.append({"t": s["t"], "box": [round(float(max(0, min(1, v))), 3) for v in box]})
    return out


def interp_keys(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, c0), (t1, c1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            if t1 == t0:
                return c1
            p = (t - t0) / (t1 - t0)
            return c0 + (c1 - c0) * (3 * p * p - 2 * p * p * p)
    return keys[-1][1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="auto", choices=["auto", "track", "center", "fit-blur", "fit-color"])
    ap.add_argument("--x", type=float, default=0.5, help="center mode: horizontal position 0..1")
    ap.add_argument("--bg", default="#101010", help="fit-color background")
    ap.add_argument("--fit-anchor", default="center", choices=["center", "upper"],
                    help="fit modes: 'upper' puts the frame at y=290 so captions sit below it (screen recordings)")
    ap.add_argument("--deadzone", type=float, default=0.08, help="track: fraction of source width the face may "
                                                                 "drift before the camera moves")
    ap.add_argument("--detector", default="auto", choices=["auto", "mediapipe", "yunet", "haar"])
    ap.add_argument("--model", help="detector model file (.tflite / .onnx / .xml)")
    ap.add_argument("--sample-fps", type=float, default=5.0)
    ap.add_argument("--json", help="default: <out dir>/../reframe.json")
    ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    need("ffmpeg")

    info = ffprobe_json(a.input)
    vs = video_stream(info)
    W, H = display_size(vs)
    dur = float(info["format"]["duration"])
    fps = vs.get("r_frame_rate", "30/1")
    ratio = W / H
    mode = a.mode
    det = None
    if mode == "auto":
        if abs(ratio - 9 / 16) < 0.02:
            mode = "scale"
        else:
            det = make_detector(a.detector, a.model)
            mode = "track" if det else "center"
            if not det:
                log("[reframe] no face detector -> static center crop. Check the result; consider --mode fit-blur.")
    elif mode in ("track",):
        det = make_detector(a.detector, a.model)
        if not det:
            log("[reframe] tracking unavailable -> falling back to center crop")
            mode = "center"
    if det is None and mode in ("scale", "center", "fit-blur", "fit-color"):
        det = make_detector(a.detector, a.model)  # face track still helps graphics placement

    samples = sample_faces(a.input, det, a.sample_fps if mode == "track" else 2.0) if det else []
    keys, coverage, crop_w = None, None, None
    if ratio > 9 / 16:
        crop_w = int(round(H * 9 / 16 / 2) * 2)
    vf = []
    if mode == "scale":
        vf.append("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920")
    elif mode in ("track", "center"):
        if ratio < 9 / 16:  # taller than 9:16 -> crop height, centered
            crop_h = int(round(W * 16 / 9 / 2) * 2)
            vf.append(f"crop={W}:{crop_h}:0:(ih-{crop_h})/2")
        else:
            if mode == "track":
                keys, coverage = lazy_camera(samples, dur, a.deadzone)
                if coverage < 0.5:
                    log(f"[reframe] faces found in only {coverage:.0%} of samples; check the crop or use fit-blur")
            else:
                free = (W - crop_w) / W
                keys = [(0.0, (crop_w / 2) / W + free * a.x)]
            vf.append(f"crop={crop_w}:{H}:'{crop_expr(keys, crop_w, W)}':0")
        vf.append("scale=1080:1920:flags=lanczos")
    elif mode in ("fit-blur", "fit-color"):
        pass
    else:
        raise SystemExit(f"unknown mode {mode}")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    common_tail = ["-r", fps, "-c:v", "libx264", "-preset", "fast", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                   "-g", str(max(1, round(parse_rate(fps)))), "-color_primaries", "bt709", "-color_trc", "bt709",
                   "-colorspace", "bt709", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart"]
    fit_y = "(H-h)/2"
    if mode in ("fit-blur", "fit-color") and a.fit_anchor == "upper":
        fit_y = f"'min(290,(H-h)/2)'"
    if mode == "fit-blur":
        fc = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              "boxblur=luma_radius=40:luma_power=2,eq=brightness=-0.12:saturation=0.85[bg];"
              "[b]scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
              f"[bg][fg]overlay=(W-w)/2:{fit_y},format=yuv420p[v]")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.input, "-filter_complex", fc,
             "-map", "[v]", "-map", "0:a?", *common_tail, str(out)])
    elif mode == "fit-color":
        color = a.bg.replace("#", "0x")
        vf_fit = (f"scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,"
                  f"pad=1080:1920:(ow-iw)/2:{fit_y.replace('H-h', 'oh-ih')}:color={color},format=yuv420p")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.input, "-vf", vf_fit,
             "-map", "0:v:0", "-map", "0:a?", *common_tail, str(out)])
    else:
        vf.append("format=yuv420p")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.input, "-vf", ",".join(vf),
             "-map", "0:v:0", "-map", "0:a?", *common_tail, str(out)])

    track = face_track_on_canvas(samples, mode, W, H, keys, crop_w or W, a.fit_anchor) if samples else []
    faced = [s["box"] for s in track if s["box"]]
    summary = None
    if faced:
        summary = {k: round(float(median([b[j] for b in faced])), 3)
                   for k, j in (("x0_median", 0), ("y0_median", 1), ("x1_median", 2), ("y1_median", 3))}
    keys = [(float(t), float(c)) for t, c in keys] if keys else keys
    rep = {"input": a.input, "output": str(out), "mode": mode, "source_size": [W, H],
           "detector": det.name if det else None, "face_coverage": coverage if coverage is not None else
           (round(len(faced) / len(track), 3) if track else None),
           "crop_width": crop_w, "keyframes": keys, "face_box_median": summary, "face_track": track}
    jpath = Path(a.json) if a.json else out.parent.parent / "reframe.json"
    save_json(rep, jpath)
    moves = (len(keys) - 1) // 2 if keys else 0
    log(f"[reframe] {mode}: {W}x{H} -> 1080x1920 ({moves} camera moves) -> {out}; face box median {summary}")


if __name__ == "__main__":
    main()
