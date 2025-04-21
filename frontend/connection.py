from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem, QMenu
from PyQt6.QtGui import QPen, QColor, QPolygonF, QAction
from PyQt6.QtCore import QPointF
import math


class ConnectionLine(QGraphicsLineItem):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = QAction("Delete Connection")
        menu.addAction(delete_action)
        delete_action.triggered.connect(self.connection.remove)
        menu.exec(event.screenPos())


class Connection:
    def __init__(self, start_block, end_block, scene):
        self.start_block = start_block
        self.end_block = end_block
        self.scene = scene

        # Line
        self.line = ConnectionLine(self)
        self.line.setPen(QPen(QColor("black"), 2))
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
        self.line.setLine(start.x(), start.y(), end.x(), end.y())

        self.update_arrow(start, end)

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
