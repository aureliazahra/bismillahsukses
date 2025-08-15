"""
Detection & processing utilities (final).
- stronger human_vs_photo heuristic (entropy, HF energy, edge density, specular)
- exposure correction, blur check, embedding match
- optional ONNX antispoof
"""

import os
import logging
import cv2
import numpy as np
from numpy.linalg import norm

# optional onnx
try:
    import onnxruntime as ort
except Exception:
    ort = None

# optional insightface
INSIGHTFACE_AVAILABLE = False
try:
    import insightface
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except Exception:
    INSIGHTFACE_AVAILABLE = False

# globals
_app = None
_use_gpu = False

# Haar fallback
_haar = None
try:
    haar_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    _haar = cv2.CascadeClassifier(haar_path)
    if _haar.empty():
        _haar = None
except Exception:
    _haar = None

# antispoof ONNX
_antispoof_session = None
_antispoof_input_name = None
_antispoof_output_name = None
_antispoof_input_shape = None

# DEBUG env
DEBUG_DETECTOR = bool(os.environ.get("DETECTOR_DEBUG", "").strip())

def initialize(use_gpu: bool = False, model_name: str = "buffalo_l"):
    global _app, _use_gpu
    _use_gpu = bool(use_gpu)
    if INSIGHTFACE_AVAILABLE:
        try:
            providers = ['CPUExecutionProvider']
            ctx_id = -1
            if _use_gpu:
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                ctx_id = 0
            logging.info("Initializing InsightFace model=%s providers=%s", model_name, providers)
            _app = FaceAnalysis(name=model_name, providers=providers)
            _app.prepare(ctx_id=ctx_id, det_size=(640, 640))
            logging.info("InsightFace initialized")
        except Exception:
            logging.exception("InsightFace init failed")
            _app = None
    else:
        logging.info("InsightFace not available; will use Haar cascade")

def load_antispoof_model(path):
    global _antispoof_session, _antispoof_input_name, _antispoof_output_name, _antispoof_input_shape
    if ort is None:
        logging.warning("onnxruntime not installed -> skip antispoof ONNX load")
        return False
    if not path or not os.path.exists(path):
        logging.warning("antispoof path missing: %s", path)
        return False
    try:
        sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
        _antispoof_session = sess
        _antispoof_input_name = sess.get_inputs()[0].name
        _antispoof_output_name = sess.get_outputs()[0].name
        _antispoof_input_shape = sess.get_inputs()[0].shape
        logging.info("Loaded antispoof ONNX %s", path)
        return True
    except Exception:
        logging.exception("Failed load antispoof ONNX")
        _antispoof_session = None
        return False

def is_initialized():
    return _app is not None or _haar is not None

# ---------- known faces ----------
def load_known_faces(target_folder=None):
    if target_folder is None:
        BASE = os.path.dirname(os.path.abspath(__file__))
        target_folder = os.path.join(BASE, "target_faces")
    known = []
    if not os.path.exists(target_folder):
        logging.info("Known faces folder not found: %s", target_folder)
        return known
    if _app is None:
        logging.info("face app not initialized; skip known faces load")
        return known
    try:
        for fn in os.listdir(target_folder):
            path = os.path.join(target_folder, fn)
            if not os.path.isfile(path):
                continue
            img = cv2.imread(path)
            if img is None:
                continue
            try:
                faces = _app.get(img)
                if not faces:
                    continue
                emb = faces[0].embedding
                name = os.path.splitext(fn)[0]
                known.append((name, emb))
            except Exception:
                logging.exception("Failed processing known face %s", path)
    except Exception:
        logging.exception("Failed reading known faces folder")
    logging.info("Loaded %d known faces", len(known))
    return known

def is_match(emb1, emb2, threshold=0.5):
    try:
        sim = float(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2)))
        # treat equality as match (>=). adjust if you prefer strict >
        return sim >= float(threshold), sim
    except Exception:
        return False, 0.0

# ---------- helpers ----------
def compute_sharpness(gray):
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return float(lap.var())

def apply_exposure_correction(bgr_face, exposure_gain=1.4, apply_clahe=True):
    try:
        ycrcb = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        y = cv2.convertScaleAbs(y, alpha=exposure_gain, beta=0)
        if apply_clahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            y = clahe.apply(y)
        ycrcb = cv2.merge((y, cr, cb))
        return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    except Exception:
        return bgr_face

def lbp_entropy(gray):
    try:
        g = gray.astype(np.int16)
        center = g[1:-1,1:-1]
        neigh = (
            (g[0:-2,0:-2] > center).astype(np.uint8) +
            (g[0:-2,1:-1] > center).astype(np.uint8) +
            (g[0:-2,2:  ] > center).astype(np.uint8) +
            (g[1:-1,0:-2] > center).astype(np.uint8) +
            (g[1:-1,2:  ] > center).astype(np.uint8) +
            (g[2:  ,0:-2] > center).astype(np.uint8) +
            (g[2:  ,1:-1] > center).astype(np.uint8) +
            (g[2:  ,2:  ] > center).astype(np.uint8)
        )
        hist = np.bincount(neigh.ravel(), minlength=9).astype(np.float32)
        hist /= (hist.sum() + 1e-9)
        ent = -np.sum(hist * np.log(hist + 1e-9))
        return float(ent)
    except Exception:
        return 0.0

def high_freq_energy(gray):
    try:
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        h,w = gray.shape
        cy, cx = h//2, w//2
        # compute energy in high-frequency ring (outside 1/8 central radius)
        ry, rx = cy//4, cx//4
        mask = np.ones_like(magnitude, dtype=np.bool_)
        mask[cy-ry:cy+ry, cx-rx:cx+rx] = False
        hf = magnitude[mask]
        return float(hf.mean()) if hf.size else 0.0
    except Exception:
        return 0.0

def edge_density(gray):
    try:
        edges = cv2.Canny(gray, 50, 150)
        return float(edges.mean())  # normalized-ish
    except Exception:
        return 0.0

def count_specular_spots(gray):
    try:
        _, thr = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = 0
        h,w = gray.shape
        for c in contours:
            a = cv2.contourArea(c)
            if 1 < a < (h*w)*0.01:
                cnt += 1
        return cnt
    except Exception:
        return 0

def human_photo_heuristic(bgr_face, entropy_thresh=0.22, hf_thresh=5.0, edge_thresh=4.0, specular_min=1):
    """
    Combine metrics:
    - entropy (LBP-like)
    - high frequency energy
    - edge density
    - specular small bright spots
    Returns (is_human_like:bool, metrics:dict)
    """
    try:
        gray = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)
        ent = lbp_entropy(gray)
        hf = high_freq_energy(gray)
        ed = edge_density(gray)
        spec = count_specular_spots(gray)
        # heuristic: photos/screens often have low entropy, low HF energy, low edges, and few speculars
        score = 0.0
        if ent >= entropy_thresh:
            score += 1.0
        if hf >= hf_thresh:
            score += 1.0
        if ed >= edge_thresh:
            score += 1.0
        if spec >= specular_min:
            score += 1.0
        is_human = (score >= 2.0)  # at least two positive indicators
        metrics = {"entropy": ent, "hf": hf, "edge": ed, "specular": spec, "score": score}
        if DEBUG_DETECTOR:
            logging.debug("human_photo metrics: %s", metrics)
        return is_human, metrics
    except Exception:
        return True, {"entropy":0.0,"hf":0.0,"edge":0.0,"specular":0.0,"score":0.0}

# ---------- antispoof ----------
def antispoof_crop_predict(bgr_face):
    global _antispoof_session, _antispoof_input_name, _antispoof_output_name, _antispoof_input_shape
    if _antispoof_session is not None and _antispoof_input_shape is not None:
        try:
            _, c, h, w = _antispoof_input_shape
            crop = cv2.resize(bgr_face, (w, h))
            rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            inp = np.expand_dims(np.transpose(rgb, (2,0,1)), axis=0).astype(np.float32)
            out = _antispoof_session.run([_antispoof_output_name], { _antispoof_input_name: inp })
            score = float(np.mean(out[0]))
            return (score >= 0.5, score)
        except Exception:
            logging.exception("ONNX antispoof failed")
    # fallback heuristic: use human_photo_heuristic metrics inverted
    try:
        gray = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)
        ent = lbp_entropy(gray)
        spec = count_specular_spots(gray)
        score = ent
        is_live = (ent > 0.25) or (spec >= 1)
        return (is_live, float(score))
    except Exception:
        return (True, None)

# ---------- detection wrappers ----------
def _detect_with_insightface(rgb_frame):
    res = []
    if _app is None:
        return res
    try:
        faces = _app.get(rgb_frame)
    except Exception:
        logging.exception("InsightFace get() failed")
        return res
    for face in faces:
        try:
            bbox = face.bbox.astype(int)
            emb = getattr(face, "embedding", None)
            res.append({"bbox": (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])), "embedding": emb})
        except Exception:
            continue
    return res

def _detect_with_haar(bgr_frame):
    results = []
    if _haar is None:
        return results
    try:
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        faces = _haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
        for (x,y,w,h) in faces:
            results.append({"bbox": (int(x),int(y),int(x+w),int(y+h)), "embedding": None})
    except Exception:
        logging.exception("Haar detection failed")
    return results

def process_frame_for_faces(frame, known_faces=None, match_threshold=0.5,
                            min_sharpness_percent=20, sharpness_var_max=1000,
                            require_human_check=False, exposure_enabled=True, exposure_gain=1.4,
                            min_luminance=60, antispoof_enabled=False, antispoof_threshold=0.5):
    """
    frame: RGB image (H,W,3)
    returns annotations list with fields:
    {bbox, name, match, score, skipped(bool), skip_reason, sharpness_percent, sharpness_var, antispoof_checked}
    """
    annotations = []
    known_faces = known_faces or []

    if frame is None:
        return annotations

    # detection
    if _app is not None:
        dets = _detect_with_insightface(frame)
    else:
        try:
            bgr_full = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception:
            bgr_full = frame
        dets = _detect_with_haar(bgr_full)

    H,W = frame.shape[:2]

    for d in dets:
        bbox = d.get("bbox")
        emb = d.get("embedding", None)
        if not bbox:
            continue
        x1,y1,x2,y2 = bbox
        x1c,y1c = max(0,x1), max(0,y1)
        x2c,y2c = min(W,x2), min(H,y2)
        if x2c <= x1c or y2c <= y1c:
            continue
        try:
            crop_rgb = frame[y1c:y2c, x1c:x2c]
            bgr_face = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2BGR)
        except Exception:
            bgr_face = None
        if bgr_face is None or bgr_face.size == 0:
            continue

        # exposure
        gray_face = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)
        mean_lum = float(gray_face.mean())
        if exposure_enabled and mean_lum < float(min_luminance):
            bgr_face = apply_exposure_correction(bgr_face, exposure_gain=exposure_gain, apply_clahe=True)
            gray_face = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)

        # sharpness
        var = compute_sharpness(gray_face)
        sharpness_percent = min(100.0, max(0.0, (var / float(max(1.0, sharpness_var_max))) * 100.0))
        # if below percent threshold -> skip
        if sharpness_percent < float(min_sharpness_percent):
            annotations.append({
                "bbox": bbox, "name": "tidak diproses (blur)", "match": False, "score": 0.0,
                "skipped": True, "skip_reason": "blur", "sharpness_percent": sharpness_percent,
                "sharpness_var": var, "antispoof_checked": False
            })
            continue

        # human-photo heuristic
        if require_human_check:
            human_like, metrics = human_photo_heuristic(bgr_face)
            if not human_like:
                annotations.append({
                    "bbox": bbox, "name": "tidak diproses (bukan manusia)", "match": False, "score": 0.0,
                    "skipped": True, "skip_reason": "not_human", "metrics": metrics,
                    "sharpness_percent": sharpness_percent, "sharpness_var": var, "antispoof_checked": False
                })
                continue

        # if no embedding -> unknown (but not skipped)
        if emb is None:
            annotations.append({
                "bbox": bbox, "name": "tidak dikenal", "match": False, "score": 0.0,
                "skipped": False, "sharpness_percent": sharpness_percent, "sharpness_var": var, "antispoof_checked": False
            })
            continue

        # match embeddings
        best_name = None
        best_score = -1.0
        matched = False
        matched_name = None
        for name, kemb in known_faces:
            try:
                match, score = is_match(emb, kemb, threshold=match_threshold)
            except Exception:
                continue
            # keep best scoring candidate for reference
            if score > best_score:
                best_score = float(score)
                best_name = name
            if match:
                matched = True
                matched_name = name
                # if you want the highest-scoring match instead of first match, remove break
                break

        # choose displayed name: only show known name if matched; otherwise "tidak dikenal"
        display_name = matched_name if matched and matched_name is not None else "tidak dikenal"

        annotations.append({
            "bbox": bbox,
            "name": display_name,
            "match": matched,
            "score": max(0.0, float(best_score) if best_score is not None else 0.0),
            "skipped": False,
            "sharpness_percent": sharpness_percent,
            "sharpness_var": var,
            "best_name": best_name,
            "antispoof_checked": False
        })

        # antispoof check (optional)
        if antispoof_enabled:
            is_live, score = antispoof_crop_predict(bgr_face)
            if is_live is False:
                # if spoof -> mark as skipped
                annotations[-1]["skipped"] = True
                annotations[-1]["skip_reason"] = "antispoof"
                annotations[-1]["name"] = "tidak diproses (spoof)"
            annotations[-1]["antispoof_checked"] = True
            annotations[-1]["antispoof_score"] = score

    return annotations
