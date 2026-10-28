"""
SettingsTab -- Comprehensive settings panel with 7 sections.

All controls bind to SettingsModel via two-way data binding.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QLabel, QSlider, QCheckBox, QComboBox, QRadioButton,
    QPushButton, QLineEdit, QScrollArea, QColorDialog,
    QFileDialog, QTextEdit, QButtonGroup, QFrame,
)

from core.config import COLORS
from i18n import tr


class SettingsTab(QWidget):
    """Full-featured Settings panel."""

    def __init__(self, settings_model, parent=None):
        super().__init__(parent)
        self.settings = settings_model
        self._building = True   # flag to suppress signals during build
        self._init_ui()
        self._sync_from_model()
        self._building = False

    # =====================================================================
    #  UI Construction
    # =====================================================================

    def _init_ui(self):
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setSpacing(14)

        self._build_detection_params()
        self._build_counting_rules()
        self._build_calibration()
        self._build_appearance()
        self._build_export_prefs()
        self._build_language()
        self._build_model_info()
        self._build_reset()

        self._layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # -- 1. Detection Parameters ---------------------------------------------

    def _build_detection_params(self):
        grp = QGroupBox(tr("grp.detection_params", self.settings.language))
        grp.setObjectName("grpDetection")
        grid = QGridLayout(grp)

        # Confidence
        grid.addWidget(QLabel(tr("lbl.confidence", self.settings.language)), 0, 0)
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setObjectName("confSlider")
        self.confidence_slider.setRange(5, 95)
        self.confidence_label = QLabel("0.25")
        grid.addWidget(self.confidence_slider, 0, 1)
        grid.addWidget(self.confidence_label, 0, 2)

        # IoU
        grid.addWidget(QLabel(tr("lbl.iou", self.settings.language)), 1, 0)
        self.iou_slider = QSlider(Qt.Orientation.Horizontal)
        self.iou_slider.setObjectName("iouSlider")
        self.iou_slider.setRange(10, 90)
        self.iou_label = QLabel("0.45")
        grid.addWidget(self.iou_slider, 1, 1)
        grid.addWidget(self.iou_label, 1, 2)

        # Low Confidence Threshold
        grid.addWidget(QLabel(tr("settings.low_conf_thresh", self.settings.language)), 2, 0)
        self.low_conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.low_conf_slider.setObjectName("lowConfSlider")
        self.low_conf_slider.setRange(10, 95)
        self.low_conf_label = QLabel("0.75")
        grid.addWidget(self.low_conf_slider, 2, 1)
        grid.addWidget(self.low_conf_label, 2, 2)

        # Connect
        self.confidence_slider.valueChanged.connect(self._on_confidence_changed)
        self.iou_slider.valueChanged.connect(self._on_iou_changed)
        self.low_conf_slider.valueChanged.connect(self._on_low_conf_changed)

        self._layout.addWidget(grp)
        self._grp_detection = grp

    # -- 2. Counting Rules (Edge Filtering) -----------------------------------

    def _build_counting_rules(self):
        grp = QGroupBox(tr("grp.counting_rules", self.settings.language))
        grp.setObjectName("grpCountingRules")
        grid = QGridLayout(grp)

        self.edge_filter_check = QCheckBox(tr("settings.edge_filter", self.settings.language))
        grid.addWidget(self.edge_filter_check, 0, 0, 1, 3)

        # Method selector
        grid.addWidget(QLabel(tr("settings.edge_method", self.settings.language)), 1, 0)
        self.edge_method_combo = QComboBox()
        self.edge_method_combo.addItem(tr("settings.edge_standard", self.settings.language), "standard")
        self.edge_method_combo.addItem(tr("settings.edge_area", self.settings.language), "area_percentage")
        grid.addWidget(self.edge_method_combo, 1, 1, 1, 2)

        # Edge margin
        grid.addWidget(QLabel(tr("settings.edge_margin", self.settings.language)), 2, 0)
        self.edge_margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.edge_margin_slider.setRange(1, 50)
        self.edge_margin_label = QLabel("5")
        grid.addWidget(self.edge_margin_slider, 2, 1)
        grid.addWidget(self.edge_margin_label, 2, 2)

        # Area threshold  (active only for Method B)
        grid.addWidget(QLabel(tr("settings.edge_area_thresh", self.settings.language)), 3, 0)
        self.edge_area_slider = QSlider(Qt.Orientation.Horizontal)
        self.edge_area_slider.setRange(10, 90)
        self.edge_area_label = QLabel("50")
        grid.addWidget(self.edge_area_slider, 3, 1)
        grid.addWidget(self.edge_area_label, 3, 2)

        # Connect
        self.edge_filter_check.stateChanged.connect(self._on_edge_filter_toggled)
        self.edge_method_combo.currentIndexChanged.connect(self._on_edge_method_changed)
        self.edge_margin_slider.valueChanged.connect(self._on_edge_margin_changed)
        self.edge_area_slider.valueChanged.connect(self._on_edge_area_changed)

        self._layout.addWidget(grp)
        self._grp_counting = grp

    # -- 3. Calibration -------------------------------------------------------

    def _build_calibration(self):
        grp = QGroupBox(tr("grp.calibration", self.settings.language))
        grp.setObjectName("grpCalibration")
        lay = QHBoxLayout(grp)

        lay.addWidget(QLabel(tr("lbl.pixels_per_mm", self.settings.language)))
        self.calibration_display = QLabel(tr("settings.not_set", self.settings.language))
        self.calibration_display.setStyleSheet("font-weight: bold; font-size: 12px;")
        lay.addWidget(self.calibration_display)
        lay.addWidget(QLabel(tr("settings.calibration_note", self.settings.language)))
        lay.addStretch()

        self._layout.addWidget(grp)
        self._grp_calibration = grp

    # -- 4. Appearance --------------------------------------------------------

    def _build_appearance(self):
        grp = QGroupBox(tr("grp.appearance", self.settings.language))
        grp.setObjectName("grpAppearance")
        layout = QVBoxLayout(grp)

        grid = QGridLayout()

        # Theme
        grid.addWidget(QLabel(tr("settings.theme", self.settings.language)), 0, 0)
        self.theme_light_radio = QRadioButton(tr("settings.theme_light", self.settings.language))
        self.theme_dark_radio = QRadioButton(tr("settings.theme_dark", self.settings.language))
        theme_group = QButtonGroup(self)
        theme_group.addButton(self.theme_light_radio, 0)
        theme_group.addButton(self.theme_dark_radio, 1)
        theme_row = QHBoxLayout()
        theme_row.addWidget(self.theme_light_radio)
        theme_row.addWidget(self.theme_dark_radio)
        theme_row.addStretch()
        grid.addLayout(theme_row, 0, 1, 1, 2)

        # Bounding Box Color
        grid.addWidget(QLabel(tr("settings.bbox_color", self.settings.language)), 1, 0)
        self.bbox_color_preview = QLabel("   ")
        self.bbox_color_preview.setFixedSize(30, 20)
        self.bbox_color_btn = QPushButton(tr("btn.pick_color", self.settings.language))
        self.bbox_color_btn.setObjectName("secondaryBtn")
        color_row = QHBoxLayout()
        color_row.addWidget(self.bbox_color_preview)
        color_row.addWidget(self.bbox_color_btn)
        color_row.addStretch()
        grid.addLayout(color_row, 1, 1, 1, 2)
        bbox_desc = QLabel(
            "Changes the color of detection rectangles drawn around stomata "
            "in Batch Analysis annotated images and Calibrate & Test preview."
        )
        bbox_desc.setWordWrap(True)
        bbox_desc.setStyleSheet("color: #757575; font-size: 9px; margin-left: 4px;")
        grid.addWidget(bbox_desc, 2, 0, 1, 3)

        # Box Text Color
        grid.addWidget(QLabel(tr("settings.box_text_color", self.settings.language)), 3, 0)
        self.box_text_color_preview = QLabel("   ")
        self.box_text_color_preview.setFixedSize(30, 20)
        self.box_text_color_btn = QPushButton(tr("btn.pick_color", self.settings.language))
        self.box_text_color_btn.setObjectName("secondaryBtn")
        text_color_row = QHBoxLayout()
        text_color_row.addWidget(self.box_text_color_preview)
        text_color_row.addWidget(self.box_text_color_btn)
        text_color_row.addStretch()
        grid.addLayout(text_color_row, 3, 1, 1, 2)

        # Marker Size
        grid.addWidget(QLabel(tr("settings.marker_size", self.settings.language)), 4, 0)
        self.marker_slider = QSlider(Qt.Orientation.Horizontal)
        self.marker_slider.setRange(4, 30)
        self.marker_label = QLabel("12")
        grid.addWidget(self.marker_slider, 4, 1)
        grid.addWidget(self.marker_label, 4, 2)
        marker_desc = QLabel(
            "Changes the size of the circle markers in the Smart Counter tab "
            "and the center dots on detected stomata."
        )
        marker_desc.setWordWrap(True)
        marker_desc.setStyleSheet("color: #757575; font-size: 9px; margin-left: 4px;")
        grid.addWidget(marker_desc, 5, 0, 1, 3)

        # Font Size
        grid.addWidget(QLabel(tr("settings.font_size", self.settings.language)), 6, 0)
        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(8, 30)
        self.font_label = QLabel("10")
        grid.addWidget(self.font_slider, 6, 1)
        grid.addWidget(self.font_label, 6, 2)
        font_desc = QLabel(
            "Changes the size of numbered labels (e.g. '1 (95%)') drawn on "
            "annotated detection images in Batch Analysis output."
        )
        font_desc.setWordWrap(True)
        font_desc.setStyleSheet("color: #757575; font-size: 9px; margin-left: 4px;")
        grid.addWidget(font_desc, 7, 0, 1, 3)

        layout.addLayout(grid)

        # Connect
        self.theme_light_radio.toggled.connect(self._on_theme_toggled)
        self.bbox_color_btn.clicked.connect(self._pick_bbox_color)
        self.box_text_color_btn.clicked.connect(self._pick_box_text_color)
        self.marker_slider.valueChanged.connect(self._on_marker_changed)
        self.font_slider.valueChanged.connect(self._on_font_changed)

        self._layout.addWidget(grp)
        self._grp_appearance = grp

    # -- 5. Export Preferences ------------------------------------------------

    def _build_export_prefs(self):
        grp = QGroupBox(tr("grp.export_prefs", self.settings.language))
        grp.setObjectName("grpExport")
        grid = QGridLayout(grp)

        # Format
        grid.addWidget(QLabel(tr("settings.export_format", self.settings.language)), 0, 0)
        self.export_xlsx_radio = QRadioButton("Excel (.xlsx)")
        self.export_csv_radio = QRadioButton("CSV (.csv)")
        fmt_group = QButtonGroup(self)
        fmt_group.addButton(self.export_xlsx_radio, 0)
        fmt_group.addButton(self.export_csv_radio, 1)
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(self.export_xlsx_radio)
        fmt_row.addWidget(self.export_csv_radio)
        fmt_row.addStretch()
        grid.addLayout(fmt_row, 0, 1, 1, 2)

        # Default output dir
        grid.addWidget(QLabel(tr("settings.output_folder", self.settings.language)), 1, 0)
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setReadOnly(True)
        browse_btn = QPushButton(tr("btn.browse", self.settings.language))
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.clicked.connect(self._browse_output_folder)
        grid.addWidget(self.output_folder_edit, 1, 1)
        grid.addWidget(browse_btn, 1, 2)

        # Auto-open
        self.auto_open_check = QCheckBox(tr("settings.auto_open", self.settings.language))
        grid.addWidget(self.auto_open_check, 2, 0, 1, 3)

        # Connect
        self.export_xlsx_radio.toggled.connect(self._on_export_format_changed)
        self.auto_open_check.stateChanged.connect(self._on_auto_open_changed)

        self._layout.addWidget(grp)
        self._grp_export = grp

    # -- 6. Language ----------------------------------------------------------

    def _build_language(self):
        grp = QGroupBox(tr("grp.language", self.settings.language))
        grp.setObjectName("grpLanguage")
        lay = QHBoxLayout(grp)

        lay.addWidget(QLabel(tr("settings.language", self.settings.language)))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Deutsch", "de")
        lay.addWidget(self.lang_combo)
        lay.addStretch()

        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)

        self._layout.addWidget(grp)
        self._grp_language = grp

    # -- 7. Model Info (read-only) --------------------------------------------

    def _build_model_info(self):
        grp = QGroupBox(tr("grp.model_info", self.settings.language))
        grp.setObjectName("grpModelInfo")
        lay = QVBoxLayout(grp)

        self.model_info_text = QTextEdit()
        self.model_info_text.setReadOnly(True)
        self.model_info_text.setMaximumHeight(120)
        self.model_info_text.setPlainText(tr("lbl.no_model", self.settings.language))
        lay.addWidget(self.model_info_text)

        self.load_model_btn = QPushButton(tr("btn.load_model", self.settings.language))
        self.load_model_btn.setObjectName("primaryBtn")
        lay.addWidget(self.load_model_btn)

        self._layout.addWidget(grp)
        self._grp_model = grp

    # -- 8. Reset -------------------------------------------------------------

    def _build_reset(self):
        grp = QGroupBox(tr("grp.reset", self.settings.language))
        grp.setObjectName("grpReset")
        lay = QVBoxLayout(grp)

        self.reset_btn = QPushButton(tr("btn.reset_defaults", self.settings.language))
        self.reset_btn.setObjectName("dangerBtn")
        self.reset_btn.clicked.connect(self._on_reset)
        lay.addWidget(self.reset_btn)

        self.settings_loc_label = QLabel(
            f"{tr('settings.settings_location', self.settings.language)} "
            f"{os.path.join(os.path.expanduser('~'), '.stomata_analyzer', 'settings.json')}"
        )
        self.settings_loc_label.setStyleSheet("color: #757575; font-size: 9px;")
        lay.addWidget(self.settings_loc_label)

        self._layout.addWidget(grp)
        self._grp_reset = grp

    # =====================================================================
    #  Sync Model -> UI
    # =====================================================================

    def _sync_from_model(self):
        s = self.settings

        # Detection
        self.confidence_slider.setValue(int(s.confidence * 100))
        self.iou_slider.setValue(int(s.iou * 100))
        self.low_conf_slider.setValue(int(s.low_conf_threshold * 100))

        # Edge filtering
        self.edge_filter_check.setChecked(s.edge_filter_enabled)
        idx = self.edge_method_combo.findData(s.edge_filter_method)
        if idx >= 0:
            self.edge_method_combo.setCurrentIndex(idx)
        self.edge_margin_slider.setValue(s.edge_margin_px)
        self.edge_area_slider.setValue(s.edge_area_threshold_pct)
        self._update_edge_ui_state()

        # Calibration
        self.update_calibration_display(s.pixels_per_mm)

        # Appearance
        self.theme_light_radio.setChecked(s.theme == "light")
        self.theme_dark_radio.setChecked(s.theme == "dark")
        self._set_color_preview(s.bbox_color)
        self._set_text_color_preview(s.box_text_color)
        self.marker_slider.setValue(s.get("marker_radius", 12))
        self.font_slider.setValue(s.get("font_size", 10))

        # Export
        self.export_xlsx_radio.setChecked(s.export_format == "xlsx")
        self.export_csv_radio.setChecked(s.export_format == "csv")
        self.output_folder_edit.setText(s.default_output_folder)
        self.auto_open_check.setChecked(s.auto_open_report)

        # Language
        idx = self.lang_combo.findData(s.language)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

    # =====================================================================
    #  Slots  (UI -> Model)
    # =====================================================================

    def _on_confidence_changed(self, val):
        self.confidence_label.setText(f"{val / 100:.2f}")
        if not self._building:
            self.settings.set("confidence", val / 100.0)

    def _on_iou_changed(self, val):
        self.iou_label.setText(f"{val / 100:.2f}")
        if not self._building:
            self.settings.set("iou", val / 100.0)

    def _on_low_conf_changed(self, val):
        self.low_conf_label.setText(f"{val / 100:.2f}")
        if not self._building:
            self.settings.set("low_conf_threshold", val / 100.0)

    def _on_edge_filter_toggled(self, state):
        if not self._building:
            self.settings.set("edge_filter_enabled", bool(state))
        self._update_edge_ui_state()

    def _on_edge_method_changed(self, idx):
        if not self._building:
            method = self.edge_method_combo.currentData()
            self.settings.set("edge_filter_method", method)
        self._update_edge_ui_state()

    def _on_edge_margin_changed(self, val):
        self.edge_margin_label.setText(str(val))
        if not self._building:
            self.settings.set("edge_margin_px", val)

    def _on_edge_area_changed(self, val):
        self.edge_area_label.setText(str(val))
        if not self._building:
            self.settings.set("edge_area_threshold_pct", val)

    def _on_theme_toggled(self, checked):
        if self._building:
            return
        theme = "light" if self.theme_light_radio.isChecked() else "dark"
        self.settings.set("theme", theme)

    def _pick_bbox_color(self):
        current = QColor(self.settings.bbox_color)
        color = QColorDialog.getColor(current, self, "Select Bounding Box Color")
        if color.isValid():
            self.settings.set("bbox_color", color.name())
            self._set_color_preview(color.name())

    def _pick_box_text_color(self):
        current = QColor(self.settings.box_text_color)
        color = QColorDialog.getColor(current, self, "Select Box Text Color")
        if color.isValid():
            self.settings.set("box_text_color", color.name())
            self._set_text_color_preview(color.name())

    def _on_marker_changed(self, val):
        self.marker_label.setText(str(val))
        if not self._building:
            self.settings.set("marker_radius", val)

    def _on_font_changed(self, val):
        self.font_label.setText(str(val))
        if not self._building:
            self.settings.set("font_size", val)

    def _on_export_format_changed(self, checked):
        if self._building:
            return
        fmt = "xlsx" if self.export_xlsx_radio.isChecked() else "csv"
        self.settings.set("export_format", fmt)

    def _browse_output_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select default output folder")
        if path:
            self.output_folder_edit.setText(path)
            self.settings.set("default_output_folder", path)

    def _on_auto_open_changed(self, state):
        if not self._building:
            self.settings.set("auto_open_report", bool(state))

    def _on_language_changed(self, idx):
        if self._building:
            return
        lang = self.lang_combo.currentData()
        if lang:
            self.settings.set("language", lang)

    def _on_reset(self):
        self.settings.reset_to_defaults()
        self._building = True
        self._sync_from_model()
        self._building = False

    # =====================================================================
    #  Public API
    # =====================================================================

    def update_model_info(self, info_lines: list[str]):
        self.model_info_text.setPlainText("\n".join(info_lines))

    def update_calibration_display(self, ppm: float):
        lang = self.settings.language
        if ppm and ppm > 0:
            self.calibration_display.setText(f"{ppm:.2f} px/mm")
        else:
            self.calibration_display.setText(tr("settings.not_set", lang))

    def retranslate(self, lang: str):
        """Update all visible strings to the specified language."""
        self._grp_detection.setTitle(tr("grp.detection_params", lang))
        self._grp_counting.setTitle(tr("grp.counting_rules", lang))
        self._grp_calibration.setTitle(tr("grp.calibration", lang))
        self._grp_appearance.setTitle(tr("grp.appearance", lang))
        self._grp_export.setTitle(tr("grp.export_prefs", lang))
        self._grp_language.setTitle(tr("grp.language", lang))
        self._grp_model.setTitle(tr("grp.model_info", lang))
        self._grp_reset.setTitle(tr("grp.reset", lang))

        self.load_model_btn.setText(tr("btn.load_model", lang))
        self.reset_btn.setText(tr("btn.reset_defaults", lang))
        self.edge_filter_check.setText(tr("settings.edge_filter", lang))
        self.auto_open_check.setText(tr("settings.auto_open", lang))

    # =====================================================================
    #  Helpers
    # =====================================================================

    def _update_edge_ui_state(self):
        enabled = self.edge_filter_check.isChecked()
        self.edge_method_combo.setEnabled(enabled)
        self.edge_margin_slider.setEnabled(enabled)
        is_area = (self.edge_method_combo.currentData() == "area_percentage")
        self.edge_area_slider.setEnabled(enabled and is_area)

    def _set_color_preview(self, color_hex: str):
        self.bbox_color_preview.setStyleSheet(
            f"background-color: {color_hex}; border: 1px solid #999; border-radius: 3px;"
        )

    def _set_text_color_preview(self, color_hex: str):
        self.box_text_color_preview.setStyleSheet(
            f"background-color: {color_hex}; border: 1px solid #999; border-radius: 3px;"
        )
