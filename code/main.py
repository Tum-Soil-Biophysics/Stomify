"""
Stomatal Density Analyzer v7.0 -- Entry point.
"""

import sys
import os
import ctypes

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt

from core.config import APP_TITLE, APP_VERSION
from core.paths import resource_path


def main():
    # Force Windows to treat Stomify as a unique app (fixes Taskbar Icon Caching)
    if os.name == 'nt':
        myappid = 'vimukthi.stomify.analyzer.1_0' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    print(f"Stomatal Density Analyzer v{APP_VERSION}")
    print(f"Starting application...")

    app = QApplication(sys.argv)
    app.setApplicationName("Stomify")
    app.setStyle("Fusion")
    
    # Provide the icon globally so Windows Taskbar sets it correctly alongside AppUserModelID
    app.setWindowIcon(QIcon(resource_path("resources", "logo.png")))

    # Show splash screen
    splash_pix = QPixmap(resource_path("resources", "splash.png"))
    # Scale the splash image down to a reasonable "center box" size
    splash_pix = splash_pix.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    # Default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # NOTE: Stylesheet is loaded by MainWindow.apply_theme() — no need to load here.

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
