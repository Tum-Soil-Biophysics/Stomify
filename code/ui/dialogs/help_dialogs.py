"""
Dialogs — About, IoU help, Confidence help.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.config import COLORS, APP_TITLE, APP_VERSION, DEVELOPER_NAME, INSTITUTION, EMAIL, LINKEDIN


class _BaseHelpDialog(QDialog):
    """Styled help popup base class."""

    def __init__(self, parent, title, header_text, header_color, content):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(550, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {header_color};")
        hl = QVBoxLayout(header)
        lbl = QLabel(header_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        hl.addWidget(lbl)
        layout.addWidget(header)

        # Content
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(content)
        text.setStyleSheet(
            f"background-color: {COLORS['surface']}; font-family: Consolas; "
            "font-size: 10pt; padding: 15px;"
        )
        layout.addWidget(text)

        # Close button
        btn = QPushButton("Got it!")
        btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; "
            "font-weight: bold; padding: 8px 30px; border: none; border-radius: 4px;"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)


class IoUHelpDialog(_BaseHelpDialog):
    CONTENT = """
IoU stands for "Intersection over Union"

It controls how overlapping detection boxes are handled.


VISUAL EXPLANATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When two boxes overlap:

    ┌──────────────┐
    │   Box A      │
    │    ┌─────────┼────────┐
    │    │▓▓▓▓▓▓▓▓▓│        │
    │    │▓OVERLAP▓│        │  Box B
    └────┼─────────┘        │
         │                  │
         └──────────────────┘

    IoU = Area of Overlap / Total Area of Both Boxes


HOW IT AFFECTS YOUR RESULTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOW IoU (0.20 - 0.35):
  • Removes more overlapping boxes
  • Results in cleaner detection
  • Use if you see duplicate boxes on same stomata

MEDIUM IoU (0.40 - 0.50):  ← Default
  • Balanced approach
  • Works well for most cases

HIGH IoU (0.55 - 0.70):
  • Allows more overlapping boxes
  • May result in some duplicates
  • Use if stomata are very close together


QUICK FIX GUIDE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: Multiple boxes on the same stomata
→ Solution: Lower IoU to 0.30

Problem: Missing separate but close stomata
→ Solution: Raise IoU to 0.55
"""

    def __init__(self, parent=None):
        super().__init__(
            parent,
            "What is IoU Threshold?",
            "IoU Threshold Explained",
            COLORS["warning"],
            self.CONTENT,
        )


class ConfidenceHelpDialog(_BaseHelpDialog):
    CONTENT = """
The confidence threshold sets the minimum "certainty"
required to count a detection as a real stomata.


HOW IT WORKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The model assigns each detection a confidence score (0-100%):

  • 95% confidence = "Very sure this is a stomata"
  • 50% confidence = "Probably a stomata"
  • 20% confidence = "Might be a stomata"

Your threshold determines which detections are counted.


CHOOSING THE RIGHT VALUE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOW (0.10 - 0.20):
  ✓ Catches more stomata (higher recall)
  ✗ May include false positives
  → Use if you're missing stomata

MEDIUM (0.25 - 0.35):  ← Recommended
  ✓ Good balance
  → Use for most cases

HIGH (0.40 - 0.60):
  ✓ Very precise, fewer errors
  ✗ May miss some stomata
  → Use if you're getting false detections


QUICK FIX GUIDE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: Missing stomata
→ Solution: Lower confidence (try 0.15)

Problem: Detecting things that aren't stomata
→ Solution: Raise confidence (try 0.40)
"""

    def __init__(self, parent=None):
        super().__init__(
            parent,
            "What is Confidence Threshold?",
            "Confidence Threshold Explained",
            COLORS["primary_light"],
            self.CONTENT,
        )


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.resize(450, 350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background-color: {COLORS['primary']};")
        hl = QVBoxLayout(header)
        icon = QLabel("SDA")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 24px; color: white; font-weight: bold;")
        hl.addWidget(icon)
        layout.addWidget(header)

        # Body
        body = QFrame()
        body.setStyleSheet(f"background-color: {COLORS['surface']};")
        bl = QVBoxLayout(body)

        for text, style in [
            (APP_TITLE,
             f"font-size: 14px; font-weight: bold; color: {COLORS['primary']};"),
            (f"\nDeveloped by:\n{DEVELOPER_NAME}",
             "font-size: 11px;"),
            (INSTITUTION,
             f"font-size: 10px; color: {COLORS['text_secondary']};"),
            (EMAIL,
             f"font-size: 10px; color: {COLORS['primary']};"),
            (LINKEDIN,
             f"font-size: 10px; color: {COLORS['primary']};"),
            ("\nPowered by YOLOv8 • Python • OpenCV",
             f"font-size: 9px; color: {COLORS['text_secondary']};"),
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(style)
            bl.addWidget(lbl)

        layout.addWidget(body, stretch=1)

        btn = QPushButton("Close")
        btn.setStyleSheet(
            f"background-color: {COLORS['divider']}; color: {COLORS['text']}; "
            "padding: 5px 30px; border: none; border-radius: 4px;"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)
