from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
import re
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))


class ConditionalBlockEditor(QWidget):
    def __init__(self, block, tab_widget):
        super().__init__()
        self.block = block
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Block Name:"))
        self.name_input = QLineEdit(block.name)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("Conditional Logic:"))
        self.condition_blocks = []
        self.condition_block_layout = QVBoxLayout()
        self.layout.addLayout(self.condition_block_layout)

        # Add default IF block
        self.add_condition_block("if")

        # Add Elif button
        self.add_elif_button = QPushButton("➕ Add Elif Block")
        self.add_elif_button.clicked.connect(lambda: self.add_condition_block("elif"))
        self.layout.addWidget(self.add_elif_button)

        # Add Else block
        self.else_label = QLabel("else:")
        self.else_code = QTextEdit()
        self.condition_block_layout.addWidget(self.else_label)
        self.condition_block_layout.addWidget(self.else_code)

        # Save and Show Code button
        self.show_code_button = QPushButton("💾 Save and Show Generated Code")
        self.show_code_button.clicked.connect(self.save_changes)
        self.layout.addWidget(self.show_code_button)

        self.generated_code_output = QTextEdit()
        self.generated_code_output.setReadOnly(True)
        self.layout.addWidget(self.generated_code_output)

        self.load_from_block()

    def add_condition_block(self, block_type, condition="", code=""):
        block_widget = QWidget()
        row_layout = QVBoxLayout(block_widget)

        label = QLabel(f"{block_type} condition:")
        condition_input = QLineEdit(condition)
        code_input = QTextEdit()
        code_input.setPlainText(code)

        row_layout.addWidget(label)
        row_layout.addWidget(condition_input)
        row_layout.addWidget(code_input)

        # Insert before the else: section (which is the last 2 widgets in layout)
        insert_index = self.condition_block_layout.count() - 2
        self.condition_block_layout.insertWidget(insert_index, block_widget)

        self.condition_blocks.append({
            "type": block_type,
            "condition_input": condition_input,
            "code_input": code_input,
            "widget": block_widget
        })

    def save_changes(self):
        self.block.name = self.name_input.text()
        self.tab_widget.setTabText(self.tab_widget.indexOf(self), self.block.name)

        code_lines = []
        for block in self.condition_blocks:
            cond_type = block["type"]
            condition = block["condition_input"].text().strip()
            code = block["code_input"].toPlainText().strip()

            if not condition:
                QMessageBox.warning(self, "Missing Condition", f"{cond_type} condition is empty.")
                return

            code_lines.append(f"{cond_type} {condition}:")
            for line in code.splitlines():
                code_lines.append(f"    {line}")

        # Add else
        else_code = self.else_code.toPlainText().strip()
        code_lines.append("else:")
        for line in else_code.splitlines():
            code_lines.append(f"    {line}")

        full_code = "\n".join(code_lines)
        self.block.code = full_code
        self.generated_code_output.setPlainText(full_code)

        # Extract input/output names
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
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("if ") or line.startswith("elif "):
                cond_type = "if" if line.startswith("if ") else "elif"
                condition = line[len(cond_type):].rstrip(":").strip()
                code_block = []
                i += 1
                while i < len(lines) and lines[i].startswith("    "):
                    code_block.append(lines[i].strip())
                    i += 1
                self.add_condition_block(cond_type, condition, "\n".join(code_block))
            elif line.startswith("else:"):
                else_block = []
                i += 1
                while i < len(lines) and lines[i].startswith("    "):
                    else_block.append(lines[i].strip())
                    i += 1
                self.else_code.setPlainText("\n".join(else_block))
            else:
                i += 1
