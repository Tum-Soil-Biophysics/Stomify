"""
SmartCounterTab — AI-assisted stomata counting with manual correction.

Layout: Left sidebar (list + export) | Centre canvas | Right sidebar (actions).
"""

import math
import os

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QFileDialog, QFrame, QGroupBox, QSizePolicy,
    QListWidget, QListWidgetItem, QAbstractItemView, QCheckBox,
    QSlider, QSpinBox, QMenu, QInputDialog, QApplication,
    QGraphicsSimpleTextItem,
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPixmap, QPen, QBrush, QColor, QWheelEvent, QMouseEvent, QKeyEvent, QFont,
)

from core.config import COLORS, IMAGE_EXTENSIONS


# ── Constants ────────────────────────────────────────────────────────────────
BOX_SIZE = 30           # default half-size when adding manually
SNAP_RADIUS = 30        # right-click snap distance
DEDUP_RADIUS = 18       # AI import dedup radius
BOX_LINE_WIDTH = 3      # bounding box outline thickness


# ═════════════════════════════════════════════════════════════════════════════
#  CountingGraphicsView
# ═════════════════════════════════════════════════════════════════════════════
class CountingGraphicsView(QGraphicsView):
    box_add_requested = Signal(float, float)
    box_remove_requested = Signal(float, float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = QPointF()
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor("#1E1E1E"))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
            self._zoom *= factor
        else:
            self.scale(1 / factor, 1 / factor)
            self._zoom /= factor

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.position().toPoint())
            self.box_add_requested.emit(sp.x(), sp.y())
            return
        if event.button() == Qt.MouseButton.RightButton:
            sp = self.mapToScene(event.position().toPoint())
            self.box_remove_requested.emit(sp.x(), sp.y())
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y()))
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.CrossCursor)
            return
        super().mouseReleaseEvent(event)

    def fit_image(self, pixmap_item):
        if pixmap_item:
            self.fitInView(pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom = self.transform().m11()


# ═════════════════════════════════════════════════════════════════════════════
#  SmartCounterTab
# ═════════════════════════════════════════════════════════════════════════════
class SmartCounterTab(QWidget):
    """AI-assisted stomata counter with manual correction."""

    count_changed = Signal(int)
    request_ai_count = Signal(str)
    request_batch_ai = Signal(list)  # List of paths
    request_export = Signal()

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._image_boxes: dict[str, list[tuple]] = {}  # (x1,y1,x2,y2, is_manual)
        self._image_paths: list[str] = []
        self._current_index: int = -1
        self._box_items: list[QGraphicsRectItem | QGraphicsEllipseItem] = []
        self._pixmap_item = None
        # Undo / Redo stacks — each entry is ('add'|'remove', box_data_tuple)
        self._undo_stack: list[tuple] = []
        self._redo_stack: list[tuple] = []
        self._build_ui()
        self._connect_signals()

    # ── UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ═══════════════════════════════════════════════════════════════════
        #  LEFT PANEL — Images list + navigation + export
        # ═══════════════════════════════════════════════════════════════════
        left = QFrame()
        left.setFixedWidth(240)
        left.setObjectName("sidebarFrame")
        lp = QVBoxLayout(left)
        lp.setContentsMargins(10, 10, 10, 10)
        lp.setSpacing(8)

        # Title
        lt = QLabel("📁 Images")
        lt.setObjectName("sidebarTitle")
        lp.addWidget(lt)

        # Add Images button
        self.open_images_btn = QPushButton("📂  Add Images")
        self.open_images_btn.setMinimumHeight(36)
        self.open_images_btn.setObjectName("primaryBtn")
        self.open_images_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lp.addWidget(self.open_images_btn)

        # Nav buttons
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setMinimumHeight(30)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setObjectName("secondaryBtn")
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setMinimumHeight(30)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setObjectName("secondaryBtn")
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.next_btn)
        lp.addLayout(nav)

        # Image list
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.image_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self._show_context_menu)
        lp.addWidget(self.image_list, stretch=1)

        # Remove Selected / Clear All row
        list_mgmt = QHBoxLayout()
        list_mgmt.setSpacing(4)

        self.remove_sel_btn = QPushButton("✕ Remove")
        self.remove_sel_btn.setMinimumHeight(28)
        self.remove_sel_btn.setObjectName("dangerBtn")
        self.remove_sel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_sel_btn.setToolTip("Remove selected image from list")
        list_mgmt.addWidget(self.remove_sel_btn)

        self.clear_list_btn = QPushButton("🗑 Clear All")
        self.clear_list_btn.setMinimumHeight(28)
        self.clear_list_btn.setObjectName("dangerBtn")
        self.clear_list_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_list_btn.setToolTip("Remove all images from list")
        list_mgmt.addWidget(self.clear_list_btn)

        lp.addLayout(list_mgmt)

        # Export button
        self.export_btn = QPushButton("📊  Export Report")
        self.export_btn.setMinimumHeight(38)
        self.export_btn.setObjectName("successBtn")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lp.addWidget(self.export_btn)

        # Keyboard hint
        hint = QLabel("← → or A D = navigate")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 10px; border: none;")
        lp.addWidget(hint)

        root.addWidget(left)

        # ═══════════════════════════════════════════════════════════════════
        #  CENTRE — Canvas
        # ═══════════════════════════════════════════════════════════════════
        self._scene = QGraphicsScene(self)
        self._view = CountingGraphicsView(self._scene, self)
        self._view.setSizePolicy(QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Expanding)
        root.addWidget(self._view, stretch=1)

        # ═══════════════════════════════════════════════════════════════════
        #  RIGHT PANEL — Counter + AI actions
        # ═══════════════════════════════════════════════════════════════════
        right = QFrame()
        right.setFixedWidth(220)
        right.setObjectName("sidebarFrame")
        rp = QVBoxLayout(right)
        rp.setContentsMargins(10, 10, 10, 10)
        rp.setSpacing(10)

        # Title
        rt = QLabel("🧠 Smart Counter")
        rt.setObjectName("sidebarTitle")
        rp.addWidget(rt)

        # Counter badge
        counter = QFrame()
        counter.setStyleSheet(
            f"QFrame {{ background: {COLORS['primary']}; border-radius: 10px; }}")
        cf = QVBoxLayout(counter)
        cf.setContentsMargins(8, 12, 8, 12)
        self.count_label = QLabel("0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet(
            "font-size: 48px; font-weight: bold; color: white; border: none;")
        cf.addWidget(self.count_label)
        self.count_desc = QLabel("stomata detected")
        self.count_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_desc.setStyleSheet(
            "color: #BBDEFB; font-size: 12px; border: none;")
        cf.addWidget(self.count_desc)
        rp.addWidget(counter)

        # Confidence Threshold
        conf_group = QGroupBox("Confidence Threshold")
        conf_group.setStyleSheet(
            f"QGroupBox {{ font-weight: bold; color: {COLORS['text']}; "
            f"border: 1px solid {COLORS['divider']}; border-radius: 6px; margin-top: 6px; }}"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        cg = QVBoxLayout(conf_group)
        cg.setContentsMargins(10, 15, 10, 10)

        c_row = QHBoxLayout()
        self.conf_val_label = QLabel("25%")
        self.conf_val_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(1, 99)
        self.conf_slider.setValue(25)
        self.conf_slider.valueChanged.connect(
            lambda v: self.conf_val_label.setText(f"{v}%"))
        
        c_row.addWidget(self.conf_slider)
        c_row.addWidget(self.conf_val_label)
        cg.addLayout(c_row)
        rp.addWidget(conf_group)

        # AI Count button
        self.ai_count_btn = QPushButton("🤖  AI Count")
        self.ai_count_btn.setMinimumHeight(40)
        self.ai_count_btn.setObjectName("successBtn")
        self.ai_count_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_count_btn.setEnabled(False)
        rp.addWidget(self.ai_count_btn)

        # Auto Count All button
        self.auto_all_btn = QPushButton("⚡  Auto Count All")
        self.auto_all_btn.setMinimumHeight(40)
        self.auto_all_btn.setObjectName("primaryBtn")
        self.auto_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_all_btn.setToolTip("Run AI detection on ALL images in the list")
        self.auto_all_btn.setEnabled(False)
        rp.addWidget(self.auto_all_btn)

        # Clear button
        self.clear_btn = QPushButton("🗑️  Clear Boxes")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rp.addWidget(self.clear_btn)

        # Undo / Redo row
        undo_redo_row = QHBoxLayout()
        undo_redo_row.setSpacing(6)

        self.undo_btn = QPushButton("↩  Undo")
        self.undo_btn.setMinimumHeight(34)
        self.undo_btn.setObjectName("secondaryBtn")
        self.undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_btn.setToolTip("Undo last action (Ctrl+Z)")
        undo_redo_row.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("↪  Redo")
        self.redo_btn.setMinimumHeight(34)
        self.redo_btn.setObjectName("secondaryBtn")
        self.redo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.redo_btn.setToolTip("Redo last undone action (Ctrl+Y)")
        undo_redo_row.addWidget(self.redo_btn)

        rp.addLayout(undo_redo_row)

        rp.addStretch()

        # Instructions
        info = QLabel(
            "<b>Left click</b> — add count<br>"
            "<b>Right click</b> — remove count<br>"
            "<b>Ctrl+Z</b> — undo<br>"
            "<b>Ctrl+Y</b> — redo<br>"
            "<b>Scroll</b> — zoom<br>"
            "<b>Middle drag</b> — pan")
        info.setWordWrap(True)
        info.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; "
            "border: none; line-height: 1.6;")
        rp.addWidget(info)

        root.addWidget(right)

    # ── Wiring ───────────────────────────────────────────────────────────
    def _connect_signals(self):
        self._view.box_add_requested.connect(self._on_add)
        self._view.box_remove_requested.connect(self._on_remove)
        self.open_images_btn.clicked.connect(self._open_images)
        self.ai_count_btn.clicked.connect(self._request_ai)
        self.auto_all_btn.clicked.connect(self._request_batch_ai)
        self.clear_btn.clicked.connect(self.clear_boxes)
        self.undo_btn.clicked.connect(self._undo)
        self.redo_btn.clicked.connect(self._redo)
        self.remove_sel_btn.clicked.connect(self._remove_selected_image)
        self.clear_list_btn.clicked.connect(self._clear_all_images)
        self.export_btn.clicked.connect(lambda: self.request_export.emit())
        self.prev_btn.clicked.connect(self._go_prev)
        self.next_btn.clicked.connect(self._go_next)
        self.image_list.currentRowChanged.connect(self._on_list_select)

    # ══════════════════════════════════════════════════════════════════════
    #  PUBLIC API
    # ══════════════════════════════════════════════════════════════════════

    def import_ai_boxes(self, box_data: list):
        """
        Import AI bounding boxes.
        box_data: List of (bbox, confidence) tuples OR just bboxes.
        """
        if self._current_index < 0:
            return
            
        threshold = self.conf_slider.value() / 100.0
        current_count = len(self._box_items)
        
        for item in box_data:
            conf = 0.0
            # Handle both formats: [x1,y1,x2,y2] OR ([x1,y1,x2,y2], conf)
            if isinstance(item, (tuple, list)) and len(item) == 2 and isinstance(item[1], float):
                box, conf = item
                if conf < threshold:
                    continue
            else:
                box = item

            x1, y1, x2, y2 = [int(v) for v in box[:4]]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if self._has_nearby_box(cx, cy, DEDUP_RADIUS):
                continue
            
            current_count += 1
            self._draw_box(x1, y1, x2, y2, is_manual=False, conf=conf, count_id=current_count)
        self._save_current()
        self._update_count()
        self._refresh_label(self._current_index)

    def remove_ai_boxes(self, path=None):
        """Remove all non-manual (AI) boxes from the specified image."""
        target_path = path or self.current_image_path()
        if not target_path:
            return

        # 1. Update data structure
        if target_path in self._image_boxes:
            # Keep only manual boxes (index 4 is is_manual)
            # Tuple structure might be (x1, y1, x2, y2, is_manual, conf)
            new_list = []
            for box in self._image_boxes[target_path]:
                # Handle flexible length just in case
                if len(box) > 4 and box[4]: # is_manual is True
                    new_list.append(box)
            self._image_boxes[target_path] = new_list

        # 2. Update scene if currently viewing
        if self._current_index >= 0 and self._image_paths[self._current_index] == target_path:
            items_to_remove = []
            for item in self._box_items:
                is_manual = item.data(0)
                if not is_manual:
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                self._scene.removeItem(item)
                self._box_items.remove(item)
            
            # Re-index remaining boxes?
            # We will rely on reload or just leave as is until next load
            self._save_current() # Ensure current state matches
            self._update_count()

        self._refresh_label(self._image_paths.index(target_path) if target_path in self._image_paths else -1)

    def clear_boxes(self):
        for item in self._box_items:
            self._scene.removeItem(item)
        self._box_items.clear()
        self._save_current()
        self._update_count()
        self._refresh_label(self._current_index)

    def current_image_path(self):
        if 0 <= self._current_index < len(self._image_paths):
            return self._image_paths[self._current_index]
        return None

    def get_all_counts(self) -> dict:
        return {p: len(self._image_boxes.get(p, [])) for p in self._image_paths}

    def add_boxes_to_path(self, path: str, box_data: list):
        """
        Add boxes to a specific image path without loading it.
        box_data: List of (bbox, confidence) tuples OR just bboxes.
        """
        if path not in self._image_paths:
            return
            
        current_boxes = self._image_boxes.get(path, [])
        threshold = self.conf_slider.value() / 100.0
        
        # Convert existing boxes to centers for dedup
        existing_centers = []
        for b in current_boxes:
            # b is tuple (x1, y1, x2, y2, is_manual) or (x1, y1, x2, y2)
            # handle potential length differences if data format changed
            x1, y1, x2, y2 = b[:4]
            existing_centers.append(((x1+x2)/2, (y1+y2)/2))
        
        for item in box_data:
            conf = 0.0
            if isinstance(item, (tuple, list)) and len(item) == 2 and isinstance(item[1], float):
                box, conf = item
                if conf < threshold:
                    continue
            else:
                box = item
            
            x1, y1, x2, y2 = [int(v) for v in box[:4]]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            
            # Simple dedup against existing boxes
            duplicate = False
            for ecx, ecy in existing_centers:
                if math.hypot(ecx - cx, ecy - cy) < DEDUP_RADIUS:
                    duplicate = True
                    break
            
            if not duplicate:
                # Add as AI box (is_manual=False)
                # Appending directly to data structure
                # STRUCTURE: x1, y1, x2, y2, is_manual, conf
                current_boxes.append((x1, y1, x2, y2, False, conf))
                existing_centers.append((cx, cy))
        
        self._image_boxes[path] = current_boxes
        
        # Update list item if possible
        try:
            idx = self._image_paths.index(path)
            self._refresh_label(idx)
        except ValueError:
            pass

    def reload_current(self):
        """Reload the currently displayed image to reflect data changes."""
        if self._current_index >= 0:
            self._load_image(self._current_index)

    def is_auto_count_on(self) -> bool:
        return False  # Deprecated

    # ══════════════════════════════════════════════════════════════════════
    #  SLOTS
    # ══════════════════════════════════════════════════════════════════════

    def _open_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.jpg *.jpeg *.png *.tif *.tiff *.bmp);;All Files (*)")
        if not paths:
            return
        added = False
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                continue
            if p in self._image_boxes:
                continue
            self._image_paths.append(p)
            self._image_boxes[p] = []
            self.image_list.addItem(
                QListWidgetItem(f"{os.path.basename(p)}  [0]"))
            added = True
        if added:
            if self._current_index < 0:
                self.image_list.setCurrentRow(0)
            # Enable buttons if we have images
            if self._image_paths:
                self.ai_count_btn.setEnabled(True)
                self.auto_all_btn.setEnabled(True)

    def _show_context_menu(self, pos):
        item = self.image_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        copy_action = menu.addAction("📄 Copy Filename")
        rename_action = menu.addAction("✏️ Rename File")
        
        action = menu.exec(self.image_list.mapToGlobal(pos))
        
        if action == copy_action:
            self._copy_filename(item)
        elif action == rename_action:
            self._rename_file(item)

    def _copy_filename(self, item):
        row = self.image_list.row(item)
        if row < 0 or row >= len(self._image_paths):
            return
        path = self._image_paths[row]
        filename = os.path.basename(path)
        QApplication.clipboard().setText(filename)

    def _rename_file(self, item):
        row = self.image_list.row(item)
        if row < 0 or row >= len(self._image_paths):
            return
        old_path = self._image_paths[row]
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(
            self, "Rename File", "New filename:", text=old_name)
            
        if ok and new_name and new_name != old_name:
            # Construct new path
            folder = os.path.dirname(old_path)
            new_path = os.path.join(folder, new_name)
            
            # Basic validation
            if os.path.exists(new_path):
                # Simple error handling via print/status (or MessageBox if we imported it)
                print(f"Error: File already exists: {new_path}")
                return
                
            try:
                os.rename(old_path, new_path)
                
                # Update data structures
                self._image_paths[row] = new_path
                # Move boxes data
                if old_path in self._image_boxes:
                    self._image_boxes[new_path] = self._image_boxes.pop(old_path)
                
                # Update list item text (keep count)
                count = len(self._image_boxes.get(new_path, []))
                item.setText(f"{new_name}  [{count}]")
                
            except Exception as e:
                print(f"Error renaming file: {e}")

    def _on_list_select(self, row: int):
        if row < 0 or row >= len(self._image_paths):
            return
        if self._current_index >= 0:
            self._save_current()
        self._current_index = row
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._load_image(row)

    def _remove_selected_image(self):
        """Remove the currently selected image from the list."""
        row = self.image_list.currentRow()
        if row < 0 or row >= len(self._image_paths):
            return
        path = self._image_paths[row]
        # Remove from data
        self._image_paths.pop(row)
        self._image_boxes.pop(path, None)
        self.image_list.takeItem(row)
        self._undo_stack.clear()
        self._redo_stack.clear()

        # Adjust selection
        if len(self._image_paths) == 0:
            self._current_index = -1
            self._scene.clear()
            self._pixmap_item = None
            self._box_items.clear()
            self._update_count()
        else:
            new_row = min(row, len(self._image_paths) - 1)
            self._current_index = -1  # Reset so _on_list_select triggers load
            self.image_list.setCurrentRow(new_row)

    def _clear_all_images(self):
        """Remove all images from the list."""
        if not self._image_paths:
            return
        self._image_paths.clear()
        self._image_boxes.clear()
        self.image_list.clear()
        self._current_index = -1
        self._scene.clear()
        self._pixmap_item = None
        self._box_items.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_count()

    def _on_add(self, x: float, y: float):
        if self._pixmap_item is None:
            return
        
        hs = getattr(self.settings, 'marker_radius', 12) if self.settings else 12
        # Manual boxes get confidence 1.0 (or -1 to indicate manual)
        box_data = (int(x - hs), int(y - hs), int(x + hs), int(y + hs), True, 1.0)
        
        # We need to determine the count ID. It's roughly len + 1
        current_count = len(self._box_items) + 1
        
        self._draw_box(*box_data, count_id=current_count)
        self._undo_stack.append(('add', box_data))
        self._redo_stack.clear()  # New action invalidates redo history
        self._save_current()
        self._update_count()
        self._refresh_label(self._current_index)

    def _on_remove(self, x: float, y: float):
        if not self._box_items:
            return
        nearest, best = None, float('inf')
        for item in self._box_items:
            r = item.rect()
            d = math.hypot(r.center().x() - x, r.center().y() - y)
            if d < best:
                best, nearest = d, item
        zoom = max(self._view._zoom, 0.01)
        if nearest and best < SNAP_RADIUS / zoom:
            # Save removed box data for undo
            r = nearest.rect()
            is_manual = nearest.data(0) if nearest.data(0) is not None else False
            conf = nearest.data(1) if nearest.data(1) is not None else 0.0
            
            removed_data = (int(r.x()), int(r.y()),
                            int(r.x() + r.width()), int(r.y() + r.height()),
                            is_manual, conf)
            self._scene.removeItem(nearest)
            self._box_items.remove(nearest)
            self._undo_stack.append(('remove', removed_data))
            self._redo_stack.clear()
            self._save_current()
            
            # Refresh all labels to keep numbering contiguous? 
            # User might prefer simple refresh
            self._reload_scene_from_data() 
            
            self._update_count()
            self._refresh_label(self._current_index)

    def _undo(self):
        """Undo last add or remove action."""
        if not self._undo_stack:
            return
        action, box_data = self._undo_stack.pop()
        if action == 'add':
            # Undo an add = remove the last added item
            if self._box_items:
                last = self._box_items[-1]
                self._scene.removeItem(last)
                self._box_items.pop()
            self._redo_stack.append(('add', box_data))
        elif action == 'remove':
            # Undo a remove = re-draw the removed box
            # box_data probably has 6 elements now
            self._draw_box(*box_data, count_id=len(self._box_items)+1)
            self._redo_stack.append(('remove', box_data))
        self._save_current()
        self._update_count()
        self._refresh_label(self._current_index)

    def _redo(self):
        """Redo last undone action."""
        if not self._redo_stack:
            return
        action, box_data = self._redo_stack.pop()
        if action == 'add':
            # Redo an add = re-draw the box
            self._draw_box(*box_data, count_id=len(self._box_items)+1)
            self._undo_stack.append(('add', box_data))
        elif action == 'remove':
            # Redo a remove = remove the last item again
            if self._box_items:
                last = self._box_items[-1]
                self._scene.removeItem(last)
                self._box_items.pop()
            self._undo_stack.append(('remove', box_data))
        self._save_current()
        self._update_count()
        self._refresh_label(self._current_index)

    def _request_ai(self):
        path = self.current_image_path()
        if path:
            self.request_ai_count.emit(path)

    def _request_batch_ai(self):
        if self._image_paths:
            self.request_batch_ai.emit(self._image_paths)

    def _go_prev(self):
        if self._current_index > 0:
            self.image_list.setCurrentRow(self._current_index - 1)

    def _go_next(self):
        if self._current_index < len(self._image_paths) - 1:
            self.image_list.setCurrentRow(self._current_index + 1)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        
        # Ctrl+Z = Undo
        if key == Qt.Key.Key_Z and modifiers & Qt.KeyboardModifier.ControlModifier:
            self._undo()
            return
        # Ctrl+Y = Redo
        if key == Qt.Key.Key_Y and modifiers & Qt.KeyboardModifier.ControlModifier:
            self._redo()
            return
        
        if key in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self._go_prev()
            return
        if key in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self._go_next()
            return
        super().keyPressEvent(event)

    # ══════════════════════════════════════════════════════════════════════
    #  INTERNAL
    # ══════════════════════════════════════════════════════════════════════

    def _load_image(self, index: int):
        path = self._image_paths[index]
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        self._box_items.clear()
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
        self._view.fit_image(self._pixmap_item)
        
        boxes = self._image_boxes.get(path, [])
        for i, box in enumerate(boxes):
            # unpack safely to handle legacy data (4 or 5 elements vs 6)
            # Standard: x1, y1, x2, y2, is_manual, conf
            # Legacy: x1, y1, x2, y2, [is_manual]
            
            x1, y1, x2, y2 = box[:4]
            is_manual = box[4] if len(box) > 4 else False
            conf = box[5] if len(box) > 5 else 0.0
            
            self._draw_box(x1, y1, x2, y2, is_manual, conf, count_id=i+1)
        self._update_count()
        self.ai_count_btn.setEnabled(True)
        self.auto_all_btn.setEnabled(True)

    def _draw_box(self, x1: int, y1: int, x2: int, y2: int, is_manual: bool, 
                  conf: float = 0.0, count_id: int = 0):
        rect = QRectF(x1, y1, x2 - x1, y2 - y1)
        
        if is_manual:
            # Manual count: Draw big bright yellow dot
            pen = QPen(QColor("#000000"), 2)              # Black outline for contrast
            brush = QBrush(QColor(255, 235, 59, 230))     # Bright yellow, mostly opaque
            item = self._scene.addEllipse(rect, pen, brush)
            label_text = f"#{count_id} (Man)"
        else:
            # AI count: Draw Bounding Box
            color_hex = getattr(self.settings, 'bbox_color', "#00E676") if self.settings else "#00E676"
            pen = QPen(QColor(color_hex), BOX_LINE_WIDTH)
            brush_col = QColor(color_hex)
            brush_col.setAlpha(35)
            brush = QBrush(brush_col)
            item = self._scene.addRect(rect, pen, brush)
            label_text = f"#{count_id} {conf:.2f}"

        item.setZValue(100)
        # Store manual flag and confidence
        item.setData(0, is_manual)
        item.setData(1, conf)
        
        # Add label
        if count_id > 0:
            text_item = QGraphicsSimpleTextItem(label_text, parent=item)
            text_color_hex = getattr(self.settings, 'box_text_color', "#FFFFFF") if self.settings else "#FFFFFF"
            text_item.setBrush(QBrush(QColor(text_color_hex)))
            f_size = getattr(self.settings, 'font_size', 10) if self.settings else 10
            f = QFont("Arial", f_size)
            f.setBold(True)
            text_item.setFont(f)
            # Position text at top-left of rect, slightly shifted up
            # Or inside top-left
            text_item.setPos(rect.x(), rect.y() - 12) 
            
            # Add a background rect for readability? 
            # For simplicity, high contrast text is usually okay, but background is better.
            # But QGraphicSimpleTextItem doesn't support background.
            # We could rely on shadow or outline?
            # Let's keep it simple for now, user asked "like preview".
            # Preview uses cv2.putText white.
            
            text_item.setFlag(QGraphicsSimpleTextItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
            # The above flag keeps text size constant regardless of zoom. 
            # But position needs to be correct.
            # Actually, standard usage in preview usually scales with image. 
            # Let's try constant size for readability.

        self._box_items.append(item)

    def _reload_scene_from_data(self):
        """Re-draws all boxes from self._image_boxes for current path."""
        # This acts like a partial _load_image without reloading the pixmap
        path = self.current_image_path()
        if not path: 
            return
            
        # First save current state into data? 
        # No, this method assumes _image_boxes is source of truth and we want scene to match.
        # usually called after removing an item from data.
        
        # Clear current items
        for item in self._box_items:
            self._scene.removeItem(item)
        self._box_items.clear()
        
        # Redraw
        boxes = self._image_boxes.get(path, [])
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box[:4]
            is_manual = box[4] if len(box) > 4 else False
            conf = box[5] if len(box) > 5 else 0.0
            self._draw_box(x1, y1, x2, y2, is_manual, conf, count_id=i+1)

    def _save_current(self):
        if self._current_index < 0:
            return
        path = self._image_paths[self._current_index]
        boxes = []
        for item in self._box_items:
            # Retrieve shape from item
            if isinstance(item, QGraphicsRectItem):
                r = item.rect()
                # Rely on data now
            else:
                r = item.rect()

            is_manual = item.data(0) if item.data(0) is not None else False
            conf = item.data(1) if item.data(1) is not None else 0.0

            boxes.append((int(r.x()), int(r.y()),
                          int(r.x() + r.width()), int(r.y() + r.height()),
                          is_manual, conf))
        self._image_boxes[path] = boxes

    def _has_nearby_box(self, x: float, y: float, radius: float) -> bool:
        for item in self._box_items:
            r = item.rect()
            if math.hypot(r.center().x() - x, r.center().y() - y) < radius:
                return True
        return False

    def _update_count(self):
        n = len(self._box_items)
        self.count_label.setText(str(n))
        self.count_changed.emit(n)

    def _refresh_label(self, index: int):
        if index < 0 or index >= len(self._image_paths):
            return
        path = self._image_paths[index]
        count = len(self._image_boxes.get(path, []))
        item = self.image_list.item(index)
        if item:
            item.setText(f"{os.path.basename(path)}  [{count}]")



