"""
BatchController -- Manages the batch analysis workflow, the AnalysisWorker
thread, and the ReviewDialog lifecycle.
"""

import os
from datetime import datetime

import cv2
import numpy as np
import pandas as pd

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTreeWidgetItem

from core.config import COLORS
from core.detector import StomataDetectorML
from core.filename_parser import FilenameParser
from core.report_generator import ReportGenerator
from i18n import tr
from models.settings_model import SettingsModel
from models.app_state import AppState
from models.edge_filter import EdgeFilter


# ═══════════════════════════════════════════════════════════════════════════════
#                        BACKGROUND ANALYSIS WORKER
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisWorker(QThread):
    """Run batch detection in the background."""

    progress = Signal(int, int, str)        # current, total, filename
    result_ready = Signal(int, dict)        # index, result_dict
    finished_all = Signal(list)             # all results
    error = Signal(str)

    def __init__(self, detector, image_files, output_dir, show_conf,
                 pixels_per_mm=None, settings=None, parent=None):
        super().__init__(parent)
        self.detector = detector
        self.image_files = image_files
        self.output_dir = output_dir
        self.show_conf = show_conf
        self.pixels_per_mm = pixels_per_mm
        self.settings = settings
        self._stop = False

    def request_stop(self):
        self._stop = True

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        annotated_dir = os.path.join(self.output_dir, "Annotated_Images")
        os.makedirs(annotated_dir, exist_ok=True)

        results = []
        total = len(self.image_files)

        for i, img in enumerate(self.image_files):
            if self._stop:
                break

            self.progress.emit(i + 1, total, img["filename"])

            count, annotated, info = self.detector.detect(
                img["filepath"],
                show_confidence=self.show_conf,
                settings=self.settings,
            )

            if count is not None:
                out_path = os.path.join(annotated_dir, f"detected_{img['filename']}")
                cv2.imwrite(out_path, annotated)

                avg_conf = info["avg_confidence"] if isinstance(info, dict) else 0

                result = {
                    "filename": img["filename"],
                    "filepath": img["filepath"],
                    "annotated_path": out_path,
                    "plant_id": img["plant_id"],
                    "position": img["position"],
                    "replicate": img["replicate"],
                    "stomata_count": count,
                    "avg_confidence": avg_conf,
                    "stomata_info": info.get("stomata", []) if isinstance(info, dict) else [],
                }

                try:
                    if annotated is not None:
                        h, w = annotated.shape[:2]
                        result["image_width_px"] = w
                        result["image_height_px"] = h
                        if self.pixels_per_mm and self.pixels_per_mm > 0:
                            area_mm2 = (w * h) / (self.pixels_per_mm ** 2)
                            result["area_mm2"] = round(area_mm2, 4)
                            if count > 0 and area_mm2 > 0:
                                result["density_per_mm2"] = round(count / area_mm2, 4)
                except Exception:
                    pass

                results.append(result)
                self.result_ready.emit(i, result)

        self.finished_all.emit(results)


# ═══════════════════════════════════════════════════════════════════════════════
#                            BATCH CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class BatchController(QObject):
    """Manages the batch analysis workflow."""

    def __init__(self, window, settings: SettingsModel, app_state: AppState,
                 detector: StomataDetectorML, parent=None):
        super().__init__(parent)
        self.w = window
        self.settings = settings
        self.state = app_state
        self.detector = detector
        self._worker: AnalysisWorker | None = None

    def connect_all(self):
        at = self.w.analysis_tab
        at.browse_folder_btn.clicked.connect(self.browse_input)
        at.browse_images_btn.clicked.connect(self.browse_images)
        at.browse_output_btn.clicked.connect(self.browse_output)
        at.analyze_btn.clicked.connect(self.start_analysis)
        at.stop_btn.clicked.connect(self.stop_analysis)
        at.clear_btn.clicked.connect(self.clear)

        # Review button
        if hasattr(at, "review_flagged_btn"):
            at.review_flagged_btn.clicked.connect(self.show_review_dialog)

    # -- Input browsing -------------------------------------------------------

    def browse_input(self):
        path = QFileDialog.getExistingDirectory(self.w, "Select folder with images")
        if not path:
            return
        self.w.analysis_tab.input_path_edit.setText(path)
        if not self.w.analysis_tab.output_path_edit.text():
            self.w.analysis_tab.output_path_edit.setText(
                os.path.join(path, "Output")
            )
        self._scan_folder()

    def browse_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self.w, "Select images to analyze", "",
            "Image files (*.jpg *.jpeg *.png *.tif *.tiff *.bmp);;All files (*)",
        )
        if not paths:
            return
        parent = os.path.dirname(paths[0])
        self.w.analysis_tab.input_path_edit.setText(f"Selected {len(paths)} images")
        if not self.w.analysis_tab.output_path_edit.text():
            self.w.analysis_tab.output_path_edit.setText(
                os.path.join(parent, "Output")
            )
        self.clear()

        from core.config import IMAGE_EXTENSIONS
        for p in paths:
            fname = os.path.basename(p)
            parsed = FilenameParser.parse(fname)
            self.state.image_files.append({"filepath": p, "filename": fname, **parsed})
            self.w.analysis_tab.tree.addTopLevelItem(QTreeWidgetItem([
                fname, parsed["plant_id"], parsed["position"],
                str(parsed["replicate"]), "-", "-",
            ]))
        self._set_status(f"Selected {len(self.state.image_files)} images")

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self.w, "Select output folder")
        if path:
            self.w.analysis_tab.output_path_edit.setText(path)

    def _scan_folder(self):
        from core.config import IMAGE_EXTENSIONS
        input_dir = self.w.analysis_tab.input_path_edit.text()
        if not input_dir or not os.path.isdir(input_dir):
            QMessageBox.critical(self.w, "Error", "Please select a valid input folder")
            return
        self.clear()
        for f in sorted(os.listdir(input_dir)):
            if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS:
                fp = os.path.join(input_dir, f)
                parsed = FilenameParser.parse(f)
                self.state.image_files.append({"filepath": fp, "filename": f, **parsed})
                self.w.analysis_tab.tree.addTopLevelItem(QTreeWidgetItem([
                    f, parsed["plant_id"], parsed["position"],
                    str(parsed["replicate"]), "-", "-",
                ]))
        self._set_status(f"Found {len(self.state.image_files)} images in folder")

    # -- Analysis -------------------------------------------------------------

    def start_analysis(self):
        lang = self.settings.language
        if not self.detector.model:
            QMessageBox.critical(self.w, "Error", tr("err.no_model", lang))
            return
        if not self.state.image_files:
            QMessageBox.critical(self.w, "Error", tr("err.no_images", lang))
            return

        self.detector.confidence_threshold = self.settings.confidence
        self.detector.iou_threshold = self.settings.iou

        output_dir = self.w.analysis_tab.output_path_edit.text()
        if not output_dir:
            base = (
                self.w.analysis_tab.input_path_edit.text()
                if os.path.isdir(self.w.analysis_tab.input_path_edit.text())
                else os.path.dirname(self.state.image_files[0]["filepath"])
            )
            output_dir = os.path.join(base, "Output")
            self.w.analysis_tab.output_path_edit.setText(output_dir)

        self.state.results = []
        self.state.low_confidence_images = []
        # Hide review button until analysis completes
        if hasattr(self.w.analysis_tab, "review_flagged_btn"):
            self.w.analysis_tab.review_flagged_btn.setVisible(False)

        ppm = self.settings.pixels_per_mm or None

        self._worker = AnalysisWorker(
            self.detector,
            self.state.image_files,
            output_dir,
            show_conf=True,
            pixels_per_mm=ppm,
            settings=self.settings,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.result_ready.connect(self._on_result)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def stop_analysis(self):
        if self._worker and self._worker.isRunning():
            self._worker.request_stop()
            self._set_status("Stopping analysis... please wait")

    @Slot(int, int, str)
    def _on_progress(self, current, total, filename):
        pct = int(current / total * 100)
        self.w.analysis_tab.progress_bar.setValue(pct)
        lang = self.settings.language
        self._set_status(
            tr("status.processing", lang, current=current, total=total, filename=filename)
        )

    @Slot(int, dict)
    def _on_result(self, idx, result):
        self.state.results.append(result)
        avg_conf = result["avg_confidence"]

        self.w.analysis_tab.update_tree_item(idx, result["stomata_count"], avg_conf)

        thresh = self.settings.low_conf_threshold
        if 0 < avg_conf < thresh:
            self.state.low_confidence_images.append({
                "filename": result["filename"],
                "filepath": result["annotated_path"],
                "original_path": result["filepath"],
                "plant_id": result["plant_id"],
                "position": result["position"],
                "stomata_count": result["stomata_count"],
                "avg_confidence": avg_conf,
            })

    @Slot(list)
    def _on_finished(self, results):
        lang = self.settings.language
        if not results:
            self._set_status(tr("status.stopped", lang))
            return

        df = pd.DataFrame(results)
        output_dir = self.w.analysis_tab.output_path_edit.text()
        report_path = os.path.join(
            output_dir,
            f"Stomata_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        ppm = self.settings.pixels_per_mm or None
        model_name = (
            os.path.basename(self.detector.model_path)
            if self.detector.model_path else None
        )
        ReportGenerator.generate(df, report_path, ppm, model_name)

        total_stomata = int(df["stomata_count"].sum())
        avg_stomata = df["stomata_count"].mean()
        self._set_status(tr("status.complete", lang, total=total_stomata))
        self.w.analysis_tab.results_label.setText(
            f"Total: {total_stomata} stomata | Avg: {avg_stomata:.1f}/image"
        )

        # Show review button if low confidence images found
        n_flagged = len(self.state.low_confidence_images)
        if n_flagged > 0 and hasattr(self.w.analysis_tab, "review_flagged_btn"):
            self.w.analysis_tab.review_flagged_btn.setText(
                tr("btn.review_flagged", lang, count=n_flagged)
            )
            self.w.analysis_tab.review_flagged_btn.setVisible(True)

        QMessageBox.information(
            self.w, "Analysis Complete",
            f"Successfully processed {len(results)} images\n\n"
            f"Total Stomata: {total_stomata}\n"
            f"Average: {avg_stomata:.1f} per image\n"
            f"Low Confidence: {n_flagged} images\n\n"
            f"Report: {report_path}\n"
            f"Annotated: {os.path.join(output_dir, 'Annotated_Images')}",
        )

    # -- Review Dialog --------------------------------------------------------

    def show_review_dialog(self):
        from ui.dialogs.review_dialog import ReviewDialog
        dlg = ReviewDialog(
            self.state.results,
            self.state.low_confidence_images,
            self.settings,
            parent=self.w,
        )
        dlg.exec()

    # -- Export ---------------------------------------------------------------

    def export_corrected_report(self):
        if not self.state.results:
            QMessageBox.information(self.w, "Info", "No results to export.")
            return
        output_dir = self.w.analysis_tab.output_path_edit.text()
        if not output_dir:
            QMessageBox.warning(self.w, "Warning", "No output directory set.")
            return
        try:
            df = pd.DataFrame(self.state.results)
            report_path = os.path.join(
                output_dir,
                f"Stomata_Report_corrected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )
            ppm = self.settings.pixels_per_mm or None
            model_name = (
                os.path.basename(self.detector.model_path)
                if self.detector.model_path else "Unknown"
            )
            ReportGenerator.generate(df, report_path, ppm, model_name)
            self._set_status(f"Report exported: {os.path.basename(report_path)}")
            QMessageBox.information(
                self.w, "Report Exported",
                f"Corrected report saved to:\n\n{report_path}",
            )
        except Exception as e:
            self._set_status(f"Export failed: {e}")
            QMessageBox.critical(self.w, "Export Error", f"Could not generate report:\n{e}")

    # -- Helpers --------------------------------------------------------------

    def clear(self):
        self.w.analysis_tab.clear()
        self.state.image_files.clear()
        self.state.results.clear()
        self.state.low_confidence_images.clear()
        if hasattr(self.w.analysis_tab, "review_flagged_btn"):
            self.w.analysis_tab.review_flagged_btn.setVisible(False)
        self._set_status(tr("status.cleared", self.settings.language))

    def _set_status(self, text: str):
        self.w.status_label.setText(text)
