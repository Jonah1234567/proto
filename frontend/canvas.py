from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsObject
from PyQt6.QtGui import QPainter, QColor, QWheelEvent, QPen
from PyQt6.QtCore import Qt, QPointF
from block import Block
from connection import Connection
from connection import ConnectionLine
import json


class Canvas(QGraphicsView):
    def __init__(self, tab_widget):
        super().__init__()

        self.tab_widget = tab_widget
        self.blocks = []
        self.connections = []  # 🔗 Keep track of all connections

        self.connection_start = None
        self.temp_line = None

        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.setScene(self.scene)

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

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        print(f"Clicked item: {item}, type: {type(item)}")

        selected = self.scene.selectedItems()
        print(f"Selected items: {len(selected)}")

        def get_block_parent(i):
            while i and not isinstance(i, Block):
                i = i.parentItem()
            return i

        if event.button() == Qt.MouseButton.LeftButton:
            
            if isinstance(item, QGraphicsEllipseItem):
                parent = get_block_parent(item)
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
                block = get_block_parent(item)
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

    def add_block(self):
        name = f"Block {len(self.blocks) + 1}"
        block = Block(name, self.tab_widget)
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)

    def create_connection(self, start_block, end_block):
        print(f"📍 Drawing connection from {start_block.name} to {end_block.name}")
        connection = Connection(start_block, end_block, self.scene)
        self.connections.append(connection)

    def cancel_connection(self):
        self._clear_temp_line()

    def _clear_temp_line(self):
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        self.connection_start = None

    def save_layout(self, filename):
        data = {
            "blocks": [],
            "connections": []
        }

        for block in self.blocks:
            data["blocks"].append({
                "id": block.id,
                "name": block.name,
                "x": block.pos().x(),
                "y": block.pos().y(),
                "code": getattr(block, "code", ""),
                "inputs": getattr(block, "inputs", []),
                "outputs": getattr(block, "outputs", []),
                "is_start_block": getattr(block, "is_start_block", False)
            })

        for conn in self.connections:
            data["connections"].append({
                "start_block": conn.start_block.id,
                "end_block": conn.end_block.id
            })

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Layout saved to {filename}")

    def load_layout(self, filename):
        with open(filename, "r") as f:
            data = json.load(f)

        # Clear current layout
        for block in self.blocks:
            self.scene.removeItem(block)
        for conn in self.connections:
            conn.remove()
        self.blocks.clear()
        self.connections.clear()

        # Recreate blocks
        id_to_block = {}
        for block_data in data["blocks"]:
            block = Block(block_data["name"], self.tab_widget)
            block.id = block_data["id"]
            block.code = block_data.get("code", "")
            block.inputs = block_data.get("inputs", [])
            block.outputs = block_data.get("outputs", [])
            block.is_start_block = block_data.get("is_start_block", False)
            block.setPos(block_data["x"], block_data["y"])
            self.scene.addItem(block)
            self.blocks.append(block)
            id_to_block[block.id] = block

        # Recreate connections
        for conn_data in data["connections"]:
            start = id_to_block.get(conn_data["start_block"])
            end = id_to_block.get(conn_data["end_block"])
            if start and end:
                conn = Connection(start, end, self.scene)
                self.connections.append(conn)


