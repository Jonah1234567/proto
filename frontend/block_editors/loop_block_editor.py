from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QHBoxLayout, QComboBox, QMessageBox
)
import re
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))


class LoopBlockEditor(QWidget):
    def __init__(self, block, tab_widget):
        super().__init__()
        self.block = block
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Block Name:"))
        self.name_input = QLineEdit(block.name)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("Loop Condition and Type:"))

        # ========== Loop Condition Row ==========
        loop_row = QHBoxLayout()
        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("e.g., i in range(5), item in items, x < 10")
        loop_row.addWidget(self.condition_input)

        self.loop_type_selector = QComboBox()
        self.loop_type_selector.addItems([
            "for i in range(...)", 
            "for item in collection", 
            "while condition"
        ])
        loop_row.addWidget(self.loop_type_selector)

        self.layout.addLayout(loop_row)

        # ========== Loop Body ==========
        self.layout.addWidget(QLabel("Loop Body Code:"))
        self.code_input = QTextEdit()
        self.layout.addWidget(self.code_input)

        # ========== Buttons ==========
        self.save_button = QPushButton("💾 Save and Show Generated Code")
        self.save_button.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_button)

        self.generated_code_output = QTextEdit()
        self.generated_code_output.setReadOnly(True)
        self.layout.addWidget(self.generated_code_output)

        # === Load existing code ===
        self.load_from_block()

    def generate_loop_code(self):
        loop_type = self.loop_type_selector.currentText()
        condition = self.condition_input.text().strip()
        body_code = self.code_input.toPlainText().strip()

        if not condition:
            QMessageBox.warning(self, "Missing Condition", "Please enter a loop condition.")
            return None

        if not body_code:
            QMessageBox.warning(self, "Missing Loop Body", "Please enter code to execute inside the loop.")
            return None

        # Generate loop header
        if loop_type == "for i in range(...)":
            header = f"for {condition}:"
        elif loop_type == "for item in collection":
            header = f"for {condition}:"
        elif loop_type == "while condition":
            header = f"while {condition}:"
        else:
            header = "# Unsupported loop type"

        # Indent body
        body_lines = [f"    {line}" for line in body_code.splitlines()]
        return "\n".join([header] + body_lines)

    def save_changes(self):
        self.block.name = self.name_input.text()
        self.tab_widget.setTabText(self.tab_widget.indexOf(self), self.block.name)

        full_code = self.generate_loop_code()
        if full_code is None:
            return

        self.block.code = full_code
        self.generated_code_output.setPlainText(full_code)

        # Extract inputs/outputs from the code
        input_matches = re.findall(r"\binputs\.([a-zA-Z_][a-zA-Z0-9_]*)", full_code)
        output_matches = re.findall(r"\boutputs\.([a-zA-Z_][a-zA-Z0-9_]*)", full_code)

        inputs = list(dict.fromkeys(input_matches))
        outputs = list(dict.fromkeys(output_matches))

        self.block.inputs = InputsProxy()
        self.block.outputs = OutputsProxy()

        self.block.inputs.set_names(inputs)
        self.block.outputs.set_names(outputs)
        self.block.update()

    def load_from_block(self):
        code = self.block.code.strip()
        if not code:
            return

        lines = code.splitlines()
        if not lines:
            return

        header = lines[0].strip()
        body_lines = lines[1:]
        body_code = "\n".join([line.strip() for line in body_lines])

        if header.startswith("for ") and "in range" in header:
            self.loop_type_selector.setCurrentText("for i in range(...)")
        elif header.startswith("for ") and "in " in header:
            self.loop_type_selector.setCurrentText("for item in collection")
        elif header.startswith("while "):
            self.loop_type_selector.setCurrentText("while condition")

        condition = header.split(" ", 1)[1].rstrip(":").strip()
        self.condition_input.setText(condition)
        self.code_input.setPlainText(body_code)

