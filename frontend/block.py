from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtWidgets import QMenu, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtGui import QAction

class Block(QGraphicsItem):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.width = 140
        self.height = 70

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.label = QGraphicsTextItem(name, self)
        self.label.setDefaultTextColor(QColor("black"))
        self.label.setPos(10, 10)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._drag_offset = QPointF()
        self._dragging = False

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setBrush(QBrush(QColor("#74b9ff")))
        pen_color = QColor("#d63031") if self.isSelected() else QColor("#0984e3")
        painter.setPen(QPen(pen_color, 2))
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.scene().clearSelection()
            self.setSelected(True)
            self._dragging = True
            self._drag_offset = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self.isSelected():
            new_pos = event.scenePos() - self._drag_offset
            self.setPos(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        super().mouseReleaseEvent(event)

    def center(self) -> QPointF:
        return self.pos() + QPointF(self.width / 2, self.height / 2)
    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("Edit Block")
        menu.addAction(edit_action)
        edit_action.triggered.connect(self.open_editor)
        menu.exec(event.screenPos())

    def open_editor(self):
        dialog = QDialog()
        dialog.setWindowTitle(f"Edit {self.name}")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Block Name:"))
        name_input = QLineEdit(self.name)
        layout.addWidget(name_input)

        save_button = QPushButton("Save")
        layout.addWidget(save_button)

        def save_changes():
            self.name = name_input.text()
            self.label.setPlainText(self.name)
            dialog.accept()

        save_button.clicked.connect(save_changes)
        dialog.setLayout(layout)
        dialog.exec()
