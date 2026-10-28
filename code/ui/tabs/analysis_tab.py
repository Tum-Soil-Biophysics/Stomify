"""
AnalysisTab -- Batch analysis: input/output selection, image list,
progress bar, action buttons, and review-flagged button.

Settings (confidence, IoU) moved to Settings tab.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QHeaderView,
)

from core.config import COLORS
from i18n import tr


class AnalysisTab(QWidget):
    """Batch analysis panel."""

    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings = settings_model
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        lang = self.settings.language

        # -- Input / Output paths --
        io_grp = QGroupBox(tr("grp.input_output", lang))
        io_grp.setObjectName("grpInputOutput")
        io_grid = QGridLayout(io_grp)

        io_grid.addWidget(QLabel(tr("lbl.input", lang)), 0, 0)
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setReadOnly(True)
        self.input_path_edit.setPlaceholderText("Select a folder or images...")
        io_grid.addWidget(self.input_path_edit, 0, 1)

        self.browse_folder_btn = QPushButton(tr("btn.folder", lang))
        self.browse_folder_btn.setObjectName("secondaryBtn")
        io_grid.addWidget(self.browse_folder_btn, 0, 2)

        self.browse_images_btn = QPushButton(tr("btn.images", lang))
        self.browse_images_btn.setObjectName("secondaryBtn")
        io_grid.addWidget(self.browse_images_btn, 0, 3)

        io_grid.addWidget(QLabel(tr("lbl.output", lang)), 1, 0)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Auto-generated if empty")
        io_grid.addWidget(self.output_path_edit, 1, 1)
        self.browse_output_btn = QPushButton(tr("btn.browse", lang))
        self.browse_output_btn.setObjectName("secondaryBtn")
        io_grid.addWidget(self.browse_output_btn, 1, 2, 1, 2)

        layout.addWidget(io_grp)
        self._grp_io = io_grp

        # -- Current settings display (read-only) --
        self.settings_label = QLabel(self._settings_summary())
        self.settings_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 10px; padding: 4px 8px;"
        )
        layout.addWidget(self.settings_label)

        # -- Image tree --
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Filename", "Plant ID", "Position", "Rep", "Count", "Confidence",
        ])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tree, stretch=1)



        # -- Progress --
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # -- Results label --
        self.results_label = QLabel("")
        self.results_label.setStyleSheet(
            f"font-weight: bold; color: {COLORS['primary']}; font-size: 11px;"
        )
        layout.addWidget(self.results_label)

        # -- Action buttons --
        btn_row = QHBoxLayout()

        self.analyze_btn = QPushButton(tr("btn.analyze_all", lang))
        self.analyze_btn.setObjectName("primaryBtn")
        self.analyze_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; "
            "font-weight: bold; padding: 10px 24px; border: none; border-radius: 6px; "
            "font-size: 13px;"
        )
        btn_row.addWidget(self.analyze_btn)

        self.stop_btn = QPushButton(tr("btn.stop", lang))
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.setStyleSheet(
            f"background-color: {COLORS['error']}; color: white; "
            "font-weight: bold; padding: 10px 20px; border: none; border-radius: 6px; "
            "font-size: 13px;"
        )
        btn_row.addWidget(self.stop_btn)

        self.clear_btn = QPushButton(tr("btn.clear", lang))
        self.clear_btn.setObjectName("secondaryBtn")
        btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()

        # Review Flagged button (initially hidden)
        self.review_flagged_btn = QPushButton("")
        self.review_flagged_btn.setObjectName("dangerBtn")
        self.review_flagged_btn.setStyleSheet(
            f"background-color: {COLORS['warning']}; color: white; "
            "font-weight: bold; padding: 10px 24px; border: none; border-radius: 6px; "
            "font-size: 13px;"
        )
        self.review_flagged_btn.setVisible(False)
        btn_row.addWidget(self.review_flagged_btn)

        layout.addLayout(btn_row)

        # Listen for settings changes
        self.settings.settings_changed.connect(self._on_setting_changed)

    # -- Public API --

    def update_tree_item(self, idx: int, count: int, avg_conf: float):
        item = self.tree.topLevelItem(idx)
        if item:
            item.setText(4, str(count))
            item.setText(5, f"{avg_conf:.2f}")

    def clear(self):
        self.tree.clear()
        self.progress_bar.setValue(0)
        self.results_label.setText("")


    def retranslate(self, lang: str):
        self._grp_io.setTitle(tr("grp.input_output", lang))
        self.analyze_btn.setText(tr("btn.analyze_all", lang))
        self.stop_btn.setText(tr("btn.stop", lang))
        self.clear_btn.setText(tr("btn.clear", lang))

        self.settings_label.setText(self._settings_summary())

    # -- Helpers --

    def _settings_summary(self) -> str:
        s = self.settings
        parts = [
            f"Confidence: {s.confidence:.2f}",
            f"IoU: {s.iou:.2f}",
        ]
        if s.pixels_per_mm and s.pixels_per_mm > 0:
            parts.append(f"Px/mm: {s.pixels_per_mm:.1f}")
        if s.edge_filter_enabled:
            parts.append(f"Edge Filter: {s.edge_filter_method}")
        return "  |  ".join(parts) + "  (change in Settings)"

    def _on_setting_changed(self, key, value):
        if key in ("confidence", "iou", "pixels_per_mm",
                    "edge_filter_enabled", "edge_filter_method"):
            self.settings_label.setText(self._settings_summary())

