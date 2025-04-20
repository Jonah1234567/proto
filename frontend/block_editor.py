from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog
)
import re

class BlockEditor(QWidget):
    def __init__(self, block, tab_widget):
        super().__init__()
        self.block = block
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Block Name:"))
        self.name_input = QLineEdit(block.name)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("Code:"))
        self.code_input = QTextEdit("def run():\n    pass")
        self.layout.addWidget(self.code_input)

        self.layout.addWidget(QLabel("Inputs:"))
        self.input_list = QListWidget()
        self.layout.addWidget(self.input_list)


        self.layout.addWidget(QLabel("Outputs:"))
        self.output_list = QListWidget()
        self.layout.addWidget(self.output_list)

    def add_input(self):
        text, ok = QInputDialog.getText(self, "New Input", "Input name:")
        if ok and text:
            self.input_list.addItem(QListWidgetItem(text))

    def add_output(self):
        text, ok = QInputDialog.getText(self, "New Output", "Output name:")
        if ok and text:
            self.output_list.addItem(QListWidgetItem(text))

    def save_changes(self):
        self.block.name = self.name_input.text()
        self.block.label.setPlainText(self.block.name)
        self.tab_widget.setTabText(self.tab_widget.indexOf(self), self.block.name)

        code = self.code_input.toPlainText()

        inputs = []
        match = re.search(r"def\s+\w+\((.*?)\)", code)
        if match:
            args = match.group(1)
            inputs = [arg.strip() for arg in args.split(",") if arg.strip()]

        outputs = []
        return_match = re.search(r"return\s+(.*)", code)
        if return_match:
            raw_out = return_match.group(1)
            outputs = [out.strip() for out in raw_out.split(",") if out.strip()]

        self.input_list.clear()
        for inp in inputs:
            self.input_list.addItem(inp)

        self.output_list.clear()
        for out in outputs:
            self.output_list.addItem(out)

        self.block.inputs = inputs
        self.block.outputs = outputs
