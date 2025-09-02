# connection.py
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem, QMenu
from PyQt6.QtGui import QPen, QColor, QPolygonF, QAction, QCursor
from PyQt6.QtCore import QPointF, Qt
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
        menu.exec(QCursor.pos())

class Connection:
    def __init__(self, start_block, end_block, canvas_or_scene):
        self.start_block = start_block
        self.end_block = end_block

        # Accept either a Canvas or a QGraphicsScene
        if hasattr(canvas_or_scene, "scene"):         # looks like a Canvas
            self.canvas = canvas_or_scene
            self.scene = canvas_or_scene.scene
        else:                                         # assume QGraphicsScene
            self.scene = canvas_or_scene
            # try to recover canvas if attached (see Canvas.__init__ 1-liner)
            self.canvas = getattr(self.scene, "canvas", None)

        # create graphics etc.
        self.line = ConnectionLine(self)
        self.line.setPen(QPen(QColor("black"), 4))
        self.line.setZValue(0)
        self.scene.addItem(self.line)

        self.arrow = QGraphicsPolygonItem()
        self.arrow.setBrush(QColor("black"))
        self.arrow.setPen(QPen(QColor("black")))
        self.arrow.setZValue(1)
        self.scene.addItem(self.arrow)

        self.start_block.outgoing_connections.append(self)
        self.end_block.incoming_connections.append(self)
        self.update_line()

    def update_line(self):
        start = self.start_block.output_anchor()
        end = self.end_block.input_anchor()

        path = QPainterPath(start)
        corner_radius = 20
        mid_x = (start.x() + end.x()) / 2

        path.lineTo(mid_x - corner_radius, start.y())
        path.quadTo(mid_x, start.y(), mid_x, start.y() + (end.y() - start.y()) / 2)
        path.quadTo(mid_x, end.y(), mid_x + corner_radius, end.y())
        path.lineTo(end)

        self.line.setPath(path)
        self.update_arrow(QPointF(mid_x + corner_radius, end.y()), end)

    def update_arrow(self, start: QPointF, end: QPointF):
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        length = 12
        spread = math.pi / 8
        p1 = end
        p2 = QPointF(end.x() - length * math.cos(angle - spread),
                     end.y() - length * math.sin(angle - spread))
        p3 = QPointF(end.x() - length * math.cos(angle + spread),
                     end.y() - length * math.sin(angle + spread))
        self.arrow.setPolygon(QPolygonF([p1, p2, p3]))

    def remove(self):
        # 1) unregister from blocks’ connection lists
        if self in self.start_block.outgoing_connections:
            self.start_block.outgoing_connections.remove(self)
        if self in self.end_block.incoming_connections:
            self.end_block.incoming_connections.remove(self)

        # 2) detach backend wiring on destination
        if hasattr(self.end_block, "detach_input_from"):
            self.end_block.detach_input_from(self.start_block)
        else:
            # Fallbacks if you didn’t add the helper:
            if hasattr(self.end_block, "inputs_proxy") and hasattr(self.end_block.inputs_proxy, "disconnect_from"):
                self.end_block.inputs_proxy.disconnect_from(self.start_block)
            if hasattr(self.end_block, "inputs") and isinstance(self.end_block.inputs, dict):
                for k, v in list(self.end_block.inputs.items()):
                    if isinstance(v, list):
                        self.end_block.inputs[k] = [m for m in v if m.get("src_block") is not self.start_block]

        # 3) remove graphics
        self.scene.removeItem(self.line)
        self.scene.removeItem(self.arrow)

        # 4) remove from canvas model
        if self.canvas and self in self.canvas.connections:
            self.canvas.connections.remove(self)

        # 5) notify canvas to rebuild overall wiring/caches
        if hasattr(self.canvas, "graphChanged"):
            self.canvas.graphChanged.emit()
        elif hasattr(self.canvas, "rebuild_wiring"):
            self.canvas.rebuild_wiring()

        print(self.start_block.id)
        self.end_block.input_mappings = {}

        # 6) modified flag
        if hasattr(self.canvas, "modified"):
            self.canvas.modified.emit()
