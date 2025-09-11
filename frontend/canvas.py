from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsObject
from PyQt6.QtGui import QPainter, QColor, QWheelEvent, QPen
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtCore import pyqtSignal
from io_mapper import IOMapperDialog 
from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPointF
import sys
import re
import importlib.metadata as im

try:
    from packaging.requirements import Requirement as _PkgRequirement
    from packaging.utils import canonicalize_name as _canon_name
except Exception:
    _PkgRequirement = None

def _canon_name(s: str) -> str:
    """Fallback normalizer if packaging is missing."""
    return re.sub(r"[-_.]+", "-", s).lower()
from connection import Connection
from connection import ConnectionLine
import json

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy
from backend.saving import save_file
from backend.loading import load_file, load_block_from_template
from frontend.block import Block
from frontend.requirements_overview_dialog import RequirementsOverviewDialog


class Canvas(QGraphicsView):
    modified = pyqtSignal()
    graphChanged = pyqtSignal()
    def __init__(self, tab_widget, controller):
        super().__init__()
        self.filepath= None
        
        self.tab_widget = tab_widget
        self.controller = controller
        self.blocks = []
        self.connections = []  # 🔗 Keep track of all connections

        self.connection_start = None
        self.temp_line = None

        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.scene.canvas = self     
        self.setScene(self.scene)
        self.graphChanged.connect(self.rebuild_wiring)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setStyleSheet("border: 2px solid #dcdde1;")
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setStyleSheet("""
            QGraphicsView {
                selection-background-color: rgba(0, 120, 215, 50);  /* translucent blue */
            }
        """)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.ContainsItemShape)

        self.setInteractive(True)
        self._panning = False
        self._pan_start = QPointF()
        
        self.add_start_block()

        # --- Overlay UI (stays fixed relative to the view) ---
        self._overlay_margin = 12
        self._init_requirements_button()
        self._position_overlay_controls()  # place it once on init


    def _init_requirements_button(self):
        self._req_btn = QPushButton("Check Requirements", self)
        self._req_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._req_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # don't steal canvas focus
        self._req_btn.raise_()

        self._req_btn.clicked.connect(self.check_requirements)

        # Visuals: less rounded, subtle hover, slimmer padding
        self._req_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f6fa;
                color: #2f3640;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #eef1f7;
                border-color: #c8cbd2;
            }
            QPushButton:pressed {
                background-color: #e6e9f0;
            }
        """)

        # Very subtle shadow for separation
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)     # smaller blur
        shadow.setOffset(0, 2)      # gentle offset
        shadow.setColor(Qt.GlobalColor.black)
        self._req_btn.setGraphicsEffect(shadow)

    def _position_overlay_controls(self):
        """Position overlay widgets in the top-right corner of the view."""
        if not hasattr(self, "_req_btn"):
            return
        btn = self._req_btn
        btn.adjustSize()
        x = self.viewport().width() - btn.width() - self._overlay_margin
        y = self._overlay_margin
        # Place relative to the QGraphicsView, not the scene
        btn.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_overlay_controls()

    def check_requirements(self):
        """
        Collect requirements from all blocks and show an overview dialog.
        Each block may expose:
          - block.requirements: list[str] like ['numpy', 'pandas==2.2.2']
        """
        # Gather required specs across all blocks
        required: dict[str, set[str]] = {}
        for blk in getattr(self, "blocks", []):
            reqs = getattr(blk, "requirements", None) or []
            for raw in reqs:
                # Normalize and keep full spec for comparison text
                name_part = re.split(r"[<>=!~\s]", raw.strip(), maxsplit=1)[0]
                canon = _canon_name(name_part) if _canon_name else re.sub(r"[-_.]+", "-", name_part).lower()
                required.setdefault(canon, set()).add(raw.strip())

        dlg = RequirementsOverviewDialog(self, self.controller, required)
        dlg.exec()


    def rebuild_wiring(self):
        """
        Rebuild backend wiring from self.connections.
        Adjust this to your real data structures (inputs_proxy, outputs_proxy, etc.)
        """
        # 1) Clear runtime input mappings on all blocks
        for b in self.blocks:
            # proxies version (if you have them)
            if hasattr(b, "inputs_proxy") and hasattr(b.inputs_proxy, "reset"):
                b.inputs_proxy.reset()
            # dict version (common fallback)
            if hasattr(b, "inputs") and isinstance(b.inputs, dict):
                for k in list(b.inputs.keys()):
                    b.inputs[k] = []

            # clear caches/compiled plan placeholders
            if hasattr(b, "last_result"):
                b.last_result = None

        # 2) Re-apply wiring from active connections
        for conn in self.connections:
            src = conn.start_block
            dst = conn.end_block
            # If you have named ports, use conn.src_port/conn.dst_port here
            if hasattr(dst, "inputs_proxy") and hasattr(dst.inputs_proxy, "connect_from"):
                dst.inputs_proxy.connect_from(src)  # or (src, portA, portB)
            elif hasattr(dst, "inputs") and isinstance(dst.inputs, dict):
                # generic: store a single default input list
                dst.inputs.setdefault("default", []).append({"src_block": src})

        # 3) clear any compiled plan on canvas if you keep one
        if hasattr(self, "_compiled_plan"):
            self._compiled_plan = None


    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        print(f"Clicked item: {item}, type: {type(item)}")

        selected = self.scene.selectedItems()
        print(f"Selected items: {len(selected)}")

        def get_block_from_item(item):
            if isinstance(item, QGraphicsEllipseItem):
                block = item.data(0)
                if isinstance(block, Block):
                    return block
                else:
                    print("⚠️ Port has no valid block attached!")
                    return None
            elif isinstance(item, Block):
                return item
            return None



        if event.button() == Qt.MouseButton.LeftButton:
            
            if isinstance(item, QGraphicsEllipseItem):
                self.modified.emit()

                parent = get_block_from_item(item)
                tooltip = item.toolTip()
                print(tooltip)

                if tooltip == "Output":
                    print("✔️ Clicked OUTPUT port — starting connection")
                    self.connection_start = parent

                elif tooltip == "Input":
                    if self.connection_start:
                        print("✅ Completing connection via input port")
                        self.create_connection(self.connection_start, parent)
                        self._clear_temp_line()
                    else:
                        print("⚠️ Clicked input with no connection started")

            else:
                self.modified.emit()

                block = get_block_from_item(item)
                if block and self.connection_start and block != self.connection_start:
                    print("✅ Completing connection via block body — autosnap to input port")
                    self.create_connection(self.connection_start, block)
                    self._clear_temp_line()
                else:
                    print("🛑 Clicked outside valid block — cancelling")
                    self._clear_temp_line()

        elif event.button() == Qt.MouseButton.RightButton:
            print("hi")
            if isinstance(item, ConnectionLine):
                print("📌 Right-clicked connection line in canvas")
                item.contextMenuEvent(event)  # Manually invoke the context menu
                return
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
        elif self.connection_start:
            scene_pos = self.mapToScene(event.pos())
            start_pos = self.connection_start.output_anchor()

            if self.temp_line:
                self.scene.removeItem(self.temp_line)

            pen = QPen(QColor("gray"), 2)
            self.temp_line = self.scene.addLine(
                start_pos.x(), start_pos.y(), scene_pos.x(), scene_pos.y(), pen
            )
            self.temp_line.setZValue(-1)  # ✅ draw behind all blocks and ports

        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def add_block(self, name=""):
        self.modified.emit()

        
        if name == "": ##Idk remove this maybe
            name = "Block" + str(len(self.blocks) + 1)
        
        block = Block(name, self.tab_widget, self, background_color="#74b9ff", controller=self.controller)
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)

    def add_variable_block(self):
        self.modified.emit()

        name = f"Variable Block {len(self.blocks) + 1}"
        block = Block(name, self.tab_widget, self,  background_color="#ffeaa7", controller=self.controller)
        block.block_type = "variable"
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)

    def add_conditional_block(self):
        self.modified.emit()

        name = f"Conditonal Block {len(self.blocks) + 1}"
        block = Block(name, self.tab_widget, self, background_color="#fab1a0", controller=self.controller)
        block.block_type = "conditional"
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)

    def add_loop_block(self):
        self.modified.emit()

        name = f"Loop Block {len(self.blocks) + 1}"
        block = Block(name, self.tab_widget, self, background_color="#55efc4", controller=self.controller)
        block.block_type = "loop"
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)

    def add_start_block(self):
        self.modified.emit()

        name = f"Start Block"
        block = Block(name, self.tab_widget, self, controller=self.controller)
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)
        block.mark_as_start_block()

    def open_io_mapper(self, block):
        dialog = IOMapperDialog(block, self.tab_widget)
        dialog.exec()  

    def create_connection(self, start_block, end_block):
        self.modified.emit()
        for conn in self.connections:
            if conn.start_block == start_block and conn.end_block == end_block:
                print("🚫 Duplicate connection ignored")
                return

        print(f"📍 Drawing connection from {start_block.name} to {end_block.name}")
        connection = Connection(start_block, end_block, self)  # ✅ pass canvas
        self.connections.append(connection)
        self.sync_io_to_connections()
        self.open_io_mapper(end_block)



    def cancel_connection(self):
        self._clear_temp_line()

    def _clear_temp_line(self):
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        self.connection_start = None

    def save_layout(self, filename):
        save_file(self, filename)
        
    def load_layout(self, filename):
        load_file(self, filename, self.controller)
    
    def load_block_from_template_wrapper(self, template):
        block = load_block_from_template(self, template)
        self.scene.addItem(block)
        self.blocks.append(block)

    def remove_all_connections(self):
        # remove connection graphics + detach from blocks
        for conn in list(self.connections):
            # detach from block lists
            if conn in conn.start_block.outgoing_connections:
                conn.start_block.outgoing_connections.remove(conn)
            if conn in conn.end_block.incoming_connections:
                conn.end_block.incoming_connections.remove(conn)

            # remove graphics
            self.scene.removeItem(conn.line)
            self.scene.removeItem(conn.arrow)

        # clear the canvas registry
        self.connections.clear()

        # mark every block’s IO as "not connected"
        for b in self.blocks:
            # clear model-side lists/dicts if you use them
            if hasattr(b, "incoming_connections"):
                b.incoming_connections[:] = []
            if hasattr(b, "outgoing_connections"):
                b.outgoing_connections[:] = []

            if hasattr(b, "inputs") and isinstance(b.inputs, dict):
                for k in list(b.inputs.keys()):
                    b.inputs[k] = []   # or None, depending on your schema

            if hasattr(b, "outputs") and isinstance(b.outputs, dict):
                for k in list(b.outputs.keys()):
                    b.outputs[k] = []  # or None

            # if you track a simple flag per port or have a method to flip UI state:
            if hasattr(b, "set_all_ports_connected"):
                try:
                    b.set_all_ports_connected(False)
                except Exception:
                    pass
            # (optional) if your port items change color when disconnected, do it here

        # optional: mark dirty
        if hasattr(self, "modified"):
            self.modified.emit()

    def sync_io_to_connections(self):
        """Force backend IO maps to match current visible connections."""
        # 1) Clear every block's inputs/outputs
        for b in self.blocks:
            if hasattr(b, "inputs") and isinstance(b.inputs, dict):
                for k in list(b.inputs.keys()):
                    b.inputs[k] = []    # or None if that's your schema
            if hasattr(b, "outputs") and isinstance(b.outputs, dict):
                for k in list(b.outputs.keys()):
                    b.outputs[k] = []

        # 2) Rebuild from self.connections
        for conn in self.connections:
            src = conn.start_block
            dst = conn.end_block

            # Use a stable identifier (prefer id, fallback to name)
            src_id = getattr(src, "id", getattr(src, "name", id(src)))
            dst_id = getattr(dst, "id", getattr(dst, "name", id(dst)))

            # If you have port names, add conn.src_port / conn.dst_port here.
            if hasattr(dst, "inputs") and isinstance(dst.inputs, dict):
                dst.inputs.setdefault("default", []).append({"src_block_id": src_id})
            if hasattr(src, "outputs") and isinstance(src.outputs, dict):
                src.outputs.setdefault("default", []).append({"dst_block_id": dst_id})
