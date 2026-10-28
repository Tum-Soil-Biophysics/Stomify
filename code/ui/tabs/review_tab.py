"""
ReviewTab — Low-confidence image review with manual correction (add/remove stomata).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.config import COLORS
from ui.widgets.image_canvas import ImageCanvas


class ReviewTab(QWidget):
    """Review tab: table of low-confidence images, canvas editor for corrections."""

    save_requested = Signal()
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(f"background-color: {COLORS['warning']};")
        hl = QHBoxLayout(header)
        self.header_label = QLabel(
            "⚠️ Low Confidence Images (< 75%) — Click to Correct"
        )
        self.header_label.setStyleSheet(
            "color: white; font-size: 11px; font-weight: bold;"
        )
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(self.header_label)
        layout.addWidget(header)

        # ── Splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: image list
        left = QWidget()
        ll = QVBoxLayout(left)

        ll.addWidget(QLabel("Select an image to review:"))

        self.review_tree = QTreeWidget()
        self.review_tree.setHeaderLabels(
            ["Filename", "Plant", "Position", "Count", "Conf"]
        )
        self.review_tree.setAlternatingRowColors(True)
        hdr = self.review_tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        ll.addWidget(self.review_tree, stretch=1)

        self.summary_label = QLabel("No images analyzed yet")
        ll.addWidget(self.summary_label)

        btn_row = QHBoxLayout()
        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.open_folder_btn)

        self.add_image_btn = QPushButton("➕ Add Image")
        self.add_image_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.add_image_btn)
        ll.addLayout(btn_row)

        splitter.addWidget(left)

        # RIGHT: canvas editor
        right = QWidget()
        rl = QVBoxLayout(right)

        # Instructions + controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel(
            "🖱️ Left-click = Add   |   Right-click = Remove"
        ))
        ctrl.addStretch()

        self.count_label = QLabel("Count: -")
        self.count_label.setStyleSheet(
            f"color: {COLORS['secondary']}; font-size: 11px; font-weight: bold;"
        )
        ctrl.addWidget(self.count_label)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet(
            f"background-color: {COLORS['secondary']}; color: white; "
            "font-weight: bold; padding: 4px 12px; border: none; border-radius: 4px;"
        )
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_requested)
        ctrl.addWidget(self.save_btn)

        self.export_btn = QPushButton("📊 Export Report")
        self.export_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; "
            "font-weight: bold; padding: 4px 12px; border: none; border-radius: 4px;"
        )
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_requested)
        ctrl.addWidget(self.export_btn)

        rl.addLayout(ctrl)

        self.canvas = ImageCanvas()
        rl.addWidget(self.canvas, stretch=1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, stretch=1)
