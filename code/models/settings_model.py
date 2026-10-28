"""
SettingsModel -- Single source of truth for all user-configurable settings.

Emits `settings_changed(key, value)` whenever a setting is modified so that
controllers and views can react.  Persists to / loads from a JSON file.
"""

import json
import os
from PySide6.QtCore import QObject, Signal


_DEFAULTS = {
    # Detection
    "confidence": 0.25,
    "iou": 0.45,
    "low_conf_threshold": 0.75,

    # Edge Filtering
    "edge_filter_enabled": False,
    "edge_filter_method": "standard",      # "standard" | "area_percentage"
    "edge_margin_px": 5,
    "edge_area_threshold_pct": 50,

    # Calibration
    "pixels_per_mm": 0.0,

    # Appearance
    "theme": "light",                      # "light" | "dark"
    "bbox_color": "#00E676",
    "box_text_color": "#FFFFFF",
    "marker_radius": 12,
    "font_size": 10,

    # Export
    "export_format": "xlsx",               # "xlsx" | "csv"
    "default_output_folder": "",
    "auto_open_report": False,

    # Language
    "language": "en",                      # "en" | "de"

    # Model (last used)
    "model_path": "",
}


class SettingsModel(QObject):
    """Observable settings store backed by a JSON file."""

    settings_changed = Signal(str, object)  # key, new_value

    def __init__(self, settings_dir: str | None = None, parent=None):
        super().__init__(parent)

        if settings_dir is None:
            settings_dir = os.path.join(os.path.expanduser("~"), ".stomata_analyzer")
        self._settings_dir = settings_dir
        self._settings_file = os.path.join(settings_dir, "settings.json")
        self._data: dict = dict(_DEFAULTS)

    # -- Public API -----------------------------------------------------------

    def get(self, key: str, fallback=None):
        return self._data.get(key, fallback)

    def set(self, key: str, value):
        if self._data.get(key) == value:
            return
        self._data[key] = value
        self.settings_changed.emit(key, value)

    # Convenience typed accessors
    @property
    def confidence(self) -> float:
        return float(self._data["confidence"])

    @property
    def iou(self) -> float:
        return float(self._data["iou"])

    @property
    def low_conf_threshold(self) -> float:
        return float(self._data["low_conf_threshold"])

    @property
    def pixels_per_mm(self) -> float:
        return float(self._data["pixels_per_mm"])

    @property
    def theme(self) -> str:
        return str(self._data["theme"])

    @property
    def language(self) -> str:
        return str(self._data["language"])

    @property
    def export_format(self) -> str:
        return str(self._data["export_format"])

    @property
    def model_path(self) -> str:
        return str(self._data.get("model_path", ""))

    @property
    def edge_filter_enabled(self) -> bool:
        return bool(self._data["edge_filter_enabled"])

    @property
    def edge_filter_method(self) -> str:
        return str(self._data["edge_filter_method"])

    @property
    def edge_margin_px(self) -> int:
        return int(self._data["edge_margin_px"])

    @property
    def edge_area_threshold_pct(self) -> int:
        return int(self._data["edge_area_threshold_pct"])

    @property
    def bbox_color(self) -> str:
        return str(self._data["bbox_color"])

    @property
    def box_text_color(self) -> str:
        return str(self._data["box_text_color"])

    @property
    def auto_open_report(self) -> bool:
        return bool(self._data["auto_open_report"])

    @property
    def default_output_folder(self) -> str:
        return str(self._data.get("default_output_folder", ""))

    # -- Persistence ----------------------------------------------------------

    def save_to_file(self, path: str | None = None):
        target = path or self._settings_file
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
        except Exception as exc:
            print(f"[SettingsModel] save failed: {exc}")

    def load_from_file(self, path: str | None = None):
        target = path or self._settings_file
        if not os.path.isfile(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            for key, val in saved.items():
                if key in _DEFAULTS:
                    self._data[key] = val
        except Exception as exc:
            print(f"[SettingsModel] load failed: {exc}")

    def reset_to_defaults(self):
        for key, val in _DEFAULTS.items():
            self.set(key, val)

    def as_dict(self) -> dict:
        return dict(self._data)
