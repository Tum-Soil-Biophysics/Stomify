"""
ReviewDialog -- Popup dialog for manual correction of low-confidence detections.

Replaces the old ReviewTab. Shown either:
  1. From the batch analysis "Review Flagged" button.
  2. From View > Review Window in the menu bar.
"""

import os

import cv2
import numpy as np

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPixmap, QPen, QBrush, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
    QGraphicsScene, QWidget, QHeaderView, QFrame,
)

from core.config import COLORS
from i18n import tr
from ui.widgets.image_canvas import ImageCanvas


class ReviewDialog(QDialog):
    """Popup dialog for reviewing and correcting low-confidence detections."""

    MARKER_RADIUS = 18

    def __init__(self, all_results: list[dict],
                 low_conf_images: list[dict],
                 settings,
                 parent=None):
        super().__init__(parent)
        self.all_results = all_results
        self.low_conf_images = low_conf_images
        self.settings = settings
        self._corrections: dict = {}  # {filename: stomata_count after correction}

        lang = settings.language
        self.setWindowTitle(tr("review.title", lang))
        self.resize(1100, 750)
        self.setModal(True)

        self._build_ui(lang)
        self._populate_list()

    # =====================================================================
    #  UI Build
    # =====================================================================

    def _build_ui(self, lang: str):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {COLORS['warning']};")
        hl = QVBoxLayout(header)
        title_lbl = QLabel(tr("review.title", lang))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        hl.addWidget(title_lbl)
        main_layout.addWidget(header)

        # Splitter: list | canvas
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # -- Left Panel: Image list ---
        left = QWidget()
        left_lay = QVBoxLayout(left)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        left_lay.addWidget(self.summary_label)

        self.image_tree = QTreeWidget()
        self.image_tree.setHeaderLabels(["Filename", "Count", "Confidence"])
        self.image_tree.setColumnCount(3)
        hdr = self.image_tree.header()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.image_tree.currentItemChanged.connect(self._on_image_selected)
        left_lay.addWidget(self.image_tree)

        open_folder_btn = QPushButton(tr("btn.open_folder", lang))
        open_folder_btn.setObjectName("secondaryBtn")
        open_folder_btn.clicked.connect(self._open_folder)
        left_lay.addWidget(open_folder_btn)

        splitter.addWidget(left)

        # -- Right Panel: Canvas ---
        right = QWidget()
        right_lay = QVBoxLayout(right)

        instr = QLabel(tr("review.instructions", lang))
        instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instr.setStyleSheet(
            f"background-color: {COLORS['hover']}; padding: 6px; "
            f"color: {COLORS['primary_dark']}; font-weight: bold; border-radius: 4px;"
        )
        right_lay.addWidget(instr)

        self.canvas = ImageCanvas()
        self.canvas.enable_review_mode(True)
        self.canvas.review_click.connect(self._on_canvas_click)
        right_lay.addWidget(self.canvas)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 10px;"
        )
        right_lay.addWidget(self.status_label)

        splitter.addWidget(right)
        splitter.setSizes([300, 800])

        main_layout.addWidget(splitter, stretch=1)

        # Footer buttons
        footer = QHBoxLayout()
        footer.setContentsMargins(10, 6, 10, 10)

        self.export_btn = QPushButton(tr("btn.export_report", lang))
        self.export_btn.setObjectName("secondaryBtn")
        footer.addWidget(self.export_btn)

        footer.addStretch()

        self.save_close_btn = QPushButton(tr("btn.save_close", lang))
        self.save_close_btn.setObjectName("primaryBtn")
        self.save_close_btn.setStyleSheet(
            f"background-color: {COLORS['secondary']}; color: white; "
            "font-weight: bold; padding: 10px 28px; border: none; border-radius: 6px;"
        )
        self.save_close_btn.clicked.connect(self._save_and_close)
        footer.addWidget(self.save_close_btn)

        main_layout.addLayout(footer)

    # =====================================================================
    #  Populate & Navigate
    # =====================================================================

    def _populate_list(self):
        lang = self.settings.language
        n = len(self.low_conf_images)
        if n == 0:
            self.summary_label.setText(tr("review.all_good", lang))
            return
        self.summary_label.setText(tr("review.need_review", lang, count=n))

        for img in self.low_conf_images:
            item = QTreeWidgetItem([
                img.get("filename", ""),
                str(img.get("stomata_count", 0)),
                f"{img.get('avg_confidence', 0):.2f}",
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, img)
            self.image_tree.addTopLevelItem(item)

        if n > 0:
            self.image_tree.setCurrentItem(self.image_tree.topLevelItem(0))

    def _on_image_selected(self, current, previous):
        if current is None:
            return
        img_data = current.data(0, Qt.ItemDataRole.UserRole)
        if not img_data:
            return

        # Save previous image corrections
        if previous is not None:
            self._save_current_corrections(previous)

        # Load the annotated image (or original)
        filepath = img_data.get("filepath") or img_data.get("original_path", "")
        if filepath and os.path.isfile(filepath):
            self.canvas.set_image_from_path(filepath)
            self.status_label.setText(os.path.basename(filepath))
        else:
            original = img_data.get("original_path", "")
            if original and os.path.isfile(original):
                self.canvas.set_image_from_path(original)
                self.status_label.setText(os.path.basename(original))

    # =====================================================================
    #  Click handling: add/remove stomata
    # =====================================================================

    def _on_canvas_click(self, scene_x, scene_y, button):
        lang = self.settings.language
        if button == Qt.MouseButton.LeftButton:
            self._add_marker(scene_x, scene_y)
            self.status_label.setText(
                tr("review.added_stoma", lang, x=int(scene_x), y=int(scene_y))
            )
        elif button == Qt.MouseButton.RightButton:
            removed = self._remove_nearest_marker(scene_x, scene_y)
            if removed:
                self.status_label.setText(tr("review.removed_stoma", lang))
            else:
                self.status_label.setText(tr("review.no_nearby", lang))

    def _add_marker(self, x, y):
        r = self.MARKER_RADIUS
        pen = QPen(QColor(COLORS["secondary"]), 3)
        brush = QBrush(QColor(0, 200, 0, 100))
        ellipse = self.canvas._scene.addEllipse(
            QRectF(x - r, y - r, 2 * r, 2 * r), pen, brush,
        )
        ellipse.setZValue(200)
        ellipse.setData(0, "review_marker")

    def _remove_nearest_marker(self, x, y) -> bool:
        closest = None
        min_dist = float("inf")
        for item in self.canvas._scene.items():
            if item.data(0) == "review_marker":
                rect = item.boundingRect()
                cx = rect.center().x()
                cy = rect.center().y()
                d = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
                if d < min_dist:
                    min_dist = d
                    closest = item
        if closest and min_dist < 50:
            self.canvas._scene.removeItem(closest)
            return True
        return False

    # =====================================================================
    #  Save & Close
    # =====================================================================

    def _save_current_corrections(self, tree_item):
        """Count markers on current canvas and update the result."""
        if tree_item is None:
            return
        img_data = tree_item.data(0, Qt.ItemDataRole.UserRole)
        if not img_data:
            return
        marker_count = sum(
            1 for item in self.canvas._scene.items()
            if item.data(0) == "review_marker"
        )
        filename = img_data.get("filename", "")
        original_count = img_data.get("stomata_count", 0)
        new_count = original_count + marker_count  # markers are net additions
        self._corrections[filename] = new_count
        tree_item.setText(1, str(new_count))

    def _save_and_close(self):
        # Save current image's corrections
        current = self.image_tree.currentItem()
        if current:
            self._save_current_corrections(current)

        # Apply corrections back to all_results
        for result in self.all_results:
            fname = result.get("filename", "")
            if fname in self._corrections:
                result["stomata_count"] = self._corrections[fname]
                result["manually_corrected"] = True

        self.accept()

    def _open_folder(self):
        current = self.image_tree.currentItem()
        if current is None:
            return
        img_data = current.data(0, Qt.ItemDataRole.UserRole)
        if not img_data:
            return
        path = img_data.get("filepath") or img_data.get("original_path", "")
        if path:
            folder = os.path.dirname(path)
            os.startfile(folder)
