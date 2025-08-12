# main.py
"""
Main application with Admin Panel (PyQt5) — updated:
- AdminPanel allows editing per-camera 'show_skipped_blur' and blur thresholds
- Saves cameras.json and reloads CameraWidgets
- Shows camera runtime stats (pending tasks, last annotation, show_skipped_blur)
"""

import sys
import logging
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QFormLayout, QLineEdit, QSpinBox, QMessageBox,
    QComboBox, QDoubleSpinBox, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt

# local modules (gui.py provides CameraWidget and config helpers)
from gui import CameraWidget, read_cameras_config, write_cameras_config, read_app_config, write_app_config, GLOBAL_FACE_WORKER_POOL
from logger import init_logger
import detector

init_logger(logging.INFO)
logging.info("App start (AdminPanel with debug & stats)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_CONFIG_PATH = os.path.join(BASE_DIR, "app_config.json")

class AdminPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.cameras = read_cameras_config()
        self.app_cfg = read_app_config()
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # cameras list
        layout.addWidget(QLabel("Cameras"))
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)
        layout.addWidget(self.list_widget)

        # populate list
        self.reload_list()

        # form fields
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.source_edit = QLineEdit()
        self.width_spin = QSpinBox(); self.width_spin.setRange(32, 3840)
        self.height_spin = QSpinBox(); self.height_spin.setRange(32, 2160)
        self.display_interval_spin = QSpinBox(); self.display_interval_spin.setRange(1, 2000)
        self.detect_interval_spin = QSpinBox(); self.detect_interval_spin.setRange(1, 240)
        self.reconnect_spin = QSpinBox(); self.reconnect_spin.setRange(1, 60)
        self.match_threshold_edit = QDoubleSpinBox(); self.match_threshold_edit.setRange(0.0, 1.0); self.match_threshold_edit.setSingleStep(0.01)
        # new settings
        self.blur_threshold_spin = QSpinBox(); self.blur_threshold_spin.setRange(1, 100000)
        self.exposure_chk = QCheckBox()
        self.exposure_gain_spin = QDoubleSpinBox(); self.exposure_gain_spin.setRange(1.0, 5.0); self.exposure_gain_spin.setSingleStep(0.1)
        self.min_luminance_spin = QSpinBox(); self.min_luminance_spin.setRange(0, 255)
        self.frame_buffer_spin = QSpinBox(); self.frame_buffer_spin.setRange(1, 10)
        self.require_human_chk = QCheckBox()
        self.antispoof_chk = QCheckBox()
        self.antispoof_interval_spin = QSpinBox(); self.antispoof_interval_spin.setRange(1, 300)
        self.antispoof_model_edit = QLineEdit()
        # new: show skipped blur toggle per camera
        self.show_skipped_blur_chk = QCheckBox("Tampilkan bounding box wajah blur yang di-skip")
        # optional backoff config
        self.backoff_trigger_spin = QSpinBox(); self.backoff_trigger_spin.setRange(1, 20)
        self.backoff_frames_spin = QSpinBox(); self.backoff_frames_spin.setRange(0, 300)

        form.addRow("Name", self.name_edit)
        form.addRow("Source (int or rtsp)", self.source_edit)
        form.addRow("Width", self.width_spin)
        form.addRow("Height", self.height_spin)
        form.addRow("Display refresh (ms)", self.display_interval_spin)
        form.addRow("Detect every N frames", self.detect_interval_spin)
        form.addRow("Reconnect delay (s)", self.reconnect_spin)
        form.addRow("Match threshold (0-1)", self.match_threshold_edit)

        form.addRow("Blur threshold (Laplacian var)", self.blur_threshold_spin)
        form.addRow(self.show_skipped_blur_chk)
        form.addRow("Backoff trigger (consec blur checks)", self.backoff_trigger_spin)
        form.addRow("Backoff frames (skip frames after trigger)", self.backoff_frames_spin)
        form.addRow("Require human-only check", self.require_human_chk)
        form.addRow("Exposure enabled", self.exposure_chk)
        form.addRow("Exposure gain", self.exposure_gain_spin)
        form.addRow("Min luminance", self.min_luminance_spin)
        form.addRow("Frame buffer (grabs)", self.frame_buffer_spin)
        form.addRow("Antispoof enabled", self.antispoof_chk)
        form.addRow("Antispoof interval (frames)", self.antispoof_interval_spin)
        form.addRow("Antispoof ONNX path", self.antispoof_model_edit)

        layout.addLayout(form)

        # buttons row: add/update/delete + start/stop selected
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Camera")
        self.add_btn.clicked.connect(self.on_add)
        self.update_btn = QPushButton("Update Camera")
        self.update_btn.clicked.connect(self.on_update)
        self.delete_btn = QPushButton("Delete Camera")
        self.delete_btn.clicked.connect(self.on_delete)
        self.start_btn = QPushButton("Start Selected")
        self.start_btn.clicked.connect(self.on_start_selected)
        self.stop_btn = QPushButton("Stop Selected")
        self.stop_btn.clicked.connect(self.on_stop_selected)
        self.browse_antispoof_btn = QPushButton("Browse Antispoof ONNX")
        self.browse_antispoof_btn.clicked.connect(self.on_browse_antispoof)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.update_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.browse_antispoof_btn)
        layout.addLayout(btn_row)

        # camera stats button
        stats_row = QHBoxLayout()
        self.stats_btn = QPushButton("Show Selected Camera Stats")
        self.stats_btn.clicked.connect(self.on_show_stats)
        stats_row.addWidget(self.stats_btn)
        layout.addLayout(stats_row)

        # device selector + debug toggle
        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("Processing Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["CPU", "GPU"])
        device = self.app_cfg.get("device", "CPU")
        self.device_combo.setCurrentIndex(0 if str(device).upper() != "GPU" else 1)
        device_row.addWidget(self.device_combo)
        self.apply_device_btn = QPushButton("Apply Device")
        self.apply_device_btn.clicked.connect(self.on_apply_device)
        device_row.addWidget(self.apply_device_btn)

        # debug toggle
        self.debug_chk = QCheckBox("Enable Detector Debug (restart required)")
        self.debug_chk.setChecked(bool(self.app_cfg.get("debug", False)))
        device_row.addWidget(self.debug_chk)

        layout.addLayout(device_row)

        self.status_log = QLabel("Admin ready")
        self.status_log.setWordWrap(True)
        layout.addWidget(self.status_log)

        # select first if available
        if self.cameras:
            self.list_widget.setCurrentRow(0)
            self.on_select(0)

    def reload_list(self):
        self.cameras = read_cameras_config()
        self.list_widget.clear()
        for cam in self.cameras:
            self.list_widget.addItem(str(cam.get("name", cam.get("source", ""))))

    def on_select(self, idx):
        if idx < 0 or idx >= len(self.cameras):
            return
        cam = self.cameras[idx]
        self.name_edit.setText(cam.get("name", ""))
        self.source_edit.setText(str(cam.get("source", "")))
        self.width_spin.setValue(int(cam.get("width", 320)))
        self.height_spin.setValue(int(cam.get("height", 240)))
        self.display_interval_spin.setValue(int(cam.get("display_interval_ms", 50)))
        self.detect_interval_spin.setValue(int(cam.get("detect_interval_frames", cam.get("interval", 4))))
        self.reconnect_spin.setValue(int(cam.get("reconnect_delay", 5)))
        self.match_threshold_edit.setValue(float(cam.get("match_threshold", 0.5)))

        self.blur_threshold_spin.setValue(int(cam.get("min_sharpness_percent", cam.get("blur_threshold", 60))))
        self.show_skipped_blur_chk.setChecked(bool(cam.get("show_skipped_blur", False)))
        self.backoff_trigger_spin.setValue(int(cam.get("blur_backoff_trigger", cam.get("backoff_trigger", 3))))
        self.backoff_frames_spin.setValue(int(cam.get("blur_backoff_frames", cam.get("backoff_frames", 5))))
        self.require_human_chk.setChecked(bool(cam.get("require_human_check", cam.get("require_human_check", False))))
        self.exposure_chk.setChecked(bool(cam.get("exposure_enabled", cam.get("exposure_enhance", True))))
        self.exposure_gain_spin.setValue(float(cam.get("exposure_gain", cam.get("exposure_gain", 1.4))))
        self.min_luminance_spin.setValue(int(cam.get("min_luminance", cam.get("min_luminance", 60))))
        self.frame_buffer_spin.setValue(int(cam.get("frame_buffer", cam.get("frame_buffer", 1))))
        self.antispoof_chk.setChecked(bool(cam.get("antispoof_enabled", False)))
        self.antispoof_interval_spin.setValue(int(cam.get("antispoof_interval", 15)))
        self.antispoof_model_edit.setText(str(cam.get("antispoof_model_path", "")))
        self.status_log.setText(f"Selected: {cam.get('name')}")

    def _gather_form(self):
        src_val = self.source_edit.text().strip()
        if src_val.isdigit():
            source = int(src_val)
        else:
            source = src_val
        cam = {
            "name": self.name_edit.text().strip() or "Camera",
            "source": source,
            "width": int(self.width_spin.value()),
            "height": int(self.height_spin.value()),
            "display_interval_ms": int(self.display_interval_spin.value()),
            "detect_interval_frames": int(self.detect_interval_spin.value()),
            "reconnect_delay": int(self.reconnect_spin.value()),
            "match_threshold": float(self.match_threshold_edit.value()),
            "min_sharpness_percent": int(self.blur_threshold_spin.value()),
            "sharpness_var_max": 1000,
            "require_human_check": bool(self.require_human_chk.isChecked()),
            "exposure_enabled": bool(self.exposure_chk.isChecked()),
            "exposure_gain": float(self.exposure_gain_spin.value()),
            "min_luminance": int(self.min_luminance_spin.value()),
            "frame_buffer": int(self.frame_buffer_spin.value()),
            "antispoof_enabled": bool(self.antispoof_chk.isChecked()),
            "antispoof_interval": int(self.antispoof_interval_spin.value()),
            "antispoof_model_path": str(self.antispoof_model_edit.text().strip()),
            "antispoof_threshold": 0.5,
            "show_skipped_blur": bool(self.show_skipped_blur_chk.isChecked()),
            "blur_backoff_trigger": int(self.backoff_trigger_spin.value()),
            "blur_backoff_frames": int(self.backoff_frames_spin.value())
        }
        return cam

    def on_add(self):
        try:
            cam = self._gather_form()
            self.cameras.append(cam)
            ok = write_cameras_config(self.cameras)
            if not ok:
                QMessageBox.critical(self, "Error", "Failed to write cameras.json")
                return
            self.reload_list()
            self.status_log.setText("Added camera. Reloaded list.")
        except Exception as e:
            logging.exception("Add camera failed")
            QMessageBox.critical(self, "Error", f"Failed to add: {e}")

    def on_update(self):
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.cameras):
            QMessageBox.warning(self, "No selection", "Select a camera first")
            return
        try:
            cam = self._gather_form()
            self.cameras[idx] = cam
            ok = write_cameras_config(self.cameras)
            if not ok:
                QMessageBox.critical(self, "Error", "Failed to write cameras.json")
                return
            self.parent.reload_cameras()  # restart all cameras (simpler & safe)
            self.reload_list()
            self.status_log.setText("Updated camera and reloaded running cameras.")
        except Exception as e:
            logging.exception("Update camera failed")
            QMessageBox.critical(self, "Error", f"Failed to update: {e}")

    def on_delete(self):
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.cameras):
            QMessageBox.warning(self, "No selection", "Select a camera first")
            return
        reply = QMessageBox.question(self, "Delete", f"Delete camera '{self.cameras[idx].get('name')}'?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            del self.cameras[idx]
            ok = write_cameras_config(self.cameras)
            if not ok:
                QMessageBox.critical(self, "Error", "Failed to write cameras.json")
                return
            self.parent.reload_cameras()
            self.reload_list()
            self.status_log.setText("Deleted camera and reloaded.")
        except Exception as e:
            logging.exception("Delete camera failed")
            QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def on_start_selected(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "No selection", "Select a camera first")
            return
        self.parent.start_camera(idx)
        self.status_log.setText(f"Requested start for camera idx={idx}")

    def on_stop_selected(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "No selection", "Select a camera first")
            return
        self.parent.stop_camera(idx)
        self.status_log.setText(f"Requested stop for camera idx={idx}")

    def on_apply_device(self):
        device = "GPU" if self.device_combo.currentIndex() == 1 else "CPU"
        # also record debug setting
        debug_flag = bool(self.debug_chk.isChecked())
        ok = write_app_config({"device": device, "debug": debug_flag})
        if not ok:
            QMessageBox.critical(self, "Error", "Failed to save app_config")
            return
        QMessageBox.information(self, "Restart required", "Please restart the app to apply device/debug change.")
        self.status_log.setText(f"Saved device: {device} (debug={debug_flag})")

    def on_browse_antispoof(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Antispoof ONNX model", os.path.expanduser("~"), "ONNX files (*.onnx);;All files (*)")
        if path:
            self.antispoof_model_edit.setText(path)

    def on_show_stats(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "No selection", "Select a camera first")
            return
        info = self.parent.get_camera_stats(idx)
        QMessageBox.information(self, f"Stats for camera idx={idx}", info)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition CCTV - Admin (with Debug & Stats)")
        self.resize(1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        central.setLayout(layout)

        # left area: camera grid
        self.grid_area = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_area.setLayout(self.grid_layout)
        layout.addWidget(self.grid_area, 3)

        # right area: admin panel
        self.admin = AdminPanel(self)
        layout.addWidget(self.admin, 1)

        # camera widgets list
        self.camera_widgets = []
        # load & show per cameras.json
        self.load_and_show_cameras()

    def load_and_show_cameras(self):
        # read config
        cams = read_cameras_config()
        # stop and clear existing
        for w in self.camera_widgets:
            try:
                if w:
                    w.stop()
            except Exception:
                pass
            try:
                self.grid_layout.removeWidget(w)
                w.deleteLater()
            except Exception:
                pass
        self.camera_widgets.clear()

        # place new widgets (start them)
        cols = 2
        rows = (len(cams) + cols - 1) // cols if cams else 0
        positions = [(r, c) for r in range(rows) for c in range(cols)]
        for idx, cam in enumerate(cams):
            try:
                widget = CameraWidget(cam)
                r, c = positions[idx]
                self.grid_layout.addWidget(widget, r, c)
                self.camera_widgets.append(widget)
            except Exception:
                logging.exception("Failed creating CameraWidget for idx=%d", idx)

    def reload_cameras(self):
        logging.info("reload_cameras invoked")
        self.load_and_show_cameras()

    def start_camera(self, idx):
        cams = read_cameras_config()
        if idx < 0 or idx >= len(cams):
            QMessageBox.warning(self, "Invalid index", "Camera index out of range")
            return
        try:
            # stop existing widget if present
            if idx < len(self.camera_widgets) and self.camera_widgets[idx]:
                try:
                    self.camera_widgets[idx].stop()
                except Exception:
                    pass
                try:
                    self.grid_layout.removeWidget(self.camera_widgets[idx])
                    self.camera_widgets[idx].deleteLater()
                except Exception:
                    pass
            # recreate widget
            cam = cams[idx]
            widget = CameraWidget(cam)
            cols = 2
            rows = (len(cams) + cols - 1) // cols if cams else 0
            positions = [(r, c) for r in range(rows) for c in range(cols)]
            r, c = positions[idx]
            self.grid_layout.addWidget(widget, r, c)
            if idx < len(self.camera_widgets):
                self.camera_widgets[idx] = widget
            else:
                # pad list if necessary
                while len(self.camera_widgets) < idx:
                    self.camera_widgets.append(None)
                self.camera_widgets.append(widget)
        except Exception:
            logging.exception("start_camera failed for idx=%d", idx)
            QMessageBox.critical(self, "Error", "Failed to start camera")

    def stop_camera(self, idx):
        if idx < 0 or idx >= len(self.camera_widgets):
            QMessageBox.warning(self, "Invalid index", "Camera index out of range or not running")
            return
        try:
            w = self.camera_widgets[idx]
            if not w:
                QMessageBox.information(self, "Info", "Camera not running")
                return
            w.stop()
            try:
                self.grid_layout.removeWidget(w)
                w.deleteLater()
            except Exception:
                pass
            self.camera_widgets[idx] = None
        except Exception:
            logging.exception("stop_camera failed idx=%d", idx)
            QMessageBox.critical(self, "Error", "Failed to stop camera")

    def get_camera_stats(self, idx):
        """
        Return a short multi-line string with runtime stats for camera idx.
        Checks camera_widgets list and inspects thread internals if available.
        """
        cams = read_cameras_config()
        if idx < 0 or idx >= len(cams):
            return "Index out of range"

        widget = None
        if idx < len(self.camera_widgets):
            widget = self.camera_widgets[idx]
        if widget is None:
            return "Camera not running"

        # try to access thread
        try:
            thread = widget.thread
            pending = getattr(thread, "_pending_tasks", "N/A")
            max_pending = getattr(thread, "_max_pending", "N/A")
            with thread.annotations_lock:
                last_anns = list(thread.last_annotations or [])
            last_info = "no annotations"
            if last_anns:
                # take first annotation for summary
                ann = last_anns[0]
                if ann.get("skipped"):
                    last_info = f"SKIPPED:{ann.get('skip_reason','')}"
                else:
                    if ann.get("match"):
                        last_info = f"MATCH:{ann.get('name','unknown')} score={ann.get('score',0.0):.2f}"
                    else:
                        last_info = f"UNMATCHED score={ann.get('score',0.0):.2f}"
            info = (
                f"Camera index: {idx}\n"
                f"Name: {cams[idx].get('name')}\n"
                f"Pending detection tasks: {pending} / {max_pending}\n"
                f"Last annotation: {last_info}\n"
                f"Show skipped blur boxes: {bool(cams[idx].get('show_skipped_blur', False))}\n"
                f"Blur backoff trigger: {cams[idx].get('blur_backoff_trigger', 3)}\n"
                f"Blur backoff frames: {cams[idx].get('blur_backoff_frames', 5)}\n"
                f"Antispoof enabled: {bool(cams[idx].get('antispoof_enabled', False))}\n"
                f"Frame buffer: {cams[idx].get('frame_buffer', 1)}\n"
                f"Detect every N frames: {cams[idx].get('detect_interval_frames', cams[idx].get('interval',4))}\n"
            )
            return info
        except Exception as e:
            logging.exception("get_camera_stats failed")
            return f"Failed to get stats: {e}"

    def closeEvent(self, event):
        for w in self.camera_widgets:
            try:
                if w:
                    w.stop()
            except Exception:
                pass
        try:
            GLOBAL_FACE_WORKER_POOL.shutdown(wait=False)
        except Exception:
            pass
        event.accept()

def main():
    # read device config and initialize detector accordingly
    cfg = read_app_config()
    device = cfg.get("device", "CPU")
    use_gpu = True if str(device).strip().upper() == "GPU" else False
    # Set DETECTOR_DEBUG env var for detector module if requested
    debug_flag = bool(cfg.get("debug", False))
    if debug_flag:
        os.environ["DETECTOR_DEBUG"] = "1"
    else:
        os.environ.pop("DETECTOR_DEBUG", None)
    logging.info("Initializing detector; use_gpu=%s debug=%s", use_gpu, debug_flag)
    detector.initialize(use_gpu=use_gpu)

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
