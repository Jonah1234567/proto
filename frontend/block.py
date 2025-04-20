from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog, QMenu
)
import re

class Block(QGraphicsItem):
    def __init__(self, name, tab_widget):
        super().__init__()
        self.name = name
        self.tab_widget = tab_widget
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

    def open_editor(self, save_changes):
        tab_widget = self.tab_widget

        # Avoid duplicate tabs
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == self.name:
                tab_widget.setCurrentIndex(i)
                return

        editor = QWidget()
        layout = QVBoxLayout(editor)

        # Block Name
        layout.addWidget(QLabel("Block Name:"))
        name_input = QLineEdit(self.name)
        name_input.setStyleSheet("color: black;")
        layout.addWidget(name_input)

        # Code Editor
        layout.addWidget(QLabel("Code:"))
        code_input = QTextEdit("def run():\n    pass")  # Replace with your actual block code
        code_input.setStyleSheet("color: black;")
        layout.addWidget(code_input)

        # Inputs
        layout.addWidget(QLabel("Inputs:"))
        input_list = QListWidget()
        input_list.setStyleSheet("color: black;")
        layout.addWidget(input_list)

        add_input_btn = QPushButton("+ Add Input")
        add_input_btn.setStyleSheet("color: black;")
        layout.addWidget(add_input_btn)

        def add_input():
            text, ok = QInputDialog.getText(editor, "New Input", "Input name:")
            if ok and text:
                item = QListWidgetItem(text)
                input_list.addItem(item)

        add_input_btn.clicked.connect(add_input)

        # Outputs
        layout.addWidget(QLabel("Outputs:"))
        output_list = QListWidget()
        output_list.setStyleSheet("color: black;")
        layout.addWidget(output_list)

        add_output_btn = QPushButton("+ Add Output")
        add_output_btn.setStyleSheet("color: black;")
        layout.addWidget(add_output_btn)

        def add_output():
            text, ok = QInputDialog.getText(editor, "New Output", "Output name:")
            if ok and text:
                item = QListWidgetItem(text)
                output_list.addItem(item)

        add_output_btn.clicked.connect(add_output)

        # Save Button
        save_button = QPushButton("Save")
        layout.addWidget(save_button)

        def save_changes():
            # === Update block name ===
            self.name = name_input.text()
            self.label.setPlainText(self.name)
            tab_widget.setTabText(tab_widget.indexOf(editor), self.name)

            # === Get code ===
            code = code_input.toPlainText()

            # === Extract inputs from def line ===
            inputs = []
            match = re.search(r"def\s+\w+\((.*?)\)", code)
            if match:
                args = match.group(1)
                inputs = [arg.strip() for arg in args.split(",") if arg.strip()]

            # === Extract outputs from return statement ===
            outputs = []
            return_match = re.search(r"return\s+(.*)", code)
            if return_match:
                raw_out = return_match.group(1)
                outputs = [out.strip() for out in raw_out.split(",") if out.strip()]

            # === Refresh Inputs List ===
            input_list.clear()
            for inp in inputs:
                input_list.addItem(inp)

            # === Refresh Outputs List ===
            output_list.clear()
            for out in outputs:
                output_list.addItem(out)

            # Store for use later
            self.inputs = inputs
            self.outputs = outputs

        editor.save_changes = save_changes
        save_button.clicked.connect(save_changes)
        
        # Add to tab widget
        tab_widget.addTab(editor, self.name)
        tab_widget.setCurrentWidget(editor)