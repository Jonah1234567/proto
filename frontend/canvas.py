from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPainter, QColor, QWheelEvent
from PyQt6.QtCore import Qt, QPointF
from block import Block

class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create the scene with a huge virtual space
        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.setScene(self.scene)

        # Zoom & pan config
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Scrollbars hidden
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Outline for canvas (optional, using style)
        self.setStyleSheet("border: 2px solid #dcdde1;")

        # Panning state
        self._panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
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
        block = Block(name)
        block.setPos(50 + len(self.blocks) * 20, 100)
        self.scene.addItem(block)
        self.blocks.append(block)