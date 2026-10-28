"""
MainController -- Orchestrates model-loading, preview, calibration,
project save/load, and global signal wiring.
"""

import math
import os

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog, QMessageBox

from core.config import COLORS
from core.detector import StomataDetectorML
from i18n import tr
from models.settings_model import SettingsModel
from models.app_state import AppState
from ui.dialogs.calibration_dialog import CalibrationDialog


class MainController(QObject):
    """Handles model I/O, preview detection, calibration, and project persistence."""

    def __init__(self, window, settings: SettingsModel, app_state: AppState,
                 detector: StomataDetectorML, parent=None):
        super().__init__(parent)
        self.w = window
        self.settings = settings
        self.state = app_state
        self.detector = detector

    # -- Public: wire signals -------------------------------------------------

    def connect_all(self):
        """Connect View signals to Controller slots."""
        w = self.w

        # Header load model
        w.header_load_btn.clicked.connect(self.browse_model)

        # Preview tab
        w.preview_tab.load_btn.clicked.connect(self.load_preview_image)
        w.preview_tab.request_preview_detect.connect(self.run_preview_detection)
        w.preview_tab.calibrate_btn.clicked.connect(self.toggle_calibration)
        w.preview_tab.canvas.line_drawn.connect(self.on_calibration_line)

        # Settings: model load button (if present on settings tab)
        if hasattr(w.settings_tab, "load_model_btn"):
            w.settings_tab.load_model_btn.clicked.connect(self.browse_model)

        # Settings changes
        self.settings.settings_changed.connect(self._on_setting_changed)

    # -- Model ----------------------------------------------------------------

    def browse_model(self):
        lang = self.settings.language
        path, _ = QFileDialog.getOpenFileName(
            self.w,
            "Select trained model (YOLOv8)",
            "",
            "PyTorch Model (*.pt);;All files (*)",
        )
        if not path:
            return

        self._set_status(tr("status.loading_model", lang))
        success, message = self.detector.load_model(path)

        if success:
            self.state.model_path = path
            self.settings.set("model_path", path)
            self._update_model_ui(path)
            self.settings.save_to_file()
        else:
            self.w.header_model_label.setText(tr("err.load_failed", lang))
            QMessageBox.critical(self.w, "Error", message)

    # -- Preview --------------------------------------------------------------

    def load_preview_image(self):
        import cv2
        path, _ = QFileDialog.getOpenFileName(
            self.w, "Select image to preview", "",
            "Image files (*.jpg *.jpeg *.png *.tif *.tiff);;All files (*)",
        )
        if not path:
            return
        self.w.preview_image_path = path
        self.w.preview_tab.canvas.set_image_from_path(path)
        lang = self.settings.language
        self.w.preview_tab.count_label.setText(f"{tr('lbl.stomata', lang)} -")

        try:
            img = cv2.imread(path)
            if img is not None:
                h, w = img.shape[:2]
                size_kb = os.path.getsize(path) / 1024
                self.w.preview_tab.info_label.setText(
                    f"{w}x{h} px  |  {size_kb:.1f} KB"
                )
            else:
                self.w.preview_tab.info_label.setText("")
        except Exception:
            self.w.preview_tab.info_label.setText("")

    def run_preview_detection(self):
        lang = self.settings.language
        if not getattr(self.w, "preview_image_path", None):
            QMessageBox.critical(self.w, "Error", tr("err.load_image_first", lang))
            return
        if not self.detector.model:
            QMessageBox.critical(self.w, "Error", tr("err.no_model", lang))
            return

        self._sync_detector_settings()
        count, annotated, _ = self.detector.detect(
            self.w.preview_image_path,
            show_confidence=True,
        )
        if count is not None:
            self.w.preview_tab.canvas.set_image_from_cv(annotated)
            self.w.preview_tab.count_label.setText(
                f"{tr('lbl.stomata', lang)} {count}"
            )

    # -- Calibration ----------------------------------------------------------

    def toggle_calibration(self):
        lang = self.settings.language
        if not getattr(self.w, "preview_image_path", None):
            QMessageBox.critical(self.w, "Error", tr("err.load_image_first", lang))
            return

        canvas = self.w.preview_tab.canvas
        new_mode = not canvas.draw_mode
        canvas.set_draw_mode(new_mode)

        if new_mode:
            self.w.preview_tab.calibrate_btn.setStyleSheet(
                f"background-color: {COLORS['error']}; color: white; "
                "font-weight: bold; padding: 8px 18px; border: none; border-radius: 4px;"
            )
            self.w.preview_tab.calibrate_btn.setText(
                tr("btn.cancel_calibration", lang)
            )
            self.w.preview_tab.calibration_status.setText(
                "Click & drag along the scale bar..."
            )
            self._set_status("Calibration mode: Draw a line along the scale bar")
        else:
            self.w.preview_tab.calibrate_btn.setStyleSheet(
                f"background-color: {COLORS['primary']}; color: white; "
                "font-weight: bold; padding: 8px 18px; border: none; border-radius: 4px;"
            )
            self.w.preview_tab.calibrate_btn.setText(
                tr("btn.calibrate_scale", lang)
            )
            self.w.preview_tab.calibration_status.setText("")
            self._set_status(tr("lbl.ready", lang))

    def on_calibration_line(self, x0, y0, x1, y1):
        pixel_length = math.hypot(x1 - x0, y1 - y0)
        if pixel_length < 10:
            self.w.preview_tab.calibration_status.setText(
                "Line too short, try again"
            )
            return

        line_item = self.w.preview_tab.canvas.draw_calibration_line(x0, y0, x1, y1)

        dlg = CalibrationDialog(pixel_length, self.w)
        if dlg.exec() and dlg.pixels_per_mm is not None:
            ppm = dlg.pixels_per_mm
            self.settings.set("pixels_per_mm", round(ppm, 2))
            self.w.preview_tab.calibration_status.setText(
                f"Calibrated: {ppm:.1f} px/mm"
            )
            lang = self.settings.language
            self._set_status(tr("status.calibrated", lang, ppm=ppm))

        self.w.preview_tab.canvas.remove_item(line_item)

        # Exit calibration mode
        self.w.preview_tab.canvas.set_draw_mode(False)
        self.w.preview_tab.calibrate_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; "
            "font-weight: bold; padding: 8px 18px; border: none; border-radius: 4px;"
        )
        lang = self.settings.language
        self.w.preview_tab.calibrate_btn.setText(tr("btn.calibrate_scale", lang))

    # -- Project Save / Load --------------------------------------------------

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(
            self.w, "Save Project", "",
            "Stomata Project (*.stproj);;All Files (*)",
        )
        if not path:
            return
            
        # Sync Smart Counter data before saving
        if hasattr(self.w, "smart_counter_tab"):
            self.state.smart_counter_paths = list(self.w.smart_counter_tab._image_paths)
            self.state.smart_counter_data = {k: list(v) for k, v in self.w.smart_counter_tab._image_boxes.items()}
            
        try:
            self.state.save_project(path)
            self._set_status(f"Project saved: {os.path.basename(path)}")
        except Exception as exc:
            QMessageBox.critical(self.w, "Error", f"Could not save project:\n{exc}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self.w, "Open Project", "",
            "Stomata Project (*.stproj);;All Files (*)",
        )
        if not path:
            return
        try:
            self.state.load_project(path)
            
            # Sync Smart Counter data after loading
            if hasattr(self.w, "smart_counter_tab"):
                tab = self.w.smart_counter_tab
                tab._image_paths = list(self.state.smart_counter_paths)
                tab._image_boxes = {k: list(v) for k, v in self.state.smart_counter_data.items()}
                
                # Refresh UI
                tab.image_list.clear()
                for p in tab._image_paths:
                    count = len(tab._image_boxes.get(p, []))
                    tab.image_list.addItem(f"{os.path.basename(p)}  [{count}]")
                
                if tab._image_paths:
                    tab._current_index = -1
                    tab.image_list.setCurrentRow(0)
                else:
                    tab._clear_all_images()
                    
            # Restore model if path recorded
            if self.state.model_path and os.path.isfile(self.state.model_path):
                success, _ = self.detector.load_model(self.state.model_path)
                if success:
                    self._update_model_ui(self.state.model_path)
            self._set_status(f"Project loaded: {os.path.basename(path)}")
        except Exception as exc:
            QMessageBox.critical(self.w, "Error", f"Could not load project:\n{exc}")

    # -- Helpers --------------------------------------------------------------

    def _sync_detector_settings(self):
        self.detector.confidence_threshold = self.settings.confidence
        self.detector.iou_threshold = self.settings.iou

    def _set_status(self, text: str):
        self.w.status_label.setText(text)

    def _update_model_ui(self, path: str):
        lang = self.settings.language
        model_name = os.path.basename(path)
        model_type = "YOLOv8"

        self.w.header_model_label.setText(f"[{model_type}] {model_name}")

        # Update Settings Tab model info
        classes = ", ".join(str(v) for v in self.detector.class_names.values())
        info_lines = [
            "Model loaded successfully!",
            f"File: {model_name}",
            f"Type: {model_type}",
            f"Classes: {classes}",
            f"Stomata index: {self.detector.stomata_idx}",
            f"Artifact index: {self.detector.artifact_idx if self.detector.artifact_idx is not None else 'Not found'}",
            "",
            "Status: Ready to analyze images",
        ]
        if hasattr(self.w.settings_tab, "update_model_info"):
            self.w.settings_tab.update_model_info(info_lines)

        self._set_status(tr("status.model_loaded", lang, name=model_name))

    def _on_setting_changed(self, key: str, value):
        """React to any setting change."""
        if key == "language":
            self.w.retranslate_ui(value)
        elif key == "theme":
            self.w.apply_theme(value)
        elif key == "pixels_per_mm":
            # Update any UI that shows px/mm
            if hasattr(self.w.settings_tab, "update_calibration_display"):
                self.w.settings_tab.update_calibration_display(value)
        elif key in ("bbox_color", "marker_radius", "font_size"):
            # Instantly reflect appearance settings in the Smart Counter canvas
            if hasattr(self.w, "smart_counter_tab"):
                self.w.smart_counter_tab._reload_scene_from_data()
