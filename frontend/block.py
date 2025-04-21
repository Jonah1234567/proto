from PyQt6.QtWidgets import (
    QGraphicsObject, QGraphicsTextItem, QGraphicsEllipseItem, QMenu, QGraphicsItem
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QAction
from PyQt6.QtCore import QRectF, QPointF, Qt
from block_editor import BlockEditor


class Block(QGraphicsObject):
    def __init__(self, name, tab_widget):
        super().__init__()
        self.name = name
        self.tab_widget = tab_widget
        self.width = 140
        self.height = 70
        self._dragging = False
        self._drag_offset = QPointF()
        self.incoming_connections = []
        self.outgoing_connections = []


        self.setAcceptHoverEvents(True)

        # Create input/output ports
        self.input_port = self._create_port(-7, self.height / 2 - 7, "Input")
        self.output_port = self._create_port(self.width - 7, self.height / 2 - 7, "Output")
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def _create_port(self, x, y, tooltip):
        port = QGraphicsEllipseItem(x, y, 14, 14, self)
        port.setToolTip(tooltip)
        port.setBrush(QBrush(QColor("black")))
        port.setPen(QPen(QColor("black")))

        # Critical for interaction
        port.setAcceptHoverEvents(True)
        port.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        port.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, False)
        port.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)
        port.setZValue(10)

        return port

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        # Draw the block background
        painter.setBrush(QBrush(QColor("#74b9ff")))
        painter.setPen(QPen(QColor("#0984e3"), 2))
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)

        # Draw the block name
        painter.setPen(QColor("black"))
        painter.drawText(10, 25, self.name)

    def mousePressEvent(self, event):
        pos = event.pos()

        # Prevent drag if clicking on a port
        if self.input_port.contains(pos - self.input_port.pos()) or \
           self.output_port.contains(pos - self.output_port.pos()):
            event.ignore()
            return

        # Start dragging
        self._dragging = True
        self._drag_offset = event.pos()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.pos() - self._drag_offset
            self.setPos(self.pos() + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("Edit Block")
        delete_action = QAction("Delete Block")
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        edit_action.triggered.connect(self.open_editor)
        delete_action.triggered.connect(self.delete_block)
        menu.exec(event.screenPos())

    def open_editor(self):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == self.name:
                self.tab_widget.setCurrentIndex(i)
                return
        editor = BlockEditor(self, self.tab_widget)
        self.tab_widget.addTab(editor, self.name)
        self.tab_widget.setCurrentWidget(editor)

    def delete_block(self):
        if scene := self.scene():
            scene.removeItem(self)

    def input_anchor(self) -> QPointF:
        return self.mapToScene(self.input_port.rect().center() + self.input_port.pos())

    def output_anchor(self) -> QPointF:
        return self.mapToScene(self.output_port.rect().center() + self.output_port.pos())
    
    def itemChange(self, change, value):
        if change == QGraphicsObject.GraphicsItemChange.ItemPositionHasChanged:
            for conn in self.incoming_connections + self.outgoing_connections:
                conn.update_line()
        return super().itemChange(change, value)

    
    

