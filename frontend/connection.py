from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem, QMenu
from PyQt6.QtGui import QPen, QColor, QPolygonF, QAction
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QGraphicsPathItem, QMenu
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtGui import QPainterPath

import math


class ConnectionLine(QGraphicsPathItem):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(5)
        self.setPen(QPen(QColor("black"), 3, Qt.PenStyle.SolidLine))

    def contextMenuEvent(self, event):
        print("📌 Right-clicked on connection path")
        menu = QMenu()
        delete_action = QAction("Delete Connection")
        menu.addAction(delete_action)
        delete_action.triggered.connect(self.connection.remove)
        menu.exec(event.globalPosition().toPoint())

class Connection:
    def __init__(self, start_block, end_block, scene):
        self.start_block = start_block
        self.end_block = end_block
        self.scene = scene

        # Line
        self.line = ConnectionLine(self)
        self.line.setPen(QPen(QColor("black"), 4))

        self.line.setZValue(0)
        self.scene.addItem(self.line)

        # Arrowhead
        self.arrow = QGraphicsPolygonItem()
        self.arrow.setBrush(QColor("black"))
        self.arrow.setPen(QPen(QColor("black")))
        self.arrow.setZValue(1)
        self.scene.addItem(self.arrow)

        # Register connection
        self.start_block.outgoing_connections.append(self)
        self.end_block.incoming_connections.append(self)

        self.update_line()

  
    def update_line(self):
        start = self.start_block.output_anchor()
        end = self.end_block.input_anchor()

        # Mid x point between start and end
        mid_x = (start.x() + end.x()) / 2

        # Build orthogonal path: H → V → H
        path = QPainterPath(start)

        corner_radius = 20  # radius for rounded turns

        # First horizontal
        path.lineTo(mid_x - corner_radius, start.y())

        # First curve down
        path.quadTo(mid_x, start.y(), mid_x, start.y() + (end.y() - start.y()) / 2)

        # Second curve to end y
        path.quadTo(mid_x, end.y(), mid_x + corner_radius, end.y())

        # Final horizontal to endpoint
        path.lineTo(end)

        self.line.setPath(path)

        # Arrow goes on the last segment (horizontal)
        self.update_arrow(QPointF(mid_x + corner_radius, end.y()), end)

    def update_arrow(self, start: QPointF, end: QPointF):
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)

        length = 12
        spread = math.pi / 8

        p1 = end
        p2 = QPointF(
            end.x() - length * math.cos(angle - spread),
            end.y() - length * math.sin(angle - spread)
        )
        p3 = QPointF(
            end.x() - length * math.cos(angle + spread),
            end.y() - length * math.sin(angle + spread)
        )

        polygon = QPolygonF([p1, p2, p3])
        self.arrow.setPolygon(polygon)


    def remove(self):
        # Unregister from blocks
        if self in self.start_block.outgoing_connections:
            self.start_block.outgoing_connections.remove(self)
        if self in self.end_block.incoming_connections:
            self.end_block.incoming_connections.remove(self)

        # Remove from scene
        self.scene.removeItem(self.line)
        self.scene.removeItem(self.arrow)

        # Optional: remove from canvas.connections
        if hasattr(self.scene, "canvas") and hasattr(self.scene.canvas, "connections"):
            if self in self.scene.canvas.connections:
                self.scene.canvas.connections.remove(self)
