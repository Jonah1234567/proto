from PyQt6.QtWidgets import (
    QGraphicsObject, QGraphicsTextItem, QGraphicsEllipseItem, QMenu, QGraphicsItem, QListWidget, QTextEdit
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QAction, QPainterPath
from PyQt6.QtCore import QRectF, QPointF, Qt
from block_editor import BlockEditor
import uuid
from PyQt6.QtWidgets import QMenu

class Block(QGraphicsObject):
    def __init__(self, name, tab_widget):
        super().__init__()
        
        self.id = str(uuid.uuid4())  # assign unique ID

        
        self.name = name
        self.code = ""
        self.input_list = []
        self.output_list = []

        self.tab_widget = tab_widget
        self.width = 140
        self.height = 70
        self._dragging = False
        self._drag_offset = QPointF()
        self.incoming_connections = []
        self.outgoing_connections = []
        self.is_start_block = False



        self.setAcceptHoverEvents(True)

        # Create input/output ports
        self.input_port = self._create_port(-7, self.height / 2 - 7, "Input")
        self.output_port = self._create_port(self.width - 7, self.height / 2 - 7, "Output")
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)


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
        if self.isSelected():
            painter.setPen(QPen(QColor("#d63031"), 3))  # red border
        else:
            painter.setPen(QPen(QColor("#0984e3"), 2))  # default

        if self.is_start_block:
            painter.setPen(QPen(QColor("green"), 3))

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
        
         # If Shift or Ctrl are NOT pressed, clear selection
        if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier or
                event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            scene = self.scene()
            if scene:
                scene.clearSelection()

        # Let Qt handle selection and movement
        super().mousePressEvent(event)
        
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
        set_start_action = QAction("Set as Start Block")
        set_start_action.triggered.connect(self.mark_as_start_block)
        menu.addAction(set_start_action)
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
        scene = self.scene()
        if not scene:
            return

        # Remove all connections attached to this block
        all_connections = self.incoming_connections + self.outgoing_connections
        for conn in all_connections:
            conn.remove()  # This will remove it from the scene and from the canvas list

        # Remove this block from the scene
        scene.removeItem(self)

        # Optional: cleanup internal lists (not strictly necessary)
        self.incoming_connections.clear()
        self.outgoing_connections.clear()


    def input_anchor(self) -> QPointF:
        return self.mapToScene(self.input_port.rect().center() + self.input_port.pos())

    def output_anchor(self) -> QPointF:
        return self.mapToScene(self.output_port.rect().center() + self.output_port.pos())
    
    def itemChange(self, change, value):
        if change == QGraphicsObject.GraphicsItemChange.ItemPositionHasChanged:
            for conn in self.incoming_connections + self.outgoing_connections:
                conn.update_line()
        return super().itemChange(change, value)

    def mark_as_start_block(self):
        for item in self.scene().items():
            if isinstance(item, Block):
                item.is_start_block = False
                item.update()
        self.is_start_block = True
        self.update()


    def shape(self):
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, 10, 10)
        return path


    
    

