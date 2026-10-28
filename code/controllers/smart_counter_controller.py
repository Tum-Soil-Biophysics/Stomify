"""
SmartCounterController -- AI count and export logic for the Smart Counter tab.
"""

import os
import traceback

import pandas as pd
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog, QApplication

from core.detector import StomataDetectorML
from core.filename_parser import FilenameParser
from core.report_generator import ReportGenerator
from i18n import tr
from models.settings_model import SettingsModel
from models.app_state import AppState


class SmartCounterController(QObject):
    """Handles AI counting and export for the Smart Counter tab."""

    def __init__(self, window, settings: SettingsModel, app_state: AppState,
                 detector: StomataDetectorML, parent=None):
        super().__init__(parent)
        self.w = window
        self.settings = settings
        self.state = app_state
        self.detector = detector

    def connect_all(self):
        sc = self.w.smart_counter_tab
        sc.request_ai_count.connect(self.run_ai_count)
        sc.request_batch_ai.connect(self.run_batch_ai)
        sc.request_export.connect(self.export_smart_counter)

    # -- AI Count (single image) ----------------------------------------------

    def run_ai_count(self, image_path: str):
        lang = self.settings.language
        if not self.detector.model:
            QMessageBox.critical(self.w, "Error", tr("err.no_model", lang))
            return

        self._sync_detector()

        # Override confidence with Smart Counter's slider
        conf = self.w.smart_counter_tab.conf_slider.value() / 100.0
        self.detector.confidence_threshold = conf

        try:
            count, annotated, details = self.detector.detect(
                image_path, settings=self.settings,
            )
            if count is None:
                self._set_status(tr("status.ai_failed", lang))
                return

            stomata_list = details.get("stomata", []) if isinstance(details, dict) else []
            boxes_with_conf = [
                (s["bbox"], s["confidence"]) for s in stomata_list
            ]
            self.w.smart_counter_tab.remove_ai_boxes(image_path)
            self.w.smart_counter_tab.import_ai_boxes(boxes_with_conf)
            self._set_status(tr("status.ai_detected", lang, count=count))

        except Exception as e:
            traceback.print_exc()
            self._set_status(tr("status.ai_failed", lang))

    # -- Batch AI Count -------------------------------------------------------

    def run_batch_ai(self, image_paths: list[str]):
        lang = self.settings.language
        if not self.detector.model:
            QMessageBox.critical(self.w, "Error", tr("err.no_model", lang))
            return

        self._sync_detector()
        conf = self.w.smart_counter_tab.conf_slider.value() / 100.0
        self.detector.confidence_threshold = conf

        total = len(image_paths)
        if total == 0:
            return

        progress = QProgressDialog(
            "Running AI on all images...", "Cancel", 0, total, self.w
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        for i, path in enumerate(image_paths):
            if progress.wasCanceled():
                break

            boxes = self._detect_one(path)
            self.w.smart_counter_tab.remove_ai_boxes(path)
            self.w.smart_counter_tab.add_boxes_to_path(path, boxes)

            progress.setValue(i + 1)
            QApplication.processEvents()

        progress.close()
        self._set_status(
            tr("status.batch_complete", lang, total=total)
        )
        self.w.smart_counter_tab.reload_current()

    # -- Export ---------------------------------------------------------------

    def export_smart_counter(self):
        counts = self.w.smart_counter_tab.get_all_counts()
        if not counts:
            QMessageBox.information(self.w, "No Data", "No images to export.")
            return

        ext_filter = (
            "Excel (*.xlsx);;CSV (*.csv);;All Files (*)"
            if self.settings.export_format == "xlsx"
            else "CSV (*.csv);;Excel (*.xlsx);;All Files (*)"
        )
        path, _ = QFileDialog.getSaveFileName(
            self.w, "Save Smart Counter Report", "", ext_filter,
        )
        if not path:
            return

        ppm = self.settings.pixels_per_mm or None

        parser = FilenameParser()
        rows = []
        for img_path, cnt in counts.items():
            info = parser.parse(os.path.basename(img_path))

            img_w, img_h = 0, 0
            area_mm2 = None
            density = None
            try:
                from PySide6.QtGui import QImageReader
                reader = QImageReader(img_path)
                size = reader.size()
                if size.isValid():
                    img_w = size.width()
                    img_h = size.height()
                    if ppm and ppm > 0:
                        area_mm2 = (img_w * img_h) / (ppm * ppm)
                        if area_mm2 > 0 and cnt > 0:
                            density = cnt / area_mm2
            except Exception:
                pass

            row_data = {
                "filename": os.path.basename(img_path),
                "plant_id": info.get("plant_id", "Unknown"),
                "position": info.get("position", "Unknown"),
                "replicate": info.get("replicate", "1"),
                "stomata_count": cnt,
                "avg_confidence": 1.0,
                "image_width_px": img_w,
                "image_height_px": img_h,
            }
            if area_mm2 is not None:
                row_data["area_mm2"] = round(area_mm2, 4)
            if density is not None:
                row_data["density_per_mm2"] = round(density, 4)
            rows.append(row_data)

        df = pd.DataFrame(rows)
        model_info = (
            os.path.basename(self.detector.model_path)
            if self.detector.model_path else "Manual"
        )

        out = ReportGenerator.generate(
            df, path, pixels_per_mm=ppm, model_info=model_info,
            include_low_conf_sheet=False,
        )

        if out:
            QMessageBox.information(self.w, "Exported", f"Report saved to:\n{out}")
            self._set_status(tr("status.report_saved", self.settings.language))
        else:
            QMessageBox.warning(self.w, "Error", "Failed to generate report.")

    # -- Helpers --------------------------------------------------------------

    def _sync_detector(self):
        self.detector.confidence_threshold = self.settings.confidence
        self.detector.iou_threshold = self.settings.iou

    def _detect_one(self, path: str) -> list:
        try:
            count, annotated, details = self.detector.detect(
                path, settings=self.settings,
            )
            if count is None:
                return []
            stomata_list = details.get("stomata", []) if isinstance(details, dict) else []
            return [(s["bbox"], s["confidence"]) for s in stomata_list]
        except Exception:
            traceback.print_exc()
            return []

    def _set_status(self, text: str):
        self.w.status_label.setText(text)
