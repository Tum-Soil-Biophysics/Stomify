"""
ImageCanvas — Reusable QGraphicsView-based image display with zoom + pan.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor
import numpy as np
import cv2


class ImageCanvas(QGraphicsView):
    """Zoomable, pannable image viewer built on QGraphicsView."""

    left_clicked = Signal(float, float)   # image-space x, y
    right_clicked = Signal(float, float)
    mouse_moved = Signal(float, float)    # image-space x, y
    line_drawn = Signal(float, float, float, float)  # x0,y0,x1,y1 in image-space
    review_click = Signal(float, float, Qt.MouseButton)  # x, y, button (for ReviewDialog)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._zoom_factor = 1.0

        # Drawing state (for calibration line)
        self._drawing = False
        self._draw_start = None
        self._temp_line = None
        self.draw_mode = False  # set True to enable line drawing
        self._review_mode = False  # set True for review click handling
        self._is_manually_zoomed = False

        # Appearance
        self.setRenderHints(
            self.renderHints()
        )
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor("#E0E0E0"))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    # ── Public helpers ───────────────────────────────────────────────────

    def set_image_from_path(self, path: str):
        """Load an image file and display it."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        self._set_pixmap(pixmap)

    def set_image_from_cv(self, cv_image):
        """Display an OpenCV BGR image."""
        rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self._set_pixmap(pixmap)

    def clear_image(self):
        self._scene.clear()
        self._pixmap_item = None
        self._zoom_factor = 1.0
        self._is_manually_zoomed = False

    def fit_in_view(self):
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_factor = self.transform().m11()
            self._is_manually_zoomed = False

    def zoom(self, factor: float):
        if self._pixmap_item:
            self.scale(factor, factor)
            self._zoom_factor *= factor
            self._is_manually_zoomed = True

    def draw_circles(self, centers, radius=8, color=QColor(0, 255, 0), width=2):
        """Draw circles at given image-space (cx, cy) positions."""
        pen = QPen(color, width)
        for cx, cy in centers:
            self._scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2, pen
            )

    def remove_overlays(self):
        """Remove everything except the background pixmap."""
        for item in self._scene.items():
            if item is not self._pixmap_item:
                self._scene.removeItem(item)

    def enable_review_mode(self, enabled: bool):
        """Enable review mode: clicks emit review_click(x, y, button)."""
        self._review_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def draw_calibration_line(self, x0, y0, x1, y1):
        """Draw a persistent red line for calibration."""
        pen = QPen(QColor("#FF1744"), 3, Qt.PenStyle.SolidLine)
        return self._scene.addLine(x0, y0, x1, y1, pen)

    def remove_item(self, item):
        """Remove a specific item from the scene."""
        if item:
            self._scene.removeItem(item)

    # ── Private ──────────────────────────────────────────────────────────

    def _set_pixmap(self, pixmap: QPixmap):
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
        self.fit_in_view()

    # ── Events ───────────────────────────────────────────────────────────

    def wheelEvent(self, event):
        """Zoom in / out with scroll wheel."""
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.zoom(factor)
        else:
            self.zoom(1 / factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap_item and not getattr(self, '_is_manually_zoomed', False):
            self.fit_in_view()

    def mousePressEvent(self, event):
        if self.draw_mode and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._draw_start = scene_pos
            self._drawing = True
            return
        if self._review_mode:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.review_click.emit(scene_pos.x(), scene_pos.y(), event.button())
            return
        if event.button() == Qt.MouseButton.LeftButton and not self.draw_mode:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.left_clicked.emit(scene_pos.x(), scene_pos.y())
        elif event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.right_clicked.emit(scene_pos.x(), scene_pos.y())
        super().mousePressEvent(event)

    def set_draw_mode(self, enabled: bool):
        """Enable or disable line drawing mode."""
        self.draw_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _get_constrained_pos(self, event, start_pos):
        """Return scene position, constrained to axis if Shift is held."""
        current_pos = self.mapToScene(event.position().toPoint())
        
        # Check for Shift modifier
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier and start_pos:
            dx = abs(current_pos.x() - start_pos.x())
            dy = abs(current_pos.y() - start_pos.y())
            
            if dx > dy:
                # Snap to horizontal
                return QPointF(current_pos.x(), start_pos.y())
            else:
                # Snap to vertical
                return QPointF(start_pos.x(), current_pos.y())
                
        return current_pos

    def mouseMoveEvent(self, event):
        if self.draw_mode and self._drawing and self._draw_start is not None:
            scene_pos = self._get_constrained_pos(event, self._draw_start)
            
            if self._temp_line:
                self._scene.removeItem(self._temp_line)
                
            pen = QPen(QColor("#FF1744"), 3, Qt.PenStyle.DashLine)
            self._temp_line = self._scene.addLine(
                self._draw_start.x(), self._draw_start.y(),
                scene_pos.x(), scene_pos.y(), pen,
            )
            # Do NOT call super().mouseMoveEvent(event) here to avoid dragging effects
            # (though we disabled drag mode, it's safer)
            return
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.draw_mode and self._drawing and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self._get_constrained_pos(event, self._draw_start)
            
            self._drawing = False
            if self._temp_line:
                self._scene.removeItem(self._temp_line)
                self._temp_line = None
                
            if self._draw_start:
                # Emit the constrained coordinates
                self.line_drawn.emit(
                    self._draw_start.x(), self._draw_start.y(),
                    scene_pos.x(), scene_pos.y(),
                )
            
            self._draw_start = None
            return
            
        super().mouseReleaseEvent(event)
