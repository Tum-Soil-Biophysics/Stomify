"""
StomataDetectorML -- YOLO-based stomata detection.

Simplified detector using only YOLOv8 (no Faster R-CNN, no tiling).
Ported from FINAL_stomata_analyzer_ml_V3.py.

Now supports optional edge filtering via SettingsModel.
"""

import os

import cv2
import numpy as np


class StomataDetectorML:
    """YOLOv8-based stomata detector."""

    def __init__(self, model_path=None):
        self.model = None
        self.model_path = None
        self.confidence_threshold = 0.25
        self.iou_threshold = 0.45
        self.class_names = {0: "stomata", 1: "artifact"}
        self.stomata_idx = 0
        self.artifact_idx = 1

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    # -- Model loading --------------------------------------------------------

    def load_model(self, model_path: str):
        """Load a YOLOv8 model from a .pt file."""
        from ultralytics import YOLO

        try:
            self.model = YOLO(model_path)
            self.model_path = model_path

            # Auto-detect class indices from model
            if hasattr(self.model, "names") and self.model.names:
                self.class_names = self.model.names
                for idx, name in self.class_names.items():
                    name_lower = str(name).lower()
                    if "stomata" in name_lower:
                        self.stomata_idx = idx
                    elif "artifact" in name_lower:
                        self.artifact_idx = idx

            return True, "Model loaded successfully"
        except Exception as e:
            return False, str(e)

    # -- Detection ------------------------------------------------------------

    def detect(self, image_path, min_box_size=15, show_confidence=True,
               settings=None):
        """
        Detect stomata in an image using YOLOv8.

        Parameters
        ----------
        image_path : str
            Path to the image file.
        min_box_size : int
            Minimum width/height for a detection to be kept.
        show_confidence : bool
            Whether to draw confidence labels on the annotated image.
        settings : SettingsModel or None
            If provided, edge filtering is applied based on settings.

        Returns
        -------
        tuple : (stomata_count, annotated_image, details_dict)
        """
        if self.model is None:
            return None, None, "Model not loaded"

        img = cv2.imread(str(image_path))
        if img is None:
            return None, None, "Could not read image"

        original = img.copy()
        img_h, img_w = img.shape[:2]

        # Run inference
        results = self.model.predict(
            source=img,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )

        detections = results[0].boxes

        # -- Collect stomata detections ----------------------------------------
        raw_stomata = []
        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            conf = float(box.conf[0].cpu().numpy())
            cls = int(box.cls[0].cpu().numpy())

            # Skip small detections
            if (x2 - x1) < min_box_size or (y2 - y1) < min_box_size:
                continue

            # ONLY process stomata
            if cls == self.stomata_idx:
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                area = (x2 - x1) * (y2 - y1)

                raw_stomata.append({
                    "center": (center_x, center_y),
                    "bbox": (x1, y1, x2, y2),
                    "confidence": conf,
                    "area": area,
                })

        # -- Apply edge filtering (if settings provided and enabled) -----------
        if settings is not None:
            try:
                from models.edge_filter import EdgeFilter
                filtered = EdgeFilter.apply(raw_stomata, img_w, img_h, settings)
            except Exception:
                filtered = raw_stomata
        else:
            filtered = raw_stomata

        # -- Build output ------------------------------------------------------
        annotated = original.copy()
        stomata_info = []

        # Get bbox color from settings
        bbox_color_bgr = (0, 255, 0)
        marker_radius = 5
        font_scale = 0.7
        font_thickness = 2
        
        if settings is not None:
            try:
                hex_col = settings.bbox_color
                r = int(hex_col[1:3], 16)
                g = int(hex_col[3:5], 16)
                b = int(hex_col[5:7], 16)
                bbox_color_bgr = (b, g, r)

                # Fetch sizes
                marker_radius = getattr(settings, 'marker_radius', 12)
                # Map pt font size (e.g. 10 to 30) to OpenCV font scale (e.g. 0.5 to 1.5)
                font_pt = getattr(settings, 'font_size', 10)
                font_scale = font_pt / 14.0
                font_thickness = max(1, int(font_pt / 7.0))
            except Exception:
                pass

        for i, det in enumerate(filtered, start=1):
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]

            info = {
                "id": i,
                "center": det["center"],
                "bbox": det["bbox"],
                "confidence": conf,
                "area": det["area"],
            }
            stomata_info.append(info)

            # Draw detection
            self._draw_detection(
                annotated, x1, y1, x2, y2, conf,
                i, show_confidence, bbox_color_bgr,
                font_scale, marker_radius, font_thickness
            )

        stomata_count = len(stomata_info)

        # Draw count overlay
        self._draw_count_overlay(annotated, stomata_count, bbox_color_bgr, font_scale, font_thickness)

        avg_conf = (
            np.mean([s["confidence"] for s in stomata_info])
            if stomata_info
            else 0
        )

        return stomata_count, annotated, {
            "stomata": stomata_info,
            "avg_confidence": avg_conf,
        }

    # -- Drawing helpers ------------------------------------------------------

    @staticmethod
    def _draw_detection(img, x1, y1, x2, y2, conf, label_id, show_conf,
                        color=(0, 255, 0), font_scale=0.7, marker_radius=5, thickness=2):
        """Draw a bounding box with numbered label."""
        # Bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, max(2, thickness))

        # Center dot
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.circle(img, (cx, cy), marker_radius, color, -1)

        # Label
        if show_conf:
            label = f"{label_id} ({conf:.0%})"
        else:
            label = f"{label_id}"

        (tw, th), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        cv2.rectangle(img, (x1, y1 - th - 10), (x1 + tw + 10, y1), color, -1)
        cv2.putText(
            img, label, (x1 + 5, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness,
        )

    @staticmethod
    def _draw_count_overlay(img, count, color=(0, 255, 0), font_scale=0.7, thickness=2):
        """Draw stomata count overlay on the top-left corner dynamically sized."""
        label = f"Stomata: {count}"
        title_scale = max(0.9, font_scale * 1.5)
        title_thick = max(2, thickness + 1)
        
        (tw, th), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, title_scale, title_thick
        )
        
        box_w = tw + 30
        box_h = th + 30
        
        cv2.rectangle(img, (10, 10), (10 + box_w, 10 + box_h), (0, 0, 0), -1)
        cv2.rectangle(img, (10, 10), (10 + box_w, 10 + box_h), color, max(2, thickness))
        cv2.putText(
            img, label, (25, 10 + th + 15),
            cv2.FONT_HERSHEY_SIMPLEX, title_scale, color, title_thick,
        )
