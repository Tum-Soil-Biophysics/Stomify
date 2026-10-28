"""
MainWindow -- Thin MVC shell.

Only responsibilities:
  - Build header, tab widget, status bar, menu bar
  - Instantiate SettingsModel, AppState, Detector
  - Instantiate and connect the 3 controllers
  - Theme switching + language retranslation
"""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QStatusBar, QApplication,
    QFrame,
)

from core.config import APP_TITLE, APP_VERSION, COLORS, COLORS_DARK, DEVELOPER_NAME
from core.paths import resource_path
from core.detector import StomataDetectorML
from i18n import tr
from models.settings_model import SettingsModel
from models.app_state import AppState

from controllers.main_controller import MainController
from controllers.batch_controller import BatchController
from controllers.smart_counter_controller import SmartCounterController

from ui.tabs.analysis_tab import AnalysisTab
from ui.tabs.preview_tab import PreviewTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.help_tab import HelpTab
from ui.tabs.manual_count_tab import SmartCounterTab


class MainWindow(QMainWindow):
    """Application main window (thin MVC shell)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 850)

        # ----- Core objects (Model layer) -----
        self.settings = SettingsModel()
        self.settings.load_from_file()

        self.app_state = AppState()
        self.detector = StomataDetectorML()

        # Preview image path (ephemeral, used by MainController)
        self.preview_image_path: str | None = None

        # ----- Build UI -----
        self._build_ui()
        self._build_menu_bar()

        # ----- Controllers -----
        self.main_ctrl = MainController(self, self.settings, self.app_state, self.detector)
        self.batch_ctrl = BatchController(self, self.settings, self.app_state, self.detector)
        self.smart_ctrl = SmartCounterController(self, self.settings, self.app_state, self.detector)

        self.main_ctrl.connect_all()
        self.batch_ctrl.connect_all()
        self.smart_ctrl.connect_all()

        # ----- Restore model from settings -----
        saved_model = self.settings.model_path
        if saved_model and os.path.isfile(saved_model):
            success, _ = self.detector.load_model(saved_model)
            if success:
                self.main_ctrl._update_model_ui(saved_model)

        # ----- Apply saved theme -----
        self.apply_theme(self.settings.theme)

        self._set_status(tr("lbl.ready", self.settings.language))

    # =====================================================================
    #  UI Build
    # =====================================================================

    def _build_ui(self):
        self.setWindowIcon(QIcon(resource_path("resources", "logo.png")))
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        lang = self.settings.language

        # -- Header bar (compact, no blue box) --
        header = QFrame()
        header.setObjectName("headerFrame")
        header.setFixedHeight(36)
        header.setStyleSheet(
            "QFrame#headerFrame {"
            "  background-color: transparent;"
            "  border-bottom: 1px solid #E0E0E0;"
            "}"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)

        title_label = QLabel(APP_TITLE)
        title_label.setStyleSheet(
            "color: #1565C0; font-size: 13px; font-weight: bold;"
        )
        header_layout.addWidget(title_label)
        self._header_title = title_label

        header_layout.addStretch()

        self.header_model_label = QLabel(tr("lbl.no_model", lang))
        self.header_model_label.setStyleSheet(
            "color: #757575; font-size: 10px;"
        )
        header_layout.addWidget(self.header_model_label)

        self.header_load_btn = QPushButton(tr("btn.load_model", lang))
        self.header_load_btn.setObjectName("primaryBtn")
        self.header_load_btn.setStyleSheet(
            "background-color: #1565C0; color: white; "
            "font-weight: bold; padding: 4px 14px; border: none; border-radius: 4px;"
            "font-size: 11px;"
        )
        self.header_load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self.header_load_btn)

        main_layout.addWidget(header)

        # -- Tab widget --
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create tabs
        self.smart_counter_tab = SmartCounterTab(self.settings)
        self.analysis_tab = AnalysisTab(self.settings)
        self.preview_tab = PreviewTab(self.settings)
        self.settings_tab = SettingsTab(self.settings)

        # Add tabs in order: Smart Counter, Batch Analysis, Calibrate & Test, Settings
        self.tabs.addTab(self.smart_counter_tab, tr("tab.smart_counter", lang))
        self.tabs.addTab(self.analysis_tab, tr("tab.batch_analysis", lang))
        self.tabs.addTab(self.preview_tab, tr("tab.calibrate_test", lang))
        self.tabs.addTab(self.settings_tab, tr("tab.settings", lang))

        # Set default tab to Batch Analysis
        self.tabs.setCurrentIndex(1)

        main_layout.addWidget(self.tabs, stretch=1)

        # -- Status bar --
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.status_label = QLabel(tr("lbl.ready", lang))
        status_bar.addWidget(self.status_label, stretch=1)

        credits_label = QLabel(f"v{APP_VERSION} | {DEVELOPER_NAME}")
        credits_label.setStyleSheet("color: #9E9E9E; font-size: 9px;")
        status_bar.addPermanentWidget(credits_label)

    def _build_menu_bar(self):
        lang = self.settings.language
        menu_bar = self.menuBar()

        # -- File menu --
        file_menu = menu_bar.addMenu(tr("menu.file", lang))
        self._file_menu = file_menu

        load_model_action = QAction(tr("menu.load_model", lang), self)
        load_model_action.setShortcut("Ctrl+M")
        load_model_action.triggered.connect(lambda: self.main_ctrl.browse_model())
        file_menu.addAction(load_model_action)
        self._load_model_action = load_model_action

        file_menu.addSeparator()

        save_project_action = QAction(tr("menu.save_project", lang), self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(lambda: self.main_ctrl.save_project())
        file_menu.addAction(save_project_action)
        self._save_project_action = save_project_action

        open_project_action = QAction(tr("menu.open_project", lang), self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(lambda: self.main_ctrl.load_project())
        file_menu.addAction(open_project_action)
        self._open_project_action = open_project_action

        file_menu.addSeparator()

        exit_action = QAction(tr("menu.exit", lang), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self._exit_action = exit_action

        # -- View menu --
        view_menu = menu_bar.addMenu(tr("menu.view", lang))
        self._view_menu = view_menu

        review_action = QAction(tr("menu.review_window", lang), self)
        review_action.setShortcut("Ctrl+R")
        review_action.triggered.connect(lambda: self.batch_ctrl.show_review_dialog())
        view_menu.addAction(review_action)
        self._review_action = review_action

        # -- Help menu --
        help_menu = menu_bar.addMenu(tr("menu.help", lang))
        self._help_menu = help_menu

        how_to_use_action = QAction("How to Use", self)
        how_to_use_action.triggered.connect(self._show_how_to_use)
        help_menu.addAction(how_to_use_action)
        self._how_to_use_action = how_to_use_action

        about_action = QAction(tr("menu.about", lang), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        self._about_action = about_action

    # =====================================================================
    #  Theme Application
    # =====================================================================

    def apply_theme(self, theme: str):
        """Load and apply light or dark QSS theme."""
        if theme == "dark":
            qss_path = resource_path("resources", "style_dark.qss")
        else:
            qss_path = resource_path("resources", "style.qss")

        if os.path.isfile(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                QApplication.instance().setStyleSheet(f.read())
        else:
            # Fallback: clear custom stylesheet
            QApplication.instance().setStyleSheet("")

    # =====================================================================
    #  Language Retranslation
    # =====================================================================

    def retranslate_ui(self, lang: str):
        """Retranslate all UI strings to the given language."""
        self.tabs.setTabText(0, tr("tab.smart_counter", lang))
        self.tabs.setTabText(1, tr("tab.batch_analysis", lang))
        self.tabs.setTabText(2, tr("tab.calibrate_test", lang))
        self.tabs.setTabText(3, tr("tab.settings", lang))

        self.header_load_btn.setText(tr("btn.load_model", lang))
        self.status_label.setText(tr("lbl.ready", lang))

        # Menu
        self._file_menu.setTitle(tr("menu.file", lang))
        self._view_menu.setTitle(tr("menu.view", lang))
        self._help_menu.setTitle(tr("menu.help", lang))
        self._load_model_action.setText(tr("menu.load_model", lang))
        self._save_project_action.setText(tr("menu.save_project", lang))
        self._open_project_action.setText(tr("menu.open_project", lang))
        self._exit_action.setText(tr("menu.exit", lang))
        self._review_action.setText(tr("menu.review_window", lang))
        self._about_action.setText(tr("menu.about", lang))

        # Tabs
        if hasattr(self.analysis_tab, "retranslate"):
            self.analysis_tab.retranslate(lang)
        if hasattr(self.preview_tab, "retranslate"):
            self.preview_tab.retranslate(lang)
        if hasattr(self.settings_tab, "retranslate"):
            self.settings_tab.retranslate(lang)

    # =====================================================================
    #  Helpers
    # =====================================================================

    def _set_status(self, text: str):
        self.status_label.setText(text)

    def _show_how_to_use(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        from ui.tabs.help_tab import HelpTab
        dlg = QDialog(self)
        dlg.setWindowTitle("How to Use")
        dlg.resize(900, 700)
        lyt = QVBoxLayout(dlg)
        lyt.setContentsMargins(0, 0, 0, 0)
        h = HelpTab(self.settings, dlg)
        if hasattr(h, "retranslate"):
            h.retranslate(self.settings.language)
        lyt.addWidget(h)
        dlg.exec()

    def _show_about(self):
        from ui.dialogs.help_dialogs import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        """Save settings on exit."""
        self.settings.save_to_file()
        super().closeEvent(event)
