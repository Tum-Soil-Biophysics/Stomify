"""
PreviewTab -- Single image preview, AI detection test, and scale calibration.
Renamed to "Calibrate & Test" in the tab bar.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

from core.config import COLORS
from i18n import tr
from ui.widgets.image_canvas import ImageCanvas


class PreviewTab(QWidget):
    """Single-image preview, AI test, and scale calibration."""

    request_preview_detect = Signal()

    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings = settings_model
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        lang = self.settings.language

        # -- Top controls bar --
        top_bar = QHBoxLayout()

        self.load_btn = QPushButton(tr("btn.load_image", lang))
        self.load_btn.setObjectName("secondaryBtn")
        self.load_btn.setStyleSheet(
            f"background-color: {COLORS['primary_light']}; color: white; "
            "font-weight: bold; padding: 8px 16px; border: none; border-radius: 4px;"
        )
        top_bar.addWidget(self.load_btn)

        self.detect_btn = QPushButton(tr("btn.detect", lang))
        self.detect_btn.setObjectName("primaryBtn")
        self.detect_btn.setStyleSheet(
            f"background-color: {COLORS['secondary']}; color: white; "
            "font-weight: bold; padding: 8px 16px; border: none; border-radius: 4px;"
        )
        self.detect_btn.clicked.connect(self.request_preview_detect.emit)
        top_bar.addWidget(self.detect_btn)

        self.calibrate_btn = QPushButton(tr("btn.calibrate_scale", lang))
        self.calibrate_btn.setObjectName("secondaryBtn")
        self.calibrate_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; "
            "font-weight: bold; padding: 8px 16px; border: none; border-radius: 4px;"
        )
        top_bar.addWidget(self.calibrate_btn)

        top_bar.addStretch()

        self.zoom_out_btn = QPushButton("Zoom -")
        self.zoom_out_btn.setObjectName("secondaryBtn")
        self.zoom_out_btn.setStyleSheet(
            f"background-color: {COLORS['secondary_light']}; color: white; "
            "font-weight: bold; padding: 8px 12px; border: none; border-radius: 4px;"
        )
        self.zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_out_btn.clicked.connect(lambda: self._zoom_canvas(1 / 1.15))
        top_bar.addWidget(self.zoom_out_btn)

        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_in_btn.setObjectName("secondaryBtn")
        self.zoom_in_btn.setStyleSheet(
            f"background-color: {COLORS['secondary_light']}; color: white; "
            "font-weight: bold; padding: 8px 12px; border: none; border-radius: 4px;"
        )
        self.zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_in_btn.clicked.connect(lambda: self._zoom_canvas(1.15))
        top_bar.addWidget(self.zoom_in_btn)

        self.count_label = QLabel(f"{tr('lbl.stomata', lang)} -")
        self.count_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {COLORS['primary']}; padding: 0 10px;"
        )
        top_bar.addWidget(self.count_label)

        layout.addLayout(top_bar)

        # -- Info + calibration bar --
        info_bar = QHBoxLayout()

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        info_bar.addWidget(self.info_label)

        info_bar.addStretch()

        self.calibration_status = QLabel("")
        self.calibration_status.setStyleSheet(
            f"color: {COLORS['secondary']}; font-weight: bold; font-size: 10px;"
        )
        info_bar.addWidget(self.calibration_status)

        layout.addLayout(info_bar)

        # -- Canvas --
        self.canvas = ImageCanvas()
        layout.addWidget(self.canvas, stretch=1)



    def retranslate(self, lang: str):
        self.load_btn.setText(tr("btn.load_image", lang))
        self.detect_btn.setText(tr("btn.detect", lang))
        self.calibrate_btn.setText(tr("btn.calibrate_scale", lang))


    def _zoom_canvas(self, factor: float):
        self.canvas.zoom(factor)
