"""
EdgeFilter -- Post-processing filter to handle stomata at image edges.

Two algorithms are provided:

Method A  "Standard Top/Left Rule"
    Keep boxes touching the Top or Left margin.
    Delete boxes touching the Bottom or Right margin.

Method B  "Area Percentage Rule"
    An edge box is kept only if its area (w*h) is greater than X% of the
    median area of all *centre* (non-edge) boxes.

Both methods use a configurable margin (in pixels) to decide what
counts as "touching the edge".
"""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.settings_model import SettingsModel


def _is_near_edge(x1, y1, x2, y2, img_w, img_h, margin):
    """Return which edges this box touches (set of 'top','bottom','left','right')."""
    edges = set()
    if x1 <= margin:
        edges.add("left")
    if y1 <= margin:
        edges.add("top")
    if x2 >= img_w - margin:
        edges.add("right")
    if y2 >= img_h - margin:
        edges.add("bottom")
    return edges


class EdgeFilter:
    """Post-processing edge-stomata filter."""

    @staticmethod
    def filter_standard(detections: list[dict], img_w: int, img_h: int,
                        margin_px: int = 5) -> list[dict]:
        """Standard Top/Left Rule.

        Keep boxes touching Top or Left margin.
        Delete boxes touching Bottom or Right margin (unless they also
        touch Top or Left).
        """
        kept = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            edges = _is_near_edge(x1, y1, x2, y2, img_w, img_h, margin_px)

            if not edges:
                # Centre box, always keep
                kept.append(det)
            elif edges & {"top", "left"}:
                # Touches a "keep" edge
                kept.append(det)
            else:
                # Touches only bottom/right, discard
                pass
        return kept

    @staticmethod
    def filter_area_percentage(detections: list[dict], img_w: int, img_h: int,
                               margin_px: int = 5,
                               area_threshold_pct: int = 50) -> list[dict]:
        """Area Percentage Rule.

        1. Separate boxes into edge vs centre.
        2. Compute median area of centre boxes.
        3. Keep an edge box only if its area >= threshold% of that median.
        """
        centre = []
        edge_boxes = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            edges = _is_near_edge(x1, y1, x2, y2, img_w, img_h, margin_px)
            if edges:
                edge_boxes.append(det)
            else:
                centre.append(det)

        if not centre:
            # No centre boxes to compute median -- keep everything
            return detections

        centre_areas = [(d["bbox"][2] - d["bbox"][0]) * (d["bbox"][3] - d["bbox"][1])
                        for d in centre]
        median_area = statistics.median(centre_areas)

        if median_area <= 0:
            return detections

        threshold = median_area * (area_threshold_pct / 100.0)

        kept = list(centre)
        for det in edge_boxes:
            x1, y1, x2, y2 = det["bbox"]
            area = (x2 - x1) * (y2 - y1)
            if area >= threshold:
                kept.append(det)
        return kept

    @staticmethod
    def apply(detections: list[dict], img_w: int, img_h: int,
              settings: "SettingsModel") -> list[dict]:
        """Route to the correct filter based on current settings."""
        if not settings.edge_filter_enabled:
            return detections

        method = settings.edge_filter_method
        margin = settings.edge_margin_px

        if method == "area_percentage":
            return EdgeFilter.filter_area_percentage(
                detections, img_w, img_h,
                margin_px=margin,
                area_threshold_pct=settings.edge_area_threshold_pct,
            )
        else:
            return EdgeFilter.filter_standard(
                detections, img_w, img_h, margin_px=margin,
            )
