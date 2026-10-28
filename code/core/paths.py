"""
Centralized path resolution for both dev mode and PyInstaller frozen mode.
"""

import os
import sys


def get_base_dir() -> str:
    """Return the application's base directory.

    In development:  the stomata_yolo_app/ folder.
    When frozen by PyInstaller (--onefile): the temp _MEIPASS folder.
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        return sys._MEIPASS
    # Development: this file is  core/paths.py  →  go up one level
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts) -> str:
    """Build an absolute path to a bundled resource file.

    Usage:
        resource_path("resources", "logo.png")
        resource_path("resources", "style.qss")
    """
    return os.path.join(get_base_dir(), *parts)
