# detector.py
# Backend: InsightFace
# Perbaikan tahap-3:
# - Perkuat deteksi "foto di HP":
#   * Deteksi bingkai HP lengkap (empat sisi) via Canny + Hough, cek rasio aspek layar.
#   * Deteksi periodisitas grid piksel (moiré/screen-door) lewat autokorelasi 1D pada pita horizontal & vertikal.
#   * Kombinasi dengan indikator terang, saturasi, dan tekstur agar robust.
# - Tetap: cluster poster/kalender, throttle jumlah wajah/iframe, multi-scale fallback utk wajah jauh.
# - Tidak mengubah GUI/tampilan, tidak menyentuh cameras.json/app_config.json.
#
# Catatan: Hanya ganti file ini.

import os
import logging
import cv2
import numpy as np
from numpy.linalg import norm

# ============== Optional dependencies ==============
try:
    import onnxruntime as ort
except Exception:
    ort = None

INSIGHTFACE_AVAILABLE = False
_HAS_ALIGN = False
try:
    import insightface
    from insightface.app import FaceAnalysis
    try:
        from insightface.utils import face_align  # norm_crop
        _HAS_ALIGN = True
    except Exception:
        _HAS_ALIGN = False
    INSIGHTFACE_AVAILABLE = True
except Exception:
    INSIGHTFACE_AVAILABLE = False
    _HAS_ALIGN = False

# ============== Globals ==============
_app = None
_use_gpu = False

# Antispoof (MiniFASNet ONNX)
_antispoof_session = None
_antispoof_input_name = None
_antispoof_output_name = None
_antispoof_input_shape = None

# DEFAULT utk model 3-kelas umum: [bg, spoof, live]
_antispoof_live_index = 2
_antispoof_thresholds = {"low": 0.40, "medium": 0.55, "high": 0.70}
_antispoof_mode = "high"  # lebih ketat
_antispoof_preprocess = "rgb01"
_antispoof_smooth_k = 3

# State untuk deteksi cluster & kecepatan
_prev_small_centers = []  # [(x,y)]
_prev_frame_size = None


# ============== Public config setters ==============
def set_antispoof_params(live_index=None, thresholds=None, mode=None, preprocess=None, smooth_k=None):
    global _antispoof_live_index, _antispoof_thresholds, _antispoof_mode
    global _antispoof_preprocess, _antispoof_smooth_k
    if live_index is not None:
        try: _antispoof_live_index = int(live_index)
        except Exception: pass
    if isinstance(thresholds, dict):
        for k, v in thresholds.items():
            try: _antispoof_thresholds[k] = float(v)
            except Exception: pass
    if isinstance(mode, str) and mode.lower() in ("low", "medium", "high"):
        _antispoof_mode = mode.lower()
    if isinstance(preprocess, str):
        _antispoof_preprocess = preprocess.lower().strip()
    if smooth_k is not None:
        try: _antispoof_smooth_k = max(1, int(smooth_k))
        except Exception: pass


# ============== Init / Known faces ==============
def initialize(use_gpu: bool = False, model_name: str = "buffalo_l", detector_backend: str = "insightface"):
    """Siapkan InsightFace (deteksi & embedding)."""
    global _app, _use_gpu
    _use_gpu = bool(use_gpu)

    if INSIGHTFACE_AVAILABLE:
        try:
            providers = ['CPUExecutionProvider']; ctx_id = -1
            if _use_gpu:
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']; ctx_id = 0
            _app = FaceAnalysis(name=model_name, providers=providers)
            _app.prepare(ctx_id=ctx_id, det_size=(640, 640))

            # Longgarkan ambang krn ingin wajah jauh, tetap aman
            try:
                if hasattr(_app, "det_thresh"):
                    _app.det_thresh = min(float(getattr(_app, "det_thresh")), 0.23)
                det_models = _app.models.get("detection", None) if hasattr(_app, "models") else None
                if det_models:
                    for dm in (det_models if isinstance(det_models, (list, tuple)) else [det_models]):
                        m = getattr(dm, "model", None)
                        for attr in ("threshold", "score_thresh", "conf_threshold"):
                            if m is not None and hasattr(m, attr):
                                setattr(m, attr, min(float(getattr(m, attr)), 0.23))
            except Exception:
                pass

            logging.info("InsightFace initialized")
        except Exception:
            logging.exception("InsightFace init failed")
            _app = None
    else:
        _app = None

    logging.info("Detector active backend='insightface' | insightface_available=%s", INSIGHTFACE_AVAILABLE)


def is_initialized():
    return _app is not None


def load_known_faces(target_folder=None):
    if target_folder is None:
        BASE = os.path.dirname(os.path.abspath(__file__))
        target_folder = os.path.join(BASE, "target_faces")
    known = []
    if not os.path.exists(target_folder) or _app is None:
        logging.debug("Loaded %d known faces", 0)
        return known
    try:
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        for root, _, files in os.walk(target_folder):
            for fn in files:
                if os.path.splitext(fn)[1].lower() not in exts:
                    continue
                p = os.path.join(root, fn)
                img = cv2.imread(p)  # BGR
                if img is None:
                    continue
                faces = _app.get(img)
                if not faces:
                    continue
                emb = faces[0].embedding
                rel = os.path.relpath(p, target_folder)
                parts = rel.split(os.sep)
                name = parts[0] if len(parts) >= 2 else os.path.splitext(fn)[0]
                known.append((name, emb))
    except Exception:
        logging.exception("Failed reading known faces folder")
    logging.info("Loaded %d known faces", len(known))
    return known


# ============== Small helpers ==============
def is_match(emb1, emb2, threshold=0.6):
    try:
        sim = float(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2)))
        return sim >= float(threshold), sim
    except Exception:
        return False, 0.0


def _ensure_bgr_uint8(frame_rgb):
    """Pastikan: BGR, uint8, 3ch, contiguous."""
    if frame_rgb is None:
        return None
    img = frame_rgb
    if not isinstance(img, np.ndarray):
        img = np.asarray(img)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3].copy()
    if img.dtype != np.uint8:
        vmax = float(img.max()) if img.size else 1.0
        if vmax <= 1.5:
            img = (img * 255.0).clip(0, 255).astype(np.uint8)
        else:
            img = img.clip(0, 255).astype(np.uint8)
    try:
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    except Exception:
        bgr = img
    return np.ascontiguousarray(bgr)


def _collect_faces(faces, scale=1.0):
    res = []
    for f in faces:
        try:
            bbox = f.bbox.astype(float)
            kps = getattr(f, "kps", None)
            emb = getattr(f, "embedding", None)
            if scale != 1.0:
                bbox = bbox / float(scale)
                if kps is not None:
                    kps = np.asarray(kps, dtype=float) / float(scale)
            res.append({
                "bbox": (int(round(bbox[0])), int(round(bbox[1])),
                         int(round(bbox[2])), int(round(bbox[3]))),
                "embedding": emb,
                "kps": kps
            })
        except Exception:
            continue
    return res


def _detect_with_insightface(frame_rgb):
    """
    Return list of dict: [{'bbox':(x1,y1,x2,y2), 'embedding':vec, 'kps':(5x2)}]
    Tambahan: fallback multi-scale saat tidak ada wajah (untuk manusia jauh).
    """
    out = []
    if _app is None or frame_rgb is None:
        return out
    try:
        bgr = _ensure_bgr_uint8(frame_rgb)
        faces = _app.get(bgr)
        if faces:
            out = _collect_faces(faces, scale=1.0)
        else:
            for sc in (1.5, 2.0):
                bigger = cv2.resize(bgr, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
                faces2 = _app.get(bigger)
                if faces2:
                    out = _collect_faces(faces2, scale=sc)
                    break
    except Exception:
        logging.exception("InsightFace get() failed")
        return out

    logging.debug("[detect] faces=%d", len(out))
    return out


# ============== Antispoof (MiniFASNet) ==============
def _softmax(x, axis=1):
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / (np.sum(e, axis=axis, keepdims=True) + 1e-12)


def _prepare_antispoof_input(bgr_face):
    try:
        shape = list(_antispoof_input_shape) if _antispoof_input_shape is not None else [1, 3, 80, 80]
    except Exception:
        shape = [1, 3, 80, 80]

    def _apply(img_bgr, W, H, is_nchw, Cexp):
        use_bgr = _antispoof_preprocess.startswith("bgr")
        img = cv2.resize(img_bgr, (W, H), interpolation=cv2.INTER_LINEAR)
        if not use_bgr:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        if _antispoof_preprocess.endswith("01"):
            pass
        else:
            img = (img - 0.5) / 0.5
        if is_nchw:
            img = np.transpose(img, (2, 0, 1))
            if Cexp == 1:
                img = np.mean(img, axis=0, keepdims=True)
        else:
            if Cexp == 1:
                img = np.mean(img, axis=2, keepdims=True)
        return img

    if len(shape) == 4 and shape[1] in (1, 3):  # NCHW
        C, H, W = int(shape[1]), int(shape[2]), int(shape[3])
        x = _apply(img_bgr=bgr_face, W=W, H=H, is_nchw=True, Cexp=C)[None, ...]
    else:  # NHWC
        H = int(shape[1]) if len(shape) == 4 else 80
        W = int(shape[2]) if len(shape) == 4 else 80
        C = int(shape[3]) if len(shape) == 4 else 3
        x = _apply(img_bgr=bgr_face, W=W, H=H, is_nchw=False, Cexp=C)[None, ...]
    return x


def _minifasnet_predict(bgr_face):
    if ort is None or _antispoof_session is None:
        return True, 1.0, np.array([0.0, 1.0], dtype=np.float32)
    try:
        x = _prepare_antispoof_input(bgr_face)
        logits = _antispoof_session.run([_antispoof_output_name], {_antispoof_input_name: x})[0]
        if logits.ndim == 1:
            logits = logits[0][None, ...]
        C = int(logits.shape[1]) if logits.ndim == 2 else 1

        if C >= 2:
            probs = _softmax(logits.astype(np.float32), axis=1)[0]
            live_idx = int(_antispoof_live_index) if _antispoof_live_index is not None else (2 if C == 3 else 1)
            live_score = float(probs[live_idx]) if 0 <= live_idx < C else float(np.max(probs))
        else:
            probs = logits.astype(np.float32)[0]
            live_score = float(probs.squeeze()); C = 1

        th = float(_antispoof_thresholds.get(_antispoof_mode, 0.55))
        is_live = bool(live_score >= th)

        logging.debug("[antispoof] C=%d preprocess=%s live_idx=%s score=%.3f th=%.2f",
                      C, _antispoof_preprocess,
                      (_antispoof_live_index if _antispoof_live_index is not None else "auto"),
                      live_score, th)
        return is_live, live_score, probs
    except Exception:
        logging.exception("MiniFASNet inference failed")
        return True, 1.0, np.array([0.0, 1.0], dtype=np.float32)


# ============== Heuristics untuk foto/gambar/cluster ==============
def _inter_ocular_px(kps):
    try:
        p0 = kps[0]; p1 = kps[1]
        return float(np.hypot(p0[0] - p1[0], p0[1] - p1[1]))
    except Exception:
        return 0.0


def _expand_patch(bgr, bbox, margin_ratio=0.90):
    H, W = bgr.shape[:2]
    x1, y1, x2, y2 = bbox
    w = x2 - x1; h = y2 - y1
    m = int(max(w, h) * float(margin_ratio))
    xx1 = max(0, x1 - m); yy1 = max(0, y1 - m)
    xx2 = min(W - 1, x2 + m); yy2 = min(H - 1, y2 + m)
    if xx2 <= xx1 or yy2 <= yy1:
        return None, (x1, y1, x2, y2)
    return bgr[yy1:yy2, xx1:xx2].copy(), (xx1, yy1, xx2, yy2)


def _edge_density(img):
    if img is None or img.size == 0:
        return 0.0
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (3, 3), 0)
    edges = cv2.Canny(g, 70, 140, L2gradient=True)
    return float((edges > 0).mean())


def _resize_limit(img, max_side=256):
    """Resize agar sisi terpanjang <= max_side (hemat komputasi)."""
    h, w = img.shape[:2]
    s = float(max(h, w))
    if s <= max_side:
        return img
    sc = max_side / s
    return cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)


def _find_phone_rectangle(patch_bgr):
    """
    Cari 4 sisi layar (dua vertikal + dua horizontal) yang membentuk
    persegi panjang dengan rasio aspek 1.3–2.6 (≈ layar HP).
    """
    try:
        if patch_bgr is None or patch_bgr.size == 0:
            return False
        img = _resize_limit(patch_bgr, 256)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(gray, 65, 140, L2gradient=True)

        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80,
                                minLineLength=int(0.55*min(img.shape[:2])),
                                maxLineGap=10)
        if lines is None:
            return False

        H, W = img.shape[:2]
        verts, hors = [], []
        for l in lines[:, 0, :]:
            x1, y1, x2, y2 = map(int, l.tolist())
            dx, dy = x2 - x1, y2 - y1
            ang = np.degrees(np.arctan2(dy, dx))
            length = np.hypot(dx, dy)
            if length < 0.55*min(H, W):
                continue
            if abs(abs(ang) - 90) < 12:
                verts.append((x1, y1, x2, y2))
            elif abs(ang) < 12:
                hors.append((x1, y1, x2, y2))

        if len(verts) < 2 or len(hors) < 2:
            return False

        # Cari pasangan sisi kiri-kanan & atas-bawah
        vx = sorted([min(v[0], v[2]) for v in verts])
        vy = sorted([max(v[0], v[2]) for v in verts])
        hx = sorted([min(h[1], h[3]) for h in hors])
        hy = sorted([max(h[1], h[3]) for h in hors])
        left = vx[0]; right = vy[-1]; top = hx[0]; bottom = hy[-1]

        w = max(1, right - left); h = max(1, bottom - top)
        ar = float(max(w, h)) / float(min(w, h) + 1e-6)

        # Harus berada dekat tepi patch (menandakan bingkai penuh)
        margin_ok = (left < 0.18*W) and (right > 0.82*W) and (top < 0.18*H) and (bottom > 0.82*H)
        return margin_ok and (1.3 <= ar <= 2.6)
    except Exception:
        return False


def _grid_periodicity_score(gray):
    """
    Ukur periodisitas pola grid (subpiksel layar) via autokorelasi 1D pada
    pita horizontal & vertikal (lag 2..6 piksel).
    """
    try:
        g = _resize_limit(gray, 192)
        if g.ndim == 3:
            g = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
        g = cv2.GaussianBlur(g, (3, 3), 0)

        h, w = g.shape[:2]
        # pita horizontal & vertikal di tengah
        th = max(8, h // 8); tw = max(8, w // 8)
        band_h = g[h//2 - th//2:h//2 + th//2, :]
        band_v = g[:, w//2 - tw//2:w//2 + tw//2]

        # ke kanan
        row = band_h.mean(axis=0) - band_h.mean()
        ac = np.correlate(row, row, mode='full'); ac = ac[ac.size//2:]
        ac = ac / (ac[0] + 1e-6)
        # ke bawah
        col = band_v.mean(axis=1) - band_v.mean()
        ac2 = np.correlate(col, col, mode='full'); ac2 = ac2[ac2.size//2:]
        ac2 = ac2 / (ac2[0] + 1e-6)

        hi1 = float(np.max(ac[2:min(8, ac.size)])) if ac.size > 8 else 0.0
        hi2 = float(np.max(ac2[2:min(8, ac2.size)])) if ac2.size > 8 else 0.0
        return max(hi1, hi2)
    except Exception:
        return 0.0


def _screen_like_heuristic(bgr_full, bbox, face_crop=None):
    """
    Heuristik kuat utk layar/HP:
    - Deteksi bingkai layar (4 sisi) & aspek.
    - Periodisitas grid piksel.
    - Rasio piksel terang & saturasi tinggi.
    - Tekstur datar (varian Laplacian rendah).
    Kondisi digabung konservatif agar manusia tidak salah-flag.
    """
    try:
        patch, _ = _expand_patch(bgr_full, bbox, 0.90)
        if patch is None or patch.size == 0:
            return False

        # Quick stats
        hsv = cv2.cvtColor(_resize_limit(patch, 256), cv2.COLOR_BGR2HSV)
        sat_mean = float(hsv[:, :, 1].mean()) / 255.0
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        bright_ratio = float((gray >= 235).mean())
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        edge_dense = _edge_density(patch)

        # Sinyal khas layar
        has_rect = _find_phone_rectangle(patch)
        periodic = _grid_periodicity_score(gray)

        # Kombinasi aturan (dioptimalkan agar agresif ke layar, aman utk manusia):
        # 1) Ada bingkai + cukup terang/edge → sangat mungkin HP
        if has_rect and (bright_ratio >= 0.15 or edge_dense >= 0.22):
            return True
        # 2) Periodisitas grid kuat + tingkat terang sedang
        if periodic >= 0.38 and bright_ratio >= 0.12:
            return True
        # 3) Terang & saturasi tinggi & tekstur datar → konten layar vivid
        if (bright_ratio >= 0.30 and sat_mean >= 0.30 and lap_var < 24.0):
            return True
        # 4) Edge sangat terstruktur + periodicitas moderat
        if edge_dense >= 0.28 and periodic >= 0.32:
            return True
    except Exception:
        return False
    return False


def _match_prev_centers(curr_centers, prev_centers, max_dist=40.0):
    matches = []
    used_prev = set()
    for c in curr_centers:
        distances = [np.hypot(c[0]-p[0], c[1]-p[1]) for p in prev_centers]
        if not distances:
            continue
        j = int(np.argmin(distances))
        if distances[j] <= max_dist and j not in used_prev:
            matches.append((c, prev_centers[j]))
            used_prev.add(j)
    return matches


def _small_faces_coherent_motion(dets, prev_small_centers):
    """Deteksi poster/kalender digerakkan bersama-sama."""
    small = []
    for d in dets:
        x1, y1, x2, y2 = d["bbox"]
        w = x2 - x1; h = y2 - y1
        if min(w, h) < 80:
            cx = (x1 + x2) * 0.5
            cy = (y1 + y2) * 0.5
            small.append((cx, cy))
    if len(small) < 6 or not prev_small_centers:
        return False

    matches = _match_prev_centers(small, prev_small_centers, max_dist=50.0)
    if len(matches) < 4:
        return False

    vecs = np.array([[c[0]-p[0], c[1]-p[1]] for (c, p) in matches], dtype=np.float32)
    mags = np.linalg.norm(vecs, axis=1)
    if np.median(mags) < 1.2:
        return False
    if np.std(vecs[:, 0]) < 2.0 and np.std(vecs[:, 1]) < 2.0:
        return True
    return False


# ============== Frame processing ==============
def process_frame_for_faces(
    frame_rgb,
    known_faces=None,
    match_threshold=0.6,
    require_human_check=False,
    exposure_enabled=True,
    exposure_gain=1.4,
    min_luminance=60,
    antispoof_backend="minifasnet",
    min_live_face_size=90,
    min_interocular_px=38,
    suppress_small_faces_when_antispoof=True,
    max_faces_per_frame=8,  # throttle agar GUI tetap responsif
):
    """
    Deteksi wajah → anotasi (bbox, nama, skor).
    Urutan: deteksi → liveness → heuristik layar (HP/monitor) → matching.
    """
    global _prev_small_centers, _prev_frame_size
    annotations = []
    known_faces = known_faces or []
    if frame_rgb is None:
        logging.debug("[ann] n=0 (frame None)")
        return annotations

    dets = _detect_with_insightface(frame_rgb)
    H, W = frame_rgb.shape[:2]

    if _prev_frame_size != (W, H):
        _prev_small_centers = []
    _prev_frame_size = (W, H)

    dets.sort(key=lambda d: (d["bbox"][2]-d["bbox"][0])*(d["bbox"][3]-d["bbox"][1]), reverse=True)

    if len(dets) > max_faces_per_frame:
        dets = dets[:max_faces_per_frame]

    suppress_cluster = _small_faces_coherent_motion(dets, _prev_small_centers)

    if not hasattr(process_frame_for_faces, "_live_hist"):
        process_frame_for_faces._live_hist = []

    bgr_full = _ensure_bgr_uint8(frame_rgb)
    curr_small_centers = []

    for d in dets:
        bbox = d.get("bbox"); emb = d.get("embedding", None); kps = d.get("kps", None)
        if not bbox:
            continue

        x1, y1, x2, y2 = map(int, bbox)
        x1 = max(0, min(W - 1, x1)); x2 = max(0, min(W - 1, x2))
        y1 = max(0, min(H - 1, y1)); y2 = max(0, min(H - 1, y2))
        if x2 <= x1 or y2 <= y1:
            continue

        w = x2 - x1; h = y2 - y1
        if min(w, h) < 80:
            curr_small_centers.append(((x1+x2)*0.5, (y1+y2)*0.5))

        # --- siapkan crop wajah (prioritas aligned 80x80) ---
        bgr_face = None
        try:
            if _HAS_ALIGN and kps is not None and np.asarray(kps).shape == (5, 2):
                bgr_face = face_align.norm_crop(bgr_full, kps, image_size=80)
            else:
                crop_rgb = frame_rgb[y1:y2, x1:x2]
                if crop_rgb.size:
                    bgr_face = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2BGR)
        except Exception:
            crop_rgb = frame_rgb[y1:y2, x1:x2]
            if crop_rgb.size:
                bgr_face = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2BGR)

        backend = str(antispoof_backend or "off").strip().lower()

        # ---- Exposure ringan (opsional) ----
        if bgr_face is not None and bgr_face.size > 0 and exposure_enabled:
            try:
                gray_face = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)
                mean_lum = float(gray_face.mean()) if gray_face.size else 255.0
                if mean_lum < float(min_luminance):
                    ycrcb = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2YCrCb)
                    y, cr, cb = cv2.split(ycrcb)
                    y = cv2.convertScaleAbs(y, alpha=exposure_gain, beta=0)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    y = clahe.apply(y)
                    bgr_face = cv2.cvtColor(cv2.merge((y, cr, cb)), cv2.COLOR_YCrCb2BGR)
            except Exception:
                pass

        # ---- Liveness dulu ----
        antispoof_checked = False
        antispoof_live = True
        if bgr_face is not None and bgr_face.size > 0:
            if backend in ("heuristic", "heuristik"):
                antispoof_checked = True
                gray = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)
                antispoof_live = gray.mean() >= 20.0
            elif backend in ("heuristic_medium", "heuristik_medium", "heuristic-medium"):
                antispoof_checked = True
                gray = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)
                lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                antispoof_live = (gray.mean() >= 25.0) and (lap_var >= 55.0)
            elif backend == "minifasnet":
                antispoof_checked = True
                cur_live, _, _ = _minifasnet_predict(bgr_face)
                if _antispoof_mode == "medium":
                    hist = getattr(process_frame_for_faces, "_live_hist", [])
                    hist.append(bool(cur_live))
                    if len(hist) > _antispoof_smooth_k:
                        hist.pop(0)
                    setattr(process_frame_for_faces, "_live_hist", hist)
                    antispoof_live = (sum(hist) >= int(np.ceil(_antispoof_smooth_k / 2)))
                else:
                    antispoof_live = bool(cur_live)

        if antispoof_checked and not antispoof_live:
            continue  # bukan live → drop

        # ------ FILTER FOTO/GAMBAR (setelah liveness) ------
        if backend != "off" and bgr_face is not None and bgr_face.size > 0:
            # a) Poster/kalender bergerak bersama
            if _small_faces_coherent_motion([d], _prev_small_centers) and min(w, h) < 90:
                continue
            # b) Banyak wajah → saring ukuran kecil (noise)
            if len(dets) >= 6 and min(w, h) < 70:
                continue
            # c) Heuristik layar/HP kuat (baru)
            if _screen_like_heuristic(bgr_full, (x1, y1, x2, y2), face_crop=bgr_face):
                continue
            # d) Tambahan: jika sangat kecil & inter-ocular kecil & banyak deteksi → buang
            if suppress_small_faces_when_antispoof:
                too_small_box = (w < int(min_live_face_size)) or (h < int(min_live_face_size))
                too_small_eye = False
                if d.get("kps", None) is not None:
                    iod = _inter_ocular_px(d["kps"])
                    too_small_eye = iod < float(min_interocular_px)
                if (too_small_box or too_small_eye) and len(dets) >= 3:
                    continue

        # ---- Matching (opsional) ----
        name = "tidak dikenal"; match = False; score = 0.0; best_name = None
        if d.get("embedding", None) is not None and known_faces:
            best_score = -1.0
            for kname, kemb in known_faces:
                try:
                    m, s = is_match(d["embedding"], kemb, threshold=match_threshold)
                except Exception:
                    continue
                if s > best_score:
                    best_score = float(s); best_name = kname
                if m:
                    match = True; name = kname; score = float(s); break
            if not match and best_score >= 0:
                score = float(best_score)

        annotations.append({
            "bbox": (x1, y1, x2, y2),
            "name": name,
            "match": match,
            "score": score,
            "skipped": False,
            "best_name": best_name,
            "antispoof_checked": antispoof_checked,
            "antispoof_live": antispoof_live,
        })

    _prev_small_centers = curr_small_centers[:50]
    logging.debug("[ann] n=%d", len(annotations))
    return annotations


# ============== Load antispoof ONNX ==============
def load_antispoof_model(path: str = "", use_gpu: bool = False):
    try:
        if ort is None:
            logging.error("onnxruntime not available; cannot load antispoof model.")
            return False

        model_path = ""
        p = (path or "").strip()
        if p and os.path.isdir(p):
            for fn in os.listdir(p):
                if fn.lower().endswith(".onnx"):
                    model_path = os.path.join(p, fn); break
        elif p and os.path.isfile(p):
            model_path = p
        else:
            BASE = os.path.dirname(os.path.abspath(__file__))
            default_dir = os.path.join(BASE, "models", "antispoof", "minifasnet")
            if os.path.isdir(default_dir):
                for fn in os.listdir(default_dir):
                    if fn.lower().endswith(".onnx"):
                        model_path = os.path.join(default_dir, fn); break

        if not model_path:
            logging.warning("Antispoof ONNX not found. Provide a valid file or folder.")
            return False

        global _antispoof_session, _antispoof_input_name, _antispoof_output_name, _antispoof_input_shape
        providers = ["CPUExecutionProvider"]
        if use_gpu:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        _antispoof_session = ort.InferenceSession(model_path, providers=providers)

        meta = _antispoof_session.get_inputs()[0]
        _antispoof_input_name = meta.name
        _antispoof_input_shape = meta.shape
        _antispoof_output_name = _antispoof_session.get_outputs()[0].name

        logging.info("Loaded antispoof ONNX: %s | providers=%s", os.path.basename(model_path), providers)
        return True
    except Exception:
        logging.exception("Failed to load antispoof ONNX model")
        return False
