from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QCheckBox,
    QPushButton, QListWidget, QListWidgetItem, QHBoxLayout, QInputDialog, QComboBox
)
from PyQt6.QtGui import QTextCursor
import re
from io_mapper import IOMapperDialog

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy


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

        # =================== Variable Definition Section ===================
        self.layout.addWidget(QLabel("Define Variables:"))
        self.variable_definitions = []
        self.variable_list_layout = QVBoxLayout()
        self.layout.addLayout(self.variable_list_layout)

        self.add_variable_button = QPushButton("➕ Add Variable")
        self.add_variable_button.clicked.connect(self.add_variable_row)
        self.layout.addWidget(self.add_variable_button)

        # Show code checkbox + output
        self.show_code_checkbox = QCheckBox("Show Generated Code")
        self.show_code_checkbox.toggled.connect(self.update_generated_code)
        self.layout.addWidget(self.show_code_checkbox)

        self.generated_code_output = QTextEdit()
        self.generated_code_output.setReadOnly(True)
        self.generated_code_output.hide()
        self.load_from_block()
        self.layout.addWidget(self.generated_code_output)

    # =================== Variable UI ===================

    def add_variable_row(self, name="", value="", var_type="int"):
        row_layout = QHBoxLayout()

        name_input = QLineEdit()
        value_input = QLineEdit()

        type_dropdown = QComboBox()
        type_dropdown.addItems(["int", "float", "str", "bool", "None"])
        type_index = type_dropdown.findText(var_type)
        type_dropdown.setCurrentIndex(type_index if type_index != -1 else 0)

        delete_btn = QPushButton("❌")
        delete_btn.setFixedWidth(30)

        def validate_value():
            typ = type_dropdown.currentText()
            val = value_input.text().strip()

            try:
                if typ == "int":
                    int(val)
                elif typ == "float":
                    float(val)
                elif typ == "bool":
                    if val.lower() not in {"true", "false"}:
                        raise ValueError
                elif typ == "str":
                    str(val)
                elif typ == "None":
                    pass
                value_input.setStyleSheet("")  # Clear error styling
                value_input.setToolTip("")
            except Exception:
                value_input.setStyleSheet("border: 2px solid red;")
                value_input.setToolTip(f"Invalid {typ} value")

        # Connect triggers
        value_input.editingFinished.connect(validate_value)
        type_dropdown.currentTextChanged.connect(validate_value)

        row_layout.addWidget(name_input)
        row_layout.addWidget(value_input)
        row_layout.addWidget(type_dropdown)
        row_layout.addWidget(delete_btn)

        container = QWidget()
        container.setLayout(row_layout)
        self.variable_list_layout.addWidget(container)

        self.variable_definitions.append((container, name_input, value_input, type_dropdown))
        delete_btn.clicked.connect(lambda: self.remove_variable_row(container))

        # Run initial validation
        validate_value()

    def remove_variable_row(self, container):
        for i, (row, *_rest) in enumerate(self.variable_definitions):
            if row == container:
                self.variable_list_layout.removeWidget(row)
                row.deleteLater()
                self.variable_definitions.pop(i)
                break
        self.update_generated_code()

    def update_generated_code(self):
        if self.show_code_checkbox.isChecked():
            self.generated_code_output.show()
            self.generated_code_output.setPlainText(self.generate_variable_code())
        else:
            self.generated_code_output.hide()

    def generate_variable_code(self):
        code_lines = []
        for _, name_input, value_input, type_dropdown in self.variable_definitions:
            var = name_input.text().strip()
            val = value_input.text().strip()
            typ = type_dropdown.currentText()

            if var and val:
                if typ == "None":
                    code_lines.append(f"outputs.{var} = {val}")
                elif typ == "str":
                    code_lines.append(f"outputs.{var} = str('{val}')")
                else:
                    code_lines.append(f"outputs.{var} = {typ}({val})")
        return "\n".join(code_lines)

    # =================== Other UI ==================

    def save_changes(self):
        self.update_generated_code()
        # Update the block name and its tab
        self.block.name = self.name_input.text()
        self.tab_widget.setTabText(self.tab_widget.indexOf(self), self.block.name)

        # Generate code from variable definitions and store it
        generated_code = self.generate_variable_code()
        self.block.code = generated_code

        # Since this is a variable-defining block, inputs will always be empty
        self.block.inputs = InputsProxy()

        # Extract output variable names from the generated code
        output_matches = re.findall(r"\boutputs\.([a-zA-Z_][a-zA-Z0-9_]*)", generated_code)
        outputs = list(dict.fromkeys(output_matches))  # deduplicate

        # Update the block's outputs
        self.block.outputs = OutputsProxy()
        self.block.outputs.set_names(outputs)

        # Redraw block
        self.block.update()

    def load_from_block(self):
        code = self.block.code.strip()
        if not code:
            return

        pattern = r"^outputs\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:(int|float|str|bool)\((.+?)\)|(.+))$"
        for line in code.splitlines():
            match = re.match(pattern, line.strip())
            if match:
                var_name = match.group(1)
                var_type = match.group(2)
                value = match.group(3) if match.group(3) is not None else match.group(4)

                if var_type is None:
                    var_type = "None"
                if var_type == "str":
                    value = value.strip("'\"")  # remove surrounding quotes

                self._add_loaded_variable(var_name, value, var_type)

    def _add_loaded_variable(self, name, value, var_type):
        row_layout = QHBoxLayout()

        name_input = QLineEdit(name)
        value_input = QLineEdit(value)

        type_dropdown = QComboBox()
        type_dropdown.addItems(["int", "float", "str", "bool", "None"])
        type_index = type_dropdown.findText(var_type)
        if type_index != -1:
            type_dropdown.setCurrentIndex(type_index)

        delete_btn = QPushButton("❌")
        delete_btn.setFixedWidth(30)

        row_layout.addWidget(name_input)
        row_layout.addWidget(value_input)
        row_layout.addWidget(type_dropdown)
        row_layout.addWidget(delete_btn)

        container = QWidget()
        container.setLayout(row_layout)
        self.variable_list_layout.addWidget(container)

        self.variable_definitions.append((container, name_input, value_input, type_dropdown))
        delete_btn.clicked.connect(lambda: self.remove_variable_row(container))

