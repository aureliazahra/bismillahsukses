# main.py — Double-click kamera => buka window baru, langsung FULLSCREEN.
# Di fullscreen popup: tidak bisa minimize/close/keluar; TUTUP hanya dengan double-click lagi.
import sys
import logging
import os
import math
import json
import cv2

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QFormLayout, QLineEdit, QSpinBox, QMessageBox,
    QComboBox, QDoubleSpinBox, QCheckBox, QFileDialog, QSizePolicy, QGroupBox, QSlider, QShortcut,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import QKeySequence, QPixmap

from gui import CameraWidget, read_cameras_config, write_cameras_config, read_app_config, GLOBAL_FACE_WORKER_POOL
from logger import init_logger
import detector

try:
    cv2.setNumThreads(1)
except Exception:
    pass

init_logger(logging.INFO)
logging.info("App start (popup fullscreen locked)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_CONFIG_PATH = os.path.join(BASE_DIR, "app_config.json")
TARGET_DIR = os.path.join(BASE_DIR, "target_faces")
os.makedirs(TARGET_DIR, exist_ok=True)


class _DCLabel(QLabel):
    double_clicked = pyqtSignal()
    def mouseDoubleClickEvent(self, e):
        try: self.double_clicked.emit()
        except Exception: pass
        super().mouseDoubleClickEvent(e)


# ---------- Popup Window menampilkan stream kamera (kiosk mode) ----------
from PyQt5.QtWidgets import QMainWindow as BaseWindow

class CameraPopupWindow(BaseWindow):
    def __init__(self, source_widget: CameraWidget):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._src = source_widget
        self.setWindowTitle(f"Camera — {self._src.name}")
        self.resize(960, 540)

        # Kiosk-like: tanpa frame & stay on top
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        central = QWidget(); self.setCentralWidget(central)
        lay = QVBoxLayout(central); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        self.view = _DCLabel()
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self.view)

        self._last_qimage = None
        self._allow_close = False

        self._src.thread.frame_ready.connect(self.on_frame)
        self.view.double_clicked.connect(self.request_close)
        self.showFullScreen()

    def keyPressEvent(self, e):  # blokir semua hotkey
        return

    def request_close(self):
        self._allow_close = True
        try: self.close()
        finally: self._allow_close = False

    def on_frame(self, qimg):
        self._last_qimage = qimg
        try:
            pix = QPixmap.fromImage(qimg)
            if self.view.width() > 0 and self.view.height() > 0:
                pix = pix.scaled(self.view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.view.setPixmap(pix)
        except Exception:
            pass

    def resizeEvent(self, event):
        try:
            if self._last_qimage is not None:
                pix = QPixmap.fromImage(self._last_qimage)
                pix = pix.scaled(self.view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.view.setPixmap(pix)
        except Exception:
            pass
        return super().resizeEvent(event)

    def closeEvent(self, event):
        if not self._allow_close:
            event.ignore(); return
        try: self._src.thread.frame_ready.disconnect(self.on_frame)
        except Exception: pass
        event.accept()


class AdminPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.cameras = read_cameras_config()
        self.app_cfg = read_app_config()
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(); layout.setContentsMargins(6, 6, 6, 6); layout.setSpacing(6); self.setLayout(layout)

        layout.addWidget(QLabel("Cameras"))
        self.list_widget = QListWidget(); self.list_widget.currentRowChanged.connect(self.on_select)
        layout.addWidget(self.list_widget)
        self.reload_list()

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.source_edit = QLineEdit()
        self.display_interval_spin = QSpinBox(); self.display_interval_spin.setRange(1, 2000)
        self.detect_interval_spin = QSpinBox(); self.detect_interval_spin.setRange(1, 240)
        self.reconnect_spin = QSpinBox(); self.reconnect_spin.setRange(1, 60)
        self.frame_buffer_spin = QSpinBox(); self.frame_buffer_spin.setRange(1, 10)
        self.exposure_chk = QCheckBox()
        self.exposure_gain_spin = QDoubleSpinBox(); self.exposure_gain_spin.setRange(1.0, 5.0); self.exposure_gain_spin.setSingleStep(0.1)
        self.min_luminance_spin = QSpinBox(); self.min_luminance_spin.setRange(0, 255)

        form.addRow("Name", self.name_edit)
        form.addRow("Source (int or rtsp)", self.source_edit)
        form.addRow("Display refresh (ms)", self.display_interval_spin)
        form.addRow("Detect every N frames", self.detect_interval_spin)
        form.addRow("Reconnect delay (s)", self.reconnect_spin)
        form.addRow("Frame buffer (grabs)", self.frame_buffer_spin)
        form.addRow("Exposure enabled", self.exposure_chk)
        form.addRow("Exposure gain", self.exposure_gain_spin)
        form.addRow("Min luminance", self.min_luminance_spin)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Tambah"); self.btn_update = QPushButton("Update")
        self.btn_delete = QPushButton("Hapus"); self.btn_start = QPushButton("Start"); self.btn_stop = QPushButton("Stop")
        for b in (self.btn_add, self.btn_update, self.btn_delete, self.btn_start, self.btn_stop): btn_row.addWidget(b)

        self.btn_add.clicked.connect(self.on_add); self.btn_update.clicked.connect(self.on_update)
        self.btn_delete.clicked.connect(self.on_delete); self.btn_start.clicked.connect(self.on_start_selected)
        self.btn_stop.clicked.connect(self.on_stop_selected)

        layout.addLayout(form); layout.addLayout(btn_row)

        box = QGroupBox("Pengaturan Global"); box_layout = QFormLayout(); box.setLayout(box_layout)
        self.device_combo = QComboBox(); self.device_combo.addItems(["CPU","GPU"])
        self.device_combo.setCurrentIndex(1 if str(self.app_cfg.get("device","CPU")).upper()=="GPU" else 0)
        self.debug_chk = QCheckBox(); self.debug_chk.setChecked(bool(self.app_cfg.get("debug", False)))

        self.detector_combo = QComboBox(); self.detector_combo.addItems(["insightface"])
        self.detector_combo.setCurrentText("insightface")

        # ==== Tambah opsi heuristic_low & heuristic_high ====
        self.antispoof_combo = QComboBox()
        self.antispoof_combo.addItems(["off","heuristic_low","heuristic_medium","heuristic_high","minifasnet"])
        self.antispoof_combo.setCurrentText(self.app_cfg.get("antispoof_backend","off"))

        self.antispoof_model_edit = QLineEdit(self.app_cfg.get("antispoof_model_path",""))
        self.btn_browse_antispoof = QPushButton("Browse ONNX…"); self.btn_browse_antispoof.clicked.connect(self.on_browse_antispoof)

        self.match_threshold_global = QDoubleSpinBox(); self.match_threshold_global.setRange(0.0,1.0); self.match_threshold_global.setSingleStep(0.01)
        self.match_threshold_global.setValue(float(self.app_cfg.get("match_threshold",0.60)))
        self.red_cutoff_spin = QDoubleSpinBox(); self.red_cutoff_spin.setRange(0.0,1.0); self.red_cutoff_spin.setSingleStep(0.01)
        self.red_cutoff_spin.setValue(float(self.app_cfg.get("red_cutoff_threshold",0.40)))

        self.require_human_global = QCheckBox(); self.require_human_global.setChecked(bool(self.app_cfg.get("require_human_check",True)))

        self.box_thick_slider = QSlider(Qt.Horizontal); self.box_thick_slider.setMinimum(1); self.box_thick_slider.setMaximum(6)
        self.box_thick_slider.setValue(int(self.app_cfg.get("box_thickness_max",6)))
        self.box_thick_value = QLabel(str(self.box_thick_slider.value()))
        self.box_thick_slider.valueChanged.connect(lambda v: self.box_thick_value.setText(str(v)))
        row = QHBoxLayout(); row.addWidget(self.box_thick_slider); row.addWidget(self.box_thick_value)

        self.save_combo = QComboBox(); self.save_combo.addItems(["photo","video3s"])
        self.save_combo.setCurrentText(self.app_cfg.get("save_mode","photo"))
        self.save_which_combo = QComboBox(); self.save_which_combo.addItems(["green only","green & orange"])
        self.save_which_combo.setCurrentIndex(0 if str(self.app_cfg.get("save_which","green"))=="green" else 1)

        self.log_combo = QComboBox(); self.log_combo.addItems(["realtime","1","3","5","7","10"])
        curr = int(self.app_cfg.get("log_interval_seconds",0))
        self.log_combo.setCurrentIndex(["realtime","1","3","5","7","10"].index("realtime" if curr==0 else str(curr)))

        self.btn_upload_targets = QPushButton("Upload Wajah Target (global)…")
        self.btn_upload_targets.clicked.connect(self.on_upload_targets_global)

        self.btn_apply_device = QPushButton("Simpan _Terapkan Global")
        self.btn_apply_device.clicked.connect(self.on_apply_device)

        # ==== Tambahan toggle anti-spoof & filter wajah kecil ====
        self.min_live_face_size_spin = QSpinBox(); self.min_live_face_size_spin.setRange(20, 400)
        self.min_live_face_size_spin.setValue(int(self.app_cfg.get("min_live_face_size", 90)))
        self.min_interocular_spin = QSpinBox(); self.min_interocular_spin.setRange(5, 200)
        self.min_interocular_spin.setValue(int(self.app_cfg.get("min_interocular_px", 38)))
        self.suppress_small_chk = QCheckBox(); self.suppress_small_chk.setChecked(bool(self.app_cfg.get("suppress_small_faces_when_antispoof", True)))

        self.preprocess_combo = QComboBox(); self.preprocess_combo.addItems(["rgb01","bgr01","rgb_norm","bgr_norm"])
        self.preprocess_combo.setCurrentText(self.app_cfg.get("antispoof_preprocess","bgr_norm"))
        self.live_index_spin = QSpinBox(); self.live_index_spin.setRange(-1, 4)
        self.live_index_spin.setValue(int(self.app_cfg.get("antispoof_live_index", 2)))
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["low","medium","high"])
        self.mode_combo.setCurrentText(self.app_cfg.get("antispoof_mode","medium"))
        self.smooth_k_spin = QSpinBox(); self.smooth_k_spin.setRange(1, 9)
        self.smooth_k_spin.setValue(int(self.app_cfg.get("antispoof_smooth_k", 3)))

        th = dict(self.app_cfg.get("antispoof_thresholds", {"low":0.40,"medium":0.55,"high":0.70}))
        self.th_low_spin = QDoubleSpinBox(); self.th_low_spin.setRange(0.0,1.0); self.th_low_spin.setSingleStep(0.01); self.th_low_spin.setValue(float(th.get("low",0.40)))
        self.th_med_spin = QDoubleSpinBox(); self.th_med_spin.setRange(0.0,1.0); self.th_med_spin.setSingleStep(0.01); self.th_med_spin.setValue(float(th.get("medium",0.55)))
        self.th_high_spin = QDoubleSpinBox(); self.th_high_spin.setRange(0.0,1.0); self.th_high_spin.setSingleStep(0.01); self.th_high_spin.setValue(float(th.get("high",0.70)))

        box_layout.addRow("Device", self.device_combo)
        box_layout.addRow("Debug", self.debug_chk)
        box_layout.addRow("Match threshold (0-1)", self.match_threshold_global)
        box_layout.addRow("Red cutoff (<)", self.red_cutoff_spin)
        box_layout.addRow("Require human-only check", self.require_human_global)
        box_layout.addRow("Small-face box thickness (max)", row)
        box_layout.addRow("Detector backend", self.detector_combo)
        box_layout.addRow("Anti-Spoof backend", self.antispoof_combo)
        box_layout.addRow("ONNX MiniFASNet", self.antispoof_model_edit)
        box_layout.addRow(self.btn_browse_antispoof)
        box_layout.addRow("Save mode (match)", self.save_combo)
        box_layout.addRow("Save which detections", self.save_which_combo)
        box_layout.addRow("Log interval (detik)", self.log_combo)

        # Baris tambahan (minimalis, di bagian bawah supaya tidak ganggu layout lain)
        box_layout.addRow(QLabel("— Anti-Spoof Options —"))
        box_layout.addRow("Preprocess", self.preprocess_combo)
        box_layout.addRow("Live index (-1=auto)", self.live_index_spin)
        box_layout.addRow("Mode", self.mode_combo)
        box_layout.addRow("Smooth K", self.smooth_k_spin)
        box_layout.addRow("Threshold low/med/high", self._hbox3(self.th_low_spin, self.th_med_spin, self.th_high_spin))
        box_layout.addRow(QLabel("— Small-Face Filter (aktif jika anti-spoof ≠ off) —"))
        box_layout.addRow("Min live face size (px)", self.min_live_face_size_spin)
        box_layout.addRow("Min inter-ocular (px)", self.min_interocular_spin)
        box_layout.addRow("Suppress small faces", self.suppress_small_chk)

        box_layout.addRow(self.btn_upload_targets)
        box_layout.addRow(self.btn_apply_device)
        layout.addWidget(box)

        self.status_log = QLabel("Ready.")
        self.status_log.setWordWrap(True)
        layout.addWidget(self.status_log)

        if self.cameras:
            self.list_widget.setCurrentRow(0); self.on_select(0)

    def _hbox3(self, a, b, c):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0,0,0,0); h.setSpacing(6)
        for x in (a,b,c): h.addWidget(x)
        return w

    def reload_list(self):
        self.list_widget.clear()
        for i, cam in enumerate(self.cameras):
            self.list_widget.addItem(f"[{i}] {cam.get('name','Camera')}")

    def on_select(self, idx):
        if idx < 0 or idx >= len(self.cameras): return
        cam = self.cameras[idx]
        self.name_edit.setText(str(cam.get("name","Camera")))
        self.source_edit.setText(str(cam.get("source","0")))
        self.display_interval_spin.setValue(int(cam.get("display_interval_ms",50)))
        self.detect_interval_spin.setValue(int(cam.get("detect_interval_frames",3)))
        self.reconnect_spin.setValue(int(cam.get("reconnect_delay",10)))
        self.frame_buffer_spin.setValue(int(cam.get("frame_buffer",1)))
        self.exposure_chk.setChecked(bool(cam.get("exposure_enabled",True)))
        self.exposure_gain_spin.setValue(float(cam.get("exposure_gain",1.4)))
        self.min_luminance_spin.setValue(int(cam.get("min_luminance",60)))

    def _gather_form(self):
        src_val = self.source_edit.text().strip()
        source = int(src_val) if src_val.isdigit() else src_val
        return {
            "name": self.name_edit.text().strip() or "Camera",
            "source": source,
            "display_interval_ms": int(self.display_interval_spin.value()),
            "detect_interval_frames": int(self.detect_interval_spin.value()),
            "reconnect_delay": int(self.reconnect_spin.value()),
            "frame_buffer": int(self.frame_buffer_spin.value()),
            "exposure_enabled": bool(self.exposure_chk.isChecked()),
            "exposure_gain": float(self.exposure_gain_spin.value()),
            "min_luminance": int(self.min_luminance_spin.value())
        }

    def on_add(self):
        try:
            cam = self._gather_form()
            self.cameras.append(cam)
            if not write_cameras_config(self.cameras): raise RuntimeError("write cameras.json failed")
            self.reload_list(); self.status_log.setText("Added camera. Reloaded list.")
            self.parent.reload_cameras()
        except Exception as e:
            logging.exception("Add camera failed"); QMessageBox.critical(self, "Error", f"Failed to add: {e}")

    def on_update(self):
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.cameras):
            QMessageBox.warning(self, "No selection", "Select a camera first"); return
        try:
            cam = self._gather_form()
            self.cameras[idx] = cam
            if not write_cameras_config(self.cameras): raise RuntimeError("write cameras.json failed")
            self.parent.reload_cameras(); self.reload_list()
            self.status_log.setText("Updated camera and reloaded running cameras.")
        except Exception as e:
            logging.exception("Update camera failed"); QMessageBox.critical(self, "Error", f"Failed to update: {e}")

    def on_delete(self):
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.cameras):
            QMessageBox.warning(self, "No selection", "Select a camera first"); return
        reply = QMessageBox.question(self, "Delete", f"Delete camera '{self.cameras[idx].get('name')}'?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes: return
        try:
            del self.cameras[idx]
            if not write_cameras_config(self.cameras): raise RuntimeError("write cameras.json failed")
            self.parent.reload_cameras(); self.reload_list()
            self.status_log.setText("Deleted camera and reloaded.")
        except Exception as e:
            logging.exception("Delete camera failed"); QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def on_start_selected(self):
        idx = self.list_widget.currentRow()
        if idx < 0: QMessageBox.warning(self, "No selection", "Select a camera first"); return
        self.parent.start_camera(idx); self.status_log.setText(f"Requested start for camera idx={idx}")

    def on_stop_selected(self):
        idx = self.list_widget.currentRow()
        if idx < 0: QMessageBox.warning(self, "No selection", "Select a camera first"); return
        self.parent.stop_camera(idx); self.status_log.setText(f"Requested stop for camera idx={idx}")

    def on_browse_antispoof(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Antispoof ONNX model", os.path.expanduser("~"), "ONNX files (*.onnx);All files (*)")
        if path: self.antispoof_model_edit.setText(path)

    def on_upload_targets_global(self):
        os.makedirs(TARGET_DIR, exist_ok=True)
        paths, _ = QFileDialog.getOpenFileNames(self, "Pilih foto wajah target (global)", os.path.expanduser("~"),
                                                "Images (*.jpg *.jpeg *.png *.bmp);;All files (*)")
        if not paths: return
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Nama Target", "Masukkan nama target:")
        if not ok or not name.strip():
            QMessageBox.warning(self, "Nama wajib", "Nama target harus diisi."); return
        safe = name.strip().replace("/", "_").replace("\\", "_")
        dest_dir = os.path.join(TARGET_DIR, safe); os.makedirs(dest_dir, exist_ok=True)
        copied = 0
        for p in paths:
            try:
                base = os.path.basename(p); dst = os.path.join(dest_dir, base)
                i = 1; nm, ext = os.path.splitext(base)
                while os.path.exists(dst):
                    dst = os.path.join(dest_dir, f"{nm}_{i}{ext}"); i += 1
                with open(p, "rb") as fsrc, open(dst, "wb") as fdst: fdst.write(fsrc.read())
                copied += 1
            except Exception:
                logging.exception("failed copying target face")
        self.parent.broadcast_reload_known_faces()
        QMessageBox.information(self, "Sukses", f"Copied {copied} file(s) ke target_faces/{safe} dan reload.")

    def on_apply_device(self):
        device = "GPU" if self.device_combo.currentIndex() == 1 else "CPU"
        debug_flag = bool(self.debug_chk.isChecked())
        detector_backend = self.detector_combo.currentText().strip().lower()  # selalu insightface
        antispoof_backend = self.antispoof_combo.currentText().strip().lower()
        save_mode = self.save_combo.currentText().strip().lower()
        save_which = "green" if self.save_which_combo.currentIndex()==0 else "green_orange"
        log_map = {"realtime":0, "1":1, "3":3, "5":5, "7":7, "10":10}
        log_interval = log_map[self.log_combo.currentText()]

        # kumpulkan threshold dict
        thresholds = {
            "low": float(self.th_low_spin.value()),
            "medium": float(self.th_med_spin.value()),
            "high": float(self.th_high_spin.value()),
        }
        live_index = int(self.live_index_spin.value())
        if live_index < 0:
            live_index = None  # auto

        cfg = {
            "device": device, "debug": debug_flag,
            "detector_backend": detector_backend,
            "antispoof_backend": antispoof_backend,
            "antispoof_model_path": self.antispoof_model_edit.text().strip(),
            "match_threshold": float(self.match_threshold_global.value()),
            "red_cutoff_threshold": float(self.red_cutoff_spin.value()),
            "require_human_check": bool(self.require_human_global.isChecked()),
            "box_thickness_max": int(self.box_thick_slider.value()),
            "save_mode": save_mode,
            "save_which": save_which,
            "log_interval_seconds": log_interval,

            # tambahan baru:
            "antispoof_preprocess": self.preprocess_combo.currentText(),
            "antispoof_live_index": live_index if live_index is not None else -1,
            "antispoof_mode": self.mode_combo.currentText(),
            "antispoof_thresholds": thresholds,
            "antispoof_smooth_k": int(self.smooth_k_spin.value()),
            "min_live_face_size": int(self.min_live_face_size_spin.value()),
            "min_interocular_px": int(self.min_interocular_spin.value()),
            "suppress_small_faces_when_antispoof": bool(self.suppress_small_chk.isChecked()),
        }
        try:
            with open(APP_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            QMessageBox.critical(self, "Error", "Failed to save app_config"); return
        try:
            use_gpu = True if device.upper()=="GPU" else False
            detector.initialize(use_gpu=use_gpu, detector_backend=detector_backend)
            if antispoof_backend == "minifasnet":
                detector.load_antispoof_model(cfg.get("antispoof_model_path",""))
            # terapkan parameter anti-spoof apapun backendnya — aman
            detector.set_antispoof_params(
                live_index=None if cfg.get("antispoof_live_index", -1) in (-1, None) else int(cfg.get("antispoof_live_index")),
                thresholds=thresholds,
                mode=cfg.get("antispoof_mode","medium"),
                preprocess=cfg.get("antispoof_preprocess","bgr_norm"),
                smooth_k=int(cfg.get("antispoof_smooth_k",3)),
            )
        except Exception:
            logging.exception("re-init detector failed")
        self.parent.reload_cameras()
        self.status_log.setText(f"Saved global config and reloaded cameras. Device={device}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition CCTV - Admin")
        self.resize(1200, 700)

        central = QWidget(); self.setCentralWidget(central)
        layout = QHBoxLayout(); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0); central.setLayout(layout)

        # --- Grid area dibungkus ScrollArea ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # fokus scroll vertikal
        self.scroll.viewport().installEventFilter(self)  # agar bisa hitung 2x2 berdasarkan tinggi viewport
        container = QWidget()
        self.grid_layout = QGridLayout(); self.grid_layout.setContentsMargins(0, 0, 0, 0); self.grid_layout.setSpacing(0)
        container.setLayout(self.grid_layout)
        self.scroll.setWidget(container)

        layout.addWidget(self.scroll, 1)

        self.admin = AdminPanel(self)
        layout.addWidget(self.admin)
        layout.setStretch(0, 1); layout.setStretch(1, 0)

        try:
            self.gear_btn = QPushButton("⚙", self)
            self.gear_btn.setToolTip("Tampilkan/sembunyikan panel pengaturan (F10)")
            self.gear_btn.setFixedSize(35, 35)
            self.gear_btn.clicked.connect(self.toggle_admin_panel)
            self.gear_btn.raise_()
            self.gear_btn.move(self.width() - self.gear_btn.width() - 8, 8)
        except Exception:
            self.gear_btn = None

        try:
            self._admin_shortcut = QShortcut(QKeySequence(Qt.Key_F10), self)
            self._admin_shortcut.activated.connect(self.toggle_admin_panel)
        except Exception:
            pass
        try:
            self._fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
            self._fs_shortcut.activated.connect(self.toggle_fullscreen_window)
        except Exception:
            pass

        self._popups = {}          # {CameraWidget: CameraPopupWindow}
        self.camera_widgets = []   # list[CameraWidget]
        self._tile_wrappers = []   # list[QWidget] pembungkus untuk kontrol tinggi

        self.load_and_show_cameras()

        # --- Admin Panel default TERTUTUP saat start ---
        try:
            self.admin.setVisible(False)
        except Exception:
            pass

        # pastikan ukuran tile update setelah layout siap
        QTimer.singleShot(0, self.update_tile_sizes)

    # ---------- layout helpers ----------
    def _grid_shape(self, n):
        if n <= 0: return 0, 0
        cols = 2  # kolom tetap 2; viewport selalu 2 baris (2x2) dengan tinggi tile = 1/2 viewport
        rows = int(math.ceil(n / cols))
        return rows, cols

    def _apply_grid_stretch(self, rows, cols):
        for r in range(rows): self.grid_layout.setRowStretch(r, 1)
        for c in range(cols): self.grid_layout.setColumnStretch(c, 1)

    def _tile_height(self):
        vh = max(1, self.scroll.viewport().height())
        # dua baris per viewport:
        return max(240, vh // 2)

    def update_tile_sizes(self):
        h = self._tile_height()
        for w in self._tile_wrappers:
            try:
                w.setMinimumHeight(h)
                w.setMaximumHeight(h)
            except Exception:
                pass

    # ---------- popup logic ----------
    def _open_popup(self, widget: CameraWidget):
        pop = CameraPopupWindow(widget)
        def _cleanup():
            try:
                if widget in self._popups: del self._popups[widget]
            except Exception: pass
        pop.destroyed.connect(_cleanup)
        pop.show()
        self._popups[widget] = pop

    def _toggle_popup(self, widget: CameraWidget):
        pop = self._popups.get(widget)
        if pop is None or not pop.isVisible():
            self._open_popup(widget)
        else:
            try: pop.request_close()
            except Exception: pass

    def on_full_toggle_requested(self, widget: CameraWidget):
        try: self._toggle_popup(widget)
        except Exception: logging.exception("toggle popup failed")

    # ---------- cameras ----------
    def load_and_show_cameras(self):
        try:
            for pop in list(self._popups.values()):
                try: pop.request_close()
                except Exception: pass
            self._popups.clear()
        except Exception:
            pass

        cams = read_cameras_config()

        # bersihkan grid lama
        for w in self.camera_widgets:
            try:
                if w: w.stop()
            except Exception: pass
        for wr in self._tile_wrappers:
            try:
                self.grid_layout.removeWidget(wr); wr.deleteLater()
            except Exception: pass
        self.camera_widgets.clear()
        self._tile_wrappers.clear()

        rows, cols = self._grid_shape(len(cams))
        positions = [(r, c) for r in range(rows) for c in range(cols)]
        for idx, cam in enumerate(cams):
            try:
                cam_widget = CameraWidget(cam)
                try: cam_widget.full_toggle_requested.connect(self.on_full_toggle_requested)
                except Exception: pass

                # Bungkus agar bisa dikunci tinggi tile = 1/2 viewport
                wrapper = QWidget()
                v = QVBoxLayout(wrapper)
                v.setContentsMargins(0, 0, 0, 0)
                v.setSpacing(0)
                v.addWidget(cam_widget)

                r, c = positions[idx]
                self.grid_layout.addWidget(wrapper, r, c)

                self.camera_widgets.append(cam_widget)
                self._tile_wrappers.append(wrapper)
            except Exception:
                logging.exception("Failed creating CameraWidget for idx=%d", idx)

        self._apply_grid_stretch(rows, cols)
        self.update_tile_sizes()

    def reload_cameras(self):
        logging.info("reload_cameras invoked"); self.load_and_show_cameras()

    def broadcast_reload_known_faces(self):
        for w in self.camera_widgets:
            try:
                if w and hasattr(w, "thread"): w.thread.reload_known_faces()
            except Exception: pass

    def start_camera(self, idx):
        cams = read_cameras_config()
        if idx < 0 or idx >= len(cams):
            QMessageBox.warning(self, "Invalid index", "Camera index out of range"); return
        try:
            # hapus yang lama di posisi idx (jika ada)
            if idx < len(self.camera_widgets) and self.camera_widgets[idx]:
                try:
                    pop = self._popups.get(self.camera_widgets[idx])
                    if pop: pop.request_close()
                    if self.camera_widgets[idx] in self._popups: del self._popups[self.camera_widgets[idx]]
                except Exception: pass

                # cari wrapper di posisi grid yang sama
                try:
                    old_wrapper = self._tile_wrappers[idx]
                    self.grid_layout.removeWidget(old_wrapper); old_wrapper.deleteLater()
                except Exception: pass

                try: self.camera_widgets[idx].stop()
                except Exception: pass

            cam = cams[idx]
            cam_widget = CameraWidget(cam)
            try: cam_widget.full_toggle_requested.connect(self.on_full_toggle_requested)
            except Exception: pass

            wrapper = QWidget()
            v = QVBoxLayout(wrapper); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
            v.addWidget(cam_widget)

            rows, cols = self._grid_shape(len(cams))
            positions = [(r, c) for r in range(rows) for c in range(cols)]
            r, c = positions[idx]
            self.grid_layout.addWidget(wrapper, r, c)

            # simpan kembali referensi
            if idx < len(self.camera_widgets): self.camera_widgets[idx] = cam_widget
            else:
                while len(self.camera_widgets) < idx: self.camera_widgets.append(None)
                self.camera_widgets.append(cam_widget)
            if idx < len(self._tile_wrappers): self._tile_wrappers[idx] = wrapper
            else:
                while len(self._tile_wrappers) < idx: self._tile_wrappers.append(QWidget())
                self._tile_wrappers.append(wrapper)

            self._apply_grid_stretch(rows, cols)
            self.update_tile_sizes()
        except Exception:
            logging.exception("start_camera failed for idx=%d", idx); QMessageBox.critical(self, "Error", "Failed to start camera")

    def stop_camera(self, idx):
        if idx < 0 or idx >= len(self.camera_widgets):
            QMessageBox.warning(self, "Invalid index", "Camera index out of range or not running"); return
        try:
            w = self.camera_widgets[idx]
            if not w:
                QMessageBox.information(self, "Info", "Camera not running"); return
            try:
                pop = self._popups.get(w)
                if pop: pop.request_close()
                if w in self._popups: del self._popups[w]
            except Exception: pass
            w.stop()

            try:
                wr = self._tile_wrappers[idx]
                self.grid_layout.removeWidget(wr); wr.deleteLater()
            except Exception: pass

            self.camera_widgets[idx] = None
            self._tile_wrappers[idx] = QWidget()
            self.update_tile_sizes()
        except Exception:
            logging.exception("stop_camera failed idx=%d", idx); QMessageBox.critical(self, "Error", "Failed to stop camera")

    # ---------- window & events ----------
    def toggle_admin_panel(self):
        try:
            self.admin.setVisible(not self.admin.isVisible())
            cw_layout = self.centralWidget().layout()
            cw_layout.setStretch(0, 1); cw_layout.setStretch(1, 0)
            QTimer.singleShot(0, self.update_tile_sizes)
        except Exception:
            pass

    def toggle_fullscreen_window(self):
        try:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()
            QTimer.singleShot(0, self.update_tile_sizes)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if obj is self.scroll.viewport() and event.type() == QEvent.Resize:
            self.update_tile_sizes()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        try:
            if hasattr(self, "gear_btn") and self.gear_btn is not None:
                self.gear_btn.move(self.width() - self.gear_btn.width() - 8, 8)
        except Exception:
            pass
        self.update_tile_sizes()
        return super().resizeEvent(event)

    def closeEvent(self, event):
        try:
            for pop in list(self._popups.values()):
                try: pop.request_close()
                except Exception: pass
            self._popups.clear()
        except Exception:
            pass
        for w in self.camera_widgets:
            try:
                if w: w.stop()
            except Exception: pass
        try: GLOBAL_FACE_WORKER_POOL.shutdown(wait=False)
        except Exception: pass
        event.accept()


def main():
    cfg = read_app_config()
    device = cfg.get("device", "CPU")
    use_gpu = True if str(device).strip().upper() == "GPU" else False
    debug_flag = bool(cfg.get("debug", False))
    if debug_flag: os.environ["DETECTOR_DEBUG"] = "1"
    else: os.environ.pop("DETECTOR_DEBUG", None)

    det_backend = "insightface"  # paksa insightface
    logging.info("Initializing detector; use_gpu=%s backend=%s debug=%s", use_gpu, det_backend, debug_flag)
    detector.initialize(use_gpu=use_gpu, detector_backend=det_backend)
    if cfg.get("antispoof_backend","off") == "minifasnet":
        try: detector.load_antispoof_model(cfg.get("antispoof_model_path",""))
        except Exception: logging.exception("Failed loading antispoof model")

    # Terapkan parameter anti-spoof dari app_config saat startup
    try:
        live_idx = cfg.get("antispoof_live_index", None)
        if live_idx in (-1, "", None):
            live_idx = None
        thresholds = cfg.get("antispoof_thresholds", {})
        detector.set_antispoof_params(
            live_index=live_idx if live_idx is None else int(live_idx),
            thresholds=thresholds if isinstance(thresholds, dict) else {},
            mode=str(cfg.get("antispoof_mode","medium")),
            preprocess=str(cfg.get("antispoof_preprocess","bgr_norm")),
            smooth_k=int(cfg.get("antispoof_smooth_k", 3)),
        )
    except Exception:
        logging.exception("apply antispoof params at startup failed")

    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
