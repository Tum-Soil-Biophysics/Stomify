"""
AppState -- Runtime session data: loaded images, results, corrections.

Serialisable to JSON for the Save / Load Project feature.
"""

import json
import os
from PySide6.QtCore import QObject, Signal


class AppState(QObject):
    """Holds all mutable session data for the application."""

    state_changed = Signal(str)  # key that changed

    def __init__(self, parent=None):
        super().__init__(parent)

        self.image_files: list[dict] = []
        self.results: list[dict] = []
        self.low_confidence_images: list[dict] = []

        self.model_path: str | None = None

        # Smart Counter data  {image_path: [(x1,y1,x2,y2,is_manual,conf), ...]}
        self.smart_counter_data: dict[str, list[tuple]] = {}
        self.smart_counter_paths: list[str] = []

    # -- Convenience helpers --------------------------------------------------

    def clear(self):
        self.image_files.clear()
        self.results.clear()
        self.low_confidence_images.clear()
        self.state_changed.emit("cleared")

    def clear_smart_counter(self):
        self.smart_counter_data.clear()
        self.smart_counter_paths.clear()
        self.state_changed.emit("smart_counter_cleared")

    # -- Project serialisation ------------------------------------------------

    def save_project(self, filepath: str):
        """Serialise current session to a JSON file."""
        data = {
            "version": "7.0",
            "image_files": self.image_files,
            "results": _sanitise_results(self.results),
            "low_confidence_images": self.low_confidence_images,
            "model_path": self.model_path or "",
            "smart_counter_paths": self.smart_counter_paths,
            "smart_counter_data": {
                k: [list(box) for box in v]
                for k, v in self.smart_counter_data.items()
            },
        }
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)

    def load_project(self, filepath: str):
        """Restore session from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        self.image_files = data.get("image_files", [])
        self.results = data.get("results", [])
        self.low_confidence_images = data.get("low_confidence_images", [])
        self.model_path = data.get("model_path") or None
        self.smart_counter_paths = data.get("smart_counter_paths", [])

        raw_sc = data.get("smart_counter_data", {})
        self.smart_counter_data = {
            k: [tuple(box) for box in v] for k, v in raw_sc.items()
        }

        self.state_changed.emit("project_loaded")


# -- helpers ------------------------------------------------------------------

def _sanitise_results(results: list[dict]) -> list[dict]:
    """Make results JSON-serialisable (convert numpy types, etc.)."""
    cleaned = []
    for r in results:
        row = {}
        for k, v in r.items():
            if k == "stomata_info":
                # Convert stomata_info dicts; tuples become lists
                row[k] = [
                    {
                        sk: list(sv) if isinstance(sv, tuple) else sv
                        for sk, sv in s.items()
                    }
                    for s in (v or [])
                ]
            else:
                try:
                    json.dumps(v)
                    row[k] = v
                except (TypeError, ValueError):
                    row[k] = str(v)
        cleaned.append(row)
    return cleaned
