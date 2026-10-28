"""
CalibrationDialog — Enter real-world length for a drawn pixel line.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QComboBox, QPushButton, QFrame,
)
from PySide6.QtCore import Qt

from core.config import COLORS


class CalibrationDialog(QDialog):
    """Pop-up to convert a pixel distance to real-world mm."""

    def __init__(self, pixel_length: float, parent=None):
        super().__init__(parent)
        self.pixel_length = pixel_length
        self.pixels_per_mm: float | None = None

        self.setWindowTitle("Scale Calibration")
        self.resize(420, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {COLORS['primary']};")
        hl = QVBoxLayout(header)
        lbl = QLabel("Define Scale")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        hl.addWidget(lbl)
        layout.addWidget(header)

        # Body
        body = QFrame()
        body.setStyleSheet(f"background-color: {COLORS['surface']}; padding: 15px;")
        bl = QVBoxLayout(body)

        bl.addWidget(QLabel(f"You drew a line of {pixel_length:.1f} image pixels."))
        bl.addWidget(QLabel("What real-world length does this line represent?"))

        # Input row
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Length:"))

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.01, 100000)
        self.length_spin.setValue(100)
        self.length_spin.setDecimals(2)
        input_row.addWidget(self.length_spin)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["µm", "mm"])
        input_row.addWidget(self.unit_combo)
        bl.addLayout(input_row)

        # Preview label
        self.result_label = QLabel("")
        self.result_label.setStyleSheet(f"color: {COLORS['secondary']};")
        bl.addWidget(self.result_label)

        # Connect live preview
        self.length_spin.valueChanged.connect(self._update_preview)
        self.unit_combo.currentTextChanged.connect(self._update_preview)
        self._update_preview()

        # Buttons
        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet(
            f"background-color: {COLORS['secondary']}; color: white; "
            "font-weight: bold; padding: 6px 25px; border: none; border-radius: 4px;"
        )
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            f"background-color: {COLORS['divider']}; color: {COLORS['text']}; "
            "padding: 6px 20px; border: none; border-radius: 4px;"
        )
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        bl.addLayout(btn_row)

        layout.addWidget(body, stretch=1)

    def _length_mm(self) -> float:
        val = self.length_spin.value()
        if self.unit_combo.currentText() == "µm":
            return val / 1000.0
        return val

    def _update_preview(self):
        length_mm = self._length_mm()
        if length_mm <= 0:
            self.result_label.setText("⚠️ Enter a positive length")
            return
        ppm = self.pixel_length / length_mm
        self.result_label.setText(
            f"→ {ppm:.1f} pixels/mm  "
            f"(= {self.pixel_length:.1f} px / {length_mm:.4f} mm)"
        )

    def _apply(self):
        length_mm = self._length_mm()
        if length_mm <= 0:
            return
        self.pixels_per_mm = self.pixel_length / length_mm
        self.accept()
