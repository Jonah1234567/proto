from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsObject
from PyQt6.QtGui import QPainter, QColor, QWheelEvent, QPen
from PyQt6.QtCore import Qt, QPointF
from block import Block
from connection import Connection


class Canvas(QGraphicsView):
    def __init__(self, tab_widget):
        super().__init__()

        self.tab_widget = tab_widget
        self.blocks = []
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

        self._panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())

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
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
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


    def cancel_connection(self):
        self._clear_temp_line()

    def _clear_temp_line(self):
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        self.connection_start = None
